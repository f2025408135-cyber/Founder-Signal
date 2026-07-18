"""API router — placeholder for Tier A. Full routes added in Tier B."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
async def ping() -> dict:
    return {"pong": True}
