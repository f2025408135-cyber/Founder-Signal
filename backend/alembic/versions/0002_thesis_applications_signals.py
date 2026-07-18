"""thesis apps signals scores

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-19
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # thesis_configs
    op.create_table(
        "thesis_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sectors", postgresql.JSONB, nullable=False),
        sa.Column("stage", postgresql.JSONB, nullable=False),
        sa.Column("geography", postgresql.JSONB, nullable=False),
        sa.Column("check_size_usd", sa.Integer(), nullable=False),
        sa.Column("ownership_target_pct", sa.Float(), nullable=False),
        sa.Column("risk_appetite", postgresql.JSONB, nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_thesis_configs_active", "thesis_configs", ["active"])

    # founder_scores (aggregate memory, JSONB list of snapshots — APPEND-ONLY)
    op.create_table(
        "founder_scores",
        sa.Column(
            "founder_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("founders.id"),
            primary_key=True,
        ),
        sa.Column("score_history", postgresql.JSONB, server_default="[]"),
        sa.Column("current_score", postgresql.JSONB, nullable=True),
        sa.Column("trend", sa.String(32), server_default="insufficient_data"),
        sa.Column("applications", postgresql.JSONB, server_default="[]"),
        sa.Column("first_seen_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_founder_scores_last_updated_at", "founder_scores", ["last_updated_at"])

    # founder_score_snapshots — SQL-queryable projection of score_history
    op.create_table(
        "founder_score_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "founder_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("founders.id"),
            nullable=False,
        ),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("confidence_band_low", sa.Float(), nullable=False),
        sa.Column("confidence_band_high", sa.Float(), nullable=False),
        sa.Column("trend", sa.String(32), nullable=False),
        sa.Column("trigger", sa.String(32), nullable=False),
        sa.Column("evidence_claim_ids", postgresql.JSONB, server_default="[]"),
        sa.Column("component_scores", postgresql.JSONB, server_default="{}"),
        sa.Column("cold_start", sa.Boolean(), server_default=sa.false()),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("computed_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_founder_score_snapshots_founder_id", "founder_score_snapshots", ["founder_id"])
    op.create_index(
        "ix_founder_score_snapshots_computed_at", "founder_score_snapshots", ["computed_at"]
    )

    # founder_signals (outbound scan)
    op.create_table(
        "founder_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "founder_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("founders.id"),
            nullable=False,
        ),
        sa.Column("signal_type", sa.String(64), nullable=False),
        sa.Column("detected_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("conviction_delta", sa.Float(), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=True),
    )
    op.create_index("ix_founder_signals_founder_id", "founder_signals", ["founder_id"])
    op.create_index("ix_founder_signals_detected_at", "founder_signals", ["detected_at"])

    # aggregator_outputs
    op.create_table(
        "aggregator_outputs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id"),
            nullable=True,
        ),
        sa.Column(
            "founder_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("founders.id"),
            nullable=False,
        ),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column("overall_recommendation", sa.String(32), nullable=False),
        sa.Column("overall_conviction", sa.Float(), nullable=False),
        sa.Column("axes", postgresql.JSONB, nullable=False),
        sa.Column("axes_trends", postgresql.JSONB, nullable=False),
        sa.Column("thesis_fit_score", sa.Float(), nullable=False),
        sa.Column("evidence_coverage", sa.Float(), nullable=False),
        sa.Column("open_contradictions", postgresql.JSONB, server_default="[]"),
        sa.Column("missing_required_sections", postgresql.JSONB, server_default="[]"),
        sa.Column("missing_optional_sections", postgresql.JSONB, server_default="[]"),
        sa.Column("memo_markdown", sa.Text(), nullable=False),
        sa.Column("next_actions", postgresql.JSONB, server_default="[]"),
        sa.Column("computed_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("trace_id", sa.String(128), nullable=True),
    )
    op.create_index("ix_aggregator_outputs_application_id", "aggregator_outputs", ["application_id"])
    op.create_index("ix_aggregator_outputs_founder_id", "aggregator_outputs", ["founder_id"])
    op.create_index("ix_aggregator_outputs_company_id", "aggregator_outputs", ["company_id"])
    op.create_index("ix_aggregator_outputs_computed_at", "aggregator_outputs", ["computed_at"])
    op.create_index("ix_aggregator_outputs_trace_id", "aggregator_outputs", ["trace_id"])

    # cached_aggregator (60-min TTL for card/memo views)
    op.create_table(
        "cached_aggregator",
        sa.Column(
            "founder_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("founders.id"),
            primary_key=True,
        ),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("written_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_cached_aggregator_written_at", "cached_aggregator", ["written_at"])

    # github_etag_cache
    op.create_table(
        "github_etag_cache",
        sa.Column("repo_slug", sa.String(255), primary_key=True),
        sa.Column("etag", sa.String(255), nullable=True),
        sa.Column("last_fetched_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_status", sa.Integer(), nullable=True),
    )

    # dedupe_cache
    op.create_table(
        "dedupe_cache",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("is_same", sa.Boolean(), nullable=False),
        sa.Column("decided_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("dedupe_cache")
    op.drop_table("github_etag_cache")
    op.drop_index("ix_cached_aggregator_written_at", table_name="cached_aggregator")
    op.drop_table("cached_aggregator")
    op.drop_index("ix_aggregator_outputs_trace_id", table_name="aggregator_outputs")
    op.drop_index("ix_aggregator_outputs_computed_at", table_name="aggregator_outputs")
    op.drop_index("ix_aggregator_outputs_company_id", table_name="aggregator_outputs")
    op.drop_index("ix_aggregator_outputs_founder_id", table_name="aggregator_outputs")
    op.drop_index("ix_aggregator_outputs_application_id", table_name="aggregator_outputs")
    op.drop_table("aggregator_outputs")
    op.drop_index("ix_founder_signals_detected_at", table_name="founder_signals")
    op.drop_index("ix_founder_signals_founder_id", table_name="founder_signals")
    op.drop_table("founder_signals")
    op.drop_index("ix_founder_score_snapshots_computed_at", table_name="founder_score_snapshots")
    op.drop_index("ix_founder_score_snapshots_founder_id", table_name="founder_score_snapshots")
    op.drop_table("founder_score_snapshots")
    op.drop_index("ix_founder_scores_last_updated_at", table_name="founder_scores")
    op.drop_table("founder_scores")
    op.drop_index("ix_thesis_configs_active", table_name="thesis_configs")
    op.drop_table("thesis_configs")
