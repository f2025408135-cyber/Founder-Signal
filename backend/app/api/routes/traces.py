"""GET /traces/{run_id} — Langfuse trace proxy (spec §9.2 Pipeline Trace panel).

Proxies to Langfuse's /api/public/traces/{traceId} endpoint.
"""
from __future__ import annotations

import logging
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.deps import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/traces/{run_id}",
    response_model=dict,
    summary="Langfuse trace proxy (spec §9.2 Pipeline Trace panel).",
)
async def get_trace(run_id: str) -> dict:
    """Fetch a trace from Langfuse by trace ID.

    `run_id` is the Langfuse trace ID stored on Application.trace_id.
    Falls back to a minimal stub if Langfuse is unavailable or unconfigured.
    """
    if not settings.langfuse_is_configured:
        return {
            "trace_id": run_id,
            "available": False,
            "reason": "Langfuse not configured — set LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY.",
            "nodes": [],
        }

    url = f"{settings.langfuse_host.rstrip('/')}/api/public/traces/{run_id}"
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(
                url,
                auth=(settings.langfuse_public_key, settings.langfuse_secret_key),
                headers={"Accept": "application/json"},
            )
        if r.status_code == 404:
            return {
                "trace_id": run_id,
                "available": False,
                "reason": "Trace not found in Langfuse.",
                "nodes": [],
            }
        r.raise_for_status()
        data = r.json()
        return {
            "trace_id": run_id,
            "available": True,
            "raw": data,
            # Friendly projection for the frontend
            "nodes": _project_nodes(data),
        }
    except Exception as e:
        logger.warning("Langfuse trace fetch failed for %s: %s", run_id, e)
        return {
            "trace_id": run_id,
            "available": False,
            "reason": f"Langfuse fetch failed: {e}",
            "nodes": [],
        }


def _project_nodes(data: dict) -> list[dict]:
    """Project Langfuse's trace JSON into a flat list of node spans for the frontend."""
    out: list[dict] = []
    # Langfuse trace format varies — we look for observations/spans at the top level
    observations = data.get("observations") or data.get("spans") or []
    for obs in observations:
        out.append({
            "id": obs.get("id"),
            "name": obs.get("name"),
            "type": obs.get("type"),
            "model": obs.get("model"),
            "input_tokens": obs.get("inputTokens") or obs.get("input_tokens"),
            "output_tokens": obs.get("outputTokens") or obs.get("output_tokens"),
            "latency_ms": obs.get("latency_ms") or obs.get("latencyMs"),
            "start_time": obs.get("startTime"),
            "end_time": obs.get("endTime"),
            "status": "success" if not obs.get("error") else "error",
            "level": obs.get("level", "DEFAULT"),
        })
    return out
