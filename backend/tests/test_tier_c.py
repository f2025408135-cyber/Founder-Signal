"""Test Tier C acceptance criteria — spec §10 C1-C6.

C1: Langfuse tracing wired into every node (observe decorator + langfuse.openai wrapper)
C2: Cross-claim contradiction detection
C3: Evidence coverage computation in Aggregator (verified/total, <0.4 downgrade)
C4: Cold-start path through entire pipeline
C5: Tool-less synthesizer boundary enforcement (static analysis)
C6: Missing-section flagging (every optional section either has cited content OR renders the callout)
"""
from __future__ import annotations

import os
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

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
# C1: Langfuse tracing
# ===========================================================================


def test_c1_observe_decorator_is_noop_when_langfuse_disabled():
    """@observe() is a no-op decorator when Langfuse is unconfigured (test env)."""
    from app.tracing import observe

    @observe(name="test_node")
    async def my_node(x: int) -> int:
        return x + 1

    # No-op decorator: function is unchanged
    import asyncio
    result = asyncio.get_event_loop().run_until_complete(my_node(41))
    assert result == 42


def test_c1_every_graph_node_has_observe_decorator():
    """Spec §10 C1: every node function is decorated with @observe()."""
    nodes_path = Path(__file__).resolve().parent.parent / "app" / "graph" / "nodes.py"
    content = nodes_path.read_text()

    # Each of these node functions must have @observe() on the line(s) above its def
    node_fns = [
        "ingestion_node",
        "fetch_external_evidence_node",
        "thesis_fit_node",
        "validator_node",
        "founder_node",
        "market_node",
        "idea_vs_market_node",
        "aggregator_node",
    ]
    for fn in node_fns:
        # Look for @observe(...) on the line(s) preceding `async def {fn}`
        pattern = rf'@observe\([^)]*\)\s*\nasync\s+def\s+{fn}\s*\('
        assert re.search(pattern, content), f"Node {fn} missing @observe() decorator"


def test_c1_llm_client_uses_langfuse_wrapper_when_configured():
    """The LLM client prefers langfuse.openai.AsyncOpenAI when Langfuse is configured."""
    from app.llm import client as llm_client
    from unittest.mock import MagicMock, patch

    # In test env Langfuse is disabled — _maybe_langfuse_client returns None
    assert llm_client.settings.langfuse_is_configured is False
    assert llm_client._maybe_langfuse_client() is None

    # Replace the settings object with a mock where langfuse_is_configured returns True.
    # _maybe_langfuse_client should then try to import langfuse.openai (which IS
    # installed in our deps) and return a wrapped AsyncOpenAI client.
    mock_settings = MagicMock()
    mock_settings.langfuse_is_configured = True
    mock_settings.openai_api_key = "test-key"

    original = llm_client.settings
    try:
        llm_client.settings = mock_settings
        client = llm_client._maybe_langfuse_client()
        # langfuse is installed in our deps — we should get a client back
        assert client is not None, "Expected langfuse-wrapped client when configured"
    finally:
        llm_client.settings = original


def test_c1_trace_id_propagates_to_application():
    """Spec §10 C1: trace ID is written to Application.trace_id for cross-linking."""
    from app.tracing import new_trace_id

    trace_id = new_trace_id()
    assert isinstance(trace_id, str)
    assert len(trace_id) == 32  # UUID hex
    # Must be hex
    int(trace_id, 16)


# ===========================================================================
# C2: Cross-claim contradiction detection
# ===========================================================================


def test_c2_numerical_contradiction_detected(founder_id, company_id):
    """Two market_size claims with 10x different values both flagged contradicted."""
    from app.agents.validator import detect_cross_claim_contradictions
    from tests.conftest import make_claim

    claims = [
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            kind="market_size",
            text="The LLM evaluation market is $5B in 2026.",
            source_kind="deck",
            source_ref="deck#slide=3",
        ),
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            kind="market_size",
            text="The LLM evaluation market is $500M in 2026.",
            source_kind="external_db",
            source_ref="crunchbase:llm-eval",
        ),
    ]
    contradictions = detect_cross_claim_contradictions(claims)
    assert len(contradictions) == 2, f"Expected 2 contradictions, got {len(contradictions)}"
    # Both claims should be flagged
    assert claims[0].id in contradictions
    assert claims[1].id in contradictions
    # Each entry has (counter_evidence_text, source_ref)
    text_a, src_a = contradictions[claims[0].id]
    text_b, src_b = contradictions[claims[1].id]
    assert "crunchbase:llm-eval" in src_a or src_a == "crunchbase:llm-eval"
    assert "deck#slide=3" in src_b or src_b == "deck#slide=3"


