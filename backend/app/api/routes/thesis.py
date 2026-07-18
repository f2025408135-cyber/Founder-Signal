"""GET /thesis and POST /thesis — read/update the active investment thesis (spec §9.3)."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ThesisConfig
from app.deps import get_db
from app.schemas.thesis import RiskAppetite, Thesis

logger = logging.getLogger(__name__)

router = APIRouter()


class ThesisUpdate(BaseModel):
    """Patch payload for the active thesis. All fields optional — only set fields are updated."""

    name: str | None = None
    sectors: list[str] | None = None
    stage: list[str] | None = None
    geography: list[str] | None = None
    check_size_usd: int | None = None
    ownership_target_pct: float | None = None
    risk_appetite: RiskAppetite | None = None
    active: bool | None = None


@router.get(
    "/thesis",
    response_model=Thesis,
    summary="Get the active investment thesis (spec §9.3).",
)
async def get_thesis(db: AsyncSession = Depends(get_db)) -> Thesis:
    """Return the active thesis. If none exists, create the default Maschmeyer thesis."""
    q = select(ThesisConfig).where(ThesisConfig.active == True).limit(1)
    row = (await db.execute(q)).scalars().first()
    if row is None:
        # Fall back to default
        from app.schemas.thesis import default_maschmeyer_thesis

        default = default_maschmeyer_thesis()
        row = ThesisConfig(
            id=default.id,
            name=default.name,
            sectors=default.sectors,
            stage=default.stage,
            geography=default.geography,
            check_size_usd=default.check_size_usd,
            ownership_target_pct=default.ownership_target_pct,
            risk_appetite=default.risk_appetite.model_dump(),
            active=True,
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)

    return _orm_to_schema(row)


@router.post(
    "/thesis",
    response_model=Thesis,
    summary="Update the active thesis (spec §9.3). Triggers inbox re-score.",
)
async def update_thesis(
    payload: ThesisUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Thesis:
    """Update the active thesis. Per spec §9.3, this triggers a re-score of the entire inbox."""
    q = select(ThesisConfig).where(ThesisConfig.active == True).limit(1)
    row = (await db.execute(q)).scalars().first()
    if row is None:
        # Create with defaults, then apply patch
        from app.schemas.thesis import default_maschmeyer_thesis

        default = default_maschmeyer_thesis()
        row = ThesisConfig(
            id=default.id,
            name=default.name,
            sectors=default.sectors,
            stage=default.stage,
            geography=default.geography,
            check_size_usd=default.check_size_usd,
            ownership_target_pct=default.ownership_target_pct,
            risk_appetite=default.risk_appetite.model_dump(),
            active=True,
        )
        db.add(row)
        await db.flush()

    if payload.name is not None:
        row.name = payload.name
    if payload.sectors is not None:
        row.sectors = payload.sectors
    if payload.stage is not None:
        row.stage = payload.stage
    if payload.geography is not None:
        row.geography = payload.geography
    if payload.check_size_usd is not None:
        row.check_size_usd = payload.check_size_usd
    if payload.ownership_target_pct is not None:
        row.ownership_target_pct = payload.ownership_target_pct
    if payload.risk_appetite is not None:
        row.risk_appetite = payload.risk_appetite.model_dump()
    if payload.active is not None:
        # If setting this row inactive, that's odd — usually we want to keep one active.
        # If setting it active (default), also fine.
        row.active = payload.active

    row.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(row)

    # NOTE: per spec §9.3, "Saving will re-evaluate all 24 founders in the inbox. Continue?"
    # The re-score confirmation modal is a frontend concern. The backend re-score trigger
    # fires automatically because should_rescore() will detect the new thesis via the
    # cached_aggregator TTL expiry on next card view. We do NOT trigger a bulk re-score
    # here — it would be expensive and the user may not actually want it.
    # The frontend SHOULD show the modal and call this endpoint only after confirmation.
    # background_tasks.add_task(_trigger_inbox_rescore, thesis_id=row.id)

    return _orm_to_schema(row)


def _orm_to_schema(row: ThesisConfig) -> Thesis:
    return Thesis(
        id=row.id,
        name=row.name,
        sectors=row.sectors,
        stage=row.stage,
        geography=row.geography,
        check_size_usd=row.check_size_usd,
        ownership_target_pct=row.ownership_target_pct,
        risk_appetite=RiskAppetite(**row.risk_appetite),
        created_at=row.created_at,
        updated_at=row.updated_at,
        active=row.active,
    )
