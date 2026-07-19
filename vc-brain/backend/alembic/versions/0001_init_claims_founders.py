"""init claims founders companies applications

Revision ID: 0001
Revises:
Create Date: 2026-07-19
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "founders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("bio_text", sa.Text(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_founders_email", "founders", ["email"])

    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "founder_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("founders.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("website_url", sa.String(2048), nullable=True),
        sa.Column("hq_country", sa.String(2), nullable=False),
        sa.Column("sector_self_reported", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_companies_founder_id", "companies", ["founder_id"])

    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
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
        sa.Column("received_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("status", sa.String(32), server_default="pending"),
        sa.Column("raw_payload", postgresql.JSONB, nullable=False),
        sa.Column("aggregator_output_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("trace_id", sa.String(128), nullable=True),
        sa.Column("ingestion_complete_at", sa.DateTime(), nullable=True),
        sa.Column("validator_complete_at", sa.DateTime(), nullable=True),
        sa.Column("scoring_complete_at", sa.DateTime(), nullable=True),
        sa.Column("aggregator_complete_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_applications_founder_id", "applications", ["founder_id"])
    op.create_index("ix_applications_company_id", "applications", ["company_id"])
    op.create_index("ix_applications_received_at", "applications", ["received_at"])
    op.create_index("ix_applications_trace_id", "applications", ["trace_id"])

    op.create_table(
        "claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
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
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id"),
            nullable=True,
        ),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("source", postgresql.JSONB, nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0.5"),
        sa.Column("flags", postgresql.JSONB, server_default="[]"),
        # embedding column added in 0003 (pgvector)
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("superseded_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_claims_founder_id", "claims", ["founder_id"])
    op.create_index("ix_claims_company_id", "claims", ["company_id"])
    op.create_index("ix_claims_application_id", "claims", ["application_id"])
    op.create_index("ix_claims_kind", "claims", ["kind"])
    op.create_index("ix_claims_created_at", "claims", ["created_at"])
    # Composite index for dedupe blocking — (founder_id, kind)
    op.create_index("ix_claims_founder_kind", "claims", ["founder_id", "kind"])


def downgrade() -> None:
    op.drop_index("ix_claims_founder_kind", table_name="claims")
    op.drop_index("ix_claims_created_at", table_name="claims")
    op.drop_index("ix_claims_kind", table_name="claims")
    op.drop_index("ix_claims_application_id", table_name="claims")
    op.drop_index("ix_claims_company_id", table_name="claims")
    op.drop_index("ix_claims_founder_id", table_name="claims")
    op.drop_table("claims")

    op.drop_index("ix_applications_trace_id", table_name="applications")
    op.drop_index("ix_applications_received_at", table_name="applications")
    op.drop_index("ix_applications_company_id", table_name="applications")
    op.drop_index("ix_applications_founder_id", table_name="applications")
    op.drop_table("applications")

    op.drop_index("ix_companies_founder_id", table_name="companies")
    op.drop_table("companies")

    op.drop_index("ix_founders_email", table_name="founders")
    op.drop_table("founders")