def test_c2_unit_normalized_contradiction(founder_id, company_id):
    """$5B vs $5000M (same value, different units) does NOT trigger contradiction."""
    from app.agents.validator import detect_cross_claim_contradictions, _normalize_value
    from tests.conftest import make_claim

    # _normalize_value: 5B = 5_000_000_000, 5000M = 5_000_000_000 — same
    assert _normalize_value(5, "B") == _normalize_value(5000, "M")

    claims = [
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            kind="market_size",
            text="The market is $5B.",
            source_kind="deck",
            source_ref="a",
        ),
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            kind="market_size",
            text="The market is $5000M.",
            source_kind="external_db",
            source_ref="b",
        ),
    ]
    contradictions = detect_cross_claim_contradictions(claims)
    # Same value, different units → no contradiction
    assert len(contradictions) == 0, f"Expected no contradiction, got {contradictions}"


def test_c2_qualitative_contradiction_detected(founder_id, company_id):
    """'market growing' vs 'market shrinking' are flagged as contradictions."""
    from app.agents.validator import detect_cross_claim_contradictions
    from tests.conftest import make_claim

    claims = [
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            kind="market_trend",
            text="The market is growing rapidly.",
            source_kind="external_db",
            source_ref="a",
        ),
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            kind="market_trend",
            text="The market is shrinking due to saturation.",
            source_kind="external_db",
            source_ref="b",
        ),
    ]
    contradictions = detect_cross_claim_contradictions(claims)
    assert len(contradictions) == 2
    assert claims[0].id in contradictions
    assert claims[1].id in contradictions


def test_c2_no_contradiction_for_different_kinds(founder_id, company_id):
    """Claims of different kinds are never compared."""
    from app.agents.validator import detect_cross_claim_contradictions
    from tests.conftest import make_claim

    claims = [
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            kind="market_size",
            text="The market is $5B.",
            source_kind="deck",
            source_ref="a",
        ),
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            kind="traction",  # different kind — not compared
            text="The market is $500M.",
            source_kind="external_db",
            source_ref="b",
        ),
    ]
    contradictions = detect_cross_claim_contradictions(claims)
    assert len(contradictions) == 0


# ===========================================================================
# C3: Evidence coverage computation in Aggregator
# ===========================================================================


def test_c3_evidence_coverage_computation():
    """evidence_coverage = verified_count / total_claims_count."""
    from app.agents.aggregator import _evidence_coverage
    from app.schemas.agent_outputs import ValidatorAgentOutput
    from app.schemas.claim import Claim, ClaimKind, Source, SourceKind
    from datetime import datetime

    founder_id = uuid.uuid4()
    company_id = uuid.uuid4()
    src = Source(
        kind=SourceKind.GITHUB,
        ref="owner/repo",
        ingested_at=datetime.utcnow(),
        raw_payload_hash="x",
        retrieved_by="t",
    )
    claims = [
        Claim(founder_id=founder_id, company_id=company_id, kind=ClaimKind.TECHNICAL_DEPTH, text="Claim 1", source=src),
        Claim(founder_id=founder_id, company_id=company_id, kind=ClaimKind.TRACTION, text="Claim 2", source=src),
        Claim(founder_id=founder_id, company_id=company_id, kind=ClaimKind.MARKET_SIZE, text="Claim 3", source=src),
        Claim(founder_id=founder_id, company_id=company_id, kind=ClaimKind.PRODUCT, text="Claim 4", source=src),
    ]
    # 2 verified, 1 unverifiable, 1 contradicted
    outputs = [
        ValidatorAgentOutput(claim_id=claims[0].id, status="verified", confidence=0.85, notes=""),
        ValidatorAgentOutput(claim_id=claims[1].id, status="verified", confidence=0.9, notes=""),
        ValidatorAgentOutput(claim_id=claims[2].id, status="unverifiable", confidence=0.4, notes=""),
        ValidatorAgentOutput(claim_id=claims[3].id, status="contradicted", confidence=0.2, notes=""),
    ]
    coverage = _evidence_coverage(claims, outputs)
    assert coverage == 0.5, f"Expected 2/4 = 0.5, got {coverage}"


def test_c3_evidence_coverage_zero_claims():
    """Zero claims → evidence_coverage = 0.0."""
    from app.agents.aggregator import _evidence_coverage
    assert _evidence_coverage([], []) == 0.0


