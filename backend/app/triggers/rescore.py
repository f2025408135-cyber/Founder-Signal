"""Re-scoring trigger logic — spec §8.

Principle: the pipeline is expensive (multiple LLM calls + external API fetches).
Card/memo views are cheap. We re-run the pipeline only when genuinely new
information arrives; we serve cached output otherwise.

Cache TTL: 60 minutes. Within 60 min of the last AggregatorOutput, card/memo
views return the cache without invoking any LLM.

Re-score triggers (any one fires a re-run):
1. New application received from this founder (Application.received_at within TTL window).
2. New external signal with conviction_delta > 5 detected by the outbound scan cron.
3. No prior score exists for this founder (first time we see them).
4. Last score is older than 24 hours (stale-cache sweep).

Cache-hit (do NOT re-run):
- Card/memo view request, no new application, no threshold-crossing signal, last score < 60 min old.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import (
    AggregatorOutputORM,
    Application as ApplicationORM,
    CachedAggregator,
    FounderSignalORM,
    FounderScoreSnapshot,
)
from app.db.session import async_session
from app.schemas.agent_outputs import AggregatorOutput

logger = logging.getLogger(__name__)

RESCORE_CACHE_TTL_MINUTES = settings.rescore_cache_ttl_minutes
STALE_CACHE_HOURS = settings.stale_cache_hours


async def should_rescore(
    founder_id: uuid.UUID,
    application_id: Optional[uuid.UUID],
    session: Optional[AsyncSession] = None,
) -> tuple[bool, str]:
    """Decide whether to re-run the full pipeline or serve cached AggregatorOutput.

    Returns (rescore: bool, reason: str).

    Reasons:
      - "new_application": trigger #1
      - "signal_threshold_crossed": trigger #2
      - "no_prior_score": trigger #3
      - "stale_cache_24h": trigger #4
      - "cache_hit": no trigger fired
      - "cache_miss": TTL expired but no trigger fired (rare)
    """
    now = datetime.utcnow()
    ttl_cutoff = now - timedelta(minutes=RESCORE_CACHE_TTL_MINUTES)
    stale_cutoff = now - timedelta(hours=STALE_CACHE_HOURS)

    async def _check(s: AsyncSession) -> tuple[bool, str]:
        # 1. New application within TTL window? (spec §8 trigger 1: "New application
        # received FROM THIS FOUNDER" — we check ALL the founder's applications,
        # not just the passed-in application_id.)
        app_q = (
            select(ApplicationORM)
            .where(
                ApplicationORM.founder_id == founder_id,
                ApplicationORM.received_at >= ttl_cutoff,
            )
            .order_by(desc(ApplicationORM.received_at))
            .limit(1)
        )
        recent_app = (await s.execute(app_q)).scalars().first()
        if recent_app is not None:
            return True, "new_application"

        # 2. New external signal crossing conviction threshold (>5)?
        sig_q = (
            select(FounderSignalORM)
            .where(
                FounderSignalORM.founder_id == founder_id,
                FounderSignalORM.detected_at >= ttl_cutoff,
            )
            .order_by(desc(FounderSignalORM.detected_at))
        )
        recent_signals = (await s.execute(sig_q)).scalars().all()
        if any(sig.conviction_delta > 5 for sig in recent_signals):
            return True, "signal_threshold_crossed"

        # 3. No prior score exists?
        last_score_q = (
            select(FounderScoreSnapshot)
            .where(FounderScoreSnapshot.founder_id == founder_id)
            .order_by(desc(FounderScoreSnapshot.computed_at))
        )
        last_score = (await s.execute(last_score_q)).scalars().first()
        if last_score is None:
            return True, "no_prior_score"

        # 4. Stale cache (>24h)?
        if last_score.computed_at < stale_cutoff:
            return True, "stale_cache_24h"

        # 5. Cache hit — last score is fresh, no triggers fired
        return False, "cache_hit"

    if session is not None:
        return await _check(session)

    async with async_session() as s:
        return await _check(s)


async def get_cached_aggregator(founder_id: uuid.UUID) -> Optional[dict[str, Any]]:
    """Read the cached AggregatorOutput for a founder. Returns None if no cache row exists."""
    async with async_session() as s:
        row = await s.get(CachedAggregator, founder_id)
        if row is None:
            return None
        # Check TTL — written_at within TTL window
        if row.written_at < datetime.utcnow() - timedelta(minutes=RESCORE_CACHE_TTL_MINUTES):
            return None
        return row.payload


async def write_cached_aggregator(founder_id: uuid.UUID, payload: dict[str, Any]) -> None:
    """Upsert the cached AggregatorOutput for a founder."""
    async with async_session() as s:
        existing = await s.get(CachedAggregator, founder_id)
        if existing:
            existing.payload = payload
            existing.written_at = datetime.utcnow()
        else:
            s.add(CachedAggregator(founder_id=founder_id, payload=payload))
        await s.commit()


async def get_latest_aggregator_output(founder_id: uuid.UUID) -> Optional[AggregatorOutput]:
    """Read the most recent AggregatorOutput row for a founder (used as fallback cache)."""
    async with async_session() as s:
        q = (
            select(AggregatorOutputORM)
            .where(AggregatorOutputORM.founder_id == founder_id)
            .order_by(desc(AggregatorOutputORM.computed_at))
            .limit(1)
        )
        row = (await s.execute(q)).scalars().first()
        if row is None:
            return None
        return _orm_to_schema(row)


def _orm_to_schema(row: AggregatorOutputORM) -> AggregatorOutput:
    """Convert an AggregatorOutputORM row to an AggregatorOutput schema object."""
    return AggregatorOutput(
        id=row.id,
        application_id=row.application_id,
        founder_id=row.founder_id,
        company_id=row.company_id,
        overall_recommendation=row.overall_recommendation,  # type: ignore[arg-type]
        overall_conviction=row.overall_conviction,
        axes=row.axes,
        axes_trends=row.axes_trends,
        thesis_fit_score=row.thesis_fit_score,
        evidence_coverage=row.evidence_coverage,
        open_contradictions=row.open_contradictions or [],
        missing_required_sections=row.missing_required_sections or [],
        missing_optional_sections=row.missing_optional_sections or [],
        memo_markdown=row.memo_markdown,
        next_actions=row.next_actions or [],
        computed_at=row.computed_at,
        trace_id=row.trace_id,
    )


async def get_or_compute(
    founder_id: uuid.UUID,
    application_id: Optional[uuid.UUID],
    *,
    raw_inputs: Optional[list[dict]] = None,
    company_id: Optional[uuid.UUID] = None,
    thesis=None,
    prior_founder_score=None,
    market_descriptors: Optional[list[str]] = None,
) -> tuple[Optional[AggregatorOutput], str]:
    """Entry point for card/memo view endpoints.

    Returns (aggregator_output, reason).

    If `raw_inputs` is provided and a re-score is needed, the pipeline runs with them.
    Otherwise we use the cache or the latest persisted AggregatorOutput row.
    """
    should, reason = await should_rescore(founder_id, application_id)

    if not should:
        # Try the cache first
        cached = await get_cached_aggregator(founder_id)
        if cached is not None:
            return AggregatorOutput(**cached), reason
        # Cache miss (rare — TTL expired but stale_check passed): fall through
        reason = "cache_miss"

    # If we don't have raw_inputs to re-run with, fall back to the latest persisted output
    if raw_inputs is None or company_id is None or thesis is None:
        latest = await get_latest_aggregator_output(founder_id)
        if latest is not None:
            return latest, reason if reason != "cache_miss" else "fallback_latest"
        return None, reason

    # Re-run pipeline with AsyncPostgresSaver checkpointer (spec §10 A6 + B7).
    # thread_id = founder_id so LangGraph resumes from checkpoint if interrupted.
    from app.graph.pipeline import get_pipeline, get_thread_config

    pipeline = await get_pipeline()
    state = await pipeline.ainvoke(
        {
            "founder_id": founder_id,
            "company_id": company_id,
            "application_id": application_id,
            "thesis": thesis,
            "raw_inputs": raw_inputs,
            "prior_founder_score": prior_founder_score,
            "market_descriptors": market_descriptors or [],
            "validator_outputs": [],
            "errors": [],
        },
        config=get_thread_config(founder_id),
    )
    out: Optional[AggregatorOutput] = state.get("aggregator_output")
    if out is None:
        return None, "pipeline_failed"

    # Persist + cache the result
    await write_cached_aggregator(founder_id, out.model_dump(mode="json"))
    return out, reason
