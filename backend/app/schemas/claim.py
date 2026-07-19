"""Claim record — the atomic unit of evidence that flows through the pipeline.

Mirrors spec §3.1 exactly. Every downstream agent reads/writes Claims; this is
the canonical data contract.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ClaimKind(str, Enum):
    FOUNDER_BACKGROUND = "founder_background"
    FOUNDER_NETWORK = "founder_network"
    TECHNICAL_DEPTH = "technical_depth"
    MARKET_SIZE = "market_size"
    MARKET_TREND = "market_trend"
    TRACTION = "traction"
    PRODUCT = "product"
    COMPETITIVE = "competitive"
    FINANCIAL = "financial"
    TEAM = "team"
    COLD_START_INFERRED = "cold_start_inferred"  # mandatory emission when no external signal exists


class SourceKind(str, Enum):
    DECK = "deck"
    APPLICATION_FORM = "application_form"
    GITHUB = "github"
    ARXIV = "arxiv"
    HACKERNEWS = "hackernews"
    PRODUCTHUNT = "producthunt"
    INTERVIEW = "interview"
    ACCELERATOR_COHORT = "accelerator_cohort"
    COMPANY_WEBSITE = "company_website"  # only URLs the founder explicitly provided
    FOUNDER_BIO = "founder_bio"  # self-reported, pasted by founder
    EXTERNAL_DB = "external_db"  # Crunchbase API mock for demo


# Convenience sets used by multiple agents
EXTERNAL_SOURCE_KINDS = {
    SourceKind.GITHUB,
    SourceKind.ARXIV,
    SourceKind.HACKERNEWS,
    SourceKind.PRODUCTHUNT,
    SourceKind.ACCELERATOR_COHORT,
    SourceKind.EXTERNAL_DB,
    SourceKind.COMPANY_WEBSITE,
}
SELF_REPORTED_SOURCE_KINDS = {SourceKind.DECK, SourceKind.APPLICATION_FORM, SourceKind.FOUNDER_BIO}


class Source(BaseModel):
    """Provenance for a Claim. Never mutated after creation."""

    kind: SourceKind
    ref: str  # URL, "deck#slide=4", arxiv id, "owner/repo"
    ingested_at: datetime
    raw_payload_hash: str  # sha256 hex of raw payload — dedupe + re-verification key
    retrieved_by: str  # agent name + Langfuse span id, e.g. "github.fetch_github_signals@trace_abc/span_123"


class ClaimFlag(BaseModel):
    """A flag set by the Validator on a Claim. Only the Validator writes flags."""

    flag: Literal[
        "verified",
        "unverifiable",
        "contradicted",
        "not_disclosed",
        "low_evidence",
        "cold_start_inferred",
    ]
    set_by: str  # validator run id (Langfuse trace id)
    set_at: datetime
    reason: str
    counter_evidence_ref: Optional[str] = None  # source.ref of contradicting/confirming evidence


class Claim(BaseModel):
    """Atomic, single-proposition evidence record."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    founder_id: uuid.UUID
    company_id: uuid.UUID
    application_id: Optional[uuid.UUID] = None
    kind: ClaimKind
    text: str  # single declarative sentence — enforced by Ingestion Agent
    source: Source
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)  # set by Validator, never by other agents
    flags: list[ClaimFlag] = Field(default_factory=list)
    embedding: Optional[list[float]] = None  # 384-dim, for similarity + dedupe escalation
    created_at: datetime = Field(default_factory=datetime.utcnow)
    superseded_by: Optional[uuid.UUID] = None  # set when a newer claim contradicts + replaces — never hard-delete

    # ---- Convenience helpers ----
    @property
    def validator_status(self) -> Optional[str]:
        """Returns the latest Validator flag's status, or None if unflagged."""
        if not self.flags:
            return None
        # flags are Literal strings (not enums) since ClaimFlag doesn't use_enum_values
        return self.flags[-1].flag

    @property
    def is_external(self) -> bool:
        return self.source.kind in EXTERNAL_SOURCE_KINDS
