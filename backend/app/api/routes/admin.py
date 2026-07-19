"""GET /admin/latency — p50/p95 latency per pipeline phase (spec §10 B10)."""
from __future__ import annotations

import logging
import statistics
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Application as ApplicationORM
from app.deps import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/admin/latency",
    response_model=dict,
    summary="p50/p95 latency per pipeline phase (spec §10 B10).",
)
async def get_latency(
    hours: int = Query(24, ge=1, le=168, description="Look back this many hours"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return p50/p95 latency for each pipeline phase:
    - ingestion: received_at -> ingestion_complete_at
    - validator: ingestion_complete_at -> validator_complete_at
    - scoring: validator_complete_at -> scoring_complete_at
    - aggregator: scoring_complete_at -> aggregator_complete_at
    - end_to_end: received_at -> aggregator_complete_at
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    q = select(ApplicationORM).where(
        ApplicationORM.received_at >= cutoff,
        ApplicationORM.aggregator_complete_at.is_not(None),
    )
    apps = (await db.execute(q)).scalars().all()

    phases: dict[str, list[float]] = {
        "ingestion": [],
        "validator": [],
        "scoring": [],
        "aggregator": [],
        "end_to_end": [],
    }

    for app in apps:
        if app.ingestion_complete_at and app.received_at:
            phases["ingestion"].append((app.ingestion_complete_at - app.received_at).total_seconds())
        if app.validator_complete_at and app.ingestion_complete_at:
            phases["validator"].append((app.validator_complete_at - app.ingestion_complete_at).total_seconds())
        if app.scoring_complete_at and app.validator_complete_at:
            phases["scoring"].append((app.scoring_complete_at - app.validator_complete_at).total_seconds())
        if app.aggregator_complete_at and app.scoring_complete_at:
            phases["aggregator"].append((app.aggregator_complete_at - app.scoring_complete_at).total_seconds())
        if app.aggregator_complete_at and app.received_at:
            phases["end_to_end"].append((app.aggregator_complete_at - app.received_at).total_seconds())

    return {
        "window_hours": hours,
        "n_applications": len(apps),
        "phases": {
            phase: {
                "count": len(samples),
                "p50_seconds": round(statistics.median(samples), 2) if samples else None,
                "p95_seconds": round(_percentile(samples, 95), 2) if samples else None,
                "mean_seconds": round(statistics.mean(samples), 2) if samples else None,
                "max_seconds": round(max(samples), 2) if samples else None,
            }
            for phase, samples in phases.items()
        },
        # Spec §10 B10 acceptance: all 5 timestamps populated within 90s of POST /applications
        "acceptance_90s": (
            all(
                app.ingestion_complete_at
                and app.validator_complete_at
                and app.scoring_complete_at
                and app.aggregator_complete_at
                and (app.aggregator_complete_at - app.received_at).total_seconds() <= 90
                for app in apps
            )
            if apps
            else False
        ),
    }


def _percentile(samples: list[float], pct: float) -> float:
    """Compute the pct-percentile (0-100) of a list of floats."""
    if not samples:
        return 0.0
    sorted_samples = sorted(samples)
    k = (len(sorted_samples) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_samples) - 1)
    if f == c:
        return sorted_samples[f]
    return sorted_samples[f] + (sorted_samples[c] - sorted_samples[f]) * (k - f)
