"""RapidFuzz dedupe with LLM escalation.

Per spec §7:
- Block on (founder_id, claim.kind)
- WRatio >= 90 → auto-merge (keep earliest ingested_at, set superseded_by on the other)
- 80 <= WRatio < 90 → escalate to LLM (single YES/NO call to gpt-5.6-luna)
- WRatio < 80 → treat as distinct claims
- LLM escalation cached by (sha256(t1) + sha256(t2)) in dedupe_cache table

Splink/Dedupe are NOT used — hackathon volumes are too small to justify the infra.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime
from typing import Optional

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.models import DedupeCache
from app.db.session import async_session
from app.llm import client as llm_client
from app.schemas.claim import Claim
from app.config import settings

logger = logging.getLogger(__name__)

DEDUPE_THRESHOLD = 90
BORDERLINE_LOW = 80
BORDERLINE_HIGH = 90


def _pair_key(t1: str, t2: str) -> str:
    """Stable cache key — order-independent."""
    h1 = hashlib.sha256(t1.encode()).hexdigest()[:16]
    h2 = hashlib.sha256(t2.encode()).hexdigest()[:16]
    return f"{min(h1, h2)}:{max(h1, h2)}"


async def llm_says_same_claim(t1: str, t2: str) -> bool:
    """Single YES/NO LLM call to decide if two borderline claims are the same proposition.

    Cached by stable pair key in dedupe_cache table. Falls back to an in-memory
    cache when Postgres is unavailable (e.g. in unit tests).
    """
    cache_key = _pair_key(t1, t2)

    # Try the DB cache first; fall back to in-memory if DB unavailable.
    cached = await _cache_get(cache_key)
    if cached is not None:
        return cached

    prompt = (
        'Are these two atomic claims expressing the SAME verifiable proposition? '
        'Answer only "YES" or "NO".\n\n'
        f"Claim A: {t1}\nClaim B: {t2}"
    )
    try:
        response = await llm_client.llm_complete(prompt, model=settings.worker_model, temperature=0.0, max_tokens=8)
        is_same = response.strip().upper().startswith("Y")
    except Exception as e:
        logger.warning("dedupe LLM call failed (%s, %s): %s — defaulting to NOT same", t1[:50], t2[:50], e)
        is_same = False

    await _cache_set(cache_key, is_same)
    return is_same


# In-memory fallback cache — used when Postgres is unavailable.
_MEMORY_DEDUPE_CACHE: dict[str, bool] = {}


async def _cache_get(key: str) -> Optional[bool]:
    """Read from Postgres dedupe_cache; fall back to in-memory on connection failure."""
    try:
        async with async_session() as s:
            cached = await s.get(DedupeCache, key)
            if cached:
                # Mirror to memory so subsequent reads in the same test session are fast.
                _MEMORY_DEDUPE_CACHE[key] = cached.is_same
                return cached.is_same
        return None
    except Exception as e:
        logger.debug("dedupe cache DB read failed (%s) — using in-memory cache", e)
        return _MEMORY_DEDUPE_CACHE.get(key)


async def _cache_set(key: str, is_same: bool) -> None:
    """Write to Postgres dedupe_cache; fall back to in-memory on connection failure."""
    _MEMORY_DEDUPE_CACHE[key] = is_same
    try:
        async with async_session() as s:
            stmt = pg_insert(DedupeCache).values(key=key, is_same=is_same)
            stmt = stmt.on_conflict_do_update(
                index_elements=[DedupeCache.key],
                set_={"is_same": stmt.excluded.is_same, "decided_at": datetime.utcnow()},
            )
            await s.execute(stmt)
            await s.commit()
    except Exception as e:
        logger.debug("dedupe cache DB write failed (%s) — kept in-memory only", e)


def _fuzz_score(t1: str, t2: str) -> float:
    """RapidFuzz WRatio — returns float in [0, 100]."""
    return float(fuzz.WRatio(t1, t2))


def _keep_earliest(c1: Claim, c2: Claim) -> tuple[Claim, Claim]:
    """Return (keep, drop) — keep the claim with earlier ingested_at."""
    if c1.source.ingested_at <= c2.source.ingested_at:
        return c1, c2
    return c2, c1


async def dedupe_claims(claims: list[Claim]) -> list[Claim]:
    """Returns a new list with duplicates merged.

    Superseded claims get `superseded_by` set on them — they remain in Postgres
    for audit trail (never hard-deleted).
    """
    if len(claims) <= 1:
        return list(claims)

    # 1. Block by (founder_id, kind)
    blocks: dict[tuple, list[Claim]] = {}
    for c in claims:
        kind_val = c.kind.value if hasattr(c.kind, "value") else str(c.kind)
        blocks.setdefault((c.founder_id, kind_val), []).append(c)

    out: list[Claim] = []
    borderline_pairs: list[tuple[Claim, Claim]] = []

    for (fid, kind), block in blocks.items():
        if len(block) == 1:
            out.extend(block)
            continue

        merged_ids: set = set()
        # Track which claims are already in `out` to avoid double-add
        added_ids: set = set()

        for i, c1 in enumerate(block):
            if c1.id in merged_ids:
                continue
            for c2 in block[i + 1 :]:
                if c2.id in merged_ids:
                    continue
                score = _fuzz_score(c1.text, c2.text)
                if score >= DEDUPE_THRESHOLD:
                    keep, drop = _keep_earliest(c1, c2)
                    drop.superseded_by = keep.id
                    merged_ids.add(drop.id)
                    logger.debug("dedupe auto-merge (score=%.1f): %r ~ %r", score, drop.text[:60], keep.text[:60])
                elif BORDERLINE_LOW <= score < BORDERLINE_HIGH:
                    borderline_pairs.append((c1, c2))
            # c1 is kept (either no merge happened, or it survived merges)
            if c1.id not in added_ids:
                out.append(c1)
                added_ids.add(c1.id)

        # Add unmerged stragglers
        for c in block:
            if c.id not in merged_ids and c.id not in added_ids:
                out.append(c)
                added_ids.add(c.id)

    # 2. Resolve borderline pairs in parallel
    if borderline_pairs:
        tasks = [llm_says_same_claim(c1.text, c2.text) for c1, c2 in borderline_pairs]
        decisions = await asyncio.gather(*tasks, return_exceptions=False)

        to_supersede: dict = {}  # drop_id -> keep_id
        for (c1, c2), same in zip(borderline_pairs, decisions):
            if same:
                keep, drop = _keep_earliest(c1, c2)
                to_supersede[drop.id] = keep.id

        if to_supersede:
            for c in out:
                if c.id in to_supersede:
                    c.superseded_by = to_supersede[c.id]
            # Remove superseded claims from the output list (they remain in DB for audit)
            out = [c for c in out if c.id not in to_supersede]

    logger.info(
        "dedupe: %d input -> %d output (%d auto-merged, %d borderline escalated, %d LLM-merged)",
        len(claims),
        len(out),
        sum(1 for c in claims if c.superseded_by),  # approximate
        len(borderline_pairs),
        sum(1 for c in out if c.superseded_by),
    )
    return out


# ---- Synchronous variant for testing ----
def dedupe_claims_sync_no_llm(claims: list[Claim]) -> list[Claim]:
    """Sync dedupe that only applies the auto-merge threshold (>=90).

    Used in tests where we don't want to hit the LLM. Borderline pairs are
    left as distinct claims.
    """
    if len(claims) <= 1:
        return list(claims)

    blocks: dict[tuple, list[Claim]] = {}
    for c in claims:
        kind_val = c.kind.value if hasattr(c.kind, "value") else str(c.kind)
        blocks.setdefault((c.founder_id, kind_val), []).append(c)

    out: list[Claim] = []
    for (fid, kind), block in blocks.items():
        if len(block) == 1:
            out.extend(block)
            continue
        merged_ids: set = set()
        added_ids: set = set()
        for i, c1 in enumerate(block):
            if c1.id in merged_ids:
                continue
            for c2 in block[i + 1 :]:
                if c2.id in merged_ids:
                    continue
                score = _fuzz_score(c1.text, c2.text)
                if score >= DEDUPE_THRESHOLD:
                    keep, drop = _keep_earliest(c1, c2)
                    drop.superseded_by = keep.id
                    merged_ids.add(drop.id)
            if c1.id not in added_ids:
                out.append(c1)
                added_ids.add(c1.id)
        for c in block:
            if c.id not in merged_ids and c.id not in added_ids:
                out.append(c)
                added_ids.add(c.id)
    return out
