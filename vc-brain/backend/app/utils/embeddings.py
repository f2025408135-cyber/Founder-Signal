"""Sentence-BERT embeddings — singleton model load.

Uses `sentence-transformers/all-MiniLM-L6-v2` (384-dim) per spec §1.
The model loads lazily on first call and is cached at module level so we
pay the load cost exactly once per process.
"""
from __future__ import annotations

import asyncio
import functools
import logging
from typing import Optional

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

_EMBED_DIM = 384

# Singleton
_model = None
_model_lock = asyncio.Lock()
_load_attempted = False


def _load_model():
    """Load the SentenceTransformer model (sync). Returns None on failure."""
    global _model, _load_attempted
    if _model is not None or _load_attempted:
        return _model
    _load_attempted = True
    try:
        # Lazy import so tests that don't need embeddings can skip the heavy dep
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(
            settings.embeddings_model_name,
            device="cpu",
        )
        logger.info("Loaded SentenceTransformer model: %s", settings.embeddings_model_name)
    except Exception as e:  # pragma: no cover — best-effort fallback
        logger.warning(
            "Failed to load SentenceTransformer (%s). Falling back to deterministic hash embeddings. "
            "Cosine similarity will be approximate — install sentence-transformers for production use.",
            e,
        )
        _model = None
    return _model


def _hash_embedding(text: str, dim: int = _EMBED_DIM) -> list[float]:
    """Deterministic hash-based fallback embedding.

    NOT semantically meaningful — used only when the real model is unavailable.
    Each text produces a unique 384-dim vector via SHA-256 chunking, then L2-normalized.
    """
    import hashlib

    out = []
    h = hashlib.sha256(text.encode("utf-8")).digest()
    while len(out) < dim:
        h = hashlib.sha256(h).digest()
        out.extend(float(b) / 255.0 for b in h)
    arr = np.array(out[:dim], dtype=np.float32)
    norm = float(np.linalg.norm(arr))
    if norm > 0:
        arr = arr / norm
    return arr.tolist()


def embed_text_sync(text: str) -> list[float]:
    """Synchronous embedding — for use in non-async contexts.

    Returns a 384-dim float list. Falls back to a deterministic hash embedding
    if the SentenceTransformer model is unavailable.
    """
    if not text or not text.strip():
        # Zero vector for empty input — preserves cosine_similarity semantics
        return [0.0] * _EMBED_DIM
    model = _load_model()
    if model is None:
        return _hash_embedding(text)
    vec = model.encode(text, normalize_embeddings=True, convert_to_numpy=True)
    return vec.astype(np.float32).tolist()


async def embed_text(text: str) -> list[float]:
    """Async wrapper — runs the (CPU-bound) encode in a thread.

    Returns a 384-dim float list.
    """
    if not text or not text.strip():
        return [0.0] * _EMBED_DIM
    return await asyncio.to_thread(embed_text_sync, text)


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Batched embedding — much faster than calling embed_text in a loop."""
    if not texts:
        return []
    # Replace empty strings with a sentinel so encode doesn't break
    cleaned = [t if t and t.strip() else "empty" for t in texts]
    return await asyncio.to_thread(_embed_batch_sync, cleaned)


def _embed_batch_sync(texts: list[str]) -> list[list[float]]:
    model = _load_model()
    if model is None:
        return [_hash_embedding(t) for t in texts]
    vecs = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True, batch_size=32)
    return [v.astype(np.float32).tolist() for v in vecs]


@functools.lru_cache(maxsize=1024)
def _cosine_cached(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    arr_a = np.array(a, dtype=np.float32)
    arr_b = np.array(b, dtype=np.float32)
    na = float(np.linalg.norm(arr_a))
    nb = float(np.linalg.norm(arr_b))
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(arr_a, arr_b) / (na * nb))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity in [0, 1] for normalized vectors, [-1, 1] in general.

    Used by:
    - thesis_fit_node (founder-market cosine similarity)
    - dedupe escalation (embedding similarity fallback if LLM unavailable)
    """
    if not a or not b:
        return 0.0
    return _cosine_cached(tuple(a), tuple(b))


def embedding_dim() -> int:
    return _EMBED_DIM
