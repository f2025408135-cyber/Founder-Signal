"""GET /applications/inbox — list of compact cards for the inbox view (spec §9.1).

Also: GET /applications — list all applications with their status.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AggregatorOutputORM,
    Application as ApplicationORM,
    Company,
    Founder,
    FounderScoreSnapshot,
)
from app.deps import get_db

router = APIRouter()


@router.get(
    "/applications/inbox",
    response_model=dict,
    summary="Inbox view — list of founders ranked by overall_conviction (spec §9.1 + §9.3).",
)
async def get_inbox(
    sector: Optional[str] = Query(None, help="Filter by sector"),
    geography: Optional[str] = Query(None, help="Filter by ISO-2 country code"),
    recommendation: Optional[str] = Query(
        None, description="Filter by recommendation: fast_pass|deep_dive|pass|reject"
    ),
    cold_start: Optional[bool] = Query(None, description="Filter cold-start only (true) or exclude (false)"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the inbox list — one card per (founder, latest application) pair.

    Sorted by overall_conviction desc per spec §9.3.
    """
    # Join applications -> founders -> companies -> aggregator_outputs
    q = (
        select(
            ApplicationORM,
            Founder,
            Company,
            AggregatorOutputORM,
        )
        .join(Founder, ApplicationORM.founder_id == Founder.id)
        .join(Company, ApplicationORM.company_id == Company.id)
        .outerjoin(
            AggregatorOutputORM,
            AggregatorOutputORM.application_id == ApplicationORM.id,
        )
        .order_by(desc(ApplicationORM.received_at))
    )

    if sector:
        q = q.where(Company.sector_self_reported.ilike(f"%{sector}%"))
    if geography:
        q = q.where(Company.hq_country == geography.upper())

    rows = (await db.execute(q.limit(limit))).all()

    # Group by founder — keep only the latest application per founder
    seen_founders: dict[uuid.UUID, dict] = {}
    for app, founder, company, agg in rows:
        if founder.id in seen_founders:
            # Keep the most recent application
            if app.received_at > seen_founders[founder.id]["_received_at"]:
                pass  # fall through to overwrite
            else:
                continue
        # Always populate cold_start from the latest FounderScoreSnapshot
        # (spec §9.1: cold_start drives the amber border + ❄ icon — must reflect
        # actual founder status, not just the filter toggle).
        snap_q = (
            select(FounderScoreSnapshot)
            .where(FounderScoreSnapshot.founder_id == founder.id)
            .order_by(desc(FounderScoreSnapshot.computed_at))
            .limit(1)
        )
        snap = (await db.execute(snap_q)).scalars().first()
        cold_start_val = snap.cold_start if snap else False

        # If the cold_start filter is active, skip non-matching founders
        if cold_start is not None and cold_start_val != cold_start:
            continue

        # Keep in-flight and failed applications visible. A missing memo is a pipeline
        # state, not an absence of deal flow, and must never be mistaken for a rejection.
        if agg is None:
            if recommendation:
                continue
            seen_founders[founder.id] = {
                "founder_id": str(founder.id),
                "founder_name": founder.name,
                "company_id": str(company.id),
                "company_name": company.name,
                "geography": company.hq_country,
                "sector": company.sector_self_reported,
                "received_at": app.received_at.isoformat() if app.received_at else None,
                "founder_score": None,
                "founder_trend": "insufficient_data",
                "market_score": None,
                "idea_vs_market_score": None,
                "thesis_fit_score": None,
                "conviction": None,
                "evidence_coverage": None,
                "open_contradictions": 0,
                "recommendation": None,
                "cold_start": cold_start_val,
                "trend": "insufficient_data",
                "trace_id": app.trace_id,
                "computed_at": None,
                "application_id": str(app.id),
                "pipeline_status": app.status,
                "_received_at": app.received_at,
            }
            continue

        if recommendation and agg.overall_recommendation != recommendation:
            continue

        seen_founders[founder.id] = {
            "founder_id": str(founder.id),
            "founder_name": founder.name,
            "company_id": str(company.id),
            "company_name": company.name,
            "geography": company.hq_country,
            "sector": company.sector_self_reported,
            "received_at": app.received_at.isoformat() if app.received_at else None,
            "founder_score": round(agg.axes.get("founder", 0.0), 1),
            "founder_trend": agg.axes_trends.get("founder", "insufficient_data"),
            "market_score": _market_score_to_label(agg.axes.get("market", 0.0)),
            "idea_vs_market_score": round(agg.axes.get("idea_vs_market", 0.0), 1),
            "thesis_fit_score": round(agg.thesis_fit_score, 1),
            "conviction": round(agg.overall_conviction, 1),
            "evidence_coverage": round(agg.evidence_coverage, 3),
            "open_contradictions": len(agg.open_contradictions or []),
            "recommendation": agg.overall_recommendation,
            "cold_start": cold_start_val,
            "trend": agg.axes_trends.get("founder", "insufficient_data"),
            "trace_id": agg.trace_id,
            "computed_at": agg.computed_at.isoformat() if agg.computed_at else None,
            "application_id": str(app.id),
            "pipeline_status": app.status,
            "_received_at": app.received_at,
        }

    cards = list(seen_founders.values())
    # Remove the internal sort key
    for c in cards:
        c.pop("_received_at", None)

    # Sort by conviction desc per spec §9.3
    cards.sort(key=lambda c: c.get("conviction") or 0, reverse=True)

    return {
        "total": len(cards),
        "cards": cards,
        "filters": {
            "sector": sector,
            "geography": geography,
            "recommendation": recommendation,
            "cold_start": cold_start,
        },
    }


def _market_score_to_label(numeric: float) -> str:
    """Map numeric market score back to categorical label."""
    if numeric >= 75:
        return "bullish"
    if numeric <= 25:
        return "bear"
    return "neutral"


@router.get(
    "/applications",
    response_model=dict,
    summary="List all applications (raw, no enrichment).",
)
async def list_applications(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List applications in reverse-chronological order."""
    q = (
        select(ApplicationORM, Founder, Company)
        .join(Founder, ApplicationORM.founder_id == Founder.id)
        .join(Company, ApplicationORM.company_id == Company.id)
        .order_by(desc(ApplicationORM.received_at))
        .limit(limit)
    )
    rows = (await db.execute(q)).all()
    return {
        "total": len(rows),
        "applications": [
            {
                "id": str(app.id),
                "founder_id": str(app.founder_id),
                "founder_name": founder.name,
                "company_id": str(app.company_id),
                "company_name": company.name,
                "received_at": app.received_at.isoformat() if app.received_at else None,
                "status": app.status,
                "trace_id": app.trace_id,
                "ingestion_complete_at": app.ingestion_complete_at.isoformat() if app.ingestion_complete_at else None,
                "validator_complete_at": app.validator_complete_at.isoformat() if app.validator_complete_at else None,
                "scoring_complete_at": app.scoring_complete_at.isoformat() if app.scoring_complete_at else None,
                "aggregator_complete_at": app.aggregator_complete_at.isoformat() if app.aggregator_complete_at else None,
            }
            for app, founder, company in rows
        ],
    }
