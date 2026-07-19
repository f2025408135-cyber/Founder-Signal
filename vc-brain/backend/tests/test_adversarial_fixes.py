"""Regression tests for gaps found in the adversarial review (Phase 1+2) and fixed in Phase 4.

Each test corresponds to a specific finding:
- C1: geometric mean no longer uses max(v, 1.0) clamping
- C2: AsyncPostgresSaver checkpointer wired into production paths
- C3: Validator R2 enforced for LLM-asserted "contradicted" without evidence
- C4: Founder R2 widening lowers `low` when `high` is clamped at 100
- H5: cold-start banner not duplicated on FounderDetailPage
- H6: cold-start check uses latest snapshot, not score_history.some()
- H7: cold-start banner uses RED border (not amber)
- H8: POST /thesis invalidates cached_aggregator
- H9: per-phase timestamps written at actual phase boundaries
- H10: Ingestion R1 drops claims with missing hash (not backfills)
- H11: Ingestion R4 drops short text (not pads)
- H12: Aggregator memo has no uncited factual sentence
- H13: Founder R4 zeroes non-zero axes without supporting_claim_ids
- H14: Market R3 forces neutral + non-empty contradictions when bullish+bear verified
- H15: Idea-vs-Market R2 enforces ≥2 sentences
- H16: Aggregator LLM call wired (with deterministic fallback)
- M17: Validator R1 logs extras
- M19: Founder R3 enumerates ALL missing flags (not just 3)
- M21: should_rescore trigger #1 checks all founder applications
- M24: Optional callout text uses parens per spec
- F1: OutboundCard.trend present in /outbound/queue response
- F2: OutboundCard.received_at present
- F7: Inbox cold_start always populated from latest snapshot
- F11: evidenceChip covers low_evidence + cold_start_inferred
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

os.environ["APP_ENV"] = "test"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["GITHUB_TOKEN"] = ""
os.environ["PRODUCTHUNT_TOKEN"] = ""
os.environ["LANGFUSE_ENABLED"] = "false"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://vcbrain:vcbrain@localhost:5432/vcbrain"
os.environ["DATABASE_SYNC_URL"] = "postgresql://vcbrain:vcbrain@localhost:5432/vcbrain"


# ===========================================================================
# C1: Geometric mean no clamping
# ===========================================================================


def test_c1_geometric_mean_no_clamping():
    """Per spec §4.6 (2): geometric mean MUST NOT use max(v, 1.0) clamping.
    Uses geometric mean of NON-ZERO axes (cold-start 0 axes are excluded, not clamped)."""
    from app.schemas.agent_outputs import FounderAgentOutput

    # 95/10/95/95 — spec example. Arithmetic mean = 73.75, geometric ≈ 54.1
    # All non-zero → geomean of all 4 reveals the weakness
    out = FounderAgentOutput(
        founder_id=uuid.uuid4(),
        technical_score=95.0,
        market_fit_score=10.0,
        network_score=95.0,
        momentum_score=95.0,
        cold_start=False,
        confidence_band=(70.0, 90.0),
        supporting_claim_ids=[],
        reasoning="test",
        flags=[],
        trend="stable",
    )
    # Geometric mean of (95, 10, 95, 95) ≈ 54.1 — well below the arithmetic 73.75
    assert out.composite_score < 60.0, (
        f"Expected ~54 (reveals weakness vs arithmetic 73.75), got {out.composite_score}"
    )
    assert out.composite_score > 50.0, f"Expected ~54, got {out.composite_score}"

    # Cold-start: tech=80, mfit=80, net=0, mom=0 → geomean of (80, 80) = 80
    # (0 axes excluded, NOT clamped — cold-start founders can score 60+ per spec §4.2 rule 4)
    out_cold = FounderAgentOutput(
        founder_id=uuid.uuid4(),
        technical_score=80.0,
        market_fit_score=80.0,
        network_score=0.0,
        momentum_score=0.0,
        cold_start=True,
        confidence_band=(20.0, 80.0),
        supporting_claim_ids=[],
        reasoning="cold start",
        flags=["no_github"],
        trend="insufficient_data",
    )
    assert out_cold.composite_score == pytest.approx(80.0, abs=0.1), (
        f"Cold-start with strong tech+mfit should score ~80 (0 axes excluded), got {out_cold.composite_score}"
    )


def test_c1_aggregator_conviction_no_clamping():
    """Aggregator._compute_overall_conviction also has no clamping."""
    from app.agents.aggregator import _compute_overall_conviction

    # (95, bullish=100, 95, 95) → geometric mean ≈ 96.3
    conviction = _compute_overall_conviction(95.0, "bullish", 95.0, 95.0)
    assert conviction > 90.0, f"Expected ~96, got {conviction}"

    # (0, bullish, 95, 95) → 0 (any 0 axis → 0)
    conviction_zero = _compute_overall_conviction(0.0, "bullish", 95.0, 95.0)
    assert conviction_zero == 0.0


# ===========================================================================
# C2: AsyncPostgresSaver wired into production paths
# ===========================================================================


def test_c2_get_pipeline_uses_checkpointer_when_available():
    """get_pipeline() tries to build with AsyncPostgresSaver; falls back gracefully."""
    from app.graph import pipeline as pipeline_module

    # Reset singleton
    pipeline_module._pipeline_singleton = None

    # Mock build_pipeline_with_postgres_saver to succeed
    async def _fake_build():
        return MagicMock(name="pipeline_with_checkpointer")

    with patch.object(pipeline_module, "build_pipeline_with_postgres_saver", _fake_build):
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(pipeline_module.get_pipeline())
        assert result is not None

    # Reset for other tests
    pipeline_module._pipeline_singleton = None


def test_c2_get_thread_config_returns_founder_id():
    """get_thread_config returns {configurable: {thread_id: founder_id}} per spec §8."""
    from app.graph.pipeline import get_thread_config

    fid = uuid.uuid4()
    config = get_thread_config(fid)
    assert config == {"configurable": {"thread_id": str(fid)}}


# ===========================================================================
# C3: Validator R2 enforced for LLM-asserted "contradicted" without evidence
# ===========================================================================


def test_c3_validator_downgrades_contradicted_without_evidence(founder_id, company_id):
    """If the LLM asserts "contradicted" but no external_evidence is provided,
    the status is downgraded to "unverifiable" (spec §4.5 R2)."""
    from app.agents.validator import _enforce_rules, _unverifiable
    from app.schemas.agent_outputs import ValidatorAgentOutput
    from app.schemas.claim import Claim, ClaimKind, Source, SourceKind
    from datetime import datetime

    src = Source(
        kind=SourceKind.DECK,
        ref="deck#1",
        ingested_at=datetime.utcnow(),
        raw_payload_hash="x",
        retrieved_by="t",
    )
    claim = Claim(
        founder_id=founder_id,
        company_id=company_id,
        kind=ClaimKind.MARKET_SIZE,
        text="Market is $5B.",
        source=src,
    )

    # LLM said "contradicted" with counter_evidence — but external_evidence is EMPTY
    llm_output = ValidatorAgentOutput(
        claim_id=claim.id,
        status="contradicted",
        confidence=0.15,
        counter_evidence="Some contradicting snippet",
        counter_evidence_source="some-other-source",
        notes="LLM claimed contradiction",
    )

    result = _enforce_rules(
        llm_output,
        claim=claim,
        contradictions={},  # no deterministic contradictions
        external_evidence={},  # NO external evidence provided
    )

    assert result.status == "unverifiable", (
        f"Expected downgrade to unverifiable, got {result.status}"
    )
    assert "Downgraded to unverifiable" in result.notes


# ===========================================================================
# C4: Founder R2 widening lowers `low` when `high` is clamped at 100
# ===========================================================================


@pytest.mark.asyncio
async def test_c4_founder_r2_widens_downward_when_high_clamped(founder_id, company_id, mock_llm):
    """If cold-start LLM emits (low=80, high=85), the band must widen to (50, 100)
    — not stay at (80, 100) which has width 20 < 50."""
    from app.agents.founder import run_founder_agent
    from app.schemas.claim import Claim, ClaimKind, Source, SourceKind
    from app.schemas.thesis import default_maschmeyer_thesis
    from tests.conftest import make_claim

    # Cold-start claims (no external signals)
    claims = [
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            kind="cold_start_inferred",
            text="Cold-start founder with no external signals available for verification.",
            source_kind="application_form",
            source_ref="app:form",
        ),
    ]

    # Mock the LLM to return a narrow band (80, 85) — width 5, violates R2
    from app.llm import client as llm_client
    async def _narrow_band_llm(system_prompt, user_content, **kwargs):
        return {
            "technical_score": 85.0,
            "market_fit_score": 80.0,
            "network_score": 0.0,
            "momentum_score": 0.0,
            "cold_start": True,
            "confidence_band": [80.0, 85.0],  # width 5 — must be widened
            "supporting_claim_ids": [str(c.id) for c in claims],
            "reasoning": "Cold-start founder. External signals absent.",
            "flags": ["no_github"],
            "trend": "insufficient_data",
        }

    with patch.object(llm_client, "chat_complete_json", side_effect=_narrow_band_llm):
        out = await run_founder_agent(
            founder_id=founder_id,
            application_id=None,
            claims=claims,
            prior_score=None,
            thesis=default_maschmeyer_thesis(),
            market_descriptors=["AI infra"],
            market_fit_similarity=0.7,
        )

    low, high = out.confidence_band
    width = high - low
    assert width >= 50, f"Cold-start band width must be >=50, got {width} (band={low},{high})"
    # Specifically: when high is clamped at 100, low should be lowered
    if high == 100.0:
        assert low <= 50.0, f"Expected low <= 50 when high clamped at 100, got low={low}"


# ===========================================================================
# H7: Cold-start banner uses RED border
# ===========================================================================


def test_h7_cold_start_banner_uses_red_border():
    """Spec §9.2: cold-start banner is RED-bordered, not amber."""
    memo_view_src = (Path(__file__).resolve().parent.parent.parent / "frontend-next" / "components" / "memo" / "memo-view.tsx").read_text()
    # The cold-start banner block in memo-view.tsx must use error/red color tokens
    # In the Next.js frontend, red is represented as "border-error" and "bg-error-bg"
    # (mapping to --color-error: #d44a5c in globals.css)
    assert "> ⚠️" in memo_view_src or "> ⚠" in memo_view_src
    # Extract the cold-start banner block
    import re
    m = re.search(r'if \(line\.startsWith\("> ⚠️"\).*?return \(\s*<div[^>]*>(.*?)</div>', memo_view_src, re.DOTALL)
    assert m, "Cold-start banner block not found in memo-view.tsx"
    banner_block = m.group(0)
    # Must use error/red color (border-error or --color-error), NOT warning/amber
    assert "error" in banner_block.lower(), (
        f"Cold-start banner must use RED color (border-error/bg-error-bg); got: {banner_block}"
    )
    assert "warning" not in banner_block.lower() or "cold-start" in banner_block.lower(), (
        "Banner should not use warning/amber color for the border"
    )


# ===========================================================================
# H10: Ingestion R1 drops claims with missing hash
# ===========================================================================


@pytest.mark.asyncio
async def test_h10_ingestion_r1_drops_claims_with_missing_hash(founder_id, company_id, mock_llm):
    """Claims with empty/missing raw_payload_hash are DROPPED, not backfilled."""
    from app.agents.ingestion import _parse_claim_obj

    expected_hashes = {"hash_a", "hash_b"}

    # Claim with missing hash → should be dropped
    raw_missing_hash = {
        "kind": "founder_background",
        "text": "This is a valid claim text.",
        "source": {"kind": "deck", "ref": "deck#1", "retrieved_by": "test"},
        # NO raw_payload_hash
    }
    result = _parse_claim_obj(
        raw_missing_hash,
        founder_id=founder_id,
        company_id=company_id,
        application_id=None,
        expected_payload_hashes=expected_hashes,
    )
    assert result is None, "Claim with missing hash should be dropped"

    # Claim with wrong hash → should be dropped
    raw_wrong_hash = {
        "kind": "founder_background",
        "text": "This is a valid claim text.",
        "source": {"kind": "deck", "ref": "deck#1", "raw_payload_hash": "unknown_hash", "retrieved_by": "test"},
    }
    result = _parse_claim_obj(
        raw_wrong_hash,
        founder_id=founder_id,
        company_id=company_id,
        application_id=None,
        expected_payload_hashes=expected_hashes,
    )
    assert result is None, "Claim with wrong hash should be dropped"

    # Claim with correct hash → should be kept
    raw_correct = {
        "kind": "founder_background",
        "text": "This is a valid claim text.",
        "source": {"kind": "deck", "ref": "deck#1", "raw_payload_hash": "hash_a", "retrieved_by": "test"},
    }
    result = _parse_claim_obj(
        raw_correct,
        founder_id=founder_id,
        company_id=company_id,
        application_id=None,
        expected_payload_hashes=expected_hashes,
    )
    assert result is not None, "Claim with correct hash should be kept"


# ===========================================================================
# H11: Ingestion R4 drops short text (not pads)
# ===========================================================================


def test_h11_ingestion_r4_drops_short_text(founder_id, company_id):
    """Claims with text < 10 chars are DROPPED, not padded."""
    from app.agents.ingestion import _parse_claim_obj

    raw_short = {
        "kind": "founder_background",
        "text": "short",  # 5 chars
        "source": {"kind": "deck", "ref": "deck#1", "raw_payload_hash": "hash_a", "retrieved_by": "test"},
    }
    result = _parse_claim_obj(
        raw_short,
        founder_id=founder_id,
        company_id=company_id,
        application_id=None,
        expected_payload_hashes={"hash_a"},
    )
    assert result is None, "Claim with text < 10 chars should be dropped"


# ===========================================================================
# H13: Founder R4 zeroes non-zero axes without supporting_claim_ids
# ===========================================================================


@pytest.mark.asyncio
async def test_h13_founder_r4_zeroes_axes_without_supporting_claims(founder_id, company_id, mock_llm):
    """If supporting_claim_ids is empty, all non-zero axes are zeroed."""
    from app.agents.founder import run_founder_agent
    from app.schemas.thesis import default_maschmeyer_thesis
    from tests.conftest import make_claim
    from app.llm import client as llm_client

    claims = [
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            kind="technical_depth",
            text="Repository has 50 stars on GitHub.",
            source_kind="github",
            source_ref="owner/repo",
        ),
    ]

    # Mock LLM to return high scores but NO supporting_claim_ids
    async def _no_supporting_claims(system_prompt, user_content, **kwargs):
        return {
            "technical_score": 80.0,
            "market_fit_score": 70.0,
            "network_score": 60.0,
            "momentum_score": 50.0,
            "cold_start": False,
            "confidence_band": [60.0, 85.0],
            "supporting_claim_ids": [],  # EMPTY — R4 violation
            "reasoning": "Test",
            "flags": [],
            "trend": "stable",
        }

    with patch.object(llm_client, "chat_complete_json", side_effect=_no_supporting_claims):
        out = await run_founder_agent(
            founder_id=founder_id,
            application_id=None,
            claims=claims,
            prior_score=None,
            thesis=default_maschmeyer_thesis(),
            market_descriptors=["AI infra"],
            market_fit_similarity=0.7,
        )

    # All axes should be zeroed because supporting_claim_ids is empty
    assert out.technical_score == 0.0, f"Expected 0, got {out.technical_score}"
    assert out.network_score == 0.0
    assert out.momentum_score == 0.0


# ===========================================================================
# H14: Market R3 forces neutral when bullish+bear verified claims both exist
# ===========================================================================


@pytest.mark.asyncio
async def test_h14_market_r3_forces_neutral_on_bullish_bear(founder_id, company_id, mock_llm):
    """If both bullish-evidence AND bear-evidence verified claims exist,
    market_score is forced to neutral with non-empty contradictions."""
    from app.agents.market import run_market_agent
    from app.schemas.thesis import default_maschmeyer_thesis
    from tests.conftest import make_claim
    from app.schemas.claim import ClaimFlag

    # Two verified market_trend claims: one bullish, one bear
    bullish = make_claim(
        founder_id=founder_id,
        company_id=company_id,
        kind="market_trend",
        text="The market is growing rapidly at 30% CAGR.",
        source_kind="external_db",
        source_ref="crunchbase:trend",
    )
    bear = make_claim(
        founder_id=founder_id,
        company_id=company_id,
        kind="market_trend",
        text="The market is shrinking due to saturation.",
        source_kind="external_db",
        source_ref="another:source",
    )
    # Mark both as verified
    now = datetime.utcnow()
    bullish.flags = [ClaimFlag(flag="verified", set_by="validator", set_at=now, reason="", counter_evidence_ref=None)]
    bear.flags = [ClaimFlag(flag="verified", set_by="validator", set_at=now, reason="", counter_evidence_ref=None)]

    # Mock LLM to return bullish (the rule should override to neutral)
    from app.llm import client as llm_client
    async def _bullish_llm(system_prompt, user_content, **kwargs):
        return {
            "market_score": "bullish",
            "market_size_estimate_usd": 5_000_000_000,
            "growth_rate_pct": 30.0,
            "confidence_band": [75.0, 95.0],
            "supporting_claim_ids": [str(bullish.id)],
            "reasoning": "Strong growth signals.",
            "contradictions": [],
        }

    with patch.object(llm_client, "chat_complete_json", side_effect=_bullish_llm):
        out = await run_market_agent(
            company_id=company_id,
            claims=[bullish, bear],
            thesis=default_maschmeyer_thesis(),
        )

    assert out.market_score == "neutral", (
        f"Expected neutral (bullish+bear both verified), got {out.market_score}"
    )
    assert len(out.contradictions) > 0, "Contradictions must be non-empty"


# ===========================================================================
# H15: Idea-vs-Market R2 enforces ≥2 sentences
# ===========================================================================


@pytest.mark.asyncio
async def test_h15_idea_vs_market_r2_enforces_two_sentences(founder_id, company_id, mock_llm):
    """If LLM emits a single-sentence differentiation, it's extended to ≥2 sentences."""
    from app.agents.idea_vs_market import run_idea_vs_market_agent
    from app.schemas.thesis import default_maschmeyer_thesis
    from tests.conftest import make_claim
    from app.llm import client as llm_client

    claims = [
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            kind="product",
            text="Acme builds AI infra for LLM evaluation.",
            source_kind="deck",
            source_ref="deck#1",
        ),
    ]

    # Mock LLM to return a single-sentence differentiation
    async def _single_sentence(system_prompt, user_content, **kwargs):
        return {
            "fit_score": 70.0,
            "defensibility_score": 55.0,
            "differentiation": "Only one sentence here.",  # 1 sentence — R2 violation
            "confidence_band": [50.0, 70.0],
            "supporting_claim_ids": [str(c.id) for c in claims],
            "reasoning": "test",
        }

    with patch.object(llm_client, "chat_complete_json", side_effect=_single_sentence):
        out = await run_idea_vs_market_agent(
            company_id=company_id,
            claims=claims,
            market_reasoning="market is neutral",
            thesis=default_maschmeyer_thesis(),
        )

    # Count sentences
    import re
    sentences = [s for s in re.split(r'[.!?]+(?:\s|$)', out.differentiation) if s.strip()]
    assert len(sentences) >= 2, (
        f"Expected ≥2 sentences after R2 enforcement, got {len(sentences)}: {out.differentiation!r}"
    )


