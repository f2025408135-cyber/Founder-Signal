"""Test FastAPI routes — spec §10 B8.

Tests run WITHOUT a live Postgres (we use a stub async session) so they work
in any environment. The full DB-backed round-trip is verified in the
integration test (test_pipeline.py).
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure backend/ is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Test env
os.environ["APP_ENV"] = "test"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["GITHUB_TOKEN"] = ""
os.environ["PRODUCTHUNT_TOKEN"] = ""
os.environ["LANGFUSE_ENABLED"] = "false"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://vcbrain:vcbrain@localhost:5432/vcbrain"
os.environ["DATABASE_SYNC_URL"] = "postgresql://vcbrain:vcbrain@localhost:5432/vcbrain"

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client with all routes mounted."""
    from app.main import app
    return TestClient(app)


def test_health_endpoint(client):
    """GET /health returns ok."""
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"


def test_ping_endpoint(client):
    """GET /api/ping returns pong=True."""
    r = client.get("/api/ping")
    assert r.status_code == 200
    assert r.json() == {"pong": True}


def test_openapi_lists_all_required_endpoints(client):
    """Spec §10 B8: OpenAPI docs at /docs list all 7 endpoints."""
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    # 7 spec-required endpoints + supporting routes
    required = [
        "/api/applications",
        "/api/applications/inbox",
        "/api/founders/{founder_id}/card",
        "/api/founders/{founder_id}/memo",
        "/api/thesis",
        "/api/outbound/scan",
        "/api/query",
    ]
    for path in required:
        assert path in paths, f"Missing required endpoint: {path}"

    # Also check supporting routes from spec §9.2 + §10 B10
    supporting = [
        "/api/outbound/queue",
        "/api/traces/{run_id}",
        "/api/admin/latency",
    ]
    for path in supporting:
        assert path in paths, f"Missing supporting endpoint: {path}"


def test_post_applications_returns_202(client):
    """POST /applications returns 202 with founder_id (spec §10 B8)."""
    payload = {
        "founder_name": "Jane Doe",
        "founder_email": f"jane-{uuid.uuid4().hex[:8]}@example.com",
        "founder_bio_text": "ML engineer working on LLM evaluation.",
        "company_name": "TestCo",
        "company_website_url": "https://example.com",
        "github_repo_slugs": [],
        "accelerator": None,
        "hq_country": "DE",
        "sector_self_reported": "AI infra",
    }
    # We expect the request to fail at DB write (no Postgres) but we
    # patch the DB session to return successfully.
    with patch("app.api.routes.applications.async_session") as mock_session_cm:
        # Build a mock that yields a session-like object
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))))
        mock_session.get = AsyncMock(return_value=None)

        @asynccontextmanager
        async def _fake_session():
            yield mock_session

        mock_session_cm.side_effect = _fake_session

        # Also patch get_db dependency
        from app.deps import get_db
        async def _fake_get_db():
            yield mock_session
        app_dep_override = client.app.dependency_overrides
        app_dep_override[get_db] = _fake_get_db

        # Also patch the background task so it doesn't actually run
        with patch("app.api.routes.applications._run_pipeline_background", new=AsyncMock()):
            r = client.post("/api/applications", json=payload)

    # Clean up
    client.app.dependency_overrides.clear()

    assert r.status_code == 202, f"Expected 202, got {r.status_code}: {r.text}"
    body = r.json()
    assert "founder_id" in body or "id" in body
    assert body["status"] == "pending"


from contextlib import asynccontextmanager


def test_get_thesis_returns_default(client):
    """GET /api/thesis returns the default Maschmeyer thesis when none exists."""
    from app.deps import get_db
    from datetime import datetime

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))))
    mock_session.commit = AsyncMock()
    mock_session.flush = AsyncMock()
    # Simulate the row getting refreshed with timestamps after commit
    def _refresh_side_effect(obj, **kw):
        if hasattr(obj, "created_at") and obj.created_at is None:
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()
        return None
    mock_session.refresh = AsyncMock(side_effect=_refresh_side_effect)
    mock_session.add = MagicMock()
    mock_session.get = AsyncMock(return_value=None)

    async def _fake_get_db():
        yield mock_session

    client.app.dependency_overrides[get_db] = _fake_get_db
    try:
        r = client.get("/api/thesis")
    finally:
        client.app.dependency_overrides.clear()

    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Maschmeyer Group — AI Infra & DevTools"
    assert body["check_size_usd"] == 100000
    assert "AI infra" in body["sectors"]


def test_get_traces_returns_stub_when_langfuse_unconfigured(client):
    """GET /api/traces/{run_id} returns a stub when Langfuse is not configured."""
    r = client.get("/api/traces/some-run-id")
    assert r.status_code == 200
    body = r.json()
    assert body["trace_id"] == "some-run-id"
    assert body["available"] is False


def test_admin_latency_returns_structure(client):
    """GET /api/admin/latency returns the expected p50/p95 structure."""
    from app.deps import get_db

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
    mock_session.get = AsyncMock(return_value=None)

    async def _fake_get_db():
        yield mock_session

    client.app.dependency_overrides[get_db] = _fake_get_db
    try:
        r = client.get("/api/admin/latency?hours=24")
    finally:
        client.app.dependency_overrides.clear()

    assert r.status_code == 200
    body = r.json()
    assert "phases" in body
    for phase in ["ingestion", "validator", "scoring", "aggregator", "end_to_end"]:
        assert phase in body["phases"]
        assert "p50_seconds" in body["phases"][phase]
        assert "p95_seconds" in body["phases"][phase]


def test_query_endpoint_decomposes_and_searches(client):
    """POST /api/query accepts a compound query and returns matches."""
    from app.deps import get_db

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))))
    mock_session.get = AsyncMock(return_value=None)

    async def _fake_get_db():
        yield mock_session

    client.app.dependency_overrides[get_db] = _fake_get_db

    # Mock the LLM call
    with patch("app.api.routes.query.llm_client.chat_complete_json", new=AsyncMock(return_value={"attributes": ["technical", "Berlin", "AI infra"]})):
        try:
            r = client.post("/api/query", json={"query": "technical founder, Berlin, AI infra"})
        finally:
            client.app.dependency_overrides.clear()

    assert r.status_code == 200
    body = r.json()
    assert body["query"] == "technical founder, Berlin, AI infra"
    assert body["decomposed_attributes"] == ["technical", "Berlin", "AI infra"]
    assert isinstance(body["matches"], list)


def test_outbound_queue_returns_empty_list_when_no_signals(client):
    """GET /api/outbound/queue returns total=0 when no signals exist."""
    from app.deps import get_db

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
    mock_session.get = AsyncMock(return_value=None)

    async def _fake_get_db():
        yield mock_session

    client.app.dependency_overrides[get_db] = _fake_get_db
    try:
        r = client.get("/api/outbound/queue")
    finally:
        client.app.dependency_overrides.clear()

    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert body["founders"] == []
