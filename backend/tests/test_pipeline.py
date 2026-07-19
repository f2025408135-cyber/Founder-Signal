"""Test the full LangGraph pipeline — spec §10 A6 + C4.

`pipeline.ainvoke({...})` runs end-to-end on a fixture founder and writes
a checkpoint row to Postgres `langgraph_checkpoints` table.

For Tier A we run without Postgres (no checkpointer) — Tier B will add the
checkpoint test against a live DB.
"""
from __future__ import annotations

import uuid

import pytest

from app.schemas.thesis import expand_market_descriptors


@pytest.mark.asyncio
async def test_pipeline_runs_end_to_end_cold_start(
    cold_start_claims, founder_id, company_id, application_id, default_thesis, mock_llm
):
    """End-to-end pipeline run on a cold-start fixture produces an AggregatorOutput
    with founder_output.cold_start==true and overall_recommendation != 'fast_pass'.
    """
    from app.graph.pipeline import build_pipeline

    pipeline = build_pipeline(checkpointer=None)
    state = await pipeline.ainvoke(
        {
            "founder_id": founder_id,
            "company_id": company_id,
            "application_id": application_id,
            "thesis": default_thesis,
            "raw_inputs": [],  # claims already built in the fixture
            "prior_founder_score": None,
            "market_descriptors": expand_market_descriptors(default_thesis),
            "claims": cold_start_claims,  # pre-populated
            "validator_outputs": [],
            "errors": [],
        }
    )

    assert state.get("aggregator_output") is not None, "AggregatorOutput must be produced"
    agg = state["aggregator_output"]
    assert agg.founder_id == founder_id
    # C4 acceptance: cold_start path produces non-fast_pass recommendation
    assert agg.overall_recommendation != "fast_pass", "Cold-start must NOT be fast_pass"
    # Cold-start banner must be present in the memo
    assert "Cold-start founder" in agg.memo_markdown or "⚠️" in agg.memo_markdown


@pytest.mark.asyncio
async def test_pipeline_runs_end_to_end_verified(
    verified_claims, founder_id, company_id, application_id, default_thesis, mock_llm
):
    """End-to-end pipeline run on a verified founder produces an AggregatorOutput."""
    from app.graph.pipeline import build_pipeline

    pipeline = build_pipeline(checkpointer=None)
    state = await pipeline.ainvoke(
        {
            "founder_id": founder_id,
            "company_id": company_id,
            "application_id": application_id,
            "thesis": default_thesis,
            "raw_inputs": [],
            "prior_founder_score": None,
            "market_descriptors": expand_market_descriptors(default_thesis),
            "claims": verified_claims,
            "validator_outputs": [],
            "errors": [],
        }
    )

    agg = state["aggregator_output"]
    assert agg is not None
    assert agg.founder_id == founder_id
    assert agg.overall_recommendation in {"pass", "deep_dive", "fast_pass", "reject"}
    # Verified founder has 4 axes
    assert set(agg.axes.keys()) == {"founder", "market", "idea_vs_market"}
    # Memo must have the due diligence log section
    assert "## Due Diligence Log" in agg.memo_markdown
    # Memo must have the recommendation section
    assert "## Recommendation" in agg.memo_markdown


@pytest.mark.asyncio
async def test_pipeline_runs_end_to_end_contradicted(
    contradicted_claims, founder_id, company_id, application_id, default_thesis, mock_llm
):
    """End-to-end pipeline run on a contradicted founder flags both market_size
    claims as 'contradicted' and surfaces them in open_contradictions."""
    from app.graph.pipeline import build_pipeline

    pipeline = build_pipeline(checkpointer=None)
    state = await pipeline.ainvoke(
        {
            "founder_id": founder_id,
            "company_id": company_id,
            "application_id": application_id,
            "thesis": default_thesis,
            "raw_inputs": [],
            "prior_founder_score": None,
            "market_descriptors": expand_market_descriptors(default_thesis),
            "claims": contradicted_claims,
            "validator_outputs": [],
            "errors": [],
        }
    )

    agg = state["aggregator_output"]
    assert agg is not None
    # C2 acceptance: cross-claim contradiction detection
    validator_outputs = state.get("validator_outputs") or []
    contradicted_ids = {o.claim_id for o in validator_outputs if o.status == "contradicted"}
    market_size_claim_ids = {
        c.id for c in contradicted_claims
        if (c.kind.value if hasattr(c.kind, "value") else str(c.kind)) == "market_size"
    }
    # Both market_size claims should be flagged as contradicted
    assert len(contradicted_ids & market_size_claim_ids) == 2, (
        f"Expected both market_size claims to be contradicted, got {contradicted_ids}"
    )
    # open_contradictions should list them
    assert len(agg.open_contradictions) >= 2


@pytest.mark.asyncio
async def test_pipeline_ingestion_to_aggregator(
    cold_start_raw_inputs, founder_id, company_id, application_id, default_thesis, mock_llm
):
    """Pipeline runs ingestion_node from raw_inputs (not pre-populated claims)."""
    from app.graph.pipeline import build_pipeline

    pipeline = build_pipeline(checkpointer=None)
    state = await pipeline.ainvoke(
        {
            "founder_id": founder_id,
            "company_id": company_id,
            "application_id": application_id,
            "thesis": default_thesis,
            "raw_inputs": cold_start_raw_inputs,
            "prior_founder_score": None,
            "market_descriptors": expand_market_descriptors(default_thesis),
            "validator_outputs": [],
            "errors": [],
        }
    )

    # Ingestion node should have produced claims
    claims = state.get("claims") or []
    assert len(claims) >= 1, "Ingestion must produce >=1 claim"

    # Aggregator must have produced output
    assert state.get("aggregator_output") is not None
