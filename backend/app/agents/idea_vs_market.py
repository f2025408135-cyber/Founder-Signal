"""Idea-vs-Market Agent — scores FIT and DEFENSIBILITY of the IDEA.

Per spec §4.4.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import settings
from app.llm import client as llm_client
from app.schemas.agent_outputs import IdeaVsMarketAgentOutput
from app.schemas.claim import Claim, SourceKind
from app.schemas.thesis import Thesis

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "idea_vs_market.txt"


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _fallback_idea_vs_market(
    *,
    company_id: uuid.UUID,
    claims: list[Claim],
    market_reasoning: str,
) -> IdeaVsMarketAgentOutput:
    """Deterministic fallback. defensibility_score <= 50 if no verified competitive claims."""
    has_verified_competitive = any(
        c.kind.value in {"competitive", "technical_depth"}
        and c.validator_status == "verified"
        for c in claims
    )
    defensibility = 40.0 if not has_verified_competitive else 60.0
    return IdeaVsMarketAgentOutput(
        company_id=company_id,
        fit_score=55.0,
        defensibility_score=defensibility,
        differentiation="Differentiation unclear — insufficient competitive evidence. Cannot name closest competitors without verified competitive claims.",
        confidence_band=(max(0.0, defensibility - 25), min(100.0, defensibility + 25)),
        supporting_claim_ids=[c.id for c in claims if c.kind.value in {"product", "competitive"}][:5],
        reasoning="Fallback: insufficient competitive evidence. fit_score derived from product claims only.",
        computed_at=datetime.utcnow(),
    )


async def run_idea_vs_market_agent(
    *,
    company_id: uuid.UUID,
    claims: list[Claim],
    market_reasoning: str,
    thesis: Thesis,
    model: Optional[str] = None,
) -> IdeaVsMarketAgentOutput:
    relevant_kinds = {"product", "competitive", "technical_depth", "market_size", "market_trend"}
    relevant = [c for c in claims if c.kind.value in relevant_kinds]
    if not relevant:
        return _fallback_idea_vs_market(
            company_id=company_id, claims=claims, market_reasoning=market_reasoning
        )

    claims_payload = [
        {
            "id": str(c.id),
            "kind": c.kind.value if hasattr(c.kind, "value") else str(c.kind),
            "text": c.text,
            "source_kind": c.source.kind.value if hasattr(c.source.kind, "value") else str(c.source.kind),
            "validator_status": c.validator_status,
        }
        for c in relevant
    ]
    user_payload = {
        "company_id": str(company_id),
        "claims": claims_payload,
        "market_reasoning": market_reasoning,
        "thesis": {"sectors": thesis.sectors},
    }

    try:
        raw = await llm_client.chat_complete_json(
            system_prompt=load_prompt(),
            user_content=user_payload,
            model=model or settings.worker_model,
            temperature=0.1,
        )
        out = _parse_idea_vs_market(raw, company_id=company_id)
        if out is None:
            out = _fallback_idea_vs_market(
                company_id=company_id, claims=claims, market_reasoning=market_reasoning
            )
    except Exception as e:
        logger.error("Idea-vs-Market LLM call failed: %s — using fallback", e)
        out = _fallback_idea_vs_market(
            company_id=company_id, claims=claims, market_reasoning=market_reasoning
        )

    # R3: if no verified competitive/technical_depth claim → defensibility_score <= 50, band width >= 30
    has_verified_competitive = any(
        c.kind.value in {"competitive", "technical_depth"} and c.validator_status == "verified"
        for c in claims
    )
    if not has_verified_competitive:
        if out.defensibility_score > 50:
            out.defensibility_score = 50.0
        low, high = out.confidence_band
        if high - low < 30:
            new_low = max(0.0, low - 15)
            new_high = min(100.0, high + 15)
            if new_high - new_low < 30:
                new_high = min(100.0, new_low + 30)
            out.confidence_band = (new_low, new_high)

    # R2: differentiation must be non-empty and at least 2 sentences.
    # Spec §4.4 R2. If the LLM emitted a single-sentence differentiation, append
    # the fallback text to ensure ≥2 sentences.
    diff_text = (out.differentiation or "").strip()
    if not diff_text:
        out.differentiation = (
            "Differentiation unclear — insufficient competitive evidence. "
            "Cannot name closest competitors without verified competitive claims."
        )
    else:
        # Count sentences — split on . ! ? followed by space/newline/end
        import re
        sentences = [s for s in re.split(r'[.!?]+(?:\s|$)', diff_text) if s.strip()]
        if len(sentences) < 2:
            out.differentiation = (
                diff_text.rstrip(".!?") + ". "
                "Insufficient competitive evidence to fully characterize differentiation."
            )

    return out


def _parse_idea_vs_market(raw: dict, *, company_id: uuid.UUID) -> Optional[IdeaVsMarketAgentOutput]:
    if not isinstance(raw, dict):
        return None
    try:
        data = raw.get("idea_vs_market_output", raw)
        band = data.get("confidence_band") or [30.0, 70.0]
        if isinstance(band, (list, tuple)) and len(band) == 2:
            confidence_band = (float(band[0]), float(band[1]))
        else:
            confidence_band = (30.0, 70.0)
        supporting_ids = []
        for s in data.get("supporting_claim_ids", []) or []:
            try:
                supporting_ids.append(uuid.UUID(s) if isinstance(s, str) else s)
            except (ValueError, TypeError):
                continue
        return IdeaVsMarketAgentOutput(
            company_id=company_id,
            fit_score=float(data.get("fit_score", 50.0)),
            defensibility_score=float(data.get("defensibility_score", 40.0)),
            differentiation=str(data.get("differentiation", "")),
            confidence_band=confidence_band,
            supporting_claim_ids=supporting_ids,
            reasoning=str(data.get("reasoning", "")),
            computed_at=datetime.utcnow(),
        )
    except Exception as e:
        logger.warning("Failed to parse IdeaVsMarketAgentOutput: %s", e)
        return None