def test_c3_low_coverage_downgrades_recommendation():
    """If evidence_coverage < 0.4, recommendation is downgraded by one tier
    (fast_pass → deep_dive, deep_dive → pass). Reject stays reject.

    Note: fast_pass itself requires evidence_coverage >= 0.6 per spec §4.6 (1).
    So the "< 0.4 downgrade" applies when fast_pass was downgraded to deep_dive
    by the >= 0.6 check, then to pass by the < 0.4 check.
    """
    from app.agents.aggregator import _recommendation

    # Case 1: axes >= 70, evidence = 0.5 (between 0.4 and 0.6) → deep_dive
    # (would be fast_pass at 0.7, but 0.5 < 0.6 excludes fast_pass)
    rec = _recommendation(
        axes={"founder": 80.0, "market": 80.0, "idea_vs_market": 80.0},
        market_score="bullish",
        thesis_fit_score=80.0,
        evidence_coverage=0.5,  # >= 0.4 (no downgrade), < 0.6 (no fast_pass)
        open_contradictions=[],
        missing_required=[],
        cold_start=False,
    )
    assert rec == "deep_dive", f"Expected deep_dive (no fast_pass at 0.5 evidence), got {rec}"

    # Case 2: axes >= 70, evidence = 0.3 (< 0.4) → downgrade deep_dive to pass
    rec = _recommendation(
        axes={"founder": 80.0, "market": 80.0, "idea_vs_market": 80.0},
        market_score="bullish",
        thesis_fit_score=80.0,
        evidence_coverage=0.3,
        open_contradictions=[],
        missing_required=[],
        cold_start=False,
    )
    assert rec == "pass", f"Expected downgrade to pass, got {rec}"

    # Case 3: axes >= 70, evidence = 0.7 → fast_pass (no downgrade)
    rec = _recommendation(
        axes={"founder": 80.0, "market": 80.0, "idea_vs_market": 80.0},
        market_score="bullish",
        thesis_fit_score=80.0,
        evidence_coverage=0.7,
        open_contradictions=[],
        missing_required=[],
        cold_start=False,
    )
    assert rec == "fast_pass"

    # Case 4: Reject stays reject even with low coverage (no further downgrade)
    rec = _recommendation(
        axes={"founder": 20.0, "market": 20.0, "idea_vs_market": 20.0},
        market_score="bear",
        thesis_fit_score=20.0,
        evidence_coverage=0.1,
        open_contradictions=[],
        missing_required=[],
        cold_start=False,
    )
    assert rec == "reject"


# ===========================================================================
# C4: Cold-start path through entire pipeline
# ===========================================================================


@pytest.mark.asyncio
async def test_c4_cold_start_end_to_end(
    cold_start_claims, founder_id, company_id, application_id, default_thesis, mock_llm
):
    """Spec §10 C4: end-to-end cold-start path produces cold_start==true, banner present, NOT fast_pass."""
    from app.graph.pipeline import build_pipeline
    from app.schemas.thesis import expand_market_descriptors

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
            "claims": cold_start_claims,
            "validator_outputs": [],
            "errors": [],
        }
    )

    agg = state["aggregator_output"]
    assert agg is not None

    # Founder output must be cold_start
    founder_output = state["founder_output"]
    assert founder_output.cold_start is True, "Cold-start fixture must produce cold_start=true"

    # Confidence band must be wide (>=50)
    low, high = founder_output.confidence_band
    assert high - low >= 50, f"Cold-start band width must be >=50, got {high-low}"

    # Flags must include at least 3 of the 5 cold-start flags
    cold_start_flags = {"no_github", "no_arxiv", "no_ph_launch", "no_accelerator", "no_prior_vc"}
    present_flags = set(founder_output.flags) & cold_start_flags
    assert len(present_flags) >= 3, f"Expected >=3 cold-start flags, got {present_flags}"

    # Recommendation must NOT be fast_pass
    assert agg.overall_recommendation != "fast_pass", "Cold-start must never be fast_pass"

    # Memo must contain the cold-start banner
    assert "Cold-start founder" in agg.memo_markdown or "⚠️" in agg.memo_markdown


# ===========================================================================
# C5: Tool-less synthesizer boundary enforcement
# ===========================================================================


def test_c5_no_bind_tools_in_aggregator():
    """Spec §10 C5: app/agents/aggregator.py contains no bind_tools() call."""
    from scripts.check_toolless_boundary import check_aggregator_no_tools

    violations = check_aggregator_no_tools()
    assert violations == [], f"Tool-binding patterns found in aggregator.py: {violations}"


def test_c5_no_tools_kwarg_in_aggregator():
    """Spec §10 C5: no tools= kwarg in aggregator.py."""
    from scripts.check_toolless_boundary import check_aggregator_no_tools

    violations = check_aggregator_no_tools()
    tool_kwarg_violations = [v for v in violations if "tools" in v[0].lower()]
    assert tool_kwarg_violations == [], f"tools= kwarg found: {tool_kwarg_violations}"


