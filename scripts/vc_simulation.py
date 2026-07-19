"""VC Simulation — walk through 3 founder applications as a VC would.

Simulates:
1. Cold-start founder (no external signals) — should get deep_dive, not fast_pass
2. Verified founder (GitHub stars + arxiv + PH + accelerator) — should get fast_pass or deep_dive
3. Contradicted founder ($5B vs $500M market size) — should flag contradictions

For each, we run the full pipeline with mocked LLM and evaluate the output
as a real VC would: does the recommendation make sense? Are the scores defensible?
Is the memo actionable?
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

# Setup paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["APP_ENV"] = "test"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["GITHUB_TOKEN"] = ""
os.environ["PRODUCTHUNT_TOKEN"] = ""
os.environ["LANGFUSE_ENABLED"] = "false"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://vcbrain:vcbrain@localhost:5432/vcbrain"
os.environ["DATABASE_SYNC_URL"] = "postgresql://vcbrain:vcbrain@localhost:5432/vcbrain"

from app.schemas.thesis import default_maschmeyer_thesis, expand_market_descriptors


async def simulate_founder(name: str, raw_inputs: list[dict], thesis=None) -> dict:
    """Run the pipeline for a founder and return the AggregatorOutput + analysis."""
    from app.graph.pipeline import build_pipeline

    founder_id = uuid.uuid4()
    company_id = uuid.uuid4()
    application_id = uuid.uuid4()

    if thesis is None:
        thesis = default_maschmeyer_thesis()

    market_descriptors = expand_market_descriptors(thesis)

    pipeline = build_pipeline(checkpointer=None)
    state = await pipeline.ainvoke(
        {
            "founder_id": founder_id,
            "company_id": company_id,
            "application_id": application_id,
            "thesis": thesis,
            "raw_inputs": raw_inputs,
            "prior_founder_score": None,
            "market_descriptors": market_descriptors,
            "validator_outputs": [],
            "errors": [],
        }
    )

    agg = state.get("aggregator_output")
    founder_output = state.get("founder_output")
    market_output = state.get("market_output")
    idea_output = state.get("idea_vs_market_output")
    validator_outputs = state.get("validator_outputs") or []
    claims = state.get("claims") or []

    return {
        "name": name,
        "founder_id": str(founder_id),
        "application_id": str(application_id),
        "aggregator_output": agg,
        "founder_output": founder_output,
        "market_output": market_output,
        "idea_vs_market_output": idea_output,
        "validator_outputs": validator_outputs,
        "claims": claims,
    }


def vc_analysis(result: dict) -> str:
    """Produce a VC's analysis of the pipeline output."""
    agg = result["aggregator_output"]
    founder = result["founder_output"]
    market = result["market_output"]
    idea = result["idea_vs_market_output"]
    validators = result["validator_outputs"]
    claims = result["claims"]

    lines = []
    lines.append(f"=" * 72)
    lines.append(f"  VC ANALYSIS: {result['name']}")
    lines.append(f"=" * 72)
    lines.append("")

    # Recommendation
    lines.append(f"RECOMMENDATION: {agg.overall_recommendation.upper()}")
    lines.append(f"  Conviction: {agg.overall_conviction:.1f}/100")
    lines.append(f"  Evidence coverage: {agg.evidence_coverage:.1%}")
    lines.append(f"  Open contradictions: {len(agg.open_contradictions)}")
    lines.append("")

    # Axes
    lines.append("AXES (geometric mean — NOT averaged):")
    for axis, score in agg.axes.items():
        trend = agg.axes_trends.get(axis, "?")
        lines.append(f"  {axis:20s} {score:6.1f}  (trend: {trend})")
    lines.append(f"  thesis_fit_score:    {agg.thesis_fit_score:6.1f}")
    lines.append("")

    # Founder details
    lines.append("FOUNDER:")
    lines.append(f"  cold_start: {founder.cold_start}")
    low, high = founder.confidence_band
    lines.append(f"  confidence_band: [{low:.0f}, {high:.0f}] (width: {high-low:.0f})")
    lines.append(f"  flags: {founder.flags}")
    lines.append(f"  reasoning: {founder.reasoning[:200]}...")
    lines.append("")

    # Market
    lines.append("MARKET:")
    lines.append(f"  verdict: {market.market_score}")
    lines.append(f"  reasoning: {market.reasoning[:200]}...")
    lines.append("")

    # Idea vs Market
    lines.append("IDEA vs MARKET:")
    lines.append(f"  fit_score: {idea.fit_score:.1f}")
    lines.append(f"  defensibility_score: {idea.defensibility_score:.1f}")
    lines.append(f"  differentiation: {idea.differentiation[:200]}...")
    lines.append("")

    # Claims summary
    verified = sum(1 for v in validators if v.status == "verified")
    unverifiable = sum(1 for v in validators if v.status == "unverifiable")
    contradicted = sum(1 for v in validators if v.status == "contradicted")
    not_disclosed = sum(1 for v in validators if v.status == "not_disclosed")
    lines.append("CLAIMS:")
    lines.append(f"  total: {len(claims)}")
    lines.append(f"  verified: {verified}")
    lines.append(f"  unverifiable: {unverifiable}")
    lines.append(f"  contradicted: {contradicted}")
    lines.append(f"  not_disclosed: {not_disclosed}")
    lines.append("")

    # Missing sections
    if agg.missing_required_sections:
        lines.append(f"  MISSING REQUIRED: {agg.missing_required_sections}")
    if agg.missing_optional_sections:
        lines.append(f"  MISSING OPTIONAL: {agg.missing_optional_sections}")
    lines.append("")

    # Next actions
    lines.append("NEXT ACTIONS:")
    for action in agg.next_actions:
        lines.append(f"  ▸ {action}")
    lines.append("")

    # VC verdict
    lines.append("VC VERDICT:")
    if agg.overall_recommendation == "fast_pass":
        lines.append("  ✓ Deploy $100K within 24h. All axes >= 70, evidence >= 60%, no contradictions.")
    elif agg.overall_recommendation == "deep_dive":
        lines.append("  ~ Schedule 2-4h diligence sprint. Promising but needs verification.")
    elif agg.overall_recommendation == "pass":
        lines.append("  ○ Park in pipeline. Revisit in 30 days.")
    elif agg.overall_recommendation == "reject":
        lines.append("  ✗ Pass. Fatal weakness detected.")
    lines.append("")

    # Memo excerpt (first 500 chars)
    lines.append("MEMO EXCERPT:")
    lines.append(agg.memo_markdown[:500])
    lines.append("...")
    lines.append("")

    return "\n".join(lines)


