"""Test the outbound scan script — spec §10 B9.

Verifies the script can be imported and its main function has the right signature.
Actual external API calls are mocked.
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Also add the project root (parent of backend/) so we can import scripts.run_outbound_scan
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

os.environ["APP_ENV"] = "test"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["GITHUB_TOKEN"] = ""
os.environ["PRODUCTHUNT_TOKEN"] = ""
os.environ["LANGFUSE_ENABLED"] = "false"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://vcbrain:vcbrain@localhost:5432/vcbrain"
os.environ["DATABASE_SYNC_URL"] = "postgresql://vcbrain:vcbrain@localhost:5432/vcbrain"


def test_outbound_scan_imports():
    """The outbound scan script can be imported without error."""
    from scripts.run_outbound_scan import run_outbound_scan
    assert callable(run_outbound_scan)


@pytest.mark.asyncio
async def test_outbound_scan_runs_with_no_thesis():
    """Outbound scan returns an error summary when no active thesis exists."""
    from scripts.run_outbound_scan import run_outbound_scan

    # Mock the DB session — no thesis found
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))))

    with patch("scripts.run_outbound_scan.async_session") as mock_cm:
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _fake():
            yield mock_session
        mock_cm.side_effect = _fake

        summary = await run_outbound_scan(lookback_hours=1)

    assert summary["error"] == "no_active_thesis"
    assert summary["signals_detected"] == 0


@pytest.mark.asyncio
async def test_outbound_scan_signal_type_to_channel_mapping():
    """Signal type → channel mapping is correct (spec §9.3)."""
    from scripts.run_outbound_scan import _signal_type_to_source_kind

    from app.schemas.claim import SourceKind

    assert _signal_type_to_source_kind("new_github_repo_high_growth") == SourceKind.GITHUB
    assert _signal_type_to_source_kind("new_arxiv_paper") == SourceKind.ARXIV
    assert _signal_type_to_source_kind("new_ph_launch") == SourceKind.PRODUCTHUNT
    assert _signal_type_to_source_kind("new_hn_post_above_threshold") == SourceKind.HACKERNEWS


@pytest.mark.asyncio
async def test_outbound_scan_records_signal_and_triggers_pipeline(founder_id, company_id):
    """A signal with conviction_delta > 5 triggers the pipeline."""
    # This is a heavier integration test — we mock the DB + pipeline.
    from scripts.run_outbound_scan import _record_signal

    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))))

    summary = {
        "founders_created": 0,
        "pipelines_triggered": 0,
        "by_channel": {"github": 0, "arxiv": 0, "ph": 0, "hn": 0},
    }

    signal = {
        "founder_name": "Test Founder",
        "company_name": "TestCo",
        "source_ref": "test/repo",
        "stars": 100,
        "description": "Test repo",
        "hq_country": "US",
        "sector_self_reported": "AI infra",
        "payload": {"slug": "test/repo", "stars": 100},
        "conviction_delta": 10.0,  # > 5 → triggers pipeline
    }

    with patch("scripts.run_outbound_scan.async_session") as mock_cm:
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _fake():
            yield mock_session
        mock_cm.side_effect = _fake

        # Mock the pipeline trigger task
        with patch("scripts.run_outbound_scan.asyncio.create_task") as mock_create_task:
            await _record_signal(signal, "new_github_repo_high_growth", summary)

    assert summary["founders_created"] == 1
    assert summary["pipelines_triggered"] == 1
    # asyncio.create_task was called once
    mock_create_task.assert_called_once()