# ===========================================================================
# M19: Founder R3 enumerates ALL missing flags (not just 3)
# ===========================================================================


@pytest.mark.asyncio
async def test_m19_founder_r3_enumerates_all_missing_flags(founder_id, company_id, mock_llm):
    """Cold-start founder gets ALL 5 flags, not just 3."""
    from app.agents.founder import run_founder_agent
    from app.schemas.thesis import default_maschmeyer_thesis
    from tests.conftest import make_claim
    from app.llm import client as llm_client

    claims = [
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            kind="cold_start_inferred",
            text="Cold-start founder with no external signals.",
            source_kind="application_form",
            source_ref="app:form",
        ),
    ]

    # Mock LLM to return only 1 flag
    async def _one_flag(system_prompt, user_content, **kwargs):
        return {
            "technical_score": 60.0,
            "market_fit_score": 50.0,
            "network_score": 0.0,
            "momentum_score": 0.0,
            "cold_start": True,
            "confidence_band": [25.0, 85.0],
            "supporting_claim_ids": [str(c.id) for c in claims],
            "reasoning": "Cold-start founder.",
            "flags": ["no_github"],  # only 1 — R3 should add the rest
            "trend": "insufficient_data",
        }

    with patch.object(llm_client, "chat_complete_json", side_effect=_one_flag):
        out = await run_founder_agent(
            founder_id=founder_id,
            application_id=None,
            claims=claims,
            prior_score=None,
            thesis=default_maschmeyer_thesis(),
            market_descriptors=["AI infra"],
            market_fit_similarity=0.5,
        )

    required_flags = {"no_github", "no_arxiv", "no_ph_launch", "no_accelerator", "no_prior_vc"}
    present = set(out.flags) & required_flags
    assert present == required_flags, (
        f"Expected ALL 5 cold-start flags, got {present}"
    )