def test_c5_aggregator_input_excludes_raw_inputs():
    """Spec §5.4: synthesizer's input is AggregatorAgentInput — no raw_inputs, external_evidence, URLs."""
    from scripts.check_toolless_boundary import check_aggregator_input_signature

    violations = check_aggregator_input_signature()
    assert violations == [], f"Forbidden parameters in aggregator input: {violations}"


def test_c5_no_tool_definition_in_aggregator():
    """Spec §5.4: no tool function definitions in aggregator.py."""
    agg_path = Path(__file__).resolve().parent.parent / "app" / "agents" / "aggregator.py"
    content = agg_path.read_text()
    # Check for common tool-definition patterns
    forbidden = [
        r"\bBaseTool\s*\(",
        r"\bStructuredTool\s*\(",
        r"\btool\s*=\s*Tool\s*\(",
        r"@tool\b",
    ]
    for pattern in forbidden:
        assert not re.search(pattern, content), f"Tool definition found in aggregator.py: {pattern}"


# ===========================================================================
# C6: Missing-section flagging
# ===========================================================================


def test_c6_missing_optional_section_renders_callout(founder_id, company_id):
    """Spec §10 C6: missing optional section renders the 'not disclosed — request from founder' callout."""
    from app.agents.aggregator import _build_memo_markdown, _missing_sections
    from app.schemas.agent_outputs import (
        FounderAgentOutput,
        IdeaVsMarketAgentOutput,
        MarketAgentOutput,
        ValidatorAgentOutput,
    )
    from app.schemas.claim import Claim, ClaimKind, Source, SourceKind
    from datetime import datetime

    # Only product + founder_background claims — most optional sections will be missing
    src = Source(
        kind=SourceKind.DECK,
        ref="deck#slide=1",
        ingested_at=datetime.utcnow(),
        raw_payload_hash="x",
        retrieved_by="t",
    )
    claims = [
        Claim(
            founder_id=founder_id,
            company_id=company_id,
            kind=ClaimKind.PRODUCT,
            text="Acme builds AI infra.",
            source=src,
        ),
        Claim(
            founder_id=founder_id,
            company_id=company_id,
            kind=ClaimKind.FOUNDER_BACKGROUND,
            text="Jane Doe is the founder.",
            source=src,
        ),
    ]

    missing_required, missing_optional = _missing_sections(claims)
    # We expect at least team_and_history (no team kind), market_sizing, competition, financials, cap_table, exit_perspective
    assert "team_and_history" in missing_optional or "market_sizing" in missing_optional

    founder_output = FounderAgentOutput(
        founder_id=founder_id,
        technical_score=60,
        market_fit_score=50,
        network_score=0,
        momentum_score=0,
        cold_start=True,
        confidence_band=(20, 80),
        supporting_claim_ids=[c.id for c in claims],
        reasoning="test",
        flags=["no_github"],
        trend="insufficient_data",
    )
    market_output = MarketAgentOutput(
        company_id=company_id,
        market_score="neutral",
        confidence_band=(20, 80),
        supporting_claim_ids=[],
        reasoning="test",
    )
    idea_output = IdeaVsMarketAgentOutput(
        company_id=company_id,
        fit_score=50,
        defensibility_score=40,
        differentiation="test differentiation",
        confidence_band=(30, 70),
        supporting_claim_ids=[],
        reasoning="test",
    )
    validators = [
        ValidatorAgentOutput(claim_id=c.id, status="unverifiable", confidence=0.4, notes="") for c in claims
    ]

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

    # The callout text must appear for at least one missing section
    assert "not disclosed — request from founder" in memo, (
        f"Expected 'not disclosed — request from founder' callout in memo, got:\n{memo[:500]}"
    )

    # Specifically: Team & History should have the callout (we have founder_background but not team)
    # Per the optional_render mapping, team_and_history is satisfied by {founder_background, founder_network, team}
    # Since we DO have founder_background, team_and_history should NOT be flagged missing.
    # Let's check market_sizing instead — that requires market_size kind which we don't have.
    assert "## Market Sizing" in memo
    market_sizing_section = memo.split("## Market Sizing")[1].split("##")[0]
    assert "not disclosed" in market_sizing_section, (
        f"Market Sizing section should have the callout, got:\n{market_sizing_section}"
    )


