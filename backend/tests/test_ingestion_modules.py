"""Test the ingestion modules — spec §6.1-6.5 + §10 A4.

A unit-test fixture (sample deck PDF + sample GitHub repo slug + sample arxiv query)
produces >=5 Claim records with correct source.kind, source.ref, source.raw_payload_hash.

NOTE: these tests don't hit real external APIs — they use mocked HTTP responses.
"""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_website_fetch_extracts_title_and_h1s():
    """fetch_company_website extracts title, meta description, h1 headings."""
    from unittest.mock import AsyncMock, patch

    from app.ingestion.website import fetch_company_website

    fake_html = """
    <html>
    <head>
      <title>Acme AI — Infra for LLMs</title>
      <meta name="description" content="Acme builds developer tooling for LLM eval.">
    </head>
    <body>
      <h1>Acme AI</h1>
      <h1>Build reliable LLM apps</h1>
    </body>
    </html>
    """

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=type("R", (), {
        "status_code": 200,
        "text": fake_html,
    })())):
        out = await fetch_company_website("https://acme.ai")

    assert len(out) == 1
    content = out[0]["content"]
    assert content["title"] == "Acme AI — Infra for LLMs"
    assert "LLM eval" in content["meta_description"]
    assert "Acme AI" in content["h1_headings"]
    assert "Build reliable LLM apps" in content["h1_headings"]


@pytest.mark.asyncio
async def test_website_fetch_rejects_non_http_url():
    """Non-HTTP URLs are rejected (empty list returned)."""
    from app.ingestion.website import fetch_company_website

    out = await fetch_company_website("not-a-url")
    assert out == []

    out = await fetch_company_website("ftp://example.com/file")
    assert out == []


@pytest.mark.asyncio
async def test_website_fetch_handles_404():
    """404 returns empty list — no exception raised."""
    from unittest.mock import AsyncMock, patch

    from app.ingestion.website import fetch_company_website

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=type("R", (), {
        "status_code": 404,
        "text": "",
    })())):
        out = await fetch_company_website("https://example.com/notfound")
    assert out == []


@pytest.mark.asyncio
async def test_github_fetch_parses_repo_metadata(monkeypatch):
    """fetch_github_signals returns source+content dicts with correct fields."""
    from unittest.mock import AsyncMock, patch

    from app.ingestion import github as gh

    # Skip rate limiting
    async def _no_wait(self, tokens=1.0):
        return None

    monkeypatch.setattr(gh.bucket, "acquire", _no_wait.__get__(gh.bucket, gh.bucket.__class__))

    # Mock get_etag / set_etag
    async def _no_etag(slug):
        return None

    async def _set_etag(slug, etag, status=None):
        return None

    monkeypatch.setattr(gh, "get_etag", _no_etag)
    monkeypatch.setattr(gh, "set_etag", _set_etag)

    fake_repo_resp = type("R", (), {
        "status_code": 200,
        "headers": {"ETag": "abc"},
        "json": lambda self: {
            "stargazers_count": 850,
            "forks_count": 92,
            "language": "Python",
            "created_at": "2024-01-01T00:00:00Z",
            "pushed_at": "2026-07-10T00:00:00Z",
            "description": "AI infra tool",
            "topics": ["ai-infra"],
            "owner": {"login": "bobsmith"},
            "open_issues_count": 23,
        },
        "raise_for_status": lambda self: None,
    })()
    fake_contrib_resp = type("R", (), {
        "status_code": 200,
        "json": lambda self: [{"login": "bob", "contributions": 100}],
        "raise_for_status": lambda self: None,
    })()
    fake_commits_resp = type("R", (), {
        "status_code": 200,
        "json": lambda self: [{"commit": {"author": {"date": "2026-07-15T00:00:00Z"}}}] * 10,
        "raise_for_status": lambda self: None,
    })()

    # Patch GITHUB_TOKEN so we don't skip
    monkeypatch.setattr(gh, "GITHUB_TOKEN", "fake-token")

    call_count = [0]

    async def _fake_get(self, url, **kwargs):
        call_count[0] += 1
        if "contributors" in url:
            return fake_contrib_resp
        if "commits" in url:
            return fake_commits_resp
        return fake_repo_resp

    with patch("httpx.AsyncClient.get", new=_fake_get):
        # Patch the headers check too — httpx.AsyncClient(...).get is what we hit
        out = await gh.fetch_github_signals("bobsmith/ai-infra-tool")

    assert len(out) >= 1
    # First item is the repo metadata
    repo_item = out[0]
    assert repo_item["source"].kind.value == "github"
    assert repo_item["source"].ref == "bobsmith/ai-infra-tool"
    assert repo_item["content"]["stars"] == 850
    assert repo_item["content"]["language"] == "Python"
    assert repo_item["source"].raw_payload_hash  # non-empty


