"""GET /founders/{id}/card and GET /founders/{id}/memo — card/memo view endpoints.

Per spec §10 B8: GET /founders/{id}/card, /founders/{id}/memo.

Uses the rescore trigger logic (§8) — serves cached output if no triggers fired,
re-runs the pipeline otherwise.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AggregatorOutputORM,
    Application as ApplicationORM,
    Company,
    Founder,
    FounderScoreORM,
    FounderScoreSnapshot,
)
from app.deps import get_db
from app.schemas.agent_outputs import AggregatorOutput

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/founders/{founder_id}/card",
    response_model=dict,
    summary="Compact card view for the inbox — spec §9.1.",
)
async def get_founder_card(
    founder_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the compact card payload per spec §9.1 field list."""
    from app.triggers.rescore import get_latest_aggregator_output, should_rescore

    founder = await db.get(Founder, founder_id)
    if founder is None:
        raise HTTPException(status_code=404, detail="Founder not found")

    # Get the most recent application for this founder
    app_q = (
        select(ApplicationORM)
        .where(ApplicationORM.founder_id == founder_id)
        .order_by(ApplicationORM.received_at.desc())
        .limit(1)
    )
    app = (await db.execute(app_q)).scalars().first()

    # Check if we need to re-score
    should, reason = await should_rescore(founder_id, app.id if app else None, session=db)

    # Get the latest aggregator output (cache or DB)
    agg = await get_latest_aggregator_output(founder_id)
    if agg is None:
        # No prior run — return minimal card with "no data yet" status
        return {
            "founder_id": str(founder_id),
            "founder_name": founder.name,
            "company_name": None,
            "geography": None,
            "sector": None,
            "received_at": None,
            "founder_score": None,
            "market_score": None,
            "idea_vs_market_score": None,
            "thesis_fit_score": None,
            "conviction": None,
            "evidence_coverage": None,
            "open_contradictions": 0,
            "recommendation": None,
            "cold_start": False,
            "trend": "insufficient_data",
            "rescore_reason": reason,
        }

    # Fetch company info
    company_q = select(Company).where(Company.id == agg.company_id)
    company = (await db.execute(company_q)).scalars().first()

    # Build the card payload — matches spec §9.1 field list exactly
    founder_score = agg.axes.get("founder", 0.0)
    market_score = agg.axes.get("market", 0.0)
    idea_vs_market_score = agg.axes.get("idea_vs_market", 0.0)

    # Trend from axes_trends (string)
    trend = agg.axes_trends.get("founder", "insufficient_data")

    # Cold-start flag — read from founder_score_snapshots (last row's cold_start column)
    snap_q = (
        select(FounderScoreSnapshot)
        .where(FounderScoreSnapshot.founder_id == founder_id)
        .order_by(FounderScoreSnapshot.computed_at.desc())
        .limit(1)
    )
    last_snap = (await db.execute(snap_q)).scalars().first()
    cold_start = last_snap.cold_start if last_snap else False

    # Recommendation pill text
    rec = agg.overall_recommendation

    return {
        "founder_id": str(founder_id),
        "founder_name": founder.name,
        "company_name": company.name if company else None,
        "geography": company.hq_country if company else None,
        "sector": company.sector_self_reported if company else None,
        "received_at": app.received_at.isoformat() if app else None,
        # axes
        "founder_score": round(founder_score, 1),
        "founder_trend": trend,
        "market_score": _market_score_to_label(market_score),
        "idea_vs_market_score": round(idea_vs_market_score, 1),
        "thesis_fit_score": round(agg.thesis_fit_score, 1),
        # conviction + meta
        "conviction": round(agg.overall_conviction, 1),
        "evidence_coverage": round(agg.evidence_coverage, 3),
        "open_contradictions": len(agg.open_contradictions),
        "recommendation": rec,
        "cold_start": cold_start,
        "trend": trend,
        "rescore_reason": reason,
        "trace_id": agg.trace_id,
        "computed_at": agg.computed_at.isoformat() if agg.computed_at else None,
    }


def _market_score_to_label(numeric: float) -> str:
    """Map the numeric market score back to the categorical label."""
    if numeric >= 75:
        return "bullish"
    if numeric <= 25:
        return "bear"
    return "neutral"


@router.get(
    "/founders/{founder_id}/memo",
    response_model=dict,
    summary="Full memo view — spec §9.2.",
)
async def get_founder_memo(
    founder_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the full memo payload: AggregatorOutput + claims + validator outputs."""
    from app.triggers.rescore import get_latest_aggregator_output, should_rescore

    founder = await db.get(Founder, founder_id)
    if founder is None:
        raise HTTPException(status_code=404, detail="Founder not found")

    agg = await get_latest_aggregator_output(founder_id)
    if agg is None:
        raise HTTPException(status_code=404, detail="No memo available — pipeline has not been run for this founder.")

    should, reason = await should_rescore(founder_id, agg.application_id, session=db)

    # Pull all claims for this founder (with validator flags)
    from app.db.models import ClaimORM
    claims_q = select(ClaimORM).where(
        ClaimORM.founder_id == founder_id,
        ClaimORM.superseded_by.is_(None),
    )
    claims = (await db.execute(claims_q)).scalars().all()

    # Founder history (score snapshots)
    snaps_q = (
        select(FounderScoreSnapshot)
        .where(FounderScoreSnapshot.founder_id == founder_id)
        .order_by(FounderScoreSnapshot.computed_at.asc())
    )
    snaps = (await db.execute(snaps_q)).scalars().all()

    # Company
    company_q = select(Company).where(Company.id == agg.company_id)
    company = (await db.execute(company_q)).scalars().first()

    return {
        "founder_id": str(founder_id),
        "founder_name": founder.name,
        "company_name": company.name if company else None,
        "aggregator_output": agg.model_dump(mode="json"),
        "claims": [
            {
                "id": str(c.id),
                "kind": c.kind,
                "text": c.text,
                "source": c.source,
                "confidence": c.confidence,
                "flags": c.flags,
                "validator_status": c.flags[-1].get("flag") if c.flags else None,
                "superseded_by": str(c.superseded_by) if c.superseded_by else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in claims
        ],
        "score_history": [
            {
                "computed_at": s.computed_at.isoformat() if s.computed_at else None,
                "score": s.score,
                "trend": s.trend,
                "trigger": s.trigger,
                "cold_start": s.cold_start,
                "component_scores": s.component_scores,
                "confidence_band": [s.confidence_band_low, s.confidence_band_high],
            }
            for s in snaps
        ],
        "rescore_reason": reason,
    }
