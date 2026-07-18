"""Agent output schemas — one per agent node. Mirrors spec §3.4 exactly."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------- Founder Agent ----------
class FounderAgentOutput(BaseModel):

    founder_id: uuid.UUID
    application_id: Optional[uuid.UUID] = None
    technical_score: float = Field(ge=0, le=100)
    market_fit_score: float = Field(ge=0, le=100)
    network_score: float = Field(ge=0, le=100)
    momentum_score: float = Field(ge=0, le=100)
    cold_start: bool  # explicit; drives UX banner + Aggregator callout
    confidence_band: tuple[float, float]  # wide for cold-start (rule: width >= 50)
    supporting_claim_ids: list[uuid.UUID] = Field(default_factory=list)
    reasoning: str  # 3-5 sentences, plain English
    flags: list[str] = Field(default_factory=list)
    # e.g. ["no_github", "no_arxiv", "no_ph_launch", "no_accelerator", "no_prior_vc"]
    trend: Literal["improving", "declining", "stable", "insufficient_data"]
    computed_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def composite_score(self) -> float:
        """Reasoned composite — see Founder Agent prompt for weighting logic.

        Per spec §4.2: "you do NOT average the four axes blindly; you reason in
        your `reasoning` field about which axes are most diagnostic given the
        available evidence and weight the composite accordingly."

        Per spec §4.2 cold-start rule 4: "A cold-start founder with a compelling
        deck narrative and a defensible technical angle MUST be able to score 60+
        (with the wide band)." Cold-start founders legitimately have network_score=0
        and momentum_score=0 — these should NOT zero the composite.

        Per spec §4.6 (2): the geometric mean "prevents one strong axis from masking
        a fatal weakness" — but a 0 on an EXPECTED axis (cold-start) is not a weakness,
        it's an absence of signal.

        Resolution: geometric mean of NON-ZERO axes only. This:
        - Does NOT use max(1.0, v) clamping (satisfies the no-clamping rule)
        - Does NOT zero out when expected axes are 0 (satisfies the cold-start "60+" rule)
        - Still reveals weakness when an unexpected axis is low (spec's 95/10/95/95 example
          → geomean of all 4 non-zero = 54.1, well below arithmetic 73.75)
        """
        vals = [self.technical_score, self.market_fit_score, self.network_score, self.momentum_score]
        non_zero = [v for v in vals if v > 0]
        if not non_zero:
            return 0.0
        prod = 1.0
        for v in non_zero:
            prod *= v
        return round(prod ** (1 / len(non_zero)), 2)


# ---------- Market Agent ----------
class MarketAgentOutput(BaseModel):

    company_id: uuid.UUID
    market_score: Literal["bullish", "neutral", "bear"]  # categorical — NEVER averaged
    market_size_estimate_usd: Optional[float] = None
    growth_rate_pct: Optional[float] = None
    confidence_band: tuple[float, float]
    supporting_claim_ids: list[uuid.UUID] = Field(default_factory=list)
    reasoning: str
    contradictions: list[str] = Field(default_factory=list)  # textual "Claim A vs Claim B" pairs
    computed_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def numeric_score(self) -> float:
        """Map categorical to numeric for Aggregator's geometric mean."""
        return {"bullish": 100.0, "neutral": 50.0, "bear": 10.0}[self.market_score]


# ---------- Idea-vs-Market Agent ----------
class IdeaVsMarketAgentOutput(BaseModel):

    company_id: uuid.UUID
    fit_score: float = Field(ge=0, le=100)  # how well the idea serves the identified market
    defensibility_score: float = Field(ge=0, le=100)
    differentiation: str  # 2-4 sentences naming 2 closest competitors + the wedge
    confidence_band: tuple[float, float]
    supporting_claim_ids: list[uuid.UUID] = Field(default_factory=list)
    reasoning: str
    computed_at: datetime = Field(default_factory=datetime.utcnow)


# ---------- Validator Agent ----------
class ValidatorAgentOutput(BaseModel):

    claim_id: uuid.UUID
    status: Literal["verified", "unverifiable", "contradicted", "not_disclosed"]
    confidence: float = Field(ge=0, le=1)
    counter_evidence: Optional[str] = None  # quoted snippet from contradicting/confirming source
    counter_evidence_source: Optional[str] = None  # source.ref of that evidence
    notes: str = ""


# ---------- Aggregator ----------
class AggregatorOutput(BaseModel):

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    application_id: Optional[uuid.UUID] = None
    founder_id: uuid.UUID
    company_id: uuid.UUID
    overall_recommendation: Literal["pass", "deep_dive", "fast_pass", "reject"]
    overall_conviction: float = Field(ge=0, le=100)
    axes: dict[str, float]  # {"founder": 72, "market": 65, "idea_vs_market": 80} — NEVER averaged
    axes_trends: dict[str, str]  # {"founder": "improving", "market": "stable", ...}
    thesis_fit_score: float = Field(ge=0, le=100)
    evidence_coverage: float = Field(ge=0, le=1)  # verified_claims / total_claims
    open_contradictions: list[str] = Field(default_factory=list)
    missing_required_sections: list[str] = Field(default_factory=list)
    missing_optional_sections: list[str] = Field(default_factory=list)
    memo_markdown: str  # full memo, every fact cited [^claim_id]
    next_actions: list[str] = Field(default_factory=list)
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    trace_id: Optional[str] = None  # Langfuse trace id
