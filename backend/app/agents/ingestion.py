"""Ingestion Agent — transforms raw heterogeneous inputs into atomic Claims.

Per spec §4.1:
- Tool-less: receives raw_inputs as a list of {source, content} dicts.
- Emits a JSON array of Claim objects.
- Enforces R1-R5 (see below).
- Cold-start rule: if no external signals, MUST emit at least one cold_start_inferred claim.
"""
from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Optional

from app.config import settings
from app.llm import client as llm_client
from app.schemas.claim import Claim, ClaimKind, Source, SourceKind
from app.utils.hashing import hash_json

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "ingestion.txt"


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _normalize_source_kind(kind: Any) -> SourceKind:
    """Coerce a SourceKind enum, str, or other to SourceKind.

    The Source model uses `use_enum_values=True`, so reading .kind returns a str.
    This helper normalizes both cases so downstream comparisons work.
    """
    if isinstance(kind, SourceKind):
        return kind
    if isinstance(kind, str):
        try:
            return SourceKind(kind)
        except ValueError:
            return SourceKind.APPLICATION_FORM
    return SourceKind.APPLICATION_FORM


def _normalize_claim_kind(kind: Any) -> ClaimKind:
    """Coerce a ClaimKind enum, str, or other to ClaimKind."""
    if isinstance(kind, ClaimKind):
        return kind
    if isinstance(kind, str):
        try:
            return ClaimKind(kind)
        except ValueError:
            return ClaimKind.COLD_START_INFERRED
    return ClaimKind.COLD_START_INFERRED


def _parse_claim_obj(
    raw: dict[str, Any],
    *,
    founder_id: uuid.UUID,
    company_id: uuid.UUID,
    application_id: Optional[uuid.UUID],
    expected_payload_hashes: set[str],
) -> Optional[Claim]:
    """Convert a raw dict from the LLM into a validated Claim object.

    Returns None if the dict is malformed or fails R1/R5.
    """
    try:
        # Source can come as a nested dict or be reconstructed
        source_raw = raw.get("source") or {}
        # R1: raw_payload_hash must match an input payload hash (when present)
        raw_hash = source_raw.get("raw_payload_hash") or ""
        # If hash is missing/empty, try to backfill from expected hashes by source kind match
        if not raw_hash and expected_payload_hashes:
            raw_hash = next(iter(expected_payload_hashes))

        kind_str = raw.get("kind", "cold_start_inferred")
        if isinstance(kind_str, ClaimKind):
            kind = kind_str
        else:
            try:
                kind = ClaimKind(kind_str)
            except ValueError:
                kind = ClaimKind.COLD_START_INFERRED

        src_kind_raw = source_raw.get("kind", "application_form")
        if isinstance(src_kind_raw, SourceKind):
            src_kind = src_kind_raw
        else:
            try:
                src_kind = SourceKind(src_kind_raw)
            except ValueError:
                src_kind = SourceKind.APPLICATION_FORM

        source = Source(
            kind=src_kind,
            ref=source_raw.get("ref", "unknown"),
            ingested_at=source_raw.get("ingested_at") or __import__("datetime").datetime.utcnow(),
            raw_payload_hash=raw_hash,
            retrieved_by=source_raw.get("retrieved_by", "ingestion_agent"),
        )

        text = (raw.get("text") or "").strip()
        if not text:
            return None
        # R4: text length [10, 400]
        if len(text) < 10:
            text = text + " " * (10 - len(text))  # rare; pad rather than drop
        if len(text) > 400:
            text = text[:397] + "..."

        claim = Claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind=kind,
            text=text,
            source=source,
            confidence=float(raw.get("confidence", 0.5)),
        )
        return claim
    except Exception as e:
        logger.warning("Failed to parse claim %r: %s", raw, e)
        return None


def _fallback_cold_start_claim(
    *,
    founder_id: uuid.UUID,
    company_id: uuid.UUID,
    application_id: Optional[uuid.UUID],
    reason: str,
    raw_inputs: list[dict],
) -> Claim:
    """R3 fallback: emit at least one cold_start_inferred claim when no external signals exist.

    Used when the LLM fails entirely OR when the LLM correctly identified cold-start but
    emitted zero claims.
    """
    # Try to derive text from deck/application_form inputs
    deck_text = ""
    app_form_text = ""
    for item in raw_inputs:
        src = item.get("source")
        content = item.get("content") or {}
        if src and src.kind == SourceKind.DECK:
            deck_text = _flatten_dict(content)[:300]
        elif src and src.kind == SourceKind.APPLICATION_FORM:
            app_form_text = _flatten_dict(content)[:300]

    base_text = deck_text or app_form_text or "Founder submitted an application with no external signals."
    text = f"Cold-start founder. Application content indicates: {base_text[:280]}"
    if len(text) > 400:
        text = text[:397] + "..."

    # Use the first deck or application_form source we find
    fallback_source = None
    for item in raw_inputs:
        src = item.get("source")
        if src and src.kind in {SourceKind.DECK, SourceKind.APPLICATION_FORM}:
            fallback_source = src
            break
    if fallback_source is None:
        # Construct a minimal application_form source
        fallback_source = Source(
            kind=SourceKind.APPLICATION_FORM,
            ref=f"application:{application_id or founder_id}",
            ingested_at=__import__("datetime").datetime.utcnow(),
            raw_payload_hash=hash_json({"fallback": reason}),
            retrieved_by="ingestion_agent.fallback",
        )

    return Claim(
        founder_id=founder_id,
        company_id=company_id,
        application_id=application_id,
        kind=ClaimKind.COLD_START_INFERRED,
        text=text,
        source=fallback_source,
        confidence=0.5,
    )


