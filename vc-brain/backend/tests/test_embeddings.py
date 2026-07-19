"""Test embeddings utility — spec §10 A7.

A test embedding of "AI infrastructure" returns a 384-dim float list;
cosine_similarity of identical strings returns 1.0.
"""
from __future__ import annotations

import pytest

from app.utils.embeddings import (
    cosine_similarity,
    embed_text,
    embed_text_sync,
    embedding_dim,
)


def test_embedding_dim_is_384():
    """Spec §1: all-MiniLM-L6-v2 produces 384-dim vectors."""
    assert embedding_dim() == 384


@pytest.mark.asyncio
async def test_embed_text_returns_384_dims():
    """Embedding of 'AI infrastructure' is a 384-dim float list."""
    vec = await embed_text("AI infrastructure")
    assert len(vec) == 384
    assert all(isinstance(v, (int, float)) for v in vec)


@pytest.mark.asyncio
async def test_cosine_similarity_identical_strings_is_one():
    """cosine_similarity of identical strings returns ~1.0."""
    v1 = await embed_text("AI infrastructure")
    v2 = await embed_text("AI infrastructure")
    sim = cosine_similarity(v1, v2)
    assert sim == pytest.approx(1.0, abs=0.05), f"Expected ~1.0, got {sim}"


@pytest.mark.asyncio
async def test_cosine_similarity_unrelated_strings_is_low():
    """cosine_similarity of unrelated strings is meaningfully lower than identical.

    Skipped if sentence-transformers is not installed (hash-embedding fallback
    does not produce semantically meaningful embeddings).
    """
    from app.utils.embeddings import _load_attempted, _model
    if _model is None and _load_attempted:
        pytest.skip("sentence-transformers not installed — hash-embedding fallback lacks semantic similarity")
    v1 = await embed_text("AI infrastructure")
    v2 = await embed_text("Recipe for chocolate cake")
    sim_unrelated = cosine_similarity(v1, v2)
    sim_identical = cosine_similarity(v1, v1)
    assert sim_unrelated < sim_identical
    assert sim_unrelated < 0.5, f"Unrelated strings should have low sim, got {sim_unrelated}"


@pytest.mark.asyncio
async def test_embed_text_empty_string_returns_zero_vector():
    """Empty string returns a zero vector — preserves cosine semantics."""
    v = await embed_text("")
    assert len(v) == 384
    assert all(x == 0.0 for x in v)


def test_embed_text_sync_works():
    """Sync variant works for non-async contexts."""
    v = embed_text_sync("test sentence")
    assert len(v) == 384


@pytest.mark.asyncio
async def test_cosine_similarity_handles_zero_vectors():
    """Zero vectors don't crash — return 0.0."""
    z = [0.0] * 384
    v = await embed_text("test")
    assert cosine_similarity(z, v) == 0.0
    assert cosine_similarity(z, z) == 0.0
