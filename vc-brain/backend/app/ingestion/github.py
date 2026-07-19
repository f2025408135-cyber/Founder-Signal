"""GitHub ingestion — REST + GraphQL with ETag conditional requests.

Per spec §6.1:
- Auth: GITHUB_TOKEN env var
- REST rate limit: 5000/hr auth (bucket = 5000 tokens, refill 5000/3600 per sec)
- GraphQL rate limit: 5000 points/hr
- ETag conditional requests return 304 (don't count against quota)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.config import settings
from app.db.models import GithubEtagCache
from app.db.session import async_session
from app.schemas.claim import Source, SourceKind
from app.utils.hashing import hash_json
from app.utils.ratelimit import TokenBucket

logger = logging.getLogger(__name__)

GITHUB_TOKEN = settings.github_token
REST_BASE = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"

# Authenticated REST: 5000/hr ≈ 1.39 req/s sustained. Bucket of 5000 refilling per hour.
bucket = TokenBucket(capacity=5000, refill_per_second=5000 / 3600)


def _headers() -> dict[str, str]:
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "VC-Brain/1.0",
    }
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


async def get_etag(repo_slug: str) -> str | None:
    """Read cached ETag for a repo (or None if not cached)."""
    async with async_session() as s:
        row = await s.get(GithubEtagCache, repo_slug)
        return row.etag if row else None


async def set_etag(repo_slug: str, etag: str | None, status: int | None = None) -> None:
    """Upsert ETag + last_status for a repo."""
    async with async_session() as s:
        stmt = pg_insert(GithubEtagCache).values(
            repo_slug=repo_slug, etag=etag, last_status=status
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[GithubEtagCache.repo_slug],
            set_={
                "etag": stmt.excluded.etag,
                "last_fetched_at": datetime.utcnow(),
                "last_status": stmt.excluded.last_status,
            },
        )
        await s.execute(stmt)
        await s.commit()


async def fetch_github_signals(repo_slug: str) -> list[dict]:
    """Returns list of {source, content} dicts ready for Ingestion Agent.

    Uses ETag conditional requests to conserve quota on repeat fetches.
    """
    if not GITHUB_TOKEN:
        logger.warning("GITHUB_TOKEN not set — GitHub ingestion will be skipped for %s", repo_slug)
        return []

    out: list[dict] = []
    headers = _headers()
    async with httpx.AsyncClient(timeout=15, headers=headers) as c:
        # 1. repo metadata with ETag
        etag = await get_etag(repo_slug)
        req_headers = {"If-None-Match": etag} if etag else {}
        await bucket.acquire()
        try:
            r = await c.get(f"{REST_BASE}/repos/{repo_slug}", headers=req_headers)
        except Exception as e:
            logger.warning("github fetch repos/%s failed: %s", repo_slug, e)
            return out

        if r.status_code == 304:
            await set_etag(repo_slug, etag, status=304)
            return out  # cache hit, no new claims
        if r.status_code == 404:
            logger.info("github repo %s not found", repo_slug)
            return out
        r.raise_for_status()
        if "ETag" in r.headers:
            await set_etag(repo_slug, r.headers["ETag"], status=r.status_code)

        data = r.json()
        source = Source(
            kind=SourceKind.GITHUB,
            ref=repo_slug,
            ingested_at=datetime.utcnow(),
            raw_payload_hash=hash_json(data),
            retrieved_by="github.fetch_github_signals",
        )
        out.append(
            {
                "source": source,
                "content": {
                    "stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                    "language": data.get("language"),
                    "created_at": data.get("created_at"),
                    "pushed_at": data.get("pushed_at"),
                    "description": data.get("description"),
                    "topics": data.get("topics", []),
                    "owner": data.get("owner", {}).get("login") if isinstance(data.get("owner"), dict) else None,
                    "open_issues": data.get("open_issues_count", 0),
                },
            }
        )

        # 2. contributors (depth signal)
        await bucket.acquire()
        try:
            r2 = await c.get(
                f"{REST_BASE}/repos/{repo_slug}/contributors", params={"per_page": 30}
            )
            if r2.status_code == 200:
                contribs = r2.json()
                out.append(
                    {
                        "source": source,
                        "content": {
                            "contributors": [
                                {"login": x["login"], "contributions": x["contributions"]}
                                for x in contribs
                                if isinstance(x, dict) and "login" in x
                            ],
                            "contributor_count": len(contribs),
                        },
                    }
                )
        except Exception as e:
            logger.warning("github fetch contributors for %s failed: %s", repo_slug, e)

        # 3. recent commits (momentum)
        await bucket.acquire()
        try:
            r3 = await c.get(
                f"{REST_BASE}/repos/{repo_slug}/commits", params={"per_page": 30}
            )
            if r3.status_code == 200:
                commits = r3.json()
                commit_dates = [
                    c["commit"]["author"]["date"]
                    for c in commits
                    if isinstance(c, dict) and "commit" in c
                ]
                cutoff = datetime.now(timezone.utc) - timedelta(days=30)
                commits_30d = sum(
                    1
                    for d in commit_dates
                    if _parse_iso(d) >= cutoff
                )
                out.append(
                    {
                        "source": source,
                        "content": {
                            "recent_commit_dates": commit_dates,
                            "commit_count_30d": commits_30d,
                        },
                    }
                )
        except Exception as e:
            logger.warning("github fetch commits for %s failed: %s", repo_slug, e)
    return out


def _parse_iso(s: str) -> datetime:
    """Parse an ISO 8601 timestamp with optional Z suffix."""
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


# GraphQL bulk query — used by outbound scan when fetching many repos
BULK_QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    stargazerCount
    forkCount
    primaryLanguage { name }
    pushedAt
    createdAt
    description
    repositoryTopics(first: 10) { nodes { topic { name } } }
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 30) {
            nodes { committedDate author { user { login } } }
          }
        }
      }
    }
  }
}
"""


async def fetch_github_graphql(owner: str, name: str) -> dict:
    """Single GraphQL call replaces 3 REST calls — 1 point vs 3 req from quota."""
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN not set")
    await bucket.acquire()
    async with httpx.AsyncClient(timeout=15, headers=_headers()) as c:
        r = await c.post(
            GRAPHQL_URL,
            json={"query": BULK_QUERY, "variables": {"owner": owner, "name": name}},
        )
        r.raise_for_status()
        return r.json()["data"]["repository"]


def split_slug(slug: str) -> tuple[str, str]:
    """Split 'owner/repo' into (owner, repo). Raises ValueError on bad input."""
    parts = slug.strip("/").split("/")
    if len(parts) != 2:
        raise ValueError(f"Bad repo slug: {slug}")
    return parts[0], parts[1]