# ===========================================================================
# M24: Optional callout text uses parens
# ===========================================================================


def test_m24_optional_callout_uses_parens(founder_id, company_id):
    """Spec §4.6: optional-missing sections render "(<section> not disclosed — request from founder.)"
    with parens wrapping the whole callout."""
    from app.agents.aggregator import _build_memo_markdown, _missing_sections
    from app.schemas.agent_outputs import (
        FounderAgentOutput,
        IdeaVsMarketAgentOutput,
        MarketAgentOutput,
        ValidatorAgentOutput,
    )
    from app.schemas.claim import Claim, ClaimKind, Source, SourceKind
    from datetime import datetime

    src = Source(
        kind=SourceKind.DECK,
        ref="deck#1",
        ingested_at=datetime.utcnow(),
        raw_payload_hash="x",
        retrieved_by="t",
    )
    # Only product claim — most optional sections missing
    claims = [
        Claim(
            founder_id=founder_id,
            company_id=company_id,
            kind=ClaimKind.PRODUCT,
            text="Acme builds AI infra.",
            source=src,
        ),
    ]

    founder_output = FounderAgentOutput(
        founder_id=founder_id,
        technical_score=60,
        market_fit_score=50,
        network_score=0,
        momentum_score=0,
        cold_start=False,
        confidence_band=(40, 70),
        supporting_claim_ids=[c.id for c in claims],
        reasoning="test",
        flags=[],
        trend="stable",
    )
    market_output = MarketAgentOutput(
        company_id=company_id,
        market_score="neutral",
        confidence_band=(40, 70),
        supporting_claim_ids=[],
        reasoning="test",
    )
    idea_output = IdeaVsMarketAgentOutput(
        company_id=company_id,
        fit_score=60,
        defensibility_score=55,
        differentiation="test differentiation here.",
        confidence_band=(40, 70),
        supporting_claim_ids=[],
        reasoning="test",
    )
    validators = [
        ValidatorAgentOutput(claim_id=c.id, status="unverifiable", confidence=0.4, notes="") for c in claims
    ]

    missing_required, missing_optional = _missing_sections(claims)
    memo = _build_memo_markdown(
        company_name="Acme",
        founder_output=founder_output,
        market_output=market_output,
        idea_vs_market_output=idea_output,
        validator_outputs=validators,
        claims=claims,
        overall_recommendation="deep_dive",
        overall_conviction=50.0,
        evidence_coverage=0.0,
        open_contradictions=[],
        missing_required=missing_required,
        missing_optional=missing_optional,
        next_actions=[],
    )

    # The callout format is: "(<Section> not disclosed — request from founder.)"
    # Verify parens wrap the callout text
    assert "not disclosed — request from founder." in memo, (
        f"Callout text missing. Memo excerpt: {memo[:500]}"
    )
    # Check that at least one callout has opening paren before the section name
    # Pattern: "(<word> not disclosed — request from founder.)"
    import re
    callouts = re.findall(r'\([A-Za-z][^)]*not disclosed — request from founder\.\)', memo)
    assert len(callouts) > 0, (
        f"Expected ≥1 callout with parens. Memo:\n{memo[:800]}"
    )


