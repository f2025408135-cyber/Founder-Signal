"""POST /outbound/scan and GET /outbound/queue — outbound sourcing endpoints (spec §9.3).

POST /outbound/scan: kicks off the outbound scan script (GitHub trending + arxiv + PH + HN).
GET /outbound/queue: returns the list of outbound-sourced founders with sourcing_channel badges.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AggregatorOutputORM,
    Application as ApplicationORM,
    Company,
    Founder,
    FounderSignalORM,
    FounderScoreSnapshot,
)
from app.deps import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/outbound/scan",
    response_model=dict,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger an outbound scan (spec §10 B9). Runs in background.",
)
async def trigger_outbound_scan(
    background_tasks: BackgroundTasks,
    lookback_hours: int = Query(1, ge=1, le=24, description="Look back this many hours for new signals"),
) -> dict:
    """Kick off the outbound scan as a background task."""
    scan_id = uuid.uuid4()
    background_tasks.add_task(_run_outbound_scan, scan_id=scan_id, lookback_hours=lookback_hours)
    return {
        "scan_id": str(scan_id),
        "status": "queued",
        "lookback_hours": lookback_hours,
        "started_at": datetime.utcnow().isoformat(),
    }


async def _run_outbound_scan(*, scan_id: uuid.UUID, lookback_hours: int) -> None:
    """Background wrapper around scripts/run_outbound_scan.py."""
    import asyncio

    from scripts.run_outbound_scan import run_outbound_scan

    try:
        await run_outbound_scan(lookback_hours=lookback_hours, scan_id=scan_id)
    except Exception as e:
        logger.exception("Outbound scan %s failed: %s", scan_id, e)


@router.get(
    "/outbound/queue",
    response_model=dict,
    summary="List outbound-sourced founders with sourcing_channel badges (spec §9.3).",
)
async def get_outbound_queue(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return founders that have at least one outbound signal (founder_signals row).

    Per spec §9.3, this list shows the same compact card UI as the inbox but with
    an additional sourcing_channel badge (github | arxiv | ph | hn | accelerator).
    """
    # Find founders with outbound signals
    sig_q = (
        select(
            FounderSignalORM.founder_id,
            FounderSignalORM.signal_type,
            FounderSignalORM.detected_at,
            FounderSignalORM.conviction_delta,
        )
        .order_by(desc(FounderSignalORM.detected_at))
        .limit(500)  # broad fetch, then dedupe
    )
    sig_rows = (await db.execute(sig_q)).all()

    # Dedupe by founder_id — keep latest signal per founder
    by_founder: dict[uuid.UUID, dict] = {}
    for fid, sig_type, detected_at, conv_delta in sig_rows:
        if fid not in by_founder or detected_at > by_founder[fid]["detected_at"]:
            by_founder[fid] = {
                "signal_type": sig_type,
                "detected_at": detected_at,
                "conviction_delta": conv_delta,
            }

    if not by_founder:
        return {"total": 0, "founders": []}

    # Fetch founder + company + latest aggregator output for each
    out: list[dict] = []
    for fid, sig in by_founder.items():
        founder = await db.get(Founder, fid)
        if founder is None:
            continue

        # Get latest company
        company_q = select(Company).where(Company.founder_id == fid).order_by(desc(Company.created_at)).limit(1)
        company = (await db.execute(company_q)).scalars().first()

        # Get latest aggregator output
        agg_q = (
            select(AggregatorOutputORM)
            .where(AggregatorOutputORM.founder_id == fid)
            .order_by(desc(AggregatorOutputORM.computed_at))
            .limit(1)
        )
        agg = (await db.execute(agg_q)).scalars().first()

        # Latest snapshot (for cold_start flag)
        snap_q = (
            select(FounderScoreSnapshot)
            .where(FounderScoreSnapshot.founder_id == fid)
            .order_by(desc(FounderScoreSnapshot.computed_at))
            .limit(1)
        )
        snap = (await db.execute(snap_q)).scalars().first()

        # Map signal_type to sourcing_channel label
        channel = _signal_type_to_channel(sig["signal_type"])

        out.append({
            "founder_id": str(fid),
            "founder_name": founder.name,
            "company_id": str(company.id) if company else None,
            "company_name": company.name if company else None,
            "geography": company.hq_country if company else None,
            "sector": company.sector_self_reported if company else None,
            "sourcing_channel": channel,
            "signal_detected_at": sig["detected_at"].isoformat() if sig["detected_at"] else None,
            "conviction_delta": round(sig["conviction_delta"], 2),
            # Card fields — match InboxCard shape (spec §9.1)
            "founder_score": round(agg.axes.get("founder", 0.0), 1) if agg else None,
            "founder_trend": agg.axes_trends.get("founder", "insufficient_data") if agg else "insufficient_data",
            "market_score": _market_score_to_label(agg.axes.get("market", 0.0)) if agg else None,
            "idea_vs_market_score": round(agg.axes.get("idea_vs_market", 0.0), 1) if agg else None,
            "thesis_fit_score": round(agg.thesis_fit_score, 1) if agg else None,
            "conviction": round(agg.overall_conviction, 1) if agg else None,
            "evidence_coverage": round(agg.evidence_coverage, 3) if agg else None,
            "open_contradictions": len(agg.open_contradictions or []) if agg else 0,
            "recommendation": agg.overall_recommendation if agg else None,
            "cold_start": snap.cold_start if snap else False,
            "trend": agg.axes_trends.get("founder", "insufficient_data") if agg else "insufficient_data",
            "trace_id": agg.trace_id if agg else None,
            "computed_at": agg.computed_at.isoformat() if agg and agg.computed_at else None,
            # received_at — outbound founders don't have an application; use signal_detected_at
            "received_at": sig["detected_at"].isoformat() if sig["detected_at"] else None,
        })

    # Sort by conviction delta desc, then by conviction desc
    out.sort(key=lambda c: (c.get("conviction_delta") or 0, c.get("conviction") or 0), reverse=True)

    return {
        "total": len(out),
        "founders": out[:limit],
    }


def _signal_type_to_channel(sig_type: str) -> str:
    """Map founder_signal.signal_type to a sourcing_channel badge label."""
    if "github" in sig_type.lower():
        return "github"
    if "arxiv" in sig_type.lower():
        return "arxiv"
    if "ph" in sig_type.lower() or "producthunt" in sig_type.lower():
        return "ph"
    if "hn" in sig_type.lower() or "hackernews" in sig_type.lower():
        return "hn"
    if "accelerator" in sig_type.lower():
        return "accelerator"
    return "external"