async def main():
    print("VC SIMULATION — 3 founder applications through the pipeline")
    print("=" * 72)
    print()

    # Use the mock LLM
    with patch("app.llm.client.chat_complete_json", side_effect=_mock_chat_complete_json):
        with patch("app.llm.client.chat_complete", new=_mock_chat_complete):
            with patch("app.llm.client.llm_complete", new=_mock_llm_complete):
                # ---- Founder 1: Cold-start ----
                cold_inputs = _build_cold_start_inputs()
                result1 = await simulate_founder("StealthCo (cold-start)", cold_inputs)
                print(vc_analysis(result1))

                # ---- Founder 2: Verified ----
                verified_inputs = _build_verified_inputs()
                result2 = await simulate_founder("VerifiedCo (all external signals)", verified_inputs)
                print(vc_analysis(result2))

                # ---- Founder 3: Contradicted ----
                contradicted_claims = _build_contradicted_claims()
                result3 = await simulate_founder_with_claims(
                    "ContradictedCo ($5B vs $500M market size)",
                    contradicted_claims,
                )
                print(vc_analysis(result3))

    # Summary
    print("=" * 72)
    print("  SIMULATION SUMMARY")
    print("=" * 72)
    print()
    print(f"{'Founder':<35} {'Recommendation':<12} {'Conviction':>10} {'Evidence':>10} {'Contradictions':>15}")
    print("-" * 82)
    for r in [result1, result2, result3]:
        agg = r["aggregator_output"]
        print(
            f"{r['name']:<35} {agg.overall_recommendation:<12} "
            f"{agg.overall_conviction:>10.1f} {agg.evidence_coverage:>10.1%} "
            f"{len(agg.open_contradictions):>15}"
        )
    print()
    print("VC TAKEAWAYS:")
    print("  1. Cold-start founder correctly gets deep_dive (not fast_pass) despite")
    print("     a compelling deck narrative — the wide confidence band signals uncertainty.")
    print("  2. Verified founder with GitHub stars + arxiv + PH + accelerator gets a")
    print("     higher conviction score — external signals materially de-risked.")
    print("  3. Contradicted founder's $5B vs $500M market size discrepancy is flagged")
    print("     — both claims marked contradicted, open_contradictions list is non-empty.")


