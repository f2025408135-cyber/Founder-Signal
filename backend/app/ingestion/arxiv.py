"""arXiv ingestion — CC0, 1 req per 3s rate limit.

Per spec §6.2:
- Auth: none (CC0)
- Rate limit: 1 request per 3 seconds (Terms of Use)
- Pagination: batch 20-50 records per query
- Query syntax: 'au:"Jane Doe"' for author, 'ti:transformer' for title, 'cat:cs.AI' for category
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from xml.etree import ElementTree as ET

import httpx

from app.schemas.claim import Source, SourceKind
from app.utils.hashing import hash_json
from app.utils.ratelimit import TokenBucket

logger = logging.getLogger(__name__)

ARXIV_API = "http://export.arxiv.org/api/query"
# 1 req per 3s per arxiv Terms of Use
bucket = TokenBucket(capacity=1, refill_per_second=1 / 3)

NAMESPACES = {"atom": "http://www.w3.org/2005/Atom"}
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


async def fetch_arxiv_papers(query: str, max_results: int = 20) -> list[dict]:
    """Search arXiv. Query syntax: 'au:"Jane Doe"' for author, 'ti:transformer' for title.

    Returns list of {source, content} dicts ready for Ingestion Agent.
    """
    out: list[dict] = []
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    await bucket.acquire()
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(ARXIV_API, params=params)
            r.raise_for_status()
    except Exception as e:
        logger.warning("arxiv fetch failed for query=%r: %s", query, e)
        return out

    try:
        root = ET.fromstring(r.text)
    except ET.ParseError as e:
        logger.warning("arxiv XML parse failed: %s", e)
        return out

    for entry in root.findall("atom:entry", NAMESPACES):
        try:
            id_el = entry.find("atom:id", NAMESPACES)
            title_el = entry.find("atom:title", NAMESPACES)
            summary_el = entry.find("atom:summary", NAMESPACES)
            published_el = entry.find("atom:published", NAMESPACES)
            if id_el is None or title_el is None:
                continue

            arxiv_id = id_el.text.split("/abs/")[-1]
            title = title_el.text.strip().replace("\n", " ") if title_el.text else ""
            summary = (
                summary_el.text.strip().replace("\n", " ") if summary_el is not None and summary_el.text else ""
            )
            published = published_el.text if published_el is not None else None
            authors = [
                a.find("atom:name", NAMESPACES).text
                for a in entry.findall("atom:author", NAMESPACES)
                if a.find("atom:name", NAMESPACES) is not None and a.find("atom:name", NAMESPACES).text
            ]
            categories = [
                c.get("term")
                for c in entry.findall(f"{ARXIV_NS}primary_category")
                if c.get("term")
            ]
            entry_data = {
                "arxiv_id": arxiv_id,
                "title": title,
                "summary": summary,
                "published": published,
                "authors": authors,
                "categories": categories,
            }
            source = Source(
                kind=SourceKind.ARXIV,
                ref=arxiv_id,
                ingested_at=datetime.utcnow(),
                raw_payload_hash=hash_json(entry_data),
                retrieved_by="arxiv.fetch_arxiv_papers",
            )
            out.append({"source": source, "content": entry_data})
        except Exception as e:
            logger.warning("arxiv entry parse failed: %s", e)
            continue
    return out


async def fetch_arxiv_for_author(author_name: str, max_results: int = 10) -> list[dict]:
    """Convenience wrapper — searches by author name in quotes."""
    # arxiv au: query syntax
    query = f'au:"{author_name}"'
    return await fetch_arxiv_papers(query, max_results=max_results)
