-- 001-extensions.sql
-- Loaded by the pgvector/pgvector:0.8.0-pg18 image entrypoint on first boot.
-- Creates the vector extension required by migration 0003_pgvector_embeddings.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
