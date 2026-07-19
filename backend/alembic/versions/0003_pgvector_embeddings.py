"""pgvector embeddings + GIN trigram index

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-19

Adds:
- claims.embedding column (vector(384))
- GIN index on claims.text (pg_trgm) — speeds ILIKE / similarity queries
- IVFFLAT index on claims.embedding for cosine similarity search
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


EMBEDDING_DIM = 384


def upgrade() -> None:
    # 1. Add vector column to claims
    op.add_column(
        "claims",
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
    )

    # 2. GIN trigram index on claims.text — speeds up RapidFuzz-style similarity + ILIKE
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_claims_text_trgm ON claims USING gin (text gin_trgm_ops)"
    )

    # 3. IVFFLAT cosine index on claims.embedding — fast nearest-neighbor search.
    # lists = 100 is appropriate for ~1k-10k claims; rebuild for larger volumes.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_claims_embedding_cosine "
        "ON claims USING hnsw (embedding vector_cosine_ops)"
    )

    # 4. LangGraph checkpoint tables (AsyncPostgresSaver requires these).
    # We create them via raw SQL because langgraph-checkpoint-postgres's setup()
    # may run before our migration. Defining them here makes the migration self-sufficient.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS langgraph_checkpoints (
            thread_id TEXT NOT NULL,
            checkpoint_ns TEXT NOT NULL DEFAULT '',
            checkpoint_id TEXT NOT NULL,
            parent_checkpoint_id TEXT,
            type TEXT,
            checkpoint BYTEA,
            metadata JSONB,
            PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS langgraph_writes (
            thread_id TEXT NOT NULL,
            checkpoint_ns TEXT NOT NULL DEFAULT '',
            checkpoint_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            idx INTEGER NOT NULL,
            channel TEXT NOT NULL,
            type TEXT,
            blob BYTEA,
            PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_langgraph_writes_thread ON langgraph_writes (thread_id, checkpoint_ns, checkpoint_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_langgraph_checkpoints_thread ON langgraph_checkpoints (thread_id, checkpoint_ns, checkpoint_id)"
    )

    # 5. migration_channel ordering helper for LangGraph migrations table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS langgraph_migration_metadata (
            v INTEGER PRIMARY KEY
        )
        """
    )


def downgrade() -> None:
    op.drop_index("ix_claims_embedding_cosine", table_name="claims")
    op.drop_index("ix_claims_text_trgm", table_name="claims")
    op.drop_column("claims", "embedding")
    # Leave langgraph_* tables in place — they are owned by LangGraph runtime.
