"""ORM models — mirror the Pydantic schemas 1:1.

All tables that appear in spec §10 A3 + §8 + §9 must be defined here:
- claims, founder_scores, founder_score_snapshots, applications, founder_signals,
- thesis_configs, github_etag_cache, dedupe_cache, cached_aggregator
- founders, companies (FK targets — needed for proper relational model)
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Embeddings are 384-dim per spec §1 (all-MiniLM-L6-v2)
EMBEDDING_DIM = 384


# ---------- Foundational entities ----------
class Founder(Base):
    """A founder — created lazily on first application."""

    __tablename__ = "founders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    bio_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # founder-pasted
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    companies: Mapped[list["Company"]] = relationship(back_populates="founder")
    scores: Mapped[list["FounderScoreORM"]] = relationship(back_populates="founder")
    score_snapshots: Mapped[list["FounderScoreSnapshot"]] = relationship(back_populates="founder")
    signals: Mapped[list["FounderSignalORM"]] = relationship(back_populates="founder")


class Company(Base):
    """A company — one founder can have multiple companies over time."""

    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    founder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("founders.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    hq_country: Mapped[str] = mapped_column(String(2), nullable=False)  # ISO-3166 alpha-2
    sector_self_reported: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    founder: Mapped[Founder] = relationship(back_populates="companies")
    applications: Mapped[list["ApplicationORM"]] = relationship(back_populates="company")
    claims: Mapped[list["ClaimORM"]] = relationship(back_populates="company")


# ---------- Pipeline core ----------
class ClaimORM(Base):
    """ORM mirror of Claim (§3.1). One row per atomic claim."""

    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    founder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("founders.id"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True, index=True
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # ClaimKind enum value
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # Source is a JSONB column — {kind, ref, ingested_at, raw_payload_hash, retrieved_by}
    source: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    # flags is a list of {flag, set_by, set_at, reason, counter_evidence_ref}
    flags: Mapped[list] = mapped_column(JSONB, default=list)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    superseded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    founder: Mapped[Founder] = relationship()
    company: Mapped[Company] = relationship(back_populates="claims")
    application: Mapped["ApplicationORM | None"] = relationship(back_populates="claims")

    __table_args__ = (
        # Block dedupe queries on (founder_id, kind) — see §7.
        # A composite index supports both blocking + per-application lookups.
        # text pattern index for LIKE queries on claim text
        # (pg_trgm adds GIN support for ILIKE — created in migration 0003)
    )


class ApplicationORM(Base):
    """Inbound application row."""

    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    founder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("founders.id"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    aggregator_output_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    # Latency tracking — Tier B B10
    ingestion_complete_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    validator_complete_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scoring_complete_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    aggregator_complete_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    company: Mapped[Company] = relationship(back_populates="applications")
    founder: Mapped[Founder] = relationship()
    claims: Mapped[list["ClaimORM"]] = relationship(back_populates="application")
    aggregator_output: Mapped["AggregatorOutputORM | None"] = relationship(
        back_populates="application", foreign_keys="AggregatorOutputORM.application_id"
    )


# ---------- Founder scoring memory (APPEND-ONLY) ----------
class FounderScoreORM(Base):
    """Aggregate founder memory — current_score + score_history.

    The score_history column is APPEND-ONLY. We store snapshots as a JSONB list
    AND also write a row to founder_score_snapshots for SQL-queryable history.
    The list is the source of truth; the table is a denormalized projection.
    """

    __tablename__ = "founder_scores"

    founder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("founders.id"), primary_key=True
    )
    # JSONB list of ScoreSnapshot dicts — APPEND-ONLY
    score_history: Mapped[list] = mapped_column(JSONB, default=list)
    current_score: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    trend: Mapped[str] = mapped_column(String(32), default="insufficient_data")
    applications: Mapped[list] = mapped_column(JSONB, default=list)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    founder: Mapped[Founder] = relationship(back_populates="scores")


class FounderScoreSnapshot(Base):
    """One snapshot row per score computation — SQL-queryable history.

    This is the table the rescore trigger queries for "last score older than 24h?".
    """

    __tablename__ = "founder_score_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    founder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("founders.id"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_band_low: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_band_high: Mapped[float] = mapped_column(Float, nullable=False)
    trend: Mapped[str] = mapped_column(String(32), nullable=False)
    trigger: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_claim_ids: Mapped[list] = mapped_column(JSONB, default=list)
    component_scores: Mapped[dict] = mapped_column(JSONB, default=dict)
    cold_start: Mapped[bool] = mapped_column(Boolean, default=False)
    application_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    founder: Mapped[Founder] = relationship(back_populates="score_snapshots")


# ---------- Thesis ----------
class ThesisConfig(Base):
    """Persisted investment thesis. Only one row with active=True at a time."""

    __tablename__ = "thesis_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sectors: Mapped[list] = mapped_column(JSONB, nullable=False)
    stage: Mapped[list] = mapped_column(JSONB, nullable=False)
    geography: Mapped[list] = mapped_column(JSONB, nullable=False)
    check_size_usd: Mapped[int] = mapped_column(Integer, nullable=False)
    ownership_target_pct: Mapped[float] = mapped_column(Float, nullable=False)
    risk_appetite: Mapped[dict] = mapped_column(JSONB, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ---------- Signals (outbound scan) ----------
class FounderSignalORM(Base):
    """External signal detected by the outbound scan cron."""

    __tablename__ = "founder_signals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    founder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("founders.id"), nullable=False, index=True
    )
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    conviction_delta: Mapped[float] = mapped_column(Float, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    founder: Mapped[Founder] = relationship(back_populates="signals")


# ---------- Aggregator output cache ----------
class AggregatorOutputORM(Base):
    """Persisted AggregatorOutput. One row per pipeline run."""

    __tablename__ = "aggregator_outputs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True, index=True
    )
    founder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("founders.id"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    overall_recommendation: Mapped[str] = mapped_column(String(32), nullable=False)
    overall_conviction: Mapped[float] = mapped_column(Float, nullable=False)
    axes: Mapped[dict] = mapped_column(JSONB, nullable=False)
    axes_trends: Mapped[dict] = mapped_column(JSONB, nullable=False)
    thesis_fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    open_contradictions: Mapped[list] = mapped_column(JSONB, default=list)
    missing_required_sections: Mapped[list] = mapped_column(JSONB, default=list)
    missing_optional_sections: Mapped[list] = mapped_column(JSONB, default=list)
    memo_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    next_actions: Mapped[list] = mapped_column(JSONB, default=list)
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    trace_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    application: Mapped[ApplicationORM | None] = relationship(
        back_populates="aggregator_output", foreign_keys=[application_id]
    )


class CachedAggregator(Base):
    """60-min TTL cache for card/memo view — see §8."""

    __tablename__ = "cached_aggregator"

    founder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("founders.id"), primary_key=True
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    written_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    @classmethod
    async def read(cls, founder_id: uuid.UUID) -> "CachedAggregator | None":
        from sqlalchemy import select

        from app.db.session import async_session

        async with async_session() as s:
            q = select(cls).where(cls.founder_id == founder_id)
            return (await s.execute(q)).scalars().first()

    @classmethod
    async def write(cls, founder_id: uuid.UUID, payload: dict) -> None:
        from app.db.session import async_session

        async with async_session() as s:
            existing = await s.get(cls, founder_id)
            if existing:
                existing.payload = payload
                existing.written_at = datetime.utcnow()
            else:
                s.add(cls(founder_id=founder_id, payload=payload))
            await s.commit()


# ---------- Ingestion helpers ----------
class GithubEtagCache(Base):
    """ETag cache for GitHub conditional requests — saves API quota."""

    __tablename__ = "github_etag_cache"

    repo_slug: Mapped[str] = mapped_column(String(255), primary_key=True)
    etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_status: Mapped[int | None] = mapped_column(Integer, nullable=True)


class DedupeCache(Base):
    """Cache of LLM dedupe escalation decisions — keyed by stable pair hash."""

    __tablename__ = "dedupe_cache"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    is_same: Mapped[bool] = mapped_column(Boolean, nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# Backwards-compatible aliases — keep imports simple
FounderSignal = FounderSignalORM
Application = ApplicationORM
FounderScore = FounderScoreORM
Claim = ClaimORM
AggregatorOutput = AggregatorOutputORM
