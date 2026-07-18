"""Test the Ingestion Agent — spec §4.1 R1-R5 + cold-start rule."""
from __future__ import annotations

import uuid

import pytest

from app.agents.ingestion import run_ingestion_agent
from app.schemas.claim import ClaimKind, SourceKind


@pytest.mark.asyncio
async def test_ingestion_emits_claims_from_external_sources(
    verified_raw_inputs, founder_id, company_id, application_id, mock_llm
):
    """R1/R2: every input payload yields >=1 claim with matching raw_payload_hash."""
    claims = await run_ingestion_agent(
        founder_id=founder_id,
        company_id=company_id,
        application_id=application_id,
        raw_inputs=verified_raw_inputs,
    )
    assert len(claims) >= 5, f"Expected >=5 claims, got {len(claims)}"

    # R1: every claim's raw_payload_hash matches an input payload hash
    input_hashes = {item["source"].raw_payload_hash for item in verified_raw_inputs}
    for c in claims:
        assert c.source.raw_payload_hash in input_hashes, f"Claim {c.id} hash not in inputs"

    # R2: at least one claim per input payload
    claim_hashes = {c.source.raw_payload_hash for c in claims}
    for h in input_hashes:
        assert h in claim_hashes, f"Input hash {h} has no claim"


@pytest.mark.asyncio
async def test_ingestion_cold_start_rule(
    cold_start_raw_inputs, founder_id, company_id, application_id, mock_llm
):
    """R3: cold-start founder MUST emit at least one cold_start_inferred claim."""
    claims = await run_ingestion_agent(
        founder_id=founder_id,
        company_id=company_id,
        application_id=application_id,
        raw_inputs=cold_start_raw_inputs,
    )
    assert len(claims) >= 1, "Cold-start must emit at least 1 claim"

    # R3: at least one cold_start_inferred claim
    cold_start_claims = [c for c in claims if c.kind == ClaimKind.COLD_START_INFERRED]
    assert len(cold_start_claims) >= 1, "Must emit at least one cold_start_inferred claim"

    # Verify no external source kinds present
    external_kinds = {SourceKind.GITHUB, SourceKind.ARXIV, SourceKind.PRODUCTHUNT, SourceKind.ACCELERATOR_COHORT}
    for c in claims:
        assert c.source.kind not in external_kinds, f"Cold-start fixture should not have external claims, got {c.source.kind}"


@pytest.mark.asyncio
async def test_ingestion_text_length_rule(founder_id, company_id, mock_llm):
    """R4: claim text length in [10, 400]."""
    # Build a minimal input that exercises the rule
    from tests.conftest import make_source

    raw = [
        {
            "source": make_source(
                "application_form", "app:form", payload={"founder_name": "Test"}
            ),
            "content": {"founder_name": "Test", "company_name": "TestCo", "founder_bio_text": "x"},
        }
    ]
    claims = await run_ingestion_agent(
        founder_id=founder_id,
        company_id=company_id,
        application_id=None,
        raw_inputs=raw,
    )
    for c in claims:
        assert 10 <= len(c.text) <= 400, f"Claim text length {len(c.text)} out of bounds: {c.text!r}"


@pytest.mark.asyncio
async def test_ingestion_dedup_rule(founder_id, company_id, mock_llm):
    """R5: no two claims share (text, source.kind, source.ref)."""
    from tests.conftest import make_source

    raw = [
        {
            "source": make_source("deck", "deck#slide=1", payload={"bullet": "Founder has 8 years experience"}),
            "content": {"bullets": ["Founder has 8 years experience", "Founder has 8 years experience"]},
        }
    ]
    claims = await run_ingestion_agent(
        founder_id=founder_id,
        company_id=company_id,
        application_id=None,
        raw_inputs=raw,
    )
    triples = [(c.text, c.source.kind, c.source.ref) for c in claims]
    assert len(triples) == len(set(triples)), f"Duplicate triples found: {triples}"


@pytest.mark.asyncio
async def test_ingestion_fallback_on_llm_failure(founder_id, company_id, application_id, cold_start_raw_inputs):
    """When the LLM call fails entirely, the agent MUST still emit a cold_start_inferred claim."""
    from unittest.mock import patch

    from app.llm import client as llm_client

    async def _fail(*args, **kwargs):
        raise RuntimeError("LLM unavailable")

    with patch.object(llm_client, "chat_complete_json", side_effect=_fail):
        claims = await run_ingestion_agent(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            raw_inputs=cold_start_raw_inputs,
        )

    assert len(claims) >= 1
    assert any(c.kind == ClaimKind.COLD_START_INFERRED for c in claims)


@pytest.mark.asyncio
async def test_ingestion_empty_input_emits_cold_start(founder_id, company_id):
    """Empty raw_inputs MUST still produce a cold_start_inferred claim."""
    claims = await run_ingestion_agent(
        founder_id=founder_id,
        company_id=company_id,
        application_id=None,
        raw_inputs=[],
    )
    assert len(claims) == 1
    assert claims[0].kind == ClaimKind.COLD_START_INFERRED