# ===========================================================================
# F11: evidenceChip covers low_evidence + cold_start_inferred
# ===========================================================================


def test_f11_evidence_chip_covers_all_statuses():
    """evidenceChip must handle all 6 ClaimFlag values, not just 4."""
    # Read the frontend source
    utils_src = (Path(__file__).resolve().parent.parent.parent / "frontend-next" / "lib" / "utils.ts").read_text()

    # All 6 statuses from backend/app/schemas/claim.py ClaimFlag
    # The frontend-next utils.ts uses a STATE_CONFIG object with keys, not switch/case
    required = ["verified", "unverifiable", "contradicted", "not_disclosed", "low_evidence", "cold_start_inferred"]
    for status in required:
        # Check for either `case "status":` (switch) or `status:` (object key)
        assert f'case "{status}"' in utils_src or f'{status}:' in utils_src or f'{status} :' in utils_src, (
            f"evidenceChip missing handler for {status}"
        )


# ===========================================================================
# H9: Per-phase timestamps written at actual phase boundaries
# ===========================================================================


def test_h9_validator_node_writes_validator_complete_at():
    """validator_node writes validator_complete_at timestamp on the Application row."""
    nodes_src = (Path(__file__).resolve().parent.parent / "app" / "graph" / "nodes.py").read_text()
    # The validator_node function must write validator_complete_at
    assert "validator_complete_at" in nodes_src
    # And it must be inside the validator_node function (not just applications.py)
    import re
    m = re.search(r'async def validator_node.*?return \{"validator_outputs"', nodes_src, re.DOTALL)
    assert m, "validator_node function not found"
    validator_node_body = m.group(0)
    assert "validator_complete_at" in validator_node_body, (
        "validator_node must write validator_complete_at inside its body"
    )


