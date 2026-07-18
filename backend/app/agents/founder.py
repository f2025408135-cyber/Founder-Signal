"""Founder Agent — cold-start rule embedded.

Per spec §4.2:
- Scores founder across 4 axes: technical, market_fit, network, momentum.
- Composite score via reasoning, NOT blind average.
- COLD-START RULE (highest priority): if no external signals, wide confidence band,
  derive from deck content alone, flags missing signals.

This is the FULL implementation (Tier B will exercise it end-to-end).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import settings
from app.llm import client as llm_client
from app.schemas.agent_outputs import FounderAgentOutput
from app.schemas.claim import Claim, SourceKind
from app.schemas.founder_score import FounderScore, Trend
from app.schemas.thesis import Thesis

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "founder.txt"


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _has_external_signals(claims: list[Claim]) -> bool:
    """Check if any claim originated from an external source."""
    external_kinds = {
        SourceKind.GITHUB,
        SourceKind.ARXIV,
        SourceKind.PRODUCTHUNT,
        SourceKind.ACCELERATOR_COHORT,
        SourceKind.HACKERNEWS,
    }
    return any(c.source.kind in external_kinds for c in claims)


def _compute_trend(new_score: float, prior_score: Optional[FounderScore]) -> Trend:
    """Compare new score to mean of last 3 prior snapshots."""
    if not prior_score or not prior_score.score_history:
        return Trend.INSUFFICIENT_DATA
    last_3 = prior_score.score_history[-3:]
    if len(last_3) < 3:
        return Trend.INSUFFICIENT_DATA
    prior_mean = sum(s.score for s in last_3) / len(last_3)
    if new_score > prior_mean + 5:
        return Trend.IMPROVING
    if new_score < prior_mean - 5:
        return Trend.DECLINING
    return Trend.STABLE


def _cold_start_flags(claims: list[Claim]) -> list[str]:
    """Build the flags list based on which external signals are missing."""
    present = {c.source.kind for c in claims}
    flags: list[str] = []
    if SourceKind.GITHUB not in present:
        flags.append("no_github")
    if SourceKind.ARXIV not in present:
        flags.append("no_arxiv")
    if SourceKind.PRODUCTHUNT not in present:
        flags.append("no_ph_launch")
    if SourceKind.ACCELERATOR_COHORT not in present:
        flags.append("no_accelerator")
    # No prior VC is implied unless we have a financial claim with external corroboration
    has_vc_claim = any(
        c.kind.value in {"financial"} and c.source.kind not in {SourceKind.DECK, SourceKind.APPLICATION_FORM, SourceKind.FOUNDER_BIO}
        for c in claims
    )
    if not has_vc_claim:
        flags.append("no_prior_vc")
    return flags


def _cold_start_fallback(
    *,
    founder_id: uuid.UUID,
    application_id: Optional[uuid.UUID],
    claims: list[Claim],
    market_fit_similarity: float,
    prior_score: Optional[FounderScore],
) -> FounderAgentOutput:
    """Deterministic cold-start fallback — used if the LLM call fails OR if the LLM
    doesn't honor the cold-start rule.
    """
    flags = _cold_start_flags(claims)
    market_fit_score = round(market_fit_similarity * 100, 2)

    # Derive minimal technical_score from deck/product claims
    deck_or_product_claims = [
        c for c in claims
        if c.kind.value in {"founder_background", "cold_start_inferred", "product"}
    ]
    # Base score 50, +5 per unique claim (capped at 75)
    technical_score = min(75.0, 50.0 + 5.0 * len(deck_or_product_claims))

    supporting_claim_ids = [c.id for c in deck_or_product_claims[:5]]

    # Wide confidence band: width >= 50, clamped to [0, 100]
    low = max(0.0, technical_score - 25.0)
    high = min(100.0, technical_score + 35.0)
    if high - low < 50:
        high = min(100.0, low + 50)

    reasoning = (
        "Cold-start founder. External signals absent. Score derives from deck content alone. "
        f"Confidence band widened to reflect unverified self-reported claims. "
        f"Derived {len(deck_or_product_claims)} claims from application content; "
        f"market_fit_similarity={market_fit_similarity:.2f} suggests {'strong' if market_fit_similarity > 0.6 else 'moderate'} thesis alignment."
    )

    return FounderAgentOutput(
        founder_id=founder_id,
        application_id=application_id,
        technical_score=technical_score,
        market_fit_score=market_fit_score,
        network_score=0.0,
        momentum_score=0.0,
        cold_start=True,
        confidence_band=(low, high),
        supporting_claim_ids=supporting_claim_ids,
        reasoning=reasoning,
        flags=flags,
        trend=Trend.INSUFFICIENT_DATA.value,
        computed_at=datetime.utcnow(),
    )


async def run_founder_agent(
    *,
    founder_id: uuid.UUID,
    application_id: Optional[uuid.UUID],
    claims: list[Claim],
    prior_score: Optional[FounderScore],
    thesis: Thesis,
    market_descriptors: list[str],
    market_fit_similarity: float,
    model: Optional[str] = None,
) -> FounderAgentOutput:
    """Score the founder across 4 axes + composite.

    Implements spec §4.2 R1-R5 + cold-start rule.
    """
    is_cold_start = not _has_external_signals(claims)

    # Serialize claims for the LLM (avoid sending embeddings)
    claims_payload = [
        {
            "id": str(c.id),
            "kind": c.kind.value if hasattr(c.kind, "value") else str(c.kind),
            "text": c.text,
            "source_kind": c.source.kind.value if hasattr(c.source.kind, "value") else str(c.source.kind),
            "source_ref": c.source.ref,
            "confidence": c.confidence,
            "validator_status": c.validator_status,
        }
        for c in claims
    ]

    prior_payload = None
    if prior_score:
        prior_payload = {
            "score_history": [
                {
                    "score": s.score,
                    "computed_at": s.computed_at.isoformat(),
                    "trigger": s.trigger,
                    "cold_start": s.cold_start,
                }
                for s in prior_score.score_history[-5:]  # last 5 only
            ],
            "current_score": (
                {
                    "score": prior_score.current_score.score,
                    "computed_at": prior_score.current_score.computed_at.isoformat(),
                }
                if prior_score.current_score
                else None
            ),
            "trend": prior_score.trend.value if hasattr(prior_score.trend, "value") else str(prior_score.trend),
        }

    user_payload = {
        "founder_id": str(founder_id),
        "application_id": str(application_id) if application_id else None,
        "claims": claims_payload,
        "prior_score": prior_payload,
        "thesis": {
            "name": thesis.name,
            "sectors": thesis.sectors,
            "stage": thesis.stage,
            "geography": thesis.geography,
            "check_size_usd": thesis.check_size_usd,
        },
        "market_descriptors": market_descriptors,
        "market_fit_similarity": market_fit_similarity,
        "is_cold_start": is_cold_start,
    }

    prompt = load_prompt()
    try:
        raw = await llm_client.chat_complete_json(
            system_prompt=prompt,
            user_content=user_payload,
            model=model or settings.worker_model,
            temperature=0.1,
        )
        out = _parse_founder_output(raw, founder_id=founder_id, application_id=application_id)
    except Exception as e:
        logger.error("Founder LLM call failed: %s — using cold-start fallback", e)
        out = None

    if out is None:
        out = _cold_start_fallback(
            founder_id=founder_id,
            application_id=application_id,
            claims=claims,
            market_fit_similarity=market_fit_similarity,
            prior_score=prior_score,
        )

    # Enforce cold-start rule deterministically (R1, R2, R3)
    if is_cold_start:
        out.cold_start = True
        # R2: confidence_band width >= 50
        low, high = out.confidence_band
        if high - low < 50:
            new_high = min(100.0, low + 50)
            out.confidence_band = (low, new_high)
        # R3: flags contain >= 3 of the 5 cold-start flags
        required_flags = {"no_github", "no_arxiv", "no_ph_launch", "no_accelerator", "no_prior_vc"}
        present = set(out.flags) & required_flags
        if len(present) < 3:
            missing = required_flags - present
            # Add missing flags (up to 3 total required)
            for f in sorted(missing):
                if len(set(out.flags) & required_flags) >= 3:
                    break
                out.flags.append(f)

    # R5: compute trend against prior_score
    out.trend = _compute_trend(out.technical_score, prior_score).value  # type: ignore[assignment]

    return out


def _parse_founder_output(
    raw: dict,
    *,
    founder_id: uuid.UUID,
    application_id: Optional[uuid.UUID],
) -> Optional[FounderAgentOutput]:
    """Parse LLM output into FounderAgentOutput. Returns None on failure."""
    if not isinstance(raw, dict):
        return None
    try:
        # The LLM might return the object directly OR nested under "founder_output"
        data = raw.get("founder_output", raw)
        # Coerce UUIDs
        supporting_ids = []
        for s in data.get("supporting_claim_ids", []) or []:
            try:
                supporting_ids.append(uuid.UUID(s) if isinstance(s, str) else s)
            except (ValueError, TypeError):
                continue

        band = data.get("confidence_band") or [0.0, 50.0]
        if isinstance(band, (list, tuple)) and len(band) == 2:
            confidence_band = (float(band[0]), float(band[1]))
        else:
            confidence_band = (0.0, 50.0)

        return FounderAgentOutput(
            founder_id=founder_id,
            application_id=application_id,
            technical_score=float(data.get("technical_score", 50.0)),
            market_fit_score=float(data.get("market_fit_score", 0.0)),
            network_score=float(data.get("network_score", 0.0)),
            momentum_score=float(data.get("momentum_score", 0.0)),
            cold_start=bool(data.get("cold_start", False)),
            confidence_band=confidence_band,
            supporting_claim_ids=supporting_ids,
            reasoning=str(data.get("reasoning", "")),
            flags=list(data.get("flags", []) or []),
            trend=str(data.get("trend", "insufficient_data")),
            computed_at=datetime.utcnow(),
        )
    except Exception as e:
        logger.warning("Failed to parse FounderAgentOutput: %s", e)
        return None
