"""Test re-scoring trigger logic — spec §10 B7 + §8.

A second invocation within 60 min returns reason="cache_hit" and does NOT invoke
any LLM; an invocation after a new Application insert returns reason="new_application"
and re-runs the pipeline.
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["APP_ENV"] = "test"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["GITHUB_TOKEN"] = ""
os.environ["PRODUCTHUNT_TOKEN"] = ""
os.environ["LANGFUSE_ENABLED"] = "false"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://vcbrain:vcbrain@localhost:5432/vcbrain"
os.environ["DATABASE_SYNC_URL"] = "postgresql://vcbrain:vcbrain@localhost:5432/vcbrain"


@pytest.mark.asyncio
async def test_should_rescore_no_prior_score():
    """Trigger #3: no prior score exists → returns (True, 'no_prior_score')."""
    from app.triggers.rescore import should_rescore

    # Mock async_session to return empty results
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=None)
    # select().execute().scalars().first() -> None
    mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None), all=MagicMock(return_value=[])))))

    with patch("app.triggers.rescore.async_session") as mock_cm:
        @asynccontextmanager
        async def _fake():
            yield mock_session
        mock_cm.side_effect = _fake

        should, reason = await should_rescore(uuid.uuid4(), None)
    assert should is True
    assert reason == "no_prior_score"


from contextlib import asynccontextmanager


@pytest.mark.asyncio
async def test_should_rescore_new_application():
    """Trigger #1: new application within TTL → returns (True, 'new_application')."""
    from app.triggers.rescore import should_rescore

    app_id = uuid.uuid4()
    mock_app = MagicMock()
    mock_app.received_at = datetime.utcnow()  # within TTL

    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=mock_app)
    mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None), all=MagicMock(return_value=[])))))

    should, reason = await should_rescore(uuid.uuid4(), app_id, session=mock_session)
    assert should is True
    assert reason == "new_application"


@pytest.mark.asyncio
async def test_should_rescore_signal_threshold():
    """Trigger #2: external signal with conviction_delta > 5 → returns (True, 'signal_threshold_crossed')."""
    from app.triggers.rescore import should_rescore

    app_id = uuid.uuid4()
    # Application is OLD (outside TTL)
    mock_app = MagicMock()
    mock_app.received_at = datetime.utcnow() - timedelta(hours=2)

    # FounderSignal with delta > 5
    mock_signal = MagicMock()
    mock_signal.conviction_delta = 8.0
    mock_signal.detected_at = datetime.utcnow()  # recent

    # Prior score exists (recent)
    mock_score = MagicMock()
    mock_score.computed_at = datetime.utcnow() - timedelta(minutes=10)  # fresh

    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=mock_app)
    # First execute: signals query; second: last_score query
    sig_result = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_signal]))))
    score_result = MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_score))))
    mock_session.execute = AsyncMock(side_effect=[sig_result, score_result])

    should, reason = await should_rescore(uuid.uuid4(), app_id, session=mock_session)
    assert should is True
    assert reason == "signal_threshold_crossed"


@pytest.mark.asyncio
async def test_should_rescore_stale_cache_24h():
    """Trigger #4: last score older than 24h → returns (True, 'stale_cache_24h')."""
    from app.triggers.rescore import should_rescore

    app_id = uuid.uuid4()
    mock_app = MagicMock()
    mock_app.received_at = datetime.utcnow() - timedelta(hours=2)  # old app

    mock_score = MagicMock()
    mock_score.computed_at = datetime.utcnow() - timedelta(hours=30)  # > 24h

    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=mock_app)
    sig_result = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))
    score_result = MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_score))))
    mock_session.execute = AsyncMock(side_effect=[sig_result, score_result])

    should, reason = await should_rescore(uuid.uuid4(), app_id, session=mock_session)
    assert should is True
    assert reason == "stale_cache_24h"


@pytest.mark.asyncio
async def test_should_rescore_cache_hit():
    """No triggers fire → returns (False, 'cache_hit')."""
    from app.triggers.rescore import should_rescore

    app_id = uuid.uuid4()
    mock_app = MagicMock()
    mock_app.received_at = datetime.utcnow() - timedelta(hours=2)  # old app

    mock_score = MagicMock()
    mock_score.computed_at = datetime.utcnow() - timedelta(minutes=10)  # fresh

    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=mock_app)
    sig_result = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))
    score_result = MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_score))))
    mock_session.execute = AsyncMock(side_effect=[sig_result, score_result])

    should, reason = await should_rescore(uuid.uuid4(), app_id, session=mock_session)
    assert should is False
    assert reason == "cache_hit"
