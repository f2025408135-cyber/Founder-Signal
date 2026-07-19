"""Product Hunt ingestion — GraphQL v2, OAuth Bearer token.

Per spec §6.4 (verified 2026-07-19):
- Two-layer limit: ~900 req / 15-min window + 1000 complexity points per query
- Headers: X-Rate-Limit-Remaining, X-Rate-Limit-Reset
- Hard cap at 200 results per scan to stay well under both limits
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.config import settings
from app.schemas.claim import Source, SourceKind
from app.utils.hashing import hash_json
from app.utils.ratelimit import TokenBucket

logger = logging.getLogger(__name__)

PH_TOKEN = settings.producthunt_token
PH_GQL = "https://api.producthunt.com/v2/api/graphql"

# ~900 req / 15 min = 1 req/s sustained. Use a conservative 0.8 req/s to stay safe.
bucket = TokenBucket(capacity=10, refill_per_second=0.8)

SEARCH_QUERY = """
query($query: String!, $cursor: String) {
  search(query: $query, type: POST, first: 20, after: $cursor) {
    edges {
      node {
        ... on Post {
          id
          slug
          name
          tagline
          votesCount
          website
          launchedAt
          topics { edges { node { name } } }
          makers { name username }
        }
      }
    }
    pageInfo { endCursor hasNextPage }
  }
}
"""


async def fetch_ph_launches(query: str, lookback_days: int = 365, max_pages: int = 10) -> list[dict]:
    """Search PH for launches matching company or founder name.

    Hard cap at 200 results to stay well under both rate-limit windows.
    """
    if not PH_TOKEN:
        logger.warning("PRODUCTHUNT_TOKEN not set — PH ingestion will be skipped for query=%r", query)
        return []

    headers = {"Authorization": f"Bearer {PH_TOKEN}"}
    out: list[dict] = []
    cursor: str | None = None
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)
    page = 0

    async with httpx.AsyncClient(timeout=15, headers=headers) as c:
        while page < max_pages and len(out) < 200:
            await bucket.acquire()
            try:
                r = await c.post(
                    PH_GQL,
                    json={"query": SEARCH_QUERY, "variables": {"query": query, "cursor": cursor}},
                )
                r.raise_for_status()
            except Exception as e:
                logger.warning("PH fetch failed for query=%r page=%d: %s", query, page, e)
                break

            # Inspect rate-limit headers
            remaining = r.headers.get("X-Rate-Limit-Remaining")
            if remaining is not None and int(remaining) < 50:
                logger.info("PH rate limit low (%s remaining) — stopping early", remaining)
                break

            try:
                data = r.json()["data"]["search"]
            except (KeyError, ValueError) as e:
                logger.warning("PH response parse failed: %s", e)
                break

            for edge in data.get("edges", []):
                node = edge.get("node") or {}
                launched_str = node.get("launchedAt")
                if launched_str:
                    try:
                        launched = datetime.fromisoformat(launched_str.replace("Z", "+00:00"))
                        if launched.replace(tzinfo=None) < cutoff:
                            continue
                    except ValueError:
                        pass
                content = _normalize_node(node)
                source = Source(
                    kind=SourceKind.PRODUCTHUNT,
                    ref=f"https://www.producthunt.com/posts/{node['slug']}" if node.get("slug") else f"post:{node.get('id', 'unknown')}",
                    ingested_at=datetime.utcnow(),
                    raw_payload_hash=hash_json(content),
                    retrieved_by="producthunt.fetch_ph_launches",
                )
                out.append({"source": source, "content": content})

            if not data.get("pageInfo", {}).get("hasNextPage"):
                break
            cursor = data["pageInfo"].get("endCursor")
            page += 1
    return out[:200]  # hard cap


def _normalize_node(node: dict[str, Any]) -> dict[str, Any]:
    """Flatten a PH GraphQL node into a serializable dict."""
    topics = []
    try:
        topics = [e["node"]["name"] for e in (node.get("topics", {}) or {}).get("edges", []) if e.get("node")]
    except Exception:
        pass
    makers = []
    for m in node.get("makers", []) or []:
        if isinstance(m, dict):
            makers.append({"name": m.get("name"), "username": m.get("username")})
    return {
        "id": node.get("id"),
        "slug": node.get("slug"),
        "name": node.get("name"),
        "tagline": node.get("tagline"),
        "votesCount": node.get("votesCount", 0),
        "website": node.get("website"),
        "launchedAt": node.get("launchedAt"),
        "topics": topics,
        "makers": makers,
    }
