"""Test schema construction + validation per spec §3.

Spec §10 A2 acceptance: `python -c "from app.schemas.claim import Claim; Claim(...)"` constructs
without error; `pytest tests/test_schemas.py` passes.
"""
from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.agent_outputs import (
    AggregatorOutput,
    FounderAgentOutput,
    IdeaVsMarketAgentOutput,
    MarketAgentOutput,
    ValidatorAgentOutput,
)
from app.schemas.application import ApplicationCreate
from app.schemas.claim import Claim, ClaimFlag, ClaimKind, Source, SourceKind
from app.schemas.founder_score import FounderScore, ScoreSnapshot, Trend
from app.schemas.thesis import RiskAppetite, Thesis, default_maschmeyer_thesis


def test_claim_constructs_minimal(founder_id, company_id):
    """Claim with only required fields constructs."""
    s = Source(
        kind=SourceKind.APPLICATION_FORM,
        ref="app:form",
        ingested_at=datetime.utcnow(),
        raw_payload_hash="abc123",
        retrieved_by="test",
    )
    c = Claim(
        founder_id=founder_id,
        company_id=company_id,
        kind=ClaimKind.FOUNDER_BACKGROUND,
        text="Founder Jane Doe has 8 years of ML experience.",
        source=s,
    )
    assert c.confidence == 0.5  # default
    assert c.flags == []
    assert c.embedding is None
    assert c.superseded_by is None
    assert c.id is not None


def test_claim_confidence_bounds(founder_id, company_id):
    """confidence must be in [0, 1]."""
    s = Source(
        kind=SourceKind.GITHUB,
        ref="owner/repo",
        ingested_at=datetime.utcnow(),
        raw_payload_hash="x",
        retrieved_by="t",
    )
    with pytest.raises(ValidationError):
        Claim(
            founder_id=founder_id,
            company_id=company_id,
            kind=ClaimKind.TECHNICAL_DEPTH,
            text="Repo has 50 stars.",
            source=s,
            confidence=1.5,
        )
    with pytest.raises(ValidationError):
        Claim(
            founder_id=founder_id,
            company_id=company_id,
            kind=ClaimKind.TECHNICAL_DEPTH,
            text="Repo has 50 stars.",
            source=s,
            confidence=-0.1,
        )


def test_claim_kind_enum_values():
    """ClaimKind has all 11 spec values."""
    expected = {
        "founder_background",
        "founder_network",
        "technical_depth",
        "market_size",
        "market_trend",
        "traction",
        "product",
        "competitive",
        "financial",
        "team",
        "cold_start_inferred",
    }
    actual = {k.value for k in ClaimKind}
    assert actual == expected


def test_source_kind_enum_values():
    """SourceKind has all 11 spec values."""
    expected = {
        "deck",
        "application_form",
        "github",
        "arxiv",
        "hackernews",
        "producthunt",
        "interview",
        "accelerator_cohort",
        "company_website",
        "founder_bio",
        "external_db",
    }
    actual = {k.value for k in SourceKind}
    assert actual == expected


def test_founder_score_append_only_semantics(founder_id):
    """FounderScore.score_history is a list — appending is the only valid mutation."""
    snap1 = ScoreSnapshot(
        founder_id=founder_id,
        score=72.0,
        confidence_band=(60.0, 80.0),
        trend=Trend.STABLE,
        trigger="application",
        evidence_claim_ids=[],
        component_scores={"technical": 75},
        cold_start=False,
    )
    snap2 = ScoreSnapshot(
        founder_id=founder_id,
        score=78.0,
        confidence_band=(70.0, 85.0),
        trend=Trend.IMPROVING,
        trigger="signal_threshold",
        evidence_claim_ids=[],
        component_scores={"technical": 80},
        cold_start=False,
    )
    fs = FounderScore(founder_id=founder_id)
    fs.score_history.append(snap1)
    fs.score_history.append(snap2)
    fs.current_score = snap2
    assert len(fs.score_history) == 2
    assert fs.current_score.score == 78.0


