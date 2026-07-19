"""GET /api/events/stream — Server-Sent Events endpoint for real-time pipeline events.

Emits SSE events as pipeline nodes complete (ingestion, validator, scoring, aggregator).
The frontend SignalRadar widget subscribes to this stream to display live activity.

Event format:
    data: {"type": "github_commit", "source": "github", "founder_id": "...", "text": "...", "timestamp": "..."}

This is a real event stream — not simulated. It polls the database for recent
Application/FounderSignal/AggregatorOutput rows and emits events as they appear.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select, text

from app.db.models import (
    AggregatorOutputORM,
    Application as ApplicationORM,
    FounderSignalORM,
)
from app.db.session import async_session

logger = logging.getLogger(__name__)
router = APIRouter()

# How often to poll for new events (seconds)
POLL_INTERVAL = 2.0
# How far back to look on first connection (seconds)
INITIAL_LOOKBACK = 300  # 5 minutes


@router.get("/events/stream")
async def event_stream(request: Request):
    """SSE endpoint — emits pipeline events as they happen.

    The client connects with:
        const es = new EventSource("/api/events/stream");
        es.onmessage = (e) => { const event = JSON.parse(e.data); ... };

    Events are real: we poll the DB for new Application/Signal/AggregatorOutput rows
    and emit them as SSE events. If no new events appear, we send a heartbeat
    comment every 15 seconds to keep the connection alive.
    """
    return StreamingResponse(
        _generate_events(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


async def _generate_events(request: Request) -> AsyncGenerator[str, None]:
    """Generate SSE events by polling the database for new pipeline activity."""
    last_check = datetime.utcnow() - timedelta(seconds=INITIAL_LOOKBACK)
    heartbeat_counter = 0

    try:
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                logger.info("SSE client disconnected")
                break

            # Poll for new events
            events = await _poll_for_events(last_check)
            last_check = datetime.utcnow()

            for event in events:
                yield f"data: {json.dumps(event, default=str)}\n\n"

            # Heartbeat every ~15 seconds (when no events)
            heartbeat_counter += 1
            if heartbeat_counter >= int(15 / POLL_INTERVAL):
                yield f": heartbeat\n\n"
                heartbeat_counter = 0

            await asyncio.sleep(POLL_INTERVAL)

    except asyncio.CancelledError:
        logger.info("SSE stream cancelled")
    except Exception as e:
        logger.exception("SSE stream error: %s", e)


async def _poll_for_events(since: datetime) -> list[dict]:
    """Poll the database for new pipeline events since the given timestamp.

    Returns a list of event dicts sorted by timestamp ascending.
    """
    events: list[dict] = []

    try:
        async with async_session() as s:
            # 1. New applications received
            app_q = (
                select(ApplicationORM)
                .where(ApplicationORM.received_at >= since)
                .order_by(ApplicationORM.received_at)
                .limit(20)
            )
            apps = (await s.execute(app_q)).scalars().all()
            for app in apps:
                raw = app.raw_payload or {}
                events.append({
                    "type": "application_received",
                    "source": "inbound",
                    "founder_id": str(app.founder_id),
                    "application_id": str(app.id),
                    "text": f"Application received: {raw.get('founder_name', 'unknown')} — {raw.get('company_name', 'unknown')}",
                    "timestamp": app.received_at.isoformat() if app.received_at else datetime.utcnow().isoformat(),
                    "sector": raw.get("sector_self_reported", "unknown"),
                    "geography": raw.get("hq_country", "unknown"),
                })

            # 2. Ingestion complete
            ing_q = (
                select(ApplicationORM)
                .where(ApplicationORM.ingestion_complete_at >= since)
                .order_by(ApplicationORM.ingestion_complete_at)
                .limit(20)
            )
            ings = (await s.execute(ing_q)).scalars().all()
            for ing in ings:
                events.append({
                    "type": "ingestion_complete",
                    "source": "pipeline",
                    "founder_id": str(ing.founder_id),
                    "application_id": str(ing.id),
                    "text": f"Ingestion complete — claims extracted",
                    "timestamp": ing.ingestion_complete_at.isoformat() if ing.ingestion_complete_at else datetime.utcnow().isoformat(),
                })

            # 3. Validator complete
            val_q = (
                select(ApplicationORM)
                .where(ApplicationORM.validator_complete_at >= since)
                .order_by(ApplicationORM.validator_complete_at)
                .limit(20)
            )
            vals = (await s.execute(val_q)).scalars().all()
            for val in vals:
                events.append({
                    "type": "validator_complete",
                    "source": "pipeline",
                    "founder_id": str(val.founder_id),
                    "application_id": str(val.id),
                    "text": f"Validation complete — claims cross-checked",
                    "timestamp": val.validator_complete_at.isoformat() if val.validator_complete_at else datetime.utcnow().isoformat(),
                })

            # 4. Scoring complete
            sco_q = (
                select(ApplicationORM)
                .where(ApplicationORM.scoring_complete_at >= since)
                .order_by(ApplicationORM.scoring_complete_at)
                .limit(20)
            )
            scos = (await s.execute(sco_q)).scalars().all()
            for sco in scos:
                events.append({
                    "type": "scoring_complete",
                    "source": "pipeline",
                    "founder_id": str(sco.founder_id),
                    "application_id": str(sco.id),
                    "text": f"Scoring complete — Founder/Market/Idea-vs-Market scored",
                    "timestamp": sco.scoring_complete_at.isoformat() if sco.scoring_complete_at else datetime.utcnow().isoformat(),
                })

            # 5. Aggregator complete (final score)
            agg_q = (
                select(AggregatorOutputORM)
                .where(AggregatorOutputORM.computed_at >= since)
                .order_by(AggregatorOutputORM.computed_at)
                .limit(20)
            )
            aggs = (await s.execute(agg_q)).scalars().all()
            for agg in aggs:
                events.append({
                    "type": "aggregator_complete",
                    "source": "pipeline",
                    "founder_id": str(agg.founder_id),
                    "application_id": str(agg.application_id) if agg.application_id else None,
                    "text": f"SCORED {agg.overall_conviction:.0f} conviction — {agg.overall_recommendation}",
                    "timestamp": agg.computed_at.isoformat() if agg.computed_at else datetime.utcnow().isoformat(),
                    "recommendation": agg.overall_recommendation,
                    "conviction": agg.overall_conviction,
                    "axes": agg.axes,
                })

            # 6. New outbound signals
            sig_q = (
                select(FounderSignalORM)
                .where(FounderSignalORM.detected_at >= since)
                .order_by(FounderSignalORM.detected_at)
                .limit(20)
            )
            sigs = (await s.execute(sig_q)).scalars().all()
            for sig in sigs:
                events.append({
                    "type": "signal_detected",
                    "source": sig.signal_type.split("_")[0] if "_" in sig.signal_type else "outbound",
                    "founder_id": str(sig.founder_id),
                    "text": f"{sig.signal_type.replace('_', ' ').title()} — conviction delta +{sig.conviction_delta:.1f}",
                    "timestamp": sig.detected_at.isoformat() if sig.detected_at else datetime.utcnow().isoformat(),
                    "conviction_delta": sig.conviction_delta,
                })

    except Exception as e:
        logger.warning("Event poll failed: %s", e)

    # Sort by timestamp
    events.sort(key=lambda e: e.get("timestamp", ""))
    return events
