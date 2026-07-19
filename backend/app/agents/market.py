"""Market Agent — categorical verdict (bullish/neutral/bear). Never numeric average.

Per spec §4.3.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import settings
from app.llm import client as llm_client
from app.schemas.agent_outputs import MarketAgentOutput
from app.schemas.claim import Claim, SourceKind
from app.schemas.thesis import Thesis

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "market.txt"


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _fallback_market_output(company_id: uuid.UUID, claims: list[Claim]) -> MarketAgentOutput:
    """Deterministic fallback when LLM fails. Neutral by default (spec R2)."""
    has_verified = any(
        c.validator_status == "verified" for c in claims if c.validator_status
    )
    return MarketAgentOutput(
        company_id=company_id,
        market_score="neutral",
        market_size_estimate_usd=None,
        growth_rate_pct=None,
        confidence_band=(20.0, 80.0),
        supporting_claim_ids=[c.id for c in claims if c.kind.value in {"market_size", "market_trend"}][:5],
        reasoning="Insufficient verified market evidence." if not has_verified else "Mixed market evidence — defaulting to neutral.",
        contradictions=[],
        computed_at=datetime.utcnow(),
    )


async def run_market_agent(
    *,
    company_id: uuid.UUID,
    claims: list[Claim],
    thesis: Thesis,
    model: Optional[str] = None,
) -> MarketAgentOutput:
    """Assess the market — not the founder, not the product."""
    market_claims = [c for c in claims if c.kind.value in {"market_size", "market_trend", "competitive"}]
    if not market_claims:
        return _fallback_market_output(company_id, claims)

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
        for c in market_claims
    ]
    user_payload = {
        "company_id": str(company_id),
        "claims": claims_payload,
        "thesis": {
            "sectors": thesis.sectors,
            "geography": thesis.geography,
        },
    }

    try:
        raw = await llm_client.chat_complete_json(
            system_prompt=load_prompt(),
            user_content=user_payload,
            model=model or settings.worker_model,
            temperature=0.1,
        )
        out = _parse_market_output(raw, company_id=company_id)
        if out is None:
            out = _fallback_market_output(company_id, claims)
    except Exception as e:
        logger.error("Market LLM call failed: %s — using fallback", e)
        out = _fallback_market_output(company_id, claims)

    # R1: market_score is categorical
    if out.market_score not in {"bullish", "neutral", "bear"}:
        out.market_score = "neutral"
    # R2: if no verified claim → neutral
    if not any(c.validator_status == "verified" for c in market_claims if c.validator_status):
        out.market_score = "neutral"
    # R3: if both bullish-evidence AND bear-evidence verified claims exist → neutral
    # + contradictions non-empty. Spec §4.3 R3.
    bullish_claims = [
        c for c in market_claims
        if c.validator_status == "verified"
        and (c.kind.value if hasattr(c.kind, "value") else str(c.kind)) == "market_trend"
        and any(w in c.text.lower() for w in ["growing", "expanding", "rising", "bullish", "increasing"])
    ]
    bear_claims = [
        c for c in market_claims
        if c.validator_status == "verified"
        and (c.kind.value if hasattr(c.kind, "value") else str(c.kind)) == "market_trend"
        and any(w in c.text.lower() for w in ["shrinking", "contracting", "declining", "bearish", "decreasing"])
    ]
    if bullish_claims and bear_claims:
        out.market_score = "neutral"
        if not out.contradictions:
            out.contradictions = [
                f"Claim {bullish_claims[0].id} (bullish) vs Claim {bear_claims[0].id} (bear) — both verified."
            ]

    return out


def _parse_market_output(raw: dict, *, company_id: uuid.UUID) -> Optional[MarketAgentOutput]:
    if not isinstance(raw, dict):
        return None
    try:
        data = raw.get("market_output", raw)
        band = data.get("confidence_band") or [20.0, 80.0]
        if isinstance(band, (list, tuple)) and len(band) == 2:
            confidence_band = (float(band[0]), float(band[1]))
        else:
            confidence_band = (20.0, 80.0)
        supporting_ids = []
        for s in data.get("supporting_claim_ids", []) or []:
            try:
                supporting_ids.append(uuid.UUID(s) if isinstance(s, str) else s)
            except (ValueError, TypeError):
                continue
        return MarketAgentOutput(
            company_id=company_id,
            market_score=str(data.get("market_score", "neutral")),
            market_size_estimate_usd=float(data["market_size_estimate_usd"]) if data.get("market_size_estimate_usd") else None,
            growth_rate_pct=float(data["growth_rate_pct"]) if data.get("growth_rate_pct") else None,
            confidence_band=confidence_band,
            supporting_claim_ids=supporting_ids,
            reasoning=str(data.get("reasoning", "")),
            contradictions=list(data.get("contradictions", []) or []),
            computed_at=datetime.utcnow(),
        )
    except Exception as e:
        logger.warning("Failed to parse MarketAgentOutput: %s", e)
        return None