@pytest.mark.asyncio
async def test_github_no_token_returns_empty(monkeypatch):
    """Without GITHUB_TOKEN, fetch_github_signals returns []."""
    from app.ingestion import github as gh

    monkeypatch.setattr(gh, "GITHUB_TOKEN", "")
    out = await gh.fetch_github_signals("any/repo")
    assert out == []


@pytest.mark.asyncio
async def test_arxiv_fetch_parses_xml():
    """fetch_arxiv_papers parses Atom XML correctly."""
    from unittest.mock import AsyncMock, patch

    from app.ingestion import arxiv

    fake_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2401.12345</id>
        <title>Efficient Inference for Large Language Models</title>
        <summary>We propose a novel method.</summary>
        <published>2026-01-15T00:00:00Z</published>
        <author><name>Bob Smith</name></author>
        <author><name>Alice Lee</name></author>
      </entry>
      <entry>
        <id>http://arxiv.org/abs/2401.67890</id>
        <title>Another Paper</title>
        <summary>Another summary.</summary>
        <published>2026-02-01T00:00:00Z</published>
        <author><name>Carol Wu</name></author>
      </entry>
    </feed>"""

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=type("R", (), {
        "status_code": 200,
        "text": fake_xml,
        "raise_for_status": lambda self: None,
    })())):
        out = await arxiv.fetch_arxiv_papers("au:Bob Smith", max_results=5)

    assert len(out) == 2
    first = out[0]
    assert first["source"].kind.value == "arxiv"
    assert first["source"].ref == "2401.12345"
    assert first["content"]["title"] == "Efficient Inference for Large Language Models"
    assert "Bob Smith" in first["content"]["authors"]
    assert first["source"].raw_payload_hash


@pytest.mark.asyncio
async def test_hackernews_fetch_parses_algolia_response():
    """fetch_hn_stories parses Algolia hits."""
    from unittest.mock import AsyncMock, patch

    from app.ingestion import hackernews as hn

    fake_resp = {
        "hits": [
            {
                "objectID": "12345",
                "title": "Show HN: My AI startup",
                "url": "https://example.com",
                "points": 150,
                "num_comments": 23,
                "created_at": "2026-07-01T00:00:00Z",
                "author": "founder123",
            }
        ]
    }

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=type("R", (), {
        "status_code": 200,
        "json": lambda self: fake_resp,
        "raise_for_status": lambda self: None,
    })())):
        out = await hn.fetch_hn_stories("AI startup")

    assert len(out) == 1
    assert out[0]["source"].kind.value == "hackernews"
    assert out[0]["source"].ref == "item:12345"
    assert out[0]["content"]["points"] == 150
    assert out[0]["source"].raw_payload_hash


@pytest.mark.asyncio
async def test_producthunt_no_token_returns_empty(monkeypatch):
    """Without PRODUCTHUNT_TOKEN, fetch_ph_launches returns []."""
    from app.ingestion import producthunt as ph

    monkeypatch.setattr(ph, "PH_TOKEN", "")
    out = await ph.fetch_ph_launches("test query")
    assert out == []


@pytest.mark.asyncio
async def test_producthunt_hard_cap_200(monkeypatch):
    """PH fetch never returns more than 200 results (spec §6.4)."""
    from unittest.mock import AsyncMock, patch

    from app.ingestion import producthunt as ph

    monkeypatch.setattr(ph, "PH_TOKEN", "fake-token")

    # Build a response that always returns 20 edges with hasNextPage=True
    fake_edges = []
    for i in range(20):
        fake_edges.append({
            "node": {
                "id": f"post-{i}",
                "name": f"Launch {i}",
                "tagline": "tag",
                "votesCount": 100 + i,
                "website": "https://example.com",
                "launchedAt": "2026-06-01T00:00:00Z",
                "topics": {"edges": []},
                "makers": [],
            }
        })

    async def _fake_post(self, url, **kwargs):
        return type("R", (), {
            "status_code": 200,
            "headers": {},
            "raise_for_status": lambda self: None,
            "json": lambda self: {"data": {"search": {
                "edges": fake_edges,
                "pageInfo": {"endCursor": "abc", "hasNextPage": True},
            }}},
        })()

    with patch("httpx.AsyncClient.post", new=_fake_post):
        out = await ph.fetch_ph_launches("test", max_pages=20)

    assert len(out) <= 200, f"Hard cap violated: got {len(out)} results"