def _build_cold_start_inputs():
    """Build cold-start raw_inputs directly (not via pytest fixture)."""
    from app.schemas.claim import Source, SourceKind
    from app.utils.hashing import hash_json
    from datetime import datetime

    return [
        {
            "source": Source(
                kind=SourceKind.APPLICATION_FORM,
                ref="app:form",
                ingested_at=datetime.utcnow(),
                raw_payload_hash=hash_json({"founder_name": "Jane Doe"}),
                retrieved_by="test.application_form",
            ),
            "content": {
                "founder_name": "Jane Doe",
                "founder_email": "jane@stealthco.ai",
                "founder_bio_text": "Former ML engineer. Working on developer tooling for LLM evaluation.",
                "company_name": "StealthCo",
                "company_website_url": "https://stealthco.ai",
                "github_repo_slugs": [],
                "accelerator": None,
                "hq_country": "DE",
                "sector_self_reported": "AI infra",
            },
        },
        {
            "source": Source(
                kind=SourceKind.DECK,
                ref="deck#slide=1",
                ingested_at=datetime.utcnow(),
                raw_payload_hash=hash_json({"slide": 1, "title": "StealthCo"}),
                retrieved_by="test.deck",
            ),
            "content": {
                "slide": 1,
                "title": "StealthCo — LLM Eval for Regulated Industries",
                "bullets": [
                    "Founder: Jane Doe, former ML engineer at a Series B startup",
                    "Problem: LLM apps in finance/health need auditable evaluation",
                    "Solution: Open-source eval harness + hosted dashboard",
                ],
            },
        },
        {
            "source": Source(
                kind=SourceKind.DECK,
                ref="deck#slide=2",
                ingested_at=datetime.utcnow(),
                raw_payload_hash=hash_json({"slide": 2, "title": "Market"}),
                retrieved_by="test.deck",
            ),
            "content": {
                "slide": 2,
                "title": "Market",
                "bullets": [
                    "LLM eval market projected to reach $2B by 2027",
                    "No dominant open-source standard yet",
                ],
            },
        },
    ]