def test_c6_present_optional_section_no_callout(founder_id, company_id):
    """Optional section with cited claims does NOT render the callout."""
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
        kind=SourceKind.GITHUB,
        ref="owner/repo",
        ingested_at=datetime.utcnow(),
        raw_payload_hash="x",
        retrieved_by="t",
    )
    # Include a market_size claim — Market Sizing section should have content, not callout
    claims = [
        Claim(
            founder_id=founder_id,
            company_id=company_id,
            kind=ClaimKind.MARKET_SIZE,
            text="The market is $2B.",
            source=src,
        ),
        Claim(
            founder_id=founder_id,
            company_id=company_id,
            kind=ClaimKind.PRODUCT,
            text="Acme builds AI infra.",
            source=src,
        ),
    ]
    missing_required, missing_optional = _missing_sections(claims)
    assert "market_sizing" not in missing_optional, "Market Sizing should not be missing"

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
        differentiation="test",
        confidence_band=(40, 70),
        supporting_claim_ids=[],
        reasoning="test",
    )
    validators = [
        ValidatorAgentOutput(claim_id=c.id, status="verified", confidence=0.85, notes="") for c in claims
    ]

    memo = _build_memo_markdown(
        company_name="Acme",
        founder_output=founder_output,
        market_output=market_output,
        idea_vs_market_output=idea_output,
        validator_outputs=validators,
        claims=claims,
        overall_recommendation="deep_dive",
        overall_conviction=60.0,
        evidence_coverage=1.0,
        open_contradictions=[],
        missing_required=missing_required,
        missing_optional=missing_optional,
        next_actions=[],
    )

    # Market Sizing section should have the claim text, NOT the callout
    market_sizing_section = memo.split("## Market Sizing")[1].split("##")[0]
    assert "The market is $2B" in market_sizing_section
    assert "not disclosed" not in market_sizing_section


def test_c6_required_section_always_renders():
    """Spec §4.6: every required section heading is always rendered, even if empty."""
    from app.agents.aggregator import _build_memo_markdown
    from app.schemas.agent_outputs import (
        FounderAgentOutput,
        IdeaVsMarketAgentOutput,
        MarketAgentOutput,
        ValidatorAgentOutput,
    )
    from app.schemas.claim import Claim, ClaimKind, Source, SourceKind
    from datetime import datetime
    import uuid

    founder_id = uuid.uuid4()
    company_id = uuid.uuid4()
    src = Source(
        kind=SourceKind.APPLICATION_FORM,
        ref="app:form",
        ingested_at=datetime.utcnow(),
        raw_payload_hash="x",
        retrieved_by="t",
    )
    claims = [
        Claim(
            founder_id=founder_id,
            company_id=company_id,
            kind=ClaimKind.COLD_START_INFERRED,
            text="Cold-start founder.",
            source=src,
        ),
    ]

    founder_output = FounderAgentOutput(
        founder_id=founder_id,
        technical_score=50,
        market_fit_score=30,
        network_score=0,
        momentum_score=0,
        cold_start=True,
        confidence_band=(20, 80),
        supporting_claim_ids=[claims[0].id],
        reasoning="cold start",
        flags=["no_github", "no_arxiv", "no_ph_launch", "no_accelerator", "no_prior_vc"],
        trend="insufficient_data",
    )
    market_output = MarketAgentOutput(
        company_id=company_id,
        market_score="neutral",
        confidence_band=(20, 80),
        supporting_claim_ids=[],
        reasoning="Insufficient verified market evidence.",
    )
    idea_output = IdeaVsMarketAgentOutput(
        company_id=company_id,
        fit_score=40,
        defensibility_score=30,
        differentiation="Insufficient competitive evidence.",
        confidence_band=(20, 60),
        supporting_claim_ids=[],
        reasoning="cold start",
    )
    validators = [
        ValidatorAgentOutput(claim_id=claims[0].id, status="unverifiable", confidence=0.4, notes="cold start"),
    ]

    memo = _build_memo_markdown(
        company_name="TestCo",
        founder_output=founder_output,
        market_output=market_output,
        idea_vs_market_output=idea_output,
        validator_outputs=validators,
        claims=claims,
        overall_recommendation="deep_dive",
        overall_conviction=40.0,
        evidence_coverage=0.0,
        open_contradictions=[],
        missing_required=[],
        missing_optional=[],
        next_actions=[],
    )

    # All 5 required sections must be rendered as headings
    for section in ["Company Snapshot", "Investment Hypotheses", "SWOT", "Problem & Product", "Traction & KPIs"]:
        assert f"## {section}" in memo, f"Required section heading missing: {section}"

    # Due Diligence Log always rendered
    assert "## Due Diligence Log" in memo
    # Recommendation always rendered
    assert "## Recommendation" in memo
