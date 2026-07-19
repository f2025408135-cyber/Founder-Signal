"""FounderScore — the persistent-memory record.

CRITICAL: score_history is APPEND-ONLY. It NEVER resets across applications,
cohorts, or time. This is the persistent-memory requirement from the brief.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Trend(str, Enum):
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


class ScoreSnapshot(BaseModel):
    """One point-in-time score. Appended to FounderScore.score_history; never mutated."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    founder_id: uuid.UUID
    score: float = Field(ge=0.0, le=100.0)
    confidence_band: tuple[float, float]  # (low, high); wide for cold-start — Founder Agent rule
    trend: Trend
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    trigger: str  # "application" | "signal_threshold" | "manual" | "outbound_scan"
    evidence_claim_ids: list[uuid.UUID] = Field(default_factory=list)
    component_scores: dict[str, float] = Field(default_factory=dict)
    # {"technical": 78, "market_fit": 62, "network": 0, "momentum": 45}
    cold_start: bool  # explicit flag — drives the UX banner
    application_id: Optional[uuid.UUID] = None


class ApplicationRef(BaseModel):
    """Reference to an Application in the founder's history."""

    application_id: uuid.UUID
    received_at: datetime
    outcome: Optional[str] = None  # "pending" | "screened" | "invested" | "passed"


class FounderScore(BaseModel):
    """Aggregate founder memory — the source of truth for `prior_score`."""

    founder_id: uuid.UUID
    # CRITICAL: score_history is APPEND-ONLY. It NEVER resets across applications, cohorts, or time.
    score_history: list[ScoreSnapshot] = Field(default_factory=list)
    current_score: Optional[ScoreSnapshot] = None
    trend: Trend = Trend.INSUFFICIENT_DATA
    applications: list[ApplicationRef] = Field(default_factory=list)
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)