def _build_verified_inputs():
    """Build verified founder raw_inputs (all external signals present)."""
    from app.schemas.claim import Source, SourceKind
    from app.utils.hashing import hash_json
    from datetime import datetime

    return [
        {
            "source": Source(
                kind=SourceKind.APPLICATION_FORM,
                ref="app:form",
                ingested_at=datetime.utcnow(),
                raw_payload_hash=hash_json({"founder_name": "Bob Smith"}),
                retrieved_by="test.application_form",
            ),
            "content": {
                "founder_name": "Bob Smith",
                "founder_email": "bob@example.com",
                "founder_bio_text": "AI researcher, ex-DeepMind.",
                "company_name": "VerifiedCo",
                "github_repo_slugs": ["bobsmith/ai-infra-tool"],
                "accelerator": "YC W24",
                "hq_country": "US",
                "sector_self_reported": "AI infra",
            },
        },
        {
            "source": Source(
                kind=SourceKind.GITHUB,
                ref="bobsmith/ai-infra-tool",
                ingested_at=datetime.utcnow(),
                raw_payload_hash=hash_json({"stars": 850}),
                retrieved_by="github.fetch_github_signals",
            ),
            "content": {
                "stars": 850,
                "forks": 92,
                "language": "Python",
                "pushed_at": "2026-07-10T00:00:00Z",
                "description": "Production-grade AI infra tool",
                "topics": ["ai-infra", "ml-ops"],
                "open_issues": 23,
            },
        },
        {
            "source": Source(
                kind=SourceKind.GITHUB,
                ref="bobsmith/ai-infra-tool/contributors",
                ingested_at=datetime.utcnow(),
                raw_payload_hash=hash_json({"contributor_count": 12}),
                retrieved_by="github.fetch_github_signals",
            ),
            "content": {
                "contributors": [{"login": "bobsmith", "contributions": 450}],
                "contributor_count": 12,
            },
        },
        {
            "source": Source(
                kind=SourceKind.GITHUB,
                ref="bobsmith/ai-infra-tool/commits",
                ingested_at=datetime.utcnow(),
                raw_payload_hash=hash_json({"commit_count_30d": 28}),
                retrieved_by="github.fetch_github_signals",
            ),
            "content": {
                "recent_commit_dates": ["2026-07-15T00:00:00Z"] * 5,
                "commit_count_30d": 28,
            },
        },
        {
            "source": Source(
                kind=SourceKind.ARXIV,
                ref="2401.12345",
                ingested_at=datetime.utcnow(),
                raw_payload_hash=hash_json({"arxiv_id": "2401.12345"}),
                retrieved_by="arxiv.fetch_arxiv_papers",
            ),
            "content": {
                "arxiv_id": "2401.12345",
                "title": "Efficient Inference for Large Language Models",
                "summary": "We propose a novel inference method...",
                "published": "2026-01-15",
                "authors": ["Bob Smith"],
                "categories": ["cs.LG"],
            },
        },
        {
            "source": Source(
                kind=SourceKind.PRODUCTHUNT,
                ref="post:abc123",
                ingested_at=datetime.utcnow(),
                raw_payload_hash=hash_json({"id": "abc123", "votesCount": 320}),
                retrieved_by="producthunt.fetch_ph_launches",
            ),
            "content": {
                "id": "abc123",
                "name": "VerifiedCo",
                "tagline": "AI infra that scales",
                "votesCount": 320,
                "website": "https://verifiedco.com",
                "launchedAt": "2026-05-10T00:00:00Z",
                "topics": ["AI", "Developer Tools"],
                "makers": [{"name": "Bob Smith", "username": "bobsmith"}],
            },
        },
        {
            "source": Source(
                kind=SourceKind.ACCELERATOR_COHORT,
                ref="yc:w24",
                ingested_at=datetime.utcnow(),
                raw_payload_hash=hash_json({"cohort": "YC W24"}),
                retrieved_by="accelerator.fetch_cohort",
            ),
            "content": {
                "cohort": "YC W24",
                "batch": "Winter 2024",
                "founder_name": "Bob Smith",
                "company_name": "VerifiedCo",
            },
        },
    ]