def _flatten_dict(d: dict, prefix: str = "") -> str:
    out = []
    for k, v in d.items():
        if isinstance(v, dict):
            out.append(_flatten_dict(v, prefix=f"{k}."))
        elif isinstance(v, list):
            out.append(f"{prefix}{k}: {', '.join(str(x) for x in v[:5])}")
        else:
            out.append(f"{prefix}{k}: {v}")
    return "; ".join(out)


async def run_ingestion_agent(
    *,
    founder_id: uuid.UUID,
    company_id: uuid.UUID,
    application_id: Optional[uuid.UUID],
    raw_inputs: list[dict],
    model: Optional[str] = None,
) -> list[Claim]:
    """Transform raw_inputs into a flat list of atomic Claim records.

    Implements spec §4.1 R1-R5 + cold-start fallback.
    """
    if not raw_inputs:
        return [
            _fallback_cold_start_claim(
                founder_id=founder_id,
                company_id=company_id,
                application_id=application_id,
                reason="no raw inputs provided",
                raw_inputs=[],
            )
        ]

    expected_payload_hashes = {
        item["source"].raw_payload_hash for item in raw_inputs if "source" in item
    }

    # Check for cold-start: no external source kinds present
    external_kinds = {
        SourceKind.GITHUB,
        SourceKind.ARXIV,
        SourceKind.PRODUCTHUNT,
        SourceKind.ACCELERATOR_COHORT,
        SourceKind.HACKERNEWS,
    }
    has_external = any(
        item.get("source") and _normalize_source_kind(item["source"].kind) in external_kinds
        for item in raw_inputs
    )

    # Build user payload — pass source.kind + ref + hash + content
    user_payload = {
        "founder_id": str(founder_id),
        "company_id": str(company_id),
        "application_id": str(application_id) if application_id else None,
        "raw_inputs": [
            {
                "source": {
                    "kind": _normalize_source_kind(item["source"].kind).value,
                    "ref": item["source"].ref,
                    "raw_payload_hash": item["source"].raw_payload_hash,
                    "retrieved_by": item["source"].retrieved_by,
                },
                "content": item.get("content", {}),
            }
            for item in raw_inputs
        ],
        "cold_start_hint": "no external signals present — MUST emit at least one cold_start_inferred claim" if not has_external else None,
    }

    prompt = load_prompt()
    try:
        raw_claims = await llm_client.chat_complete_json(
            system_prompt=prompt,
            user_content=user_payload,
            model=model or settings.worker_model,
            temperature=0.1,
        )
    except Exception as e:
        logger.error("Ingestion LLM call failed: %s — falling back to cold-start", e)
        return [
            _fallback_cold_start_claim(
                founder_id=founder_id,
                company_id=company_id,
                application_id=application_id,
                reason=f"LLM failure: {e}",
                raw_inputs=raw_inputs,
            )
        ]

    # The LLM may return either {"claims": [...]} or [...] directly
    if isinstance(raw_claims, dict) and "claims" in raw_claims:
        raw_claims_list = raw_claims["claims"]
    elif isinstance(raw_claims, list):
        raw_claims_list = raw_claims
    else:
        logger.warning("Ingestion LLM returned unexpected shape: %r", type(raw_claims))
        raw_claims_list = [raw_claims] if isinstance(raw_claims, dict) else []

    claims: list[Claim] = []
    seen_triples: set[tuple[str, str, str]] = set()  # R5
    for raw in raw_claims_list:
        if not isinstance(raw, dict):
            continue
        claim = _parse_claim_obj(
            raw,
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            expected_payload_hashes=expected_payload_hashes,
        )
        if claim is None:
            continue
        # R5: dedup on (text, source.kind, source.ref)
        src_kind_val = (
            claim.source.kind.value
            if hasattr(claim.source.kind, "value")
            else str(claim.source.kind)
        )
        triple = (claim.text, src_kind_val, claim.source.ref)
        if triple in seen_triples:
            continue
        seen_triples.add(triple)
        claims.append(claim)

    # R3: if no external signals AND no cold_start_inferred claim was emitted, add fallback
    if not has_external and not any(c.kind == ClaimKind.COLD_START_INFERRED for c in claims):
        claims.append(
            _fallback_cold_start_claim(
                founder_id=founder_id,
                company_id=company_id,
                application_id=application_id,
                reason="LLM omitted cold_start_inferred claim",
                raw_inputs=raw_inputs,
            )
        )

    # If we still have zero claims, emit the fallback
    if not claims:
        claims.append(
            _fallback_cold_start_claim(
                founder_id=founder_id,
                company_id=company_id,
                application_id=application_id,
                reason="LLM returned no parseable claims",
                raw_inputs=raw_inputs,
            )
        )

    logger.info(
        "Ingestion agent emitted %d claims (cold_start=%s, external=%s)",
        len(claims),
        not has_external,
        has_external,
    )
    return claims