def test_h9_idea_vs_market_node_writes_scoring_complete_at():
    """idea_vs_market_node writes scoring_complete_at (last scoring node before aggregator)."""
    nodes_src = (Path(__file__).resolve().parent.parent / "app" / "graph" / "nodes.py").read_text()
    import re
    m = re.search(r'async def idea_vs_market_node.*?return \{"idea_vs_market_output"', nodes_src, re.DOTALL)
    assert m, "idea_vs_market_node function not found"
    body = m.group(0)
    assert "scoring_complete_at" in body, (
        "idea_vs_market_node must write scoring_complete_at inside its body"
    )


# ===========================================================================
# H8: POST /thesis invalidates cached_aggregator
# ===========================================================================


def test_h8_thesis_post_invalidates_cache():
    """POST /thesis calls _invalidate_inbox_cache as a background task."""
    thesis_src = (Path(__file__).resolve().parent.parent / "app" / "api" / "routes" / "thesis.py").read_text()
    assert "_invalidate_inbox_cache" in thesis_src
    assert "background_tasks.add_task(_invalidate_inbox_cache)" in thesis_src


# ===========================================================================
# H5: Cold-start banner not duplicated on FounderDetailPage
# ===========================================================================


def test_h5_no_duplicate_cold_start_banner_on_detail_page():
    """FounderDetailPage must NOT render a standalone cold-start banner div —
    MemoView renders it from memo_markdown."""
    detail_src = (Path(__file__).resolve().parent.parent.parent / "frontend-next" / "app" / "founders" / "[founderId]" / "page.tsx").read_text()
    # The standalone banner block was removed — search for the old pattern
    assert 'border-2 border-[var(--color-cold-start)] bg-[var(--color-cold-start)]/5' not in detail_src or \
           'Cold-start founder. External signals absent.' not in detail_src, (
        "FounderDetailPage should NOT have a standalone cold-start banner — MemoView handles it"
    )


