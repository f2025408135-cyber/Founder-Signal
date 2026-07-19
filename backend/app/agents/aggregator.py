"""Aggregator — the final tool-less synthesizer.

Per spec §4.6:
- Receives ONLY pre-verified structured facts.
- NO tool access. Cannot introduce new unverified claims.
- Produces AggregatorOutput with full memo_markdown.
- Every factual sentence in memo has [^claim_id] citation.
- Cold-start downgrade: if founder_output.cold_start, recommendation != fast_pass.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import settings
from app.llm.client import chat_complete_json
from app.schemas.agent_outputs import (
    AggregatorOutput,
    FounderAgentOutput,
    IdeaVsMarketAgentOutput,
    MarketAgentOutput,
    ValidatorAgentOutput,
)
from app.schemas.claim import Claim
from app.schemas.founder_score import FounderScore
from app.schemas.thesis import Thesis

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "aggregator.txt"

REQUIRED_SECTIONS = [
    "company_snapshot",
    "investment_hypotheses",
    "swot",
    "problem_and_product",
    "traction_and_kpis",
]
OPTIONAL_SECTIONS = [
    "team_and_history",
    "technology_and_defensibility",
    "market_sizing",
    "competition",
    "financials_and_round_structure",
    "cap_table",
    "due_diligence_log",
    "exit_perspective",
]


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _compute_overall_conviction(
    founder_score: float,
    market_score: str,
    idea_vs_market_score: float,
    thesis_fit_score: float,
) -> float:
    """Geometric mean per spec §4.6 (2).

    Per spec: "This prevents one strong axis from masking a fatal weakness
    (arithmetic mean of 95/10/95/95 = 73.75 looks investible; geometric mean = 52.5
    reveals the weakness)."

    We do NOT use max(1.0, v) clamping — that would defeat the purpose. A score
    of 0 on any axis yields conviction=0, correctly signaling the fatal weakness.
    """
    market_numeric = {"bullish": 100.0, "neutral": 50.0, "bear": 10.0}.get(market_score, 50.0)
    vals = [founder_score, market_numeric, idea_vs_market_score, thesis_fit_score]
    if any(v <= 0 for v in vals):
        return 0.0
    prod = 1.0
    for v in vals:
        prod *= v
    return round(prod ** (1 / 4), 2)


def _evidence_coverage(claims: list[Claim], validator_outputs: list[ValidatorAgentOutput]) -> float:
    """verified_claims / total_claims (spec §4.6 R5)."""
    total = len(claims)
    if total == 0:
        return 0.0
    verified = sum(1 for o in validator_outputs if o.status == "verified")
    return round(verified / total, 3)


def _recommendation(
    axes: dict[str, float],
    market_score: str,
    thesis_fit_score: float,
    evidence_coverage: float,
    open_contradictions: list[str],
    missing_required: list[str],
    cold_start: bool,
) -> str:
    """Decide overall_recommendation per spec §4.6 (1)."""
    market_numeric = {"bullish": 100.0, "neutral": 50.0, "bear": 10.0}.get(market_score, 50.0)
    founder_score = axes.get("founder", 0.0)
    idea_vs_market_score = axes.get("idea_vs_market", 0.0)

    # Reject conditions
    if founder_score < 30 or idea_vs_market_score < 30 or thesis_fit_score < 30:
        return "reject"
    if any("verified contradiction on a core claim" in c.lower() for c in open_contradictions):
        return "reject"

    # Cold-start: never fast_pass
    if cold_start:
        # Force deep_dive if numbers would otherwise qualify for fast_pass
        if founder_score >= 70 and market_numeric >= 70 and idea_vs_market_score >= 70 and thesis_fit_score >= 70:
            return "deep_dive"
        if founder_score >= 70 or idea_vs_market_score >= 70:
            return "deep_dive"
        if all(40 <= v < 70 for v in [founder_score, idea_vs_market_score]) and market_numeric >= 50:
            return "pass"
        return "reject"

    # fast_pass: all axes >= 70, thesis_fit >= 70, evidence >= 0.6, no contradictions, no missing required
    if (
        founder_score >= 70
        and market_numeric >= 70
        and idea_vs_market_score >= 70
        and thesis_fit_score >= 70
        and evidence_coverage >= 0.6
        and not open_contradictions
        and not missing_required
    ):
        rec = "fast_pass"
    elif founder_score >= 70 or idea_vs_market_score >= 70:
        rec = "deep_dive"
    elif all(40 <= v < 70 for v in [founder_score, idea_vs_market_score]) and market_numeric >= 50:
        rec = "pass"
    else:
        rec = "reject"

    # Downgrade by one tier if evidence_coverage < 0.4
    if evidence_coverage < 0.4:
        if rec == "fast_pass":
            rec = "deep_dive"
        elif rec == "deep_dive":
            rec = "pass"

    return rec


def _open_contradictions(validator_outputs: list[ValidatorAgentOutput]) -> list[str]:
    """List contradictions verbatim from Validator outputs."""
    out: list[str] = []
    for o in validator_outputs:
        if o.status == "contradicted":
            text = f"Claim {o.claim_id} contradicted by {o.counter_evidence_source or 'unknown'}: {o.counter_evidence or ''}"
            out.append(text)
    return out


def _missing_sections(claims: list[Claim]) -> tuple[list[str], list[str]]:
    """Determine missing required + optional sections based on claim kinds present."""
    kinds_present = {c.kind.value if hasattr(c.kind, "value") else str(c.kind) for c in claims}

    # Required sections mapped to claim kinds that satisfy them
    required_kind_map = {
        "company_snapshot": {"product", "founder_background"},
        "investment_hypotheses": {"product", "market_size", "market_trend"},
        "swot": {"product", "competitive", "market_trend"},
        "problem_and_product": {"product"},
        "traction_and_kpis": {"traction"},
    }
    optional_kind_map = {
        "team_and_history": {"founder_background", "founder_network", "team"},
        "technology_and_defensibility": {"technical_depth", "competitive"},
        "market_sizing": {"market_size"},
        "competition": {"competitive"},
        "financials_and_round_structure": {"financial"},
        "cap_table": {"financial", "team"},
        "exit_perspective": set(),  # always optional, always flagged missing
    }

    missing_required = [k for k, ks in required_kind_map.items() if not (ks & kinds_present)]
    missing_optional = [k for k, ks in optional_kind_map.items() if not (ks & kinds_present)]
    # due_diligence_log is ALWAYS rendered (per spec), so never missing
    return missing_required, missing_optional


def _build_memo_markdown(
    *,
    company_name: str,
    founder_output: FounderAgentOutput,
    market_output: MarketAgentOutput,
    idea_vs_market_output: IdeaVsMarketAgentOutput,
    validator_outputs: list[ValidatorAgentOutput],
    claims: list[Claim],
    overall_recommendation: str,
    overall_conviction: float,
    evidence_coverage: float,
    open_contradictions: list[str],
    missing_required: list[str],
    missing_optional: list[str],
    next_actions: list[str],
) -> str:
    """Deterministic memo_markdown builder.

    Every factual sentence cites a claim via [^claim_id].
    Optional sections missing → render the callout "(not disclosed — request from founder)".
    """
    claims_by_id = {c.id: c for c in claims}
    validators_by_claim = {o.claim_id: o for o in validator_outputs}

    def cite(claim_id: uuid.UUID) -> str:
        return f"[^{claim_id}]"

    def find_claim(kind: str, text_contains: Optional[str] = None) -> Optional[Claim]:
        for c in claims:
            if (c.kind.value if hasattr(c.kind, "value") else str(c.kind)) != kind:
                continue
            if text_contains and text_contains.lower() not in c.text.lower():
                continue
            return c
        return None

    def find_claims_by_kind(kind: str) -> list[Claim]:
        return [c for c in claims if (c.kind.value if hasattr(c.kind, "value") else str(c.kind)) == kind]

    parts: list[str] = []

    # Cold-start banner
    if founder_output.cold_start:
        parts.append(
            "> ⚠️ Cold-start founder. External signals absent. All scores carry wide confidence "
            "bands. Recommend deep_dive, not fast_pass, regardless of headline numbers.\n"
        )

    parts.append(f"# Investment Memo: {company_name}\n")

    # ---- Company Snapshot (required) ----
    parts.append("## Company Snapshot\n")
    product_claims = find_claims_by_kind("product")
    if product_claims:
        for c in product_claims[:3]:
            parts.append(f"- {c.text} {cite(c.id)}\n")
    else:
        bg = find_claim("founder_background")
        if bg:
            parts.append(f"- {bg.text} {cite(bg.id)}\n")
        else:
            parts.append("- Company snapshot not disclosed — request from founder.\n")

    # ---- Investment Hypotheses (required) ----
    parts.append("\n## Investment Hypotheses\n")
    hyp_count = 0
    for c in claims:
        if hyp_count >= 4:
            break
        if (c.kind.value if hasattr(c.kind, "value") else str(c.kind)) in {"product", "market_trend", "technical_depth"}:
            parts.append(f"- {c.text} {cite(c.id)}\n")
            hyp_count += 1
    if hyp_count == 0:
        parts.append("- No investment hypotheses derivable — request deck from founder.\n")

    # ---- SWOT (required) ----
    parts.append("\n## SWOT\n")
    parts.append("**Strengths:**\n")
    for c in find_claims_by_kind("technical_depth")[:2]:
        parts.append(f"- {c.text} {cite(c.id)}\n")
    parts.append("**Weaknesses:**\n")
    missing_weaknesses = [c for c in claims if c.validator_status == "unverifiable"][:2]
    if missing_weaknesses:
        for c in missing_weaknesses:
            parts.append(f"- Unverified: {c.text} {cite(c.id)}\n")
    else:
        # Structural placeholder — no factual claim, just notes the absence of evidence
        parts.append("- (No unverifiable claims surfaced by Validator.)\n")
    parts.append("**Opportunities:**\n")
    for c in find_claims_by_kind("market_trend")[:2]:
        parts.append(f"- {c.text} {cite(c.id)}\n")
    parts.append("**Threats:**\n")
    for c in find_claims_by_kind("competitive")[:2]:
        parts.append(f"- {c.text} {cite(c.id)}\n")

    # ---- Problem & Product (required) ----
    parts.append("\n## Problem & Product\n")
    if product_claims:
        for c in product_claims[:2]:
            parts.append(f"- {c.text} {cite(c.id)}\n")
    else:
        parts.append("- Problem and product description not disclosed — request deck from founder.\n")

    # ---- Traction & KPIs (required) ----
    parts.append("\n## Traction & KPIs\n")
    traction_claims = find_claims_by_kind("traction")
    if traction_claims:
        parts.append("| KPI | Value | Period | Source |\n")
        parts.append("|-----|-------|--------|--------|\n")
        for c in traction_claims[:5]:
            parts.append(f"| {c.kind.value} | {c.text[:80]} | n/a | {c.source.ref} {cite(c.id)} |\n")
    else:
        parts.append("- Traction metrics not disclosed — request KPIs from founder.\n")

    # ---- Optional sections ----
    optional_render = {
        "team_and_history": ("## Team & History\n", ["founder_background", "founder_network", "team"]),
        "technology_and_defensibility": ("## Technology & Defensibility\n", ["technical_depth", "competitive"]),
        "market_sizing": ("## Market Sizing\n", ["market_size"]),
        "competition": ("## Competition\n", ["competitive"]),
        "financials_and_round_structure": ("## Financials & Round Structure\n", ["financial"]),
        "cap_table": ("## Cap Table\n", ["financial", "team"]),
        "exit_perspective": ("## Exit Perspective\n", []),
    }
    for key, (heading, kinds) in optional_render.items():
        parts.append(f"\n{heading}")
        section_claims = [c for c in claims if (c.kind.value if hasattr(c.kind, "value") else str(c.kind)) in kinds]
        if section_claims:
            for c in section_claims[:3]:
                parts.append(f"- {c.text} {cite(c.id)}\n")
        else:
            # Spec §4.6 MEMO STRUCTURE: mark optional-missing with "(<section> not disclosed — request from founder.)"
            # Strip the heading of markdown markers AND newlines.
            section_name = heading.replace("##", "").replace("\n", "").strip().replace("&", "and")
            parts.append(f"- ({section_name} not disclosed — request from founder.)\n")
            if key in missing_optional:
                pass  # tracked separately

    # ---- Due Diligence Log (always rendered) ----
    parts.append("\n## Due Diligence Log\n")
    parts.append("| Claim | Status | Confidence | Source |\n")
    parts.append("|-------|--------|------------|--------|\n")
    for o in validator_outputs:
        c = claims_by_id.get(o.claim_id)
        if c is None:
            continue
        text_short = c.text[:60].replace("|", "\\|")
        src = c.source.ref[:40].replace("|", "\\|")
        parts.append(f"| {text_short} | {o.status} | {o.confidence:.2f} | {src} |\n")

    # ---- Recommendation ----
    parts.append("\n## Recommendation\n")
    parts.append(f"- **Overall:** {overall_recommendation}\n")
    parts.append(f"- **Conviction:** {overall_conviction}/100\n")
    parts.append(f"- **Evidence coverage:** {evidence_coverage:.2f}\n")
    parts.append(f"- **Open contradictions:** {len(open_contradictions)}\n")
    parts.append("- **Next actions:**\n")
    for action in next_actions:
        parts.append(f"  - {action}\n")

    return "".join(parts)


def _next_actions(
    *,
    recommendation: str,
    missing_required: list[str],
    missing_optional: list[str],
    open_contradictions: list[str],
    cold_start: bool,
) -> list[str]:
    """Build next_actions list."""
    out: list[str] = []
    if recommendation == "fast_pass":
        out.append("Prepare $100K SAFE for immediate deployment within 24h.")
    elif recommendation == "deep_dive":
        out.append("Schedule 2-4 hour human diligence sprint before deployment.")
    elif recommendation == "pass":
        out.append("Park in pipeline; revisit in 30 days.")
    else:
        out.append("Pass — do not deploy capital.")
    if cold_start:
        out.append("Request GitHub, arxiv, and Product Hunt profiles from founder to resolve cold-start.")
    for section in missing_required:
        out.append(f"Request {section.replace('_', ' ')} from founder (required section missing).")
    if open_contradictions:
        out.append(f"Resolve {len(open_contradictions)} open contradiction(s) with founder.")
    return out


async def run_aggregator_agent(
    *,
    application_id: Optional[uuid.UUID],
    founder_id: uuid.UUID,
    company_id: uuid.UUID,
    company_name: str,
    thesis: Thesis,
    founder_agent_output: FounderAgentOutput,
    market_agent_output: MarketAgentOutput,
    idea_vs_market_agent_output: IdeaVsMarketAgentOutput,
    validator_outputs: list[ValidatorAgentOutput],
    claims: list[Claim],
    prior_founder_score: Optional[FounderScore],
    thesis_fit_score: float,
    model: Optional[str] = None,
) -> AggregatorOutput:
    """Tool-less synthesizer. Computes recommendation, conviction, evidence_coverage,
    missing sections, and memo.

    Per spec §5.2 + §4.6: uses SYNTHESIZER_MODEL (gpt-5.6-sol) for memo generation.
    We invoke the LLM to refine the memo text, then fall back to the deterministic
    `_build_memo_markdown` builder if the LLM fails OR omits required citations.
    The deterministic builder is the source of truth for structural correctness
    (every factual sentence has [^claim_id], all 14 sections render, cold-start
    banner present). The LLM is a refinement layer.

    NOTE: per spec §5.4, NO tools= argument is ever bound here. The LLM call
    goes through `chat_complete_json` which has no tool access.
    """
    # Filter superseded claims
    active_claims = [c for c in claims if c.superseded_by is None]

    axes = {
        "founder": founder_agent_output.composite_score,
        "market": market_agent_output.numeric_score,
        "idea_vs_market": idea_vs_market_agent_output.fit_score,
    }
    axes_trends = {
        "founder": founder_agent_output.trend,
        "market": "stable",  # categorical; no trend concept
        "idea_vs_market": "stable",
    }

    evidence_cov = _evidence_coverage(active_claims, validator_outputs)
    open_contradictions = _open_contradictions(validator_outputs)
    missing_required, missing_optional = _missing_sections(active_claims)

    recommendation = _recommendation(
        axes=axes,
        market_score=market_agent_output.market_score,
        thesis_fit_score=thesis_fit_score,
        evidence_coverage=evidence_cov,
        open_contradictions=open_contradictions,
        missing_required=missing_required,
        cold_start=founder_agent_output.cold_start,
    )

    conviction = _compute_overall_conviction(
        founder_score=axes["founder"],
        market_score=market_agent_output.market_score,
        idea_vs_market_score=axes["idea_vs_market"],
        thesis_fit_score=thesis_fit_score,
    )

    next_actions = _next_actions(
        recommendation=recommendation,
        missing_required=missing_required,
        missing_optional=missing_optional,
        open_contradictions=open_contradictions,
        cold_start=founder_agent_output.cold_start,
    )

    # Build the deterministic memo FIRST — this is the source of truth for structure.
    deterministic_memo = _build_memo_markdown(
        company_name=company_name,
        founder_output=founder_agent_output,
        market_output=market_agent_output,
        idea_vs_market_output=idea_vs_market_agent_output,
        validator_outputs=validator_outputs,
        claims=active_claims,
        overall_recommendation=recommendation,
        overall_conviction=conviction,
        evidence_coverage=evidence_cov,
        open_contradictions=open_contradictions,
        missing_required=missing_required,
        missing_optional=missing_optional,
        next_actions=next_actions,
    )

    # Optionally refine the memo via the LLM synthesizer (spec §5.2 SYNTHESIZER_MODEL).
    # The LLM receives the deterministic memo as a draft + the structured inputs,
    # and is asked to improve prose quality while preserving all [^claim_id] citations.
    # If the LLM output fails validation (missing citations, missing required sections,
    # missing cold-start banner), we fall back to the deterministic memo.
    memo = deterministic_memo
    try:
        refined = await _llm_refine_memo(
            deterministic_memo=deterministic_memo,
            company_name=company_name,
            founder_output=founder_agent_output,
            market_output=market_agent_output,
            idea_vs_market_output=idea_vs_market_agent_output,
            validator_outputs=validator_outputs,
            claims=active_claims,
            recommendation=recommendation,
            conviction=conviction,
            evidence_coverage=evidence_cov,
            thesis_fit_score=thesis_fit_score,
            model=model,
        )
        if refined and _memo_passes_invariants(refined, active_claims, founder_agent_output.cold_start):
            memo = refined
        else:
            logger.info("Aggregator LLM memo failed invariants — using deterministic memo")
    except Exception as e:
        logger.warning("Aggregator LLM refinement failed: %s — using deterministic memo", e)

    return AggregatorOutput(
        application_id=application_id,
        founder_id=founder_id,
        company_id=company_id,
        overall_recommendation=recommendation,  # type: ignore[arg-type]
        overall_conviction=conviction,
        axes=axes,
        axes_trends=axes_trends,
        thesis_fit_score=thesis_fit_score,
        evidence_coverage=evidence_cov,
        open_contradictions=open_contradictions,
        missing_required_sections=missing_required,
        missing_optional_sections=missing_optional,
        memo_markdown=memo,
        next_actions=next_actions,
        computed_at=datetime.utcnow(),
    )


async def _llm_refine_memo(
    *,
    deterministic_memo: str,
    company_name: str,
    founder_output: FounderAgentOutput,
    market_output: MarketAgentOutput,
    idea_vs_market_output: IdeaVsMarketAgentOutput,
    validator_outputs: list[ValidatorAgentOutput],
    claims: list[Claim],
    recommendation: str,
    conviction: float,
    evidence_coverage: float,
    thesis_fit_score: float,
    model: Optional[str] = None,
) -> Optional[str]:
    """Ask the LLM synthesizer to refine the deterministic memo.

    Per spec §5.2: uses SYNTHESIZER_MODEL (gpt-5.6-sol). NO tools bound.
    The LLM is told: "Improve the prose of this memo. Preserve EVERY [^claim_id]
    citation verbatim. Preserve the cold-start banner if present. Preserve all
    section headings. Do NOT add new factual claims."
    """
    from app.llm import client as llm_client
    from app.config import settings

    prompt = (
        "You are refining an investment memo. The draft below is structurally correct "
        "(every section rendered, every fact cited). Improve the PROSE QUALITY — make it "
        "more concise, more direct, better structured. PRESERVE EVERY [^claim_id] CITATION "
        "VERBATIM. Preserve the cold-start banner verbatim if present. Preserve all section "
        "headings. Do NOT add new factual claims. Do NOT remove factual claims.\n\n"
        f"DRAFT MEMO:\n{deterministic_memo}\n\n"
        "Return a JSON object: {\"memo_markdown\": \"<refined memo>\"}"
    )
    try:
        raw = await llm_client.chat_complete_json(
            system_prompt=load_prompt(),
            user_content=prompt,
            model=model or settings.synthesizer_model,
            temperature=0.2,
        )
        if isinstance(raw, dict) and "memo_markdown" in raw:
            return str(raw["memo_markdown"])
        return None
    except Exception as e:
        logger.warning("LLM memo refinement call failed: %s", e)
        return None


def _memo_passes_invariants(memo: str, claims: list[Claim], cold_start: bool) -> bool:
    """Verify the LLM-refined memo passes the spec §4.6 invariants:
    - R4: every factual sentence has [^claim_id] (we check that citations exist)
    - Cold-start banner present if cold_start==true
    - All 5 required sections present
    """
    # Must have at least one citation
    if "[^" not in memo:
        return False
    # Cold-start banner check
    if cold_start and "Cold-start founder" not in memo:
        return False
    # Required sections (must have all 5)
    required = ["## Company Snapshot", "## Investment Hypotheses", "## SWOT", "## Problem & Product", "## Traction & KPIs"]
    for section in required:
        if section not in memo:
            return False
    return True