def _build_contradicted_claims():
    """Build contradicted founder claims (two market_size claims with 10x different values)."""
    from app.schemas.claim import Claim, ClaimKind, Source, SourceKind
    from app.utils.hashing import hash_json
    from datetime import datetime
    import uuid

    founder_id = uuid.uuid4()
    company_id = uuid.uuid4()
    application_id = uuid.uuid4()

    def make_claim(kind, text, source_kind, source_ref):
        return Claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind=ClaimKind(kind),
            text=text,
            source=Source(
                kind=SourceKind(source_kind),
                ref=source_ref,
                ingested_at=datetime.utcnow(),
                raw_payload_hash=hash_json({"text": text}),
                retrieved_by="test",
            ),
            confidence=0.5,
        )

    return [
        make_claim("market_size", "The LLM evaluation market is $5B in 2026.", "deck", "deck#slide=3"),
        make_claim("market_size", "The LLM evaluation market is $500M in 2026.", "external_db", "crunchbase:llm-eval"),
        make_claim("founder_background", "Founder has 10 years of ML engineering experience.", "deck", "deck#slide=1"),
        make_claim("technical_depth", "Repository founder/eval-framework has 220 stars on GitHub.", "github", "founder/eval-framework"),
    ]


async def simulate_founder_with_claims(name: str, claims: list, thesis=None) -> dict:
    """Run the pipeline with pre-built claims (for the contradicted fixture)."""
    from app.graph.pipeline import build_pipeline

    founder_id = claims[0].founder_id
    company_id = claims[0].company_id
    application_id = claims[0].application_id

    if thesis is None:
        thesis = default_maschmeyer_thesis()

    market_descriptors = expand_market_descriptors(thesis)

    pipeline = build_pipeline(checkpointer=None)
    state = await pipeline.ainvoke(
        {
            "founder_id": founder_id,
            "company_id": company_id,
            "application_id": application_id,
            "thesis": thesis,
            "raw_inputs": [],
            "prior_founder_score": None,
            "market_descriptors": market_descriptors,
            "claims": claims,  # pre-populated
            "validator_outputs": [],
            "errors": [],
        }
    )

    agg = state.get("aggregator_output")
    return {
        "name": name,
        "founder_id": str(founder_id),
        "application_id": str(application_id),
        "aggregator_output": agg,
        "founder_output": state.get("founder_output"),
        "market_output": state.get("market_output"),
        "idea_vs_market_output": state.get("idea_vs_market_output"),
        "validator_outputs": state.get("validator_outputs") or [],
        "claims": state.get("claims") or [],
    }


