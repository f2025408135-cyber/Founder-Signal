"""Application + signal schemas — supporting types for the inbound / outbound flows."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ApplicationCreate(BaseModel):
    """Inbound payload from POST /applications."""

    founder_name: str
    founder_email: str
    founder_bio_text: str  # founder-pasted, NOT scraped from LinkedIn
    company_name: str
    company_website_url: Optional[HttpUrl] = None  # founder-provided only; never bulk-crawled
    deck_url: Optional[HttpUrl] = None  # PDF or public link
    github_repo_slugs: list[str] = Field(default_factory=list)
    accelerator: Optional[str] = None
    hq_country: str  # ISO-3166 alpha-2
    sector_self_reported: str


class Application(BaseModel):
    """Application row — persisted raw_payload verbatim."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    founder_id: uuid.UUID
    company_id: uuid.UUID
    received_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # "pending" | "screened" | "fast_pass" | "deep_dive" | "passed" | "rejected"
    raw_payload: dict
    aggregator_output_id: Optional[uuid.UUID] = None
    trace_id: Optional[str] = None  # Langfuse trace id

    # Latency tracking — Tier B B10
    ingestion_complete_at: Optional[datetime] = None
    validator_complete_at: Optional[datetime] = None
    scoring_complete_at: Optional[datetime] = None
    aggregator_complete_at: Optional[datetime] = None


class FounderSignal(BaseModel):
    """An external signal detected by the outbound scan (new commit, paper, launch, HN post)."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    founder_id: uuid.UUID
    signal_type: str  # "new_github_commit" | "new_arxiv_paper" | "new_ph_launch" | "new_hn_post_above_threshold"
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    conviction_delta: float  # estimated score delta if re-run
    payload_hash: str
    payload: Optional[dict] = None  # raw signal payload for inspection
