"""Hacker News ingestion — Algolia Search API + Firebase top stories.

Per spec §6.3:
- Auth: none
- Rate limit: undocumented — use responsibly (~1 req/s)
- Algolia: historical search, up to 1000 hits/call
- Firebase: live top stories
"""
from __future__ import annotations

import logging
from datetime import datetime

import httpx

from app.schemas.claim import Source, SourceKind
from app.utils.hashing import hash_json
from app.utils.ratelimit import TokenBucket

logger = logging.getLogger(__name__)

ALGOLIA_SEARCH = "https://hn.algolia.com/api/v1/search"
FIREBASE_TOP = "https://hacker-news.firebaseio.com/v0/topstories.json"

# ~1 req/s sustained
bucket = TokenBucket(capacity=5, refill_per_second=1.0)


async def fetch_hn_stories(query: str, tags: str = "story") -> list[dict]:
    """Historical search via Algolia. Use for company/founder name lookups.

    Returns list of {source, content} dicts.
    """
    out: list[dict] = []
    await bucket.acquire()
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(
                ALGOLIA_SEARCH,
                params={"query": query, "tags": tags, "hitsPerPage": 50},
            )
            r.raise_for_status()
            hits = r.json().get("hits", [])
    except Exception as e:
        logger.warning("hn algolia fetch failed for query=%r: %s", query, e)
        return out

    for hit in hits:
        try:
            content = {
                "title": hit.get("title"),
                "url": hit.get("url"),
                "points": hit.get("points", 0),
                "num_comments": hit.get("num_comments", 0),
                "created_at": hit.get("created_at"),
                "author": hit.get("author"),
                "object_id": hit.get("objectID"),
            }
            source = Source(
                kind=SourceKind.HACKERNEWS,
                ref=f"item:{hit['objectID']}",
                ingested_at=datetime.utcnow(),
                raw_payload_hash=hash_json(content),
                retrieved_by="hackernews.fetch_hn_stories",
            )
            out.append({"source": source, "content": content})
        except Exception as e:
            logger.warning("hn hit parse failed: %s", e)
            continue
    return out


async def fetch_hn_topstories() -> list[int]:
    """Live top stories via Firebase. Used by outbound scan for signal detection."""
    await bucket.acquire()
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(FIREBASE_TOP)
            r.raise_for_status()
            return r.json()[:100]  # top 100 only
    except Exception as e:
        logger.warning("hn firebase topstories fetch failed: %s", e)
        return []


async def fetch_hn_item(item_id: int) -> dict | None:
    """Fetch a single HN item via Firebase. Used by outbound scan."""
    await bucket.acquire()
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json")
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning("hn firebase item %s fetch failed: %s", item_id, e)
        return None
