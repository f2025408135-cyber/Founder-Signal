"""Server-Sent pipeline telemetry for the Signal Radar.

Events are derived from persisted application, score, and signal timestamps. The
stream never invents activity or performance metrics for the frontend.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.db.models import AggregatorOutputORM, Application as ApplicationORM, FounderSignalORM
from app.db.session import async_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/events/stream")
async def event_stream(request: Request) -> StreamingResponse:
    return StreamingResponse(
        _events(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


async def _events(request: Request) -> AsyncGenerator[str, None]:
    since = datetime.utcnow() - timedelta(minutes=5)
    heartbeat = 0
    try:
        while not await request.is_disconnected():
            for event in await _poll(since):
                yield f"data: {json.dumps(event)}\n\n"
            since = datetime.utcnow()
            heartbeat += 1
            if heartbeat >= 8:
                yield ": heartbeat\n\n"
                heartbeat = 0
            await asyncio.sleep(2)
    except asyncio.CancelledError:
        return
    except Exception as exc:
        logger.warning("Signal Radar stream ended: %s", exc)


async def _poll(since: datetime) -> list[dict]:
    events: list[dict] = []
    try:
        async with async_session() as session:
            applications = (await session.execute(
                select(ApplicationORM).where(ApplicationORM.received_at >= since).order_by(ApplicationORM.received_at).limit(20)
            )).scalars().all()
            for application in applications:
                payload = application.raw_payload or {}
                events.append({
                    "type": "application_received", "source": "inbound", "founder_id": str(application.founder_id),
                    "text": f"Application received: {payload.get('company_name', 'new founder')}",
                    "timestamp": application.received_at.isoformat(),
                })
            completed = (await session.execute(
                select(AggregatorOutputORM).where(AggregatorOutputORM.computed_at >= since).order_by(AggregatorOutputORM.computed_at).limit(20)
            )).scalars().all()
            for output in completed:
                events.append({
                    "type": "aggregator_complete", "source": "pipeline", "founder_id": str(output.founder_id),
                    "text": f"Scored {output.overall_conviction:.0f} conviction - {output.overall_recommendation}",
                    "timestamp": output.computed_at.isoformat(), "recommendation": output.overall_recommendation,
                    "conviction": output.overall_conviction,
                })
            signals = (await session.execute(
                select(FounderSignalORM).where(FounderSignalORM.detected_at >= since).order_by(FounderSignalORM.detected_at).limit(20)
            )).scalars().all()
            for signal in signals:
                source = signal.signal_type.split("_")[0] if "_" in signal.signal_type else "outbound"
                events.append({
                    "type": "signal_detected", "source": source, "founder_id": str(signal.founder_id),
                    "text": f"{signal.signal_type.replace('_', ' ').title()} detected",
                    "timestamp": signal.detected_at.isoformat(),
                })
    except Exception as exc:
        logger.warning("Signal Radar poll failed: %s", exc)
    return sorted(events, key=lambda event: event["timestamp"])
