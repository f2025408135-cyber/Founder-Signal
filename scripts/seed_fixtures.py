"""Seed the three fixture founders from spec §10 (cold-start, verified, contradicted).

Usage:
    python scripts/seed_fixtures.py

Writes the three founders + their applications + raw inputs to the DB so the
InboxPage has data to render in Tier D.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Ensure backend/ is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.db.models import Application as ApplicationORM, Company, Founder, ThesisConfig
from app.db.session import async_session, engine
from app.db.base import Base
from app.schemas.application import ApplicationCreate
from app.schemas.thesis import default_maschmeyer_thesis
from sqlalchemy import select


COLD_START_APP = ApplicationCreate(
    founder_name="Jane Doe",
    founder_email="jane@stealthco.ai",
    founder_bio_text="Former ML engineer. Working on developer tooling for LLM evaluation.",
    company_name="StealthCo",
    company_website_url="https://stealthco.ai",
    github_repo_slugs=[],
    accelerator=None,
    hq_country="DE",
    sector_self_reported="AI infra",
)

VERIFIED_APP = ApplicationCreate(
    founder_name="Bob Smith",
    founder_email="bob@verifiedco.com",
    founder_bio_text="AI researcher, ex-DeepMind.",
    company_name="VerifiedCo",
    company_website_url="https://verifiedco.com",
    github_repo_slugs=["bobsmith/ai-infra-tool"],
    accelerator="YC W24",
    hq_country="US",
    sector_self_reported="AI infra",
)

CONTRADICTED_APP = ApplicationCreate(
    founder_name="Carol Wu",
    founder_email="carol@contradicted.com",
    founder_bio_text="Founder with contradictory deck claims about market size.",
    company_name="ContradictedCo",
    company_website_url="https://contradicted.com",
    github_repo_slugs=["carolwu/eval-framework"],
    accelerator=None,
    hq_country="SG",
    sector_self_reported="DevTools",
)


async def seed_thesis() -> uuid.UUID:
    """Insert the default Maschmeyer thesis if not present."""
    thesis = default_maschmeyer_thesis()
    async with async_session() as s:
        existing = await s.execute(
            select(ThesisConfig).where(ThesisConfig.name == thesis.name)
        )
        existing_row = existing.scalars().first()
        if existing_row:
            # Mark it active
            existing_row.active = True
            await s.commit()
            return existing_row.id
        row = ThesisConfig(
            id=thesis.id,
            name=thesis.name,
            sectors=thesis.sectors,
            stage=thesis.stage,
            geography=thesis.geography,
            check_size_usd=thesis.check_size_usd,
            ownership_target_pct=thesis.ownership_target_pct,
            risk_appetite=thesis.risk_appetite.model_dump(),
            active=True,
        )
        s.add(row)
        await s.commit()
        return row.id


async def seed_application(app: ApplicationCreate) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    """Insert a founder + company + application. Returns (founder_id, company_id, app_id)."""
    founder_id = uuid.uuid4()
    company_id = uuid.uuid4()
    app_id = uuid.uuid4()
    async with async_session() as s:
        founder = Founder(
            id=founder_id,
            name=app.founder_name,
            email=app.founder_email,
            bio_text=app.founder_bio_text,
        )
        company = Company(
            id=company_id,
            founder_id=founder_id,
            name=app.company_name,
            website_url=str(app.company_website_url) if app.company_website_url else None,
            hq_country=app.hq_country,
            sector_self_reported=app.sector_self_reported,
        )
        application = ApplicationORM(
            id=app_id,
            founder_id=founder_id,
            company_id=company_id,
            received_at=datetime.utcnow(),
            status="pending",
            raw_payload=app.model_dump(mode="json"),
        )
        s.add(founder)
        s.add(company)
        s.add(application)
        await s.commit()
    return founder_id, company_id, app_id


async def main():
    print("Seeding fixtures...")
    # Create tables if they don't exist (idempotent — for dev only)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    thesis_id = await seed_thesis()
    print(f"  Thesis: {thesis_id}")

    fid, cid, aid = await seed_application(COLD_START_APP)
    print(f"  Cold-start founder: {fid} (app={aid})")

    fid, cid, aid = await seed_application(VERIFIED_APP)
    print(f"  Verified founder: {fid} (app={aid})")

    fid, cid, aid = await seed_application(CONTRADICTED_APP)
    print(f"  Contradicted founder: {fid} (app={aid})")

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
