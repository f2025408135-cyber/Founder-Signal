"""Docker-free fixture API for reviewing the Next.js demo UI locally.

This server intentionally serves deterministic fixture outputs only. It does not
run agents, score founders, or replace the production FastAPI application.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Founder Signal Local Demo API")
NOW = datetime.now(timezone.utc).isoformat()

JANE = "00000000-0000-0000-0000-000000000001"
BOB = "00000000-0000-0000-0000-000000000002"
CAROL = "00000000-0000-0000-0000-000000000003"


def claim(claim_id: str, text: str, status: str, kind: str, source_kind: str, ref: str, confidence: float) -> dict:
    return {
        "id": claim_id,
        "kind": kind,
        "text": text,
        "source": {
            "kind": source_kind,
            "ref": ref,
            "raw_payload_hash": "fixture-payload-hash",
            "retrieved_by": "demo.fixture",
            "ingested_at": NOW,
        },
        "confidence": confidence,
        "flags": [{"flag": status, "set_by": "demo.fixture", "set_at": NOW, "reason": "Deterministic local demo fixture.", "counter_evidence_ref": None}],
        "validator_status": status,
        "superseded_by": None,
        "created_at": NOW,
    }


JANE_CLAIM = claim("10000000-0000-0000-0000-000000000001", "Jane is building developer tooling for LLM evaluation.", "cold_start_inferred", "cold_start_inferred", "application_form", f"application:{JANE}", 0.2)
BOB_CLAIM = claim("20000000-0000-0000-0000-000000000001", "VerifiedCo maintains an AI infrastructure repository with active public development.", "verified", "technical_depth", "github", "vercel/ai", 0.88)
CAROL_CLAIM = claim("30000000-0000-0000-0000-000000000001", "ContradictedCo reports incompatible market-size estimates across submitted evidence.", "contradicted", "market_size", "application_form", f"application:{CAROL}", 0.0)

CARDS = [
    {"founder_id": JANE, "founder_name": "Jane Doe", "company_id": "company-jane", "company_name": "StealthCo", "geography": "DE", "sector": "AI infra", "received_at": NOW, "founder_score": 48, "founder_trend": "insufficient_data", "market_score": "neutral", "idea_vs_market_score": 46, "thesis_fit_score": 68, "conviction": 47, "evidence_coverage": 0.0, "open_contradictions": 0, "recommendation": "deep_dive", "cold_start": True, "trend": "insufficient_data", "trace_id": "demo-jane", "computed_at": NOW, "application_id": JANE},
    {"founder_id": BOB, "founder_name": "Bob Smith", "company_id": "company-bob", "company_name": "VerifiedCo", "geography": "US", "sector": "AI infra", "received_at": NOW, "founder_score": 82, "founder_trend": "improving", "market_score": "bullish", "idea_vs_market_score": 79, "thesis_fit_score": 88, "conviction": 85, "evidence_coverage": 0.75, "open_contradictions": 0, "recommendation": "fast_pass", "cold_start": False, "trend": "improving", "trace_id": "demo-bob", "computed_at": NOW, "application_id": BOB},
    {"founder_id": CAROL, "founder_name": "Carol Wu", "company_id": "company-carol", "company_name": "ContradictedCo", "geography": "SG", "sector": "DevTools", "received_at": NOW, "founder_score": 61, "founder_trend": "stable", "market_score": "bear", "idea_vs_market_score": 45, "thesis_fit_score": 54, "conviction": 42, "evidence_coverage": 0.33, "open_contradictions": 1, "recommendation": "pass", "cold_start": False, "trend": "stable", "trace_id": "demo-carol", "computed_at": NOW, "application_id": CAROL},
]


def memo(founder_id: str, company: str, recommendation: str, conviction: float, claims: list[dict], markdown: str, *, cold_start: bool = False, contradictions: list[str] | None = None) -> dict:
    return {
        "founder_id": founder_id,
        "founder_name": next(card["founder_name"] for card in CARDS if card["founder_id"] == founder_id),
        "company_name": company,
        "aggregator_output": {
            "id": f"memo-{founder_id}", "overall_recommendation": recommendation, "overall_conviction": conviction,
            "axes": {"founder": next(card["founder_score"] for card in CARDS if card["founder_id"] == founder_id), "market": 50, "idea_vs_market": next(card["idea_vs_market_score"] for card in CARDS if card["founder_id"] == founder_id)},
            "axes_trends": {"founder": "insufficient_data" if cold_start else "stable", "market": "stable", "idea_vs_market": "stable"},
            "thesis_fit_score": next(card["thesis_fit_score"] for card in CARDS if card["founder_id"] == founder_id),
            "evidence_coverage": next(card["evidence_coverage"] for card in CARDS if card["founder_id"] == founder_id),
            "open_contradictions": contradictions or [], "missing_required_sections": [],
            "missing_optional_sections": ["financials_and_round_structure", "cap_table"], "memo_markdown": markdown,
            "next_actions": ["Request the missing diligence materials.", "Review the cited evidence with the investment team."],
            "computed_at": NOW, "trace_id": f"demo-{company.lower().replace(' ', '-')}",
        },
        "claims": claims,
        "score_history": [{"computed_at": NOW, "score": conviction, "trend": "stable", "trigger": "demo_fixture", "cold_start": cold_start, "component_scores": {}, "confidence_band": [20, 80] if cold_start else [78, 88]}],
        "rescore_reason": "cache_hit",
    }


MEMOS = {
    JANE: memo(JANE, "StealthCo", "deep_dive", 47, [JANE_CLAIM], "> ⚠️ Cold-start founder. External signals absent. All scores carry wide confidence bands. Recommend deep_dive, not fast_pass, regardless of headline numbers.\n\n# Investment Memo: StealthCo\n\n## Company Snapshot\n- Jane is building developer tooling for LLM evaluation. [^10000000-0000-0000-0000-000000000001]\n\n## Financials & Round Structure\n- (Financials and Round Structure not disclosed - request from founder.)\n\n## Cap Table\n- (Cap Table not disclosed - request from founder.)\n\n## Recommendation\n- **Overall:** deep_dive", cold_start=True),
    BOB: memo(BOB, "VerifiedCo", "fast_pass", 85, [BOB_CLAIM], "# Investment Memo: VerifiedCo\n\n## Company Snapshot\n- VerifiedCo maintains an AI infrastructure repository with active public development. [^20000000-0000-0000-0000-000000000001]\n\n## Technology & Defensibility\n- VerifiedCo maintains an AI infrastructure repository with active public development. [^20000000-0000-0000-0000-000000000001]\n\n## Recommendation\n- **Overall:** fast_pass"),
    CAROL: memo(CAROL, "ContradictedCo", "pass", 42, [CAROL_CLAIM], "# Investment Memo: ContradictedCo\n\n## Market Sizing\n- ContradictedCo reports incompatible market-size estimates across submitted evidence. [^30000000-0000-0000-0000-000000000001]\n\n## Recommendation\n- **Overall:** pass", contradictions=["Market-size evidence is contradicted and requires founder clarification."]),
}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "mode": "fixture_demo"}


@app.get("/api/ping")
async def ping() -> dict:
    return {"pong": True}


@app.get("/api/applications/inbox")
async def inbox() -> dict:
    return {"total": len(CARDS), "cards": CARDS, "filters": {}}


@app.get("/api/founders/{founder_id}/memo")
async def founder_memo(founder_id: str) -> dict:
    if founder_id not in MEMOS:
        raise HTTPException(status_code=404, detail="Founder not found")
    return MEMOS[founder_id]


@app.get("/api/applications/{application_id}/source")
async def application_source(application_id: str) -> dict:
    if application_id not in MEMOS:
        raise HTTPException(status_code=404, detail="Application source not found")
    return {"application_id": application_id, "source": "founder_submission", "payload": {"fixture": "Local demo data", "founder_id": application_id}}


@app.get("/api/outbound/queue")
async def outbound() -> dict:
    founders = [{**CARDS[1], "sourcing_channel": "github", "signal_detected_at": NOW, "conviction_delta": 9.0}]
    return {"total": len(founders), "founders": founders}


@app.get("/api/applications")
async def applications() -> dict:
    return {"total": len(CARDS), "applications": [{"id": card["application_id"], "founder_id": card["founder_id"], "founder_name": card["founder_name"], "company_id": card["company_id"], "company_name": card["company_name"], "received_at": NOW, "status": "screened", "trace_id": card["trace_id"]} for card in CARDS]}


@app.get("/api/thesis")
async def thesis() -> dict:
    return {"id": "demo-thesis", "name": "Demo AI Infrastructure Thesis", "sectors": ["AI infra", "DevTools"], "stage": ["pre-seed", "seed"], "geography": ["DE", "US", "SG"], "check_size_usd": 100000, "ownership_target_pct": 10, "risk_appetite": {"max_founder_age_years": 5, "accepts_no_prior_funding": True, "accepts_no_github": True, "accepts_cold_start": True, "min_conviction_score": 60, "allow_neutral_market": True}, "created_at": NOW, "updated_at": NOW, "active": True}


@app.post("/api/thesis")
async def update_thesis() -> dict:
    return await thesis()


@app.post("/api/query")
async def query() -> dict:
    return {"query": "fixture", "decomposed_attributes": ["technical", "AI infra", "verified evidence"], "matches": [{"founder_id": BOB, "founder_name": "Bob Smith", "company_name": "VerifiedCo", "score": 85, "matched_attributes": ["technical", "AI infra", "verified evidence"]}]}


@app.get("/api/traces/{trace_id}")
async def trace(trace_id: str) -> dict:
    return {"trace_id": trace_id, "available": False, "reason": "Langfuse is not started in fixture demo mode."}