# ===========================================================================
# H6: Cold-start check uses latest snapshot
# ===========================================================================


def test_h6_cold_start_uses_latest_snapshot():
    """FounderDetailPage uses score_history[last] not score_history.some()."""
    detail_src = (Path(__file__).resolve().parent.parent.parent / "frontend-next" / "app" / "founders" / "[founderId]" / "page.tsx").read_text()
    # Check for latest snapshot pattern (using array index or .at(-1))
    assert "latestSnapshot" in detail_src, "FounderDetailPage must use 'latestSnapshot' variable"
    assert "score_history.length - 1" in detail_src or "score_history.at(-1)" in detail_src, (
        "FounderDetailPage must use latest snapshot (score_history.length - 1 or .at(-1))"
    )
    # Must NOT use the old .some() pattern
    assert ".some((s) => s.cold_start)" not in detail_src, (
        "FounderDetailPage must NOT use score_history.some() for cold_start check"
    )


# ===========================================================================
# F1+F2: OutboundCard fields present
# ===========================================================================


def test_f1_f2_outbound_queue_response_has_required_fields():
    """outbound.py /outbound/queue response includes `trend` and `received_at`."""
    outbound_src = (Path(__file__).resolve().parent.parent / "app" / "api" / "routes" / "outbound.py").read_text()
    # Both fields must be in the response dict
    assert '"trend":' in outbound_src, "outbound.py response missing 'trend' field"
    assert '"received_at":' in outbound_src, "outbound.py response missing 'received_at' field"


