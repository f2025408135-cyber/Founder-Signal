"""LangGraph node functions — each wraps one agent.

Per spec §5.2. Pipeline wiring lives in pipeline.py.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select

from app.agents.aggregator import run_aggregator_agent
from app.agents.founder import run_founder_agent
from app.agents.idea_vs_market import run_idea_vs_market_agent
from app.agents.ingestion import run_ingestion_agent
from app.agents.market import run_market_agent
from app.agents.validator import apply_validator_outputs, run_validator_agent
from app.config import settings
from app.db.models import Application as ApplicationORM
from app.db.models import (
    AggregatorOutputORM,
    FounderScoreORM,
    FounderScoreSnapshot,
)
from app.db.session import async_session
from app.ingestion.dedupe import dedupe_claims
from app.schemas.agent_outputs import (
    AggregatorOutput,
    FounderAgentOutput,
    IdeaVsMarketAgentOutput,
    MarketAgentOutput,
    ValidatorAgentOutput,
)
from app.schemas.claim import Claim, SourceKind
from app.schemas.founder_score import FounderScore, ScoreSnapshot
from app.utils.embeddings import cosine_similarity, embed_text

logger = logging.getLogger(__name__)

# These are imported lazily inside functions to avoid circular imports.


# ---- Helpers (referenced in spec §5.2) ----


async def fetch_evidence_for_claims(claims: list[Claim]) -> dict[uuid.UUID, list[dict]]:
    """For each claim, fetch external evidence.

    For Tier A: we return a minimal stub — the dedupe layer + cross-claim
    contradiction detection already provides evidence. External evidence fetch
    (Crunchbase mock, web search) is wired in Tier B.
    """
    evidence: dict[uuid.UUID, list[dict]] = {}
    # For now, surface source-ref pairs as "evidence" for the Validator to use.
    for c in claims:
        # Treat other claims of the same kind as potential evidence
        same_kind = [
            other for other in claims
            if other.id != c.id
            and (other.kind.value if hasattr(other.kind, "value") else str(other.kind))
            == (c.kind.value if hasattr(c.kind, "value") else str(c.kind))
        ]
        if same_kind:
            evidence[c.id] = [
                {
                    "source_url": other.source.ref,
                    "snippet": other.text,
                    "retrieved_at": other.source.ingested_at.isoformat(),
                    "from_claim_id": str(other.id),
                }
                for other in same_kind[:3]
            ]
        else:
            evidence[c.id] = []
    return evidence


async def persist_founder_score_snapshot(
    founder_id: uuid.UUID,
    founder_output: FounderAgentOutput,
    *,
    trigger: str = "application",
    application_id: Optional[uuid.UUID] = None,
) -> None:
    """Append a new ScoreSnapshot to founder_scores.score_history.

    CRITICAL: this is APPEND-ONLY. We never delete or overwrite prior snapshots.

    Silently no-ops if Postgres is unavailable (e.g. in unit tests without a DB).
    """
    snapshot = ScoreSnapshot(
        founder_id=founder_id,
        score=founder_output.composite_score,
        confidence_band=founder_output.confidence_band,
        trend=founder_output.trend,  # type: ignore[arg-type]
        trigger=trigger,
        evidence_claim_ids=founder_output.supporting_claim_ids,
        component_scores={
            "technical": founder_output.technical_score,
            "market_fit": founder_output.market_fit_score,
            "network": founder_output.network_score,
            "momentum": founder_output.momentum_score,
        },
        cold_start=founder_output.cold_start,
        application_id=application_id,
    )

    try:
        async with async_session() as s:
            # 1. Upsert founder_scores aggregate row
            existing = await s.get(FounderScoreORM, founder_id)
            if existing is None:
                existing = FounderScoreORM(
                    founder_id=founder_id,
                    score_history=[snapshot.model_dump(mode="json")],
                    current_score=snapshot.model_dump(mode="json"),
                    trend=snapshot.trend.value if hasattr(snapshot.trend, "value") else str(snapshot.trend),
                    applications=[],
                    first_seen_at=datetime.utcnow(),
                    last_updated_at=datetime.utcnow(),
                )
                s.add(existing)
            else:
                existing.score_history = (existing.score_history or []) + [snapshot.model_dump(mode="json")]
                existing.current_score = snapshot.model_dump(mode="json")
                existing.trend = snapshot.trend.value if hasattr(snapshot.trend, "value") else str(snapshot.trend)
                existing.last_updated_at = datetime.utcnow()

            # 2. Append a row to founder_score_snapshots (SQL-queryable projection)
            snap_row = FounderScoreSnapshot(
                founder_id=founder_id,
                score=snapshot.score,
                confidence_band_low=snapshot.confidence_band[0],
                confidence_band_high=snapshot.confidence_band[1],
                trend=snapshot.trend.value if hasattr(snapshot.trend, "value") else str(snapshot.trend),
                trigger=snapshot.trigger,
                evidence_claim_ids=[str(c) for c in snapshot.evidence_claim_ids],
                component_scores=snapshot.component_scores,
                cold_start=snapshot.cold_start,
                application_id=application_id,
                computed_at=snapshot.computed_at,
            )
            s.add(snap_row)
            await s.commit()
    except Exception as e:
        logger.warning(
            "Could not persist FounderScore snapshot for %s (%s) — snapshot will not be in DB",
            founder_id, e
        )
        return

    logger.info(
        "Persisted FounderScore snapshot for %s (score=%.1f, cold_start=%s, trigger=%s)",
        founder_id,
        snapshot.score,
        snapshot.cold_start,
        trigger,
    )


# ---- Node functions ----


async def ingestion_node(state: dict) -> dict:
    """Fan-in raw_inputs -> atomic Claims. Runs dedupe before writing to state."""
    claims = await run_ingestion_agent(
        founder_id=state["founder_id"],
        company_id=state["company_id"],
        application_id=state.get("application_id"),
        raw_inputs=state["raw_inputs"],
    )
    claims = await dedupe_claims(claims)
    # Compute embeddings for downstream similarity + dedupe
    for c in claims:
        try:
            c.embedding = await embed_text(c.text)
        except Exception as e:
            logger.warning("embed_text failed for claim %s: %s", c.id, e)
    return {"claims": claims}


async def fetch_external_evidence_node(state: dict) -> dict:
    """For each claim, fetch external evidence (web search, Crunchbase mock).

    Returns dict[claim_id, list[evidence]]. This node MAY call external APIs;
    it is NOT the tool-less synthesizer boundary.
    """
    evidence = await fetch_evidence_for_claims(state["claims"])
    return {"external_evidence": evidence}


async def thesis_fit_node(state: dict) -> dict:
    """Compute founder-market-fit cosine similarity + thesis_fit_score.

    Runs in parallel with fetch_external_evidence; both feed into aggregator.
    """
    market_descriptors = state.get("market_descriptors") or []
    claims = state.get("claims") or []
    founder_text = " ".join(
        c.text for c in claims
        if (c.kind.value if hasattr(c.kind, "value") else str(c.kind))
        in {"founder_background", "cold_start_inferred", "product"}
    ) or " ".join(c.text for c in claims)

    founder_emb = await embed_text(founder_text)
    if market_descriptors:
        market_embs = [await embed_text(d) for d in market_descriptors]
        sims = [cosine_similarity(founder_emb, m) for m in market_embs]
        market_fit_similarity = max(sims) if sims else 0.0
    else:
        market_fit_similarity = 0.0

    thesis_fit_score = market_fit_similarity * 100  # 0-100
    return {
        "thesis_fit_score": thesis_fit_score,
        "market_fit_similarity": market_fit_similarity,
    }


async def validator_node(state: dict) -> dict:
    """Per-claim verification. Runs AFTER fetch_external_evidence."""
    outputs = await run_validator_agent(
        claims=state["claims"],
        external_evidence=state.get("external_evidence") or {},
    )
    # Apply outputs back onto claim objects in state
    claims = apply_validator_outputs(state["claims"], outputs)
    return {"validator_outputs": outputs, "claims": claims}


async def founder_node(state: dict) -> dict:
    """Reads Validator-flagged claims. Runs in parallel with market + idea_vs_market."""
    out = await run_founder_agent(
        founder_id=state["founder_id"],
        application_id=state.get("application_id"),
        claims=state["claims"],
        prior_score=state.get("prior_founder_score"),
        thesis=state["thesis"],
        market_descriptors=state.get("market_descriptors") or [],
        market_fit_similarity=state.get("market_fit_similarity", 0.0),
    )
    return {"founder_output": out}


async def market_node(state: dict) -> dict:
    out = await run_market_agent(
        company_id=state["company_id"],
        claims=state["claims"],
        thesis=state["thesis"],
    )
    return {"market_output": out}


async def idea_vs_market_node(state: dict) -> dict:
    """Runs AFTER market — reads market_output.reasoning."""
    market_output: MarketAgentOutput = state["market_output"]
    out = await run_idea_vs_market_agent(
        company_id=state["company_id"],
        claims=state["claims"],
        market_reasoning=market_output.reasoning,
        thesis=state["thesis"],
    )
    return {"idea_vs_market_output": out}


async def aggregator_node(state: dict) -> dict:
    """TOOL-LESS SYNTHESIZER. Receives only pre-verified structured state.

    No tool access. Cannot introduce new unverified claims.
    """
    # Load company_name from DB (or from application raw_payload)
    company_name = "Outbound Lead"
    application_id = state.get("application_id")
    if application_id:
        try:
            async with async_session() as s:
                app = await s.get(ApplicationORM, application_id)
                if app and app.raw_payload:
                    company_name = app.raw_payload.get("company_name", company_name)
        except Exception as e:
            logger.warning(
                "Could not load Application %s from DB (%s) — using fallback company_name",
                application_id, e
            )

    founder_output: Optional[FounderAgentOutput] = state.get("founder_output")
    market_output: Optional[MarketAgentOutput] = state.get("market_output")
    idea_output: Optional[IdeaVsMarketAgentOutput] = state.get("idea_vs_market_output")
    validator_outputs: list[ValidatorAgentOutput] = state.get("validator_outputs") or []

    # If any upstream node failed to produce output, log + skip aggregation
    if founder_output is None or market_output is None or idea_output is None:
        logger.error(
            "aggregator_node called with missing inputs: founder=%s market=%s idea=%s",
            founder_output is not None, market_output is not None, idea_output is not None,
        )
        # Build a minimal reject output so the pipeline doesn't crash
        from app.schemas.agent_outputs import AggregatorOutput

        out = AggregatorOutput(
            founder_id=state["founder_id"],
            company_id=state["company_id"],
            application_id=application_id,
            overall_recommendation="reject",
            overall_conviction=0.0,
            axes={"founder": 0.0, "market": 0.0, "idea_vs_market": 0.0},
            axes_trends={"founder": "insufficient_data", "market": "stable", "idea_vs_market": "stable"},
            thesis_fit_score=state.get("thesis_fit_score", 0.0),
            evidence_coverage=0.0,
            open_contradictions=[],
            missing_required_sections=[],
            missing_optional_sections=[],
            memo_markdown="# Aggregator failed — missing inputs\n",
            next_actions=["Re-run pipeline after fixing upstream node failures."],
        )
        return {"aggregator_output": out}

    out: AggregatorOutput = await run_aggregator_agent(
        application_id=application_id,
        founder_id=state["founder_id"],
        company_id=state["company_id"],
        company_name=company_name,
        thesis=state["thesis"],
        founder_agent_output=founder_output,
        market_agent_output=market_output,
        idea_vs_market_agent_output=idea_output,
        validator_outputs=validator_outputs,
        claims=state["claims"],
        prior_founder_score=state.get("prior_founder_score"),
        thesis_fit_score=state["thesis_fit_score"],
    )

    # Persist new ScoreSnapshot to founder_scores (APPEND, never replace)
    await persist_founder_score_snapshot(
        state["founder_id"],
        founder_output,
        trigger="application" if application_id else "outbound_scan",
        application_id=application_id,
    )

    # Mark aggregator_complete_at on the Application row
    if application_id:
        try:
            async with async_session() as s:
                app = await s.get(ApplicationORM, application_id)
                if app:
                    app.aggregator_complete_at = datetime.utcnow()
                    app.status = {
                        "fast_pass": "fast_pass",
                        "deep_dive": "deep_dive",
                        "pass": "passed",
                        "reject": "rejected",
                    }.get(out.overall_recommendation, "screened")
                    await s.commit()
        except Exception as e:
            logger.warning(
                "Could not update Application %s status (%s) — aggregator output is still returned",
                application_id, e
            )

    return {"aggregator_output": out}