def test_thesis_defaults():
    """Default Maschmeyer thesis has the spec-required values."""
    t = default_maschmeyer_thesis()
    assert t.name == "Maschmeyer Group — AI Infra & DevTools"
    assert t.check_size_usd == 100_000
    assert t.ownership_target_pct == 7.5
    assert t.risk_appetite.accepts_cold_start is True
    assert t.risk_appetite.min_conviction_score == 60.0
    assert "AI infra" in t.sectors
    assert "DE" in t.geography


def test_founder_agent_output_composite_score():
    """composite_score is a geometric mean — never exceeds max axis.

    Per spec §4.6 (2): NO max(v, 1.0) clamping. A 0 axis yields composite_score=0
    to reveal the weakness (spec example: 95/10/95/95 arithmetic mean = 73.75
    looks investible; geometric mean = 52.5 reveals the weakness).
    """
    # All axes 80 → composite 80
    out = FounderAgentOutput(
        founder_id=uuid.uuid4(),
        technical_score=80.0,
        market_fit_score=80.0,
        network_score=80.0,
        momentum_score=80.0,
        cold_start=False,
        confidence_band=(70.0, 85.0),
        supporting_claim_ids=[],
        reasoning="Test",
        flags=[],
        trend="stable",
    )
    assert out.composite_score == pytest.approx(80.0, abs=0.1)

    # One axis 0 → composite 0 (reveals weakness, no clamping)
    out_zero = FounderAgentOutput(
        founder_id=uuid.uuid4(),
        technical_score=80.0,
        market_fit_score=80.0,
        network_score=0.0,  # cold-start: no network
        momentum_score=0.0,  # cold-start: no momentum
        cold_start=True,
        confidence_band=(20.0, 80.0),
        supporting_claim_ids=[],
        reasoning="Cold-start test",
        flags=["no_github", "no_arxiv"],
        trend="insufficient_data",
    )
    assert out_zero.composite_score == 0.0, (
        f"Expected composite_score=0 when any axis is 0 (no clamping); got {out_zero.composite_score}"
    )


def test_market_agent_output_numeric_score():
    """numeric_score maps bullish=100, neutral=50, bear=10."""
    for kind, expected in [("bullish", 100.0), ("neutral", 50.0), ("bear", 10.0)]:
        m = MarketAgentOutput(
            company_id=uuid.uuid4(),
            market_score=kind,  # type: ignore[arg-type]
            confidence_band=(40.0, 80.0),
            supporting_claim_ids=[],
            reasoning="test",
        )
        assert m.numeric_score == expected


def test_validator_agent_output_status_enum():
    """Validator status must be one of 4 spec values."""
    with pytest.raises(ValidationError):
        ValidatorAgentOutput(
            claim_id=uuid.uuid4(),
            status="maybe",  # type: ignore[arg-type]
            confidence=0.5,
            notes="",
        )


def test_aggregator_output_axes_never_averaged():
    """axes dict has exactly 3 keys: founder, market, idea_vs_market."""
    out = AggregatorOutput(
        founder_id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        overall_recommendation="pass",
        overall_conviction=65.0,
        axes={"founder": 72.0, "market": 50.0, "idea_vs_market": 80.0},
        axes_trends={"founder": "stable", "market": "stable", "idea_vs_market": "stable"},
        thesis_fit_score=70.0,
        evidence_coverage=0.6,
        memo_markdown="# test",
    )
    assert set(out.axes.keys()) == {"founder", "market", "idea_vs_market"}


def test_application_create_minimal():
    """ApplicationCreate with only required fields."""
    a = ApplicationCreate(
        founder_name="Jane",
        founder_email="jane@example.com",
        founder_bio_text="ML engineer",
        company_name="Acme",
        hq_country="DE",
        sector_self_reported="AI infra",
    )
    assert a.github_repo_slugs == []
    assert a.company_website_url is None
