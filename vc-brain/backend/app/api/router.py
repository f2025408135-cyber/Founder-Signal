"""API router — aggregates all route modules per spec §10 B8.

Endpoints (spec §10 B8 + §9.2 Pipeline Trace + §10 B10 /admin/latency):
- POST   /api/applications            — submit a new application, 202 + founder_id
- GET    /api/applications            — list all applications
- GET    /api/applications/inbox      — inbox list (compact cards, sorted by conviction)
- GET    /api/founders/{id}/card      — compact card view (spec §9.1)
- GET    /api/founders/{id}/memo      — full memo view (spec §9.2)
- GET    /api/thesis                  — read active thesis
- POST   /api/thesis                  — update active thesis
- POST   /api/outbound/scan           — trigger outbound scan (background)
- GET    /api/outbound/queue          — list outbound-sourced founders
- POST   /api/query                   — compound query resolution (spec §9.4)
- GET    /api/traces/{run_id}         — Langfuse trace proxy (spec §9.2)
- GET    /api/admin/latency           — p50/p95 latency per phase (spec §10 B10)
- GET    /api/ping                    — health check
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import admin, applications, events, fin, founders, inbox, outbound, query, thesis, traces

router = APIRouter()

# Spec §10 B8: 7 required endpoints + supporting routes
router.include_router(applications.router, tags=["applications"])
router.include_router(inbox.router, tags=["inbox"])
router.include_router(founders.router, tags=["founders"])
router.include_router(thesis.router, tags=["thesis"])
router.include_router(outbound.router, tags=["outbound"])
router.include_router(query.router, tags=["query"])
router.include_router(traces.router, tags=["traces"])
router.include_router(admin.router, tags=["admin"])
router.include_router(events.router, tags=["events"])
router.include_router(fin.router, tags=["fin"])


@router.get("/ping")
async def ping() -> dict:
    return {"pong": True}
