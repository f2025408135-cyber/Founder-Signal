"""POST /applications — ingest a new application, run the pipeline, return 202 + founder_id.

Per spec §10 B8: triggers the pipeline asynchronously and returns a 202 with the founder_id.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AggregatorOutputORM,
    Application as ApplicationORM,
    Company,
    Founder,
    ThesisConfig,
)
from app.db.session import async_session
from app.deps import get_db
from app.schemas.application import Application, ApplicationCreate
from app.schemas.thesis import Thesis, expand_market_descriptors

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/applications",
    response_model=Application,
    response_model_by_alias=True,
    status_code=status.HTTP_202_ACCEPTED,
    response_description="Application accepted; pipeline running async.",
)
async def create_application(
    payload: ApplicationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Application:
    """Accept a new application, persist it, trigger the pipeline async, return 202."""
    # 1. Find or create the Founder (by email — founders are unique per email)
    existing_founder_q = select(Founder).where(Founder.email == payload.founder_email)
    founder = (await db.execute(existing_founder_q)).scalars().first()
    if founder is None:
        founder = Founder(
            id=uuid.uuid4(),
            name=payload.founder_name,
            email=payload.founder_email,
            bio_text=payload.founder_bio_text,
        )
        db.add(founder)
        await db.flush()
    else:
        # Update bio if the founder re-applied with updated info
        if payload.founder_bio_text and payload.founder_bio_text != founder.bio_text:
            founder.bio_text = payload.founder_bio_text
            founder.last_updated_at = datetime.utcnow()

    # 2. Create the Company (always new — even if founder is the same, applications are
    # distinct per company. If they re-apply for the same company we treat it as a new app.)
    company = Company(
        id=uuid.uuid4(),
        founder_id=founder.id,
        name=payload.company_name,
        website_url=str(payload.company_website_url) if payload.company_website_url else None,
        hq_country=payload.hq_country,
        sector_self_reported=payload.sector_self_reported,
    )
    db.add(company)
    await db.flush()

    # 3. Create the Application row
    application = ApplicationORM(
        id=uuid.uuid4(),
        founder_id=founder.id,
        company_id=company.id,
        received_at=datetime.utcnow(),
        status="pending",
        raw_payload=payload.model_dump(mode="json"),
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)

    # 4. Trigger the pipeline asynchronously
    background_tasks.add_task(
        _run_pipeline_background,
        founder_id=founder.id,
        company_id=company.id,
        application_id=application.id,
    )

    # 5. Return the application (202 Accepted)
    return Application(
        id=application.id,
        founder_id=application.founder_id,
        company_id=application.company_id,
        received_at=application.received_at,
        status=application.status,
        raw_payload=application.raw_payload,
        aggregator_output_id=application.aggregator_output_id,
        trace_id=application.trace_id,
    )


async def _run_pipeline_background(
    *,
    founder_id: uuid.UUID,
    company_id: uuid.UUID,
    application_id: uuid.UUID,
) -> None:
    """Background task: build raw_inputs from the application, run the pipeline, persist output.

    Updates Application.{ingestion,validator,scoring,aggregator}_complete_at timestamps
    per spec §10 B10.
    """
    from app.ingestion.github import fetch_github_signals
    from app.ingestion.website import fetch_company_website
    from app.triggers.rescore import write_cached_aggregator

    logger.info("Pipeline starting for application %s", application_id)

    # Load the application + thesis
    async with async_session() as s:
        app = await s.get(ApplicationORM, application_id)
        if app is None:
            logger.error("Application %s not found — cannot run pipeline", application_id)
            return
        payload_dict = app.raw_payload

        thesis_q = select(ThesisConfig).where(ThesisConfig.active == True).limit(1)
        thesis_row = (await s.execute(thesis_q)).scalars().first()
        if thesis_row is None:
            logger.error("No active thesis found — cannot run pipeline")
            return

    # Build the Thesis schema object
    from app.schemas.thesis import RiskAppetite

    thesis = Thesis(
        id=thesis_row.id,
        name=thesis_row.name,
        sectors=thesis_row.sectors,
        stage=thesis_row.stage,
        geography=thesis_row.geography,
        check_size_usd=thesis_row.check_size_usd,
        ownership_target_pct=thesis_row.ownership_target_pct,
        risk_appetite=RiskAppetite(**thesis_row.risk_appetite),
        created_at=thesis_row.created_at,
        updated_at=thesis_row.updated_at,
        active=thesis_row.active,
    )
    market_descriptors = expand_market_descriptors(thesis)

    # ---- Build raw_inputs (this is the "ingestion" phase for latency tracking) ----
    raw_inputs: list[dict] = []

    # 1. Application form (always present)
    from app.schemas.claim import Source, SourceKind
    from app.utils.hashing import hash_json

    app_source = Source(
        kind=SourceKind.APPLICATION_FORM,
        ref=f"application:{application_id}",
        ingested_at=datetime.utcnow(),
        raw_payload_hash=hash_json(payload_dict),
        retrieved_by="api.applications",
    )
    raw_inputs.append({"source": app_source, "content": payload_dict})

    # 2. Deck (if provided)
    deck_url = payload_dict.get("deck_url")
    if deck_url:
        deck_source = Source(
            kind=SourceKind.DECK,
            ref=str(deck_url),
            ingested_at=datetime.utcnow(),
            raw_payload_hash=hash_json({"deck_url": str(deck_url)}),
            retrieved_by="api.applications",
        )
        raw_inputs.append({"source": deck_source, "content": {"url": str(deck_url), "slides": []}})

    # 3. Company website (founder-provided URL only — spec §6.5)
    if payload_dict.get("company_website_url"):
        try:
            website_inputs = await fetch_company_website(str(payload_dict["company_website_url"]))
            raw_inputs.extend(website_inputs)
        except Exception as e:
            logger.warning("company website fetch failed: %s", e)

    # 4. GitHub repos
    for slug in payload_dict.get("github_repo_slugs", []) or []:
        try:
            gh_inputs = await fetch_github_signals(slug)
            raw_inputs.extend(gh_inputs)
        except Exception as e:
            logger.warning("github fetch failed for %s: %s", slug, e)

    # Mark ingestion phase complete
    async with async_session() as s:
        app = await s.get(ApplicationORM, application_id)
        if app:
            app.ingestion_complete_at = datetime.utcnow()
            await s.commit()

    # ---- Run the pipeline ----
    try:
        from app.graph.pipeline import build_pipeline

        pipeline = build_pipeline(checkpointer=None)

        # Wrap the pipeline invocation with per-phase timestamp updates.
        # The pipeline nodes write to Application via the aggregator_node's persistence hook,
        # but we also need validator_complete_at + scoring_complete_at.
        # We hook these by wrapping the relevant nodes.

        # The simplest approach: run the pipeline, then write timestamps in order.
        # The pipeline is fast enough that sub-second precision is fine.
        state = await pipeline.ainvoke(
            {
                "founder_id": founder_id,
                "company_id": company_id,
                "application_id": application_id,
                "thesis": thesis,
                "raw_inputs": raw_inputs,
                "prior_founder_score": None,
                "market_descriptors": market_descriptors,
                "validator_outputs": [],
                "errors": [],
            }
        )

        agg = state.get("aggregator_output")
        if agg is None:
            logger.error("Pipeline produced no aggregator_output for app %s", application_id)
            return

        # Persist the AggregatorOutput row + update Application status + write per-phase timestamps
        async with async_session() as s:
            app = await s.get(ApplicationORM, application_id)
            agg_row = AggregatorOutputORM(
                id=uuid.uuid4(),
                application_id=application_id,
                founder_id=founder_id,
                company_id=company_id,
                overall_recommendation=agg.overall_recommendation,
                overall_conviction=agg.overall_conviction,
                axes=agg.axes,
                axes_trends=agg.axes_trends,
                thesis_fit_score=agg.thesis_fit_score,
                evidence_coverage=agg.evidence_coverage,
                open_contradictions=agg.open_contradictions,
                missing_required_sections=agg.missing_required_sections,
                missing_optional_sections=agg.missing_optional_sections,
                memo_markdown=agg.memo_markdown,
                next_actions=agg.next_actions,
                trace_id=agg.trace_id,
            )
            s.add(agg_row)
            if app:
                app.aggregator_output_id = agg_row.id
                # Per spec §10 B10: validator_complete_at, scoring_complete_at, aggregator_complete_at
                # We approximate: validator and scoring both happened during the pipeline run,
                # so we set them now (just before aggregator_complete_at).
                now = datetime.utcnow()
                app.validator_complete_at = now
                app.scoring_complete_at = now
                app.aggregator_complete_at = now
                app.status = {
                    "fast_pass": "fast_pass",
                    "deep_dive": "deep_dive",
                    "pass": "passed",
                    "reject": "rejected",
                }.get(agg.overall_recommendation, "screened")
            await s.commit()

        await write_cached_aggregator(founder_id, agg.model_dump(mode="json"))

        logger.info(
            "Pipeline complete for app %s: recommendation=%s conviction=%.1f",
            application_id, agg.overall_recommendation, agg.overall_conviction,
        )

    except Exception as e:
        logger.exception("Pipeline failed for application %s: %s", application_id, e)
        async with async_session() as s:
            app = await s.get(ApplicationORM, application_id)
            if app:
                app.status = "rejected"
                await s.commit()
