"""Pytest configuration + fixtures.

Fixtures:
- cold_start_founder: no GitHub/arxiv/PH/accelerator signals — only deck + application_form
- verified_founder: GitHub stars, arxiv paper, PH launch — all external
- contradicted_founder: two market_size claims with 10x different values
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

# Ensure backend/ is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set test env vars BEFORE importing app modules.
# Use explicit assignment (not setdefault) to override any stale env from the host.
os.environ["APP_ENV"] = "test"
os.environ["OPENAI_API_KEY"] = "test-key-not-real"
os.environ["GITHUB_TOKEN"] = ""
os.environ["PRODUCTHUNT_TOKEN"] = ""
os.environ["LANGFUSE_ENABLED"] = "false"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://vcbrain:vcbrain@localhost:5432/vcbrain"
os.environ["DATABASE_SYNC_URL"] = "postgresql://vcbrain:vcbrain@localhost:5432/vcbrain"


@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for the whole test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def founder_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def company_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def application_id() -> uuid.UUID:
    return uuid.uuid4()


# ---- Source builders ----


def make_source(kind: str, ref: str, retrieved_by: str = "test", payload: Any = None):
    """Build a Source Pydantic object with a stable raw_payload_hash."""
    from app.schemas.claim import Source, SourceKind
    from app.utils.hashing import hash_json

    return Source(
        kind=SourceKind(kind),
        ref=ref,
        ingested_at=datetime.utcnow(),
        raw_payload_hash=hash_json(payload or {"ref": ref}),
        retrieved_by=retrieved_by,
    )


def make_claim(
    *,
    founder_id: uuid.UUID,
    company_id: uuid.UUID,
    kind: str,
    text: str,
    source_kind: str = "application_form",
    source_ref: str = "test",
    application_id: uuid.UUID | None = None,
    confidence: float = 0.5,
):
    """Build a Claim with sane defaults."""
    from app.schemas.claim import Claim, ClaimKind

    return Claim(
        founder_id=founder_id,
        company_id=company_id,
        application_id=application_id,
        kind=ClaimKind(kind),
        text=text,
        source=make_source(source_kind, source_ref, payload={"text": text}),
        confidence=confidence,
    )


# ===========================================================================
# FIXTURE 1: COLD-START FOUNDER
# No GitHub, no arxiv, no PH, no accelerator — only deck + application_form
# Ingestion Agent MUST emit a cold_start_inferred claim
# Founder Agent MUST set cold_start=true, wide band, >=3 flags
# ===========================================================================


@pytest.fixture
def cold_start_raw_inputs():
    """Raw inputs for a cold-start founder: deck + application_form only."""
    return [
        {
            "source": make_source(
                "application_form",
                "app:form",
                retrieved_by="test.application_form",
                payload={
                    "founder_name": "Jane Doe",
                    "company_name": "StealthCo",
                    "sector_self_reported": "AI infra",
                    "hq_country": "DE",
                },
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
            "source": make_source(
                "deck",
                "deck#slide=1",
                retrieved_by="test.deck",
                payload={"slide": 1, "title": "StealthCo — LLM Eval for Regulated Industries"},
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
            "source": make_source(
                "deck",
                "deck#slide=2",
                retrieved_by="test.deck",
                payload={"slide": 2, "title": "Market"},
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


@pytest.fixture
def cold_start_claims(founder_id, company_id, application_id):
    """Pre-built claims for a cold-start founder (no external sources)."""
    return [
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind="founder_background",
            text="Founder Jane Doe is a former ML engineer at a Series B startup.",
            source_kind="deck",
            source_ref="deck#slide=1",
        ),
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind="product",
            text="StealthCo builds an open-source LLM evaluation harness for regulated industries.",
            source_kind="deck",
            source_ref="deck#slide=1",
        ),
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind="market_size",
            text="LLM evaluation market is projected to reach $2B by 2027.",
            source_kind="deck",
            source_ref="deck#slide=2",
        ),
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind="cold_start_inferred",
            text="Cold-start founder with no GitHub, arxiv, Product Hunt, or accelerator signals.",
            source_kind="application_form",
            source_ref="app:form",
        ),
    ]


# ===========================================================================
# FIXTURE 2: VERIFIED FOUNDER
# Has GitHub stars, arxiv paper, PH launch — all external sources
# ===========================================================================


@pytest.fixture
def verified_raw_inputs():
    """Raw inputs for a verified founder — all external signals present."""
    return [
        {
            "source": make_source(
                "application_form",
                "app:form",
                retrieved_by="test.application_form",
                payload={"founder_name": "Bob Smith"},
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
            "source": make_source(
                "github",
                "bobsmith/ai-infra-tool",
                retrieved_by="github.fetch_github_signals",
                payload={"stars": 850},
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
            "source": make_source(
                "github",
                "bobsmith/ai-infra-tool/contributors",
                retrieved_by="github.fetch_github_signals",
                payload={"contributor_count": 12},
            ),
            "content": {
                "contributors": [{"login": "bobsmith", "contributions": 450}],
                "contributor_count": 12,
            },
        },
        {
            "source": make_source(
                "github",
                "bobsmith/ai-infra-tool/commits",
                retrieved_by="github.fetch_github_signals",
                payload={"commit_count_30d": 28},
            ),
            "content": {
                "recent_commit_dates": ["2026-07-15T00:00:00Z"] * 5,
                "commit_count_30d": 28,
            },
        },
        {
            "source": make_source(
                "arxiv",
                "2401.12345",
                retrieved_by="arxiv.fetch_arxiv_papers",
                payload={"arxiv_id": "2401.12345"},
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
            "source": make_source(
                "producthunt",
                "post:abc123",
                retrieved_by="producthunt.fetch_ph_launches",
                payload={"id": "abc123", "votesCount": 320},
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
            "source": make_source(
                "accelerator_cohort",
                "yc:w24",
                retrieved_by="accelerator.fetch_cohort",
                payload={"cohort": "YC W24"},
            ),
            "content": {
                "cohort": "YC W24",
                "batch": "Winter 2024",
                "founder_name": "Bob Smith",
                "company_name": "VerifiedCo",
            },
        },
    ]


@pytest.fixture
def verified_claims(founder_id, company_id, application_id):
    """Pre-built claims for a verified founder."""
    return [
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind="founder_background",
            text="Founder Bob Smith is an AI researcher and ex-DeepMind engineer.",
            source_kind="application_form",
            source_ref="app:form",
        ),
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind="technical_depth",
            text="Repository bobsmith/ai-infra-tool has 850 stars on GitHub.",
            source_kind="github",
            source_ref="bobsmith/ai-infra-tool",
        ),
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind="technical_depth",
            text="Repository bobsmith/ai-infra-tool received 28 commits in the last 30 days.",
            source_kind="github",
            source_ref="bobsmith/ai-infra-tool/commits",
        ),
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind="founder_network",
            text="Repository bobsmith/ai-infra-tool has 12 contributors.",
            source_kind="github",
            source_ref="bobsmith/ai-infra-tool/contributors",
        ),
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind="technical_depth",
            text="Founder Bob Smith authored arxiv paper 2401.12345 titled 'Efficient Inference for Large Language Models' published on 2026-01-15.",
            source_kind="arxiv",
            source_ref="2401.12345",
        ),
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind="traction",
            text="Product Hunt launch 'VerifiedCo' received 320 upvotes.",
            source_kind="producthunt",
            source_ref="post:abc123",
        ),
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind="founder_network",
            text="Founder Bob Smith is a member of YC W24 accelerator cohort.",
            source_kind="accelerator_cohort",
            source_ref="yc:w24",
        ),
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind="market_trend",
            text="AI infra market is growing at 28% CAGR driven by enterprise LLM adoption.",
            source_kind="external_db",
            source_ref="crunchbase:ai-infra-market",
        ),
    ]


# ===========================================================================
# FIXTURE 3: CONTRADICTED FOUNDER
# Two market_size claims with 10x different values — must both be flagged
# contradicted by the Validator.
# ===========================================================================


@pytest.fixture
def contradicted_claims(founder_id, company_id, application_id):
    """Pre-built claims with two contradictory market_size claims."""
    return [
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind="market_size",
            text="The LLM evaluation market is $5B in 2026.",
            source_kind="deck",
            source_ref="deck#slide=3",
        ),
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind="market_size",
            text="The LLM evaluation market is $500M in 2026.",
            source_kind="external_db",
            source_ref="crunchbase:llm-eval-market",
        ),
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind="founder_background",
            text="Founder has 10 years of ML engineering experience.",
            source_kind="deck",
            source_ref="deck#slide=1",
        ),
        make_claim(
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind="technical_depth",
            text="Repository founder/eval-framework has 220 stars on GitHub.",
            source_kind="github",
            source_ref="founder/eval-framework",
        ),
    ]


# ---- Thesis fixture ----


@pytest.fixture
def default_thesis():
    from app.schemas.thesis import default_maschmeyer_thesis

    return default_maschmeyer_thesis()


@pytest.fixture
def market_descriptors(default_thesis):
    from app.schemas.thesis import expand_market_descriptors

    return expand_market_descriptors(default_thesis)


# ---- LLM mock ----


@pytest.fixture
def mock_llm():
    """Patch the LLM client to return deterministic responses for tests."""
    from unittest.mock import AsyncMock, patch

    from app.llm import client as llm_client

    async def _mock_chat_complete_json(system_prompt, user_content, **kwargs):
        """Return deterministic JSON based on the prompt content."""
        if isinstance(user_content, (dict, list)):
            payload = user_content
        else:
            import json
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
                            "text": f"Repository {src_ref.split('/')[0]}/{src_ref.split('/')[0]} has {content.get('contributor_count', 0)} contributors.",
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
                    # External source — treat as verified
                    outputs.append({
                        "claim_id": cid,
                        "status": "verified",
                        "confidence": 0.85,
                        "counter_evidence": "Confirmed by external source.",
                        "counter_evidence_source": src_kind + ":" + c.get("source_ref", ""),
                        "notes": "Verified via external corroboration.",
                    })
            return {"validator_outputs": outputs}

        # Aggregator — but we use the deterministic builder, so LLM call is not made
        return {}

    with patch.object(llm_client, "chat_complete_json", side_effect=_mock_chat_complete_json):
        with patch.object(llm_client, "chat_complete", new=AsyncMock(return_value="{}")):
            with patch.object(llm_client, "llm_complete", new=AsyncMock(return_value="NO")):
                yield
