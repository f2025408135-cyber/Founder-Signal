"""Validator Agent — per-claim verification. The ONLY agent that writes claim.flags + claim.confidence.

Per spec §4.5.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import settings
from app.llm import client as llm_client
from app.schemas.agent_outputs import ValidatorAgentOutput
from app.schemas.claim import Claim, ClaimFlag, ClaimKind, SourceKind

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "validator.txt"


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


SELF_REPORTED = {SourceKind.DECK, SourceKind.APPLICATION_FORM, SourceKind.FOUNDER_BIO}


def _unverifiable(claim_id: uuid.UUID, reason: str = "no external evidence") -> ValidatorAgentOutput:
    return ValidatorAgentOutput(
        claim_id=claim_id,
        status="unverifiable",
        confidence=0.4,
        counter_evidence=None,
        counter_evidence_source=None,
        notes=reason,
    )


def _not_disclosed(claim_id: uuid.UUID, reason: str = "claim not disclosed by founder") -> ValidatorAgentOutput:
    return ValidatorAgentOutput(
        claim_id=claim_id,
        status="not_disclosed",
        confidence=0.0,
        counter_evidence=None,
        counter_evidence_source=None,
        notes=reason,
    )


def _contradicted(
    claim_id: uuid.UUID, *, counter_evidence: str, counter_evidence_source: str
) -> ValidatorAgentOutput:
    return ValidatorAgentOutput(
        claim_id=claim_id,
        status="contradicted",
        confidence=0.15,
        counter_evidence=counter_evidence,
        counter_evidence_source=counter_evidence_source,
        notes="Cross-claim contradiction detected.",
    )


def _verified(claim_id: uuid.UUID, *, counter_evidence_source: str) -> ValidatorAgentOutput:
    return ValidatorAgentOutput(
        claim_id=claim_id,
        status="verified",
        confidence=0.85,
        counter_evidence="Confirmed by external source.",
        counter_evidence_source=counter_evidence_source,
        notes="Verified via external corroboration.",
    )


def detect_cross_claim_contradictions(claims: list[Claim]) -> dict[uuid.UUID, tuple[str, str]]:
    """Heuristic cross-claim contradiction detection (spec §4.5 CONTRADICTION DETECTION).

    For each (founder_id, kind) block, look at claim text for numerical assertions
    that differ by >2x. Returns dict[claim_id -> (counter_evidence, counter_evidence_source)].

    This is the deterministic part of contradiction detection — the LLM Validator
    can add more nuanced ones, but this catches the obvious "$5B vs $500M" cases.
    """
    import re

    out: dict[uuid.UUID, tuple[str, str]] = {}
    blocks: dict[tuple, list[Claim]] = {}
    for c in claims:
        kind_val = c.kind.value if hasattr(c.kind, "value") else str(c.kind)
        blocks.setdefault((c.founder_id, kind_val), []).append(c)

    number_re = re.compile(r"\$?\s*(\d+(?:\.\d+)?)\s*(?:B|M|K|billion|million|thousand)?", re.IGNORECASE)

    for (fid, kind), block in blocks.items():
        if kind not in {"market_size", "traction", "financial"}:
            continue
        if len(block) < 2:
            continue
        # Extract first numerical value from each claim
        for i, c1 in enumerate(block):
            m1 = number_re.search(c1.text)
            if not m1:
                continue
            try:
                v1 = float(m1.group(1))
            except ValueError:
                continue
            for c2 in block[i + 1 :]:
                m2 = number_re.search(c2.text)
                if not m2:
                    continue
                try:
                    v2 = float(m2.group(1))
                except ValueError:
                    continue
                if v1 == 0 or v2 == 0:
                    continue
                ratio = max(v1, v2) / min(v1, v2)
                if ratio >= 2.0:  # 2x difference = contradiction
                    out[c1.id] = (
                        f'Claim {c2.id} says: "{c2.text}" (source: {c2.source.ref})',
                        c2.source.ref,
                    )
                    out[c2.id] = (
                        f'Claim {c1.id} says: "{c1.text}" (source: {c1.source.ref})',
                        c1.source.ref,
                    )
    return out


async def run_validator_agent(
    *,
    claims: list[Claim],
    external_evidence: dict,
    model: Optional[str] = None,
) -> list[ValidatorAgentOutput]:
    """Per-claim verification. Returns one output per input claim.

    Spec §4.5 R1-R6 enforced.
    """
    if not claims:
        return []

    # Pre-compute cross-claim contradictions deterministically
    contradictions = detect_cross_claim_contradictions(claims)

    # Build LLM input
    claims_payload = [
        {
            "id": str(c.id),
            "kind": c.kind.value if hasattr(c.kind, "value") else str(c.kind),
            "text": c.text,
            "source_kind": c.source.kind.value if hasattr(c.source.kind, "value") else str(c.source.kind),
            "source_ref": c.source.ref,
        }
        for c in claims
    ]

    # external_evidence may have UUID keys — serialize
    evidence_payload = {}
    for k, v in (external_evidence or {}).items():
        evidence_payload[str(k)] = v

    user_payload = {
        "claims": claims_payload,
        "external_evidence": evidence_payload,
        "contradictions_hint": {str(k): v for k, v in contradictions.items()},
    }

    try:
        raw = await llm_client.chat_complete_json(
            system_prompt=load_prompt(),
            user_content=user_payload,
            model=model or settings.synthesizer_model,
            temperature=0.2,
        )
        outputs = _parse_validator_outputs(raw, claims=claims)
    except Exception as e:
        logger.error("Validator LLM call failed: %s — using deterministic fallback", e)
        outputs = []

    # R1: one output per input claim — backfill any missing
    outputs_by_claim = {o.claim_id: o for o in outputs}
    final: list[ValidatorAgentOutput] = []
    for c in claims:
        out = outputs_by_claim.get(c.id)
        if out is None:
            # Deterministic fallback per spec rules
            kind_val = c.kind.value if hasattr(c.kind, "value") else str(c.kind)
            if kind_val == "cold_start_inferred":
                out = ValidatorAgentOutput(
                    claim_id=c.id,
                    status="unverifiable",
                    confidence=0.4,
                    counter_evidence=None,
                    counter_evidence_source=None,
                    notes="Cold-start inferred claim; no external corroboration available.",
                )
            elif c.id in contradictions:
                ce, ces = contradictions[c.id]
                out = _contradicted(c.id, counter_evidence=ce, counter_evidence_source=ces)
            elif not (external_evidence or {}).get(c.id):
                out = _unverifiable(c.id)
            else:
                out = _unverifiable(c.id)
        else:
            # Apply deterministic rule enforcement on top of LLM output
            out = _enforce_rules(out, claim=c, contradictions=contradictions, external_evidence=external_evidence)
        final.append(out)

    return final


def _enforce_rules(
    out: ValidatorAgentOutput,
    *,
    claim: Claim,
    contradictions: dict[uuid.UUID, tuple[str, str]],
    external_evidence: dict,
) -> ValidatorAgentOutput:
    """Apply spec §4.5 R2-R6 deterministically on top of LLM output."""
    kind_val = claim.kind.value if hasattr(claim.kind, "value") else str(claim.kind)

    # R3: cold_start_inferred → unverifiable, confidence <= 0.5
    if kind_val == "cold_start_inferred":
        out.status = "unverifiable"
        out.confidence = min(out.confidence, 0.5)
        if not out.notes:
            out.notes = "Cold-start inferred claim; no external corroboration available."
        return out

    # Cross-claim contradiction wins
    if claim.id in contradictions:
        ce, ces = contradictions[claim.id]
        return _contradicted(claim.id, counter_evidence=ce, counter_evidence_source=ces)

    # R2: no external_evidence AND not cold_start → unverifiable
    evidence_list = (external_evidence or {}).get(claim.id) or []
    if not evidence_list:
        if out.status == "verified":
            out.status = "unverifiable"
            out.confidence = min(out.confidence, 0.5)
            out.notes = "Downgraded to unverifiable — no external evidence provided."
        return out

    # R4: verified requires external (non-self-reported) source
    if out.status == "verified":
        if claim.source.kind in SELF_REPORTED:
            # Self-reported cannot be upgraded to verified
            out.status = "unverifiable"
            out.confidence = min(out.confidence, 0.5)
            out.notes = "Self-reported source cannot be verified without external corroboration."

    # R5: contradicted requires counter_evidence + counter_evidence_source
    if out.status == "contradicted":
        if not out.counter_evidence or not out.counter_evidence_source:
            out.status = "unverifiable"
            out.confidence = min(out.confidence, 0.5)
            out.notes = "Contradiction claimed but no counter-evidence cited; downgraded to unverifiable."

    # R6: not_disclosed → confidence == 0.0
    if out.status == "not_disclosed":
        out.confidence = 0.0

    return out


def _parse_validator_outputs(raw: Any, *, claims: list[Claim]) -> list[ValidatorAgentOutput]:
    """Parse LLM output into list of ValidatorAgentOutput."""
    if not isinstance(raw, dict):
        return []
    items = raw.get("validator_outputs") or raw.get("outputs") or []
    if not isinstance(items, list):
        return []
    out: list[ValidatorAgentOutput] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            claim_id_raw = item.get("claim_id")
            if not claim_id_raw:
                continue
            try:
                claim_id = uuid.UUID(claim_id_raw) if isinstance(claim_id_raw, str) else claim_id_raw
            except (ValueError, TypeError):
                continue
            status = str(item.get("status", "unverifiable"))
            if status not in {"verified", "unverifiable", "contradicted", "not_disclosed"}:
                status = "unverifiable"
            out.append(
                ValidatorAgentOutput(
                    claim_id=claim_id,
                    status=status,  # type: ignore[arg-type]
                    confidence=float(item.get("confidence", 0.4)),
                    counter_evidence=item.get("counter_evidence"),
                    counter_evidence_source=item.get("counter_evidence_source"),
                    notes=str(item.get("notes", "")),
                )
            )
        except Exception as e:
            logger.warning("Failed to parse validator output %r: %s", item, e)
            continue
    return out


def apply_validator_outputs(claims: list[Claim], outputs: list[ValidatorAgentOutput]) -> list[Claim]:
    """Apply Validator outputs onto Claim objects (sets .flags and .confidence).

    Spec: only the Validator writes claim.flags and claim.confidence.
    """
    outputs_by_claim = {o.claim_id: o for o in outputs}
    now = datetime.utcnow()
    for c in claims:
        out = outputs_by_claim.get(c.id)
        if out is None:
            continue
        c.confidence = out.confidence
        flag = ClaimFlag(
            flag=out.status,  # type: ignore[arg-type]
            set_by="validator",
            set_at=now,
            reason=out.notes,
            counter_evidence_ref=out.counter_evidence_source,
        )
        c.flags = c.flags + [flag]  # append, don't overwrite history
    return claims