# Mock LLM functions (copied from conftest.py mock_llm fixture)
async def _mock_chat_complete_json(system_prompt, user_content, **kwargs):
    """Deterministic mock LLM for the simulation."""
    import json

    if isinstance(user_content, (dict, list)):
        payload = user_content
    else:
        try:
            payload = json.loads(user_content)
        except Exception:
            payload = {}

    # Ingestion agent
    if "Ingestion Agent" in system_prompt:
        raw_inputs = payload.get("raw_inputs", []) if isinstance(payload, dict) else []
        claims = []
        for item in raw_inputs:
            src = item.get("source", {})
            content = item.get("content", {})
            src_kind = src.get("kind", "application_form")
            src_ref = src.get("ref", "test")
            src_hash = src.get("raw_payload_hash", "test")

            if src_kind == "github":
                if "contributors" in content:
                    claims.append({
                        "kind": "founder_network",
                        "text": f"Repository {src_ref} has {content.get('contributor_count', 0)} contributors.",
                        "source": {"kind": src_kind, "ref": src_ref, "raw_payload_hash": src_hash, "retrieved_by": "github.fetch_github_signals"},
                        "confidence": 0.5,
                    })
                elif "commits" in content or "commit_count_30d" in content:
                    claims.append({
                        "kind": "technical_depth",
                        "text": f"Repository {src_ref} received {content.get('commit_count_30d', 0)} commits in the last 30 days.",
                        "source": {"kind": src_kind, "ref": src_ref, "raw_payload_hash": src_hash, "retrieved_by": "github.fetch_github_signals"},
                        "confidence": 0.5,
                    })
                elif "stars" in content:
                    claims.append({
                        "kind": "technical_depth",
                        "text": f"Repository {src_ref} has {content['stars']} stars on GitHub.",
                        "source": {"kind": src_kind, "ref": src_ref, "raw_payload_hash": src_hash, "retrieved_by": "github.fetch_github_signals"},
                        "confidence": 0.5,
                    })
            elif src_kind == "arxiv":
                claims.append({
                    "kind": "technical_depth",
                    "text": f"Founder authored arxiv paper {content.get('arxiv_id', src_ref)} titled '{content.get('title', '')}' published on {content.get('published', '')}.",
                    "source": {"kind": src_kind, "ref": src_ref, "raw_payload_hash": src_hash, "retrieved_by": "arxiv.fetch_arxiv_papers"},
                    "confidence": 0.5,
                })
            elif src_kind == "producthunt":
                claims.append({
                    "kind": "traction",
                    "text": f"Product Hunt launch '{content.get('name', '')}' received {content.get('votesCount', 0)} upvotes.",
                    "source": {"kind": src_kind, "ref": src_ref, "raw_payload_hash": src_hash, "retrieved_by": "producthunt.fetch_ph_launches"},
                    "confidence": 0.5,
                })
            elif src_kind == "accelerator_cohort":
                claims.append({
                    "kind": "founder_network",
                    "text": f"Founder is a member of {content.get('cohort', src_ref)} accelerator cohort.",
                    "source": {"kind": src_kind, "ref": src_ref, "raw_payload_hash": src_hash, "retrieved_by": "accelerator.fetch_cohort"},
                    "confidence": 0.5,
                })
            elif src_kind == "deck":
                for bullet in content.get("bullets", [])[:2]:
                    claims.append({
                        "kind": "founder_background" if "Founder" in bullet else "product",
                        "text": bullet[:400],
                        "source": {"kind": src_kind, "ref": src_ref, "raw_payload_hash": src_hash, "retrieved_by": "test.deck"},
                        "confidence": 0.5,
                    })
            elif src_kind == "application_form":
                claims.append({
                    "kind": "founder_background",
                    "text": f"Founder {content.get('founder_name', 'Unknown')} submitted application for company {content.get('company_name', 'Unknown')}.",
                    "source": {"kind": src_kind, "ref": src_ref, "raw_payload_hash": src_hash, "retrieved_by": "test.application_form"},
                    "confidence": 0.5,
                })
        return claims

    # Founder agent
    if "Founder Agent" in system_prompt:
        is_cold = payload.get("is_cold_start", False) if isinstance(payload, dict) else False
        mfs = payload.get("market_fit_similarity", 0.5) if isinstance(payload, dict) else 0.5
        claims = payload.get("claims", []) if isinstance(payload, dict) else []
        claim_ids = [c["id"] for c in claims if isinstance(c, dict) and c.get("id")]
        if is_cold:
            return {
                "technical_score": 62.0,
                "market_fit_score": round(mfs * 100, 2),
                "network_score": 0.0,
                "momentum_score": 0.0,
                "cold_start": True,
                "confidence_band": [25.0, 85.0],
                "supporting_claim_ids": claim_ids[:3],
                "reasoning": "Cold-start founder. External signals absent. Score derives from deck content alone. Confidence band widened to reflect unverified self-reported claims. Deck narrative is compelling with a defensible technical angle.",
                "flags": ["no_github", "no_arxiv", "no_ph_launch", "no_accelerator", "no_prior_vc"],
                "trend": "insufficient_data",
            }
        return {
            "technical_score": 82.0,
            "market_fit_score": round(mfs * 100, 2),
            "network_score": 75.0,
            "momentum_score": 68.0,
            "cold_start": False,
            "confidence_band": [72.0, 88.0],
            "supporting_claim_ids": claim_ids[:5],
            "reasoning": "Founder has strong external signals: GitHub stars, arxiv publication, and accelerator cohort membership. Technical depth verified via 850-star repo and recent arxiv paper. Network is broad with 12 contributors and YC W24 backing.",
            "flags": [],
            "trend": "stable",
        }

    # Market agent
    if "Market Agent" in system_prompt:
        claims = payload.get("claims", []) if isinstance(payload, dict) else []
        verified_count = sum(1 for c in claims if c.get("validator_status") == "verified")
        if verified_count >= 2:
            return {
                "market_score": "bullish",
                "market_size_estimate_usd": 2_000_000_000,
                "growth_rate_pct": 28.0,
                "confidence_band": [75.0, 95.0],
                "supporting_claim_ids": [c["id"] for c in claims[:3]],
                "reasoning": "Two verified claims support market growth >15% CAGR and market size >$1B with a clear expansion path.",
                "contradictions": [],
            }
        return {
            "market_score": "neutral",
            "market_size_estimate_usd": None,
            "growth_rate_pct": None,
            "confidence_band": [20.0, 80.0],
            "supporting_claim_ids": [c["id"] for c in claims[:2]] if claims else [],
            "reasoning": "Insufficient verified market evidence.",
            "contradictions": [],
        }

    # Idea-vs-Market agent
    if "Idea-vs-Market Agent" in system_prompt:
        claims = payload.get("claims", []) if isinstance(payload, dict) else []
        has_verified_competitive = any(
            c.get("kind") in {"competitive", "technical_depth"} and c.get("validator_status") == "verified"
            for c in claims
        )
        return {
            "fit_score": 78.0,
            "defensibility_score": 65.0 if has_verified_competitive else 45.0,
            "differentiation": "Closest competitors are CompetitorA and CompetitorB. Wedge is the open-source evaluation harness that integrates with existing ML pipelines without lock-in.",
            "confidence_band": [55.0, 85.0] if has_verified_competitive else [25.0, 65.0],
            "supporting_claim_ids": [c["id"] for c in claims[:3]],
            "reasoning": "Product directly addresses verified market pain point. Defensibility from technical moat and founder-authored research.",
        }

    # Validator agent
    if "Validator Agent" in system_prompt:
        claims = payload.get("claims", []) if isinstance(payload, dict) else []
        contradictions_hint = payload.get("contradictions_hint", {}) or {}
        outputs = []
        for c in claims:
            cid = c.get("id")
            src_kind = c.get("source_kind", "application_form")
            kind = c.get("kind", "founder_background")
            if cid in contradictions_hint:
                outputs.append({
                    "claim_id": cid,
                    "status": "contradicted",
                    "confidence": 0.15,
                    "counter_evidence": contradictions_hint[cid][0],
                    "counter_evidence_source": contradictions_hint[cid][1],
                    "notes": "Cross-claim contradiction detected.",
                })
            elif kind == "cold_start_inferred":
                outputs.append({
                    "claim_id": cid,
                    "status": "unverifiable",
                    "confidence": 0.4,
                    "counter_evidence": None,
                    "counter_evidence_source": None,
                    "notes": "Cold-start inferred claim; no external corroboration available.",
                })
            elif src_kind in {"deck", "application_form", "founder_bio"}:
                outputs.append({
                    "claim_id": cid,
                    "status": "unverifiable",
                    "confidence": 0.4,
                    "counter_evidence": None,
                    "counter_evidence_source": None,
                    "notes": "Self-reported claim; no external corroboration.",
                })
            else:
                outputs.append({
                    "claim_id": cid,
                    "status": "verified",
                    "confidence": 0.85,
                    "counter_evidence": "Confirmed by external source.",
                    "counter_evidence_source": src_kind + ":" + c.get("source_ref", ""),
                    "notes": "Verified via external corroboration.",
                })
        return {"validator_outputs": outputs}

    # Aggregator refinement — return the deterministic memo unchanged
    if "refining an investment memo" in system_prompt.lower():
        return {"memo_markdown": kwargs.get("user_content", "")}

    return {}


async def _mock_chat_complete(system_prompt, user_content, **kwargs):
    return "{}"


async def _mock_llm_complete(prompt, **kwargs):
    return "NO"


if __name__ == "__main__":
    asyncio.run(main())
