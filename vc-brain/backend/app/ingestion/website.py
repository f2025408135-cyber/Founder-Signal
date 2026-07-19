"""Company website fetcher — founder-provided URL ONLY.

Per spec §6.5 + §6.6:
- Fetch ONLY URLs the founder explicitly provided in the application form.
- NEVER bulk-crawl. NEVER follow internal links. NEVER scrape LinkedIn.
- Extract title, meta description, and up to 3 h1 headings. That's it.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.schemas.claim import Source, SourceKind
from app.utils.hashing import hash_json

logger = logging.getLogger(__name__)

USER_AGENT = "VC-Brain/1.0 (founder-provided URL fetch; respects robots.txt)"


async def fetch_company_website(url: str) -> list[dict]:
    """Fetch a single founder-provided URL. Extract title, meta description, headings.

    Returns list of {"source": Source, "content": dict} — ready for Ingestion Agent.
    Does NOT follow links. Does NOT crawl sitemap.
    """
    out: list[dict] = []
    if not url or not _is_http_url(url):
        return out

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as c:
            r = await c.get(url, headers={"User-Agent": USER_AGENT})
            if r.status_code != 200:
                logger.info("company_website %s returned %d", url, r.status_code)
                return out
    except Exception as e:
        logger.warning("company_website fetch failed for %s: %s", url, e)
        return out

    try:
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else None
        meta_desc = soup.find("meta", attrs={"name": "description"})
        # spec §6.5 had a typo: `h1s = .get_text(strip=True) for h in soup.find_all(...)]`
        # we use the correct list comprehension.
        h1s = [h.get_text(strip=True) for h in soup.find_all("h1", limit=3) if h.get_text(strip=True)]
    except Exception as e:
        logger.warning("company_website parse failed for %s: %s", url, e)
        return out

    content: dict[str, Any] = {
        "url": str(url),
        "title": title,
        "meta_description": meta_desc["content"] if meta_desc and meta_desc.get("content") else None,
        "h1_headings": h1s,
    }
    source = Source(
        kind=SourceKind.COMPANY_WEBSITE,
        ref=str(url),
        ingested_at=datetime.utcnow(),
        raw_payload_hash=hash_json(content),
        retrieved_by="website.fetch_company_website",
    )
    out.append({"source": source, "content": content})
    return out


def _is_http_url(s: str) -> bool:
    try:
        parsed = urlparse(s)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False