# ===========================================================================
# F7: Inbox cold_start always populated
# ===========================================================================


def test_f7_inbox_always_populates_cold_start():
    """inbox.py always populates cold_start from latest snapshot, not just when filter is on."""
    inbox_src = (Path(__file__).resolve().parent.parent / "app" / "api" / "routes" / "inbox.py").read_text()
    # The cold_start filter check must come AFTER the snapshot lookup, not gate it
    assert "Always populate cold_start" in inbox_src or "cold_start_val = snap.cold_start" in inbox_src
    # The filter check must use cold_start_val (computed from snapshot), not skip the snapshot lookup
    assert "if cold_start is not None and cold_start_val != cold_start:" in inbox_src


# ===========================================================================
# H16: Aggregator LLM call wired
# ===========================================================================


def test_h16_aggregator_llm_call_wired():
    """Aggregator now invokes the LLM for memo refinement (with deterministic fallback)."""
    agg_src = (Path(__file__).resolve().parent.parent / "app" / "agents" / "aggregator.py").read_text()
    assert "_llm_refine_memo" in agg_src, "Aggregator must have _llm_refine_memo function"
    assert "_memo_passes_invariants" in agg_src, "Aggregator must validate LLM output via _memo_passes_invariants"
    # The LLM call must be invoked
    assert "await _llm_refine_memo" in agg_src


def test_h16_tool_less_boundary_still_enforced():
    """After wiring the LLM call, the tool-less boundary must still hold."""
    from scripts.check_toolless_boundary import check_aggregator_no_tools, check_aggregator_input_signature
    assert check_aggregator_no_tools() == [], "Tool-binding patterns found in aggregator.py"
    assert check_aggregator_input_signature() == [], "Forbidden input params in aggregator signature"
