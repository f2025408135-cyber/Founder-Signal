"""Thesis Engine config — the active investment thesis used by all agents."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RiskAppetite(BaseModel):
    """What the fund will consider — used by Aggregator + Idea-vs-Market."""

    max_founder_age_years: int = 3  # years since incorporation
    accepts_no_prior_funding: bool = True
    accepts_no_github: bool = True
    accepts_cold_start: bool = True  # MUST default True per brief
    min_conviction_score: float = 60.0  # 0-100
    allow_neutral_market: bool = True  # if False, only bullish markets are screenable


class Thesis(BaseModel):
    """The active investment thesis. Only one is active at a time (MVP)."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str  # e.g. "Maschmeyer Group — AI Infra & DevTools"
    sectors: list[str]  # e.g. ["AI infra", "DevTools", "Climate", "Robotics"]
    stage: list[str]  # e.g. ["pre-seed", "seed"]
    geography: list[str]  # ISO-3166 alpha-2, e.g. ["DE", "US", "PK", "SG"]
    check_size_usd: int  # 100_000 for this hackathon
    ownership_target_pct: float  # e.g. 7.5
    risk_appetite: RiskAppetite
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True  # MVP: only one active thesis at a time


def default_maschmeyer_thesis() -> Thesis:
    """The default thesis seed for the demo (Maschmeyer Group — AI Infra & DevTools).

    Per spec §3.3, the hackathon check size is $100K.
    """
    return Thesis(
        name="Maschmeyer Group — AI Infra & DevTools",
        sectors=["AI infra", "DevTools", "Climate", "Robotics"],
        stage=["pre-seed", "seed"],
        geography=["DE", "US", "PK", "SG"],
        check_size_usd=100_000,
        ownership_target_pct=7.5,
        risk_appetite=RiskAppetite(),
    )


def expand_market_descriptors(thesis: Thesis) -> list[str]:
    """Expand thesis.sectors into descriptor phrases used for Sentence-BERT cosine similarity.

    Each sector becomes a longer phrase so the embedding captures intent, not just a keyword.
    """
    sector_phrase_map = {
        "AI infra": "AI infrastructure, ML tooling, model training, inference, vector databases, GPU orchestration",
        "DevTools": "developer tools, IDE plugins, CI/CD, observability, code intelligence, API gateways",
        "Climate": "climate technology, carbon accounting, grid decarbonization, battery materials, MRV",
        "Robotics": "robotics, embodied AI, manipulation, autonomous navigation, robot fleets, ROS",
    }
    out: list[str] = []
    for s in thesis.sectors:
        out.append(sector_phrase_map.get(s, s))
    # Always include geography + stage context
    out.append(f"Stage preference: {', '.join(thesis.stage)}")
    out.append(f"Geography focus: {', '.join(thesis.geography)}")
    return out
