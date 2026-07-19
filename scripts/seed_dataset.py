#!/usr/bin/env python3
"""Seed the 50-founder synthetic dataset into the running Postgres database.

Inserts every founder + company + application + claim + founder_score +
founder_score_snapshot + (minimal) aggregator_output, using the SAME tables
the real ingestion pipeline writes to (per backend/app/db/models.py).

This is idempotent: re-running it will clear the previous seed (rows whose
founder_id matches one of our 50 dataset IDs) and re-insert.

The `bio_text` column on the Founder row carries a JSON blob with photo_url,
education, prior_experience, github_profile, and deck_summary — the
founder card + memo endpoints surface these fields to the frontend.

Usage:
    python scripts/seed_dataset.py            # uses DATABASE_URL env (or default)
    python scripts/seed_dataset.py --reset    # also truncate tables first
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from sqlalchemy import delete, select, text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.models import (  # noqa: E402
    AggregatorOutputORM,
    Application as ApplicationORM,
    ClaimORM,
    Company,
    Founder,
    FounderScoreORM,
    FounderScoreSnapshot,
    FounderSignalORM,
    ThesisConfig,
)
from app.db.session import async_session, engine  # noqa: E402
from app.schemas.thesis import default_maschmeyer_thesis  # noqa: E402

DATASET_DIR = REPO_ROOT / "dataset"
FOUNDERS_DIR = DATASET_DIR / "founders"


# ============================================================
# Helpers
# ============================================================
def _load_founders() -> list[dict]:
    files = sorted(FOUNDERS_DIR.glob("*.json"))
    if len(files) != 50:
        print(f"WARNING: expected 50 founder JSON files, found {len(files)}", file=sys.stderr)
    out = []
    for p in files:
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


def _bio_text_json(founder: dict) -> str:
    """Pack demo-only fields into Founder.bio_text as JSON.

    The bio_text column already accepts arbitrary text; the memo endpoint parses
    this JSON to surface photo_url / education / prior_experience / etc. to the
    frontend. This keeps the existing schema unchanged while still letting the
    demo render photos and education.
    """
    return json.dumps({
        "bio": founder["deck_summary"],
        "photo_url": founder["photo_url"],
        "university_image_url": founder["university_image_url"],
        "image_source": founder["image_source"],
        "education": founder["education"],
        "prior_experience": founder["prior_experience"],
        "github_profile": founder["github_profile"],
        "deck_summary": founder["deck_summary"],
        "categories": founder["categories"],
    }, default=str)


def _build_memo_markdown(founder: dict, claims: list[ClaimORM]) -> str:
    """Build a minimal but valid memo_markdown so /founders/{id}/memo renders.

    Real pipeline runs populate this via the Aggregator Agent. For the seed we
    synthesize a structured memo that exercises every section MemoView knows
    how to render — headings, paragraphs, bullets, table, citation chips.
    """
    is_cold = "cold_start" in founder["categories"]
    is_contra = "contradicted" in founder["categories"]
    is_missing = "missing_data" in founder["categories"]
    is_rich = "rich_signal" in founder["categories"]

    score = founder["founder_score_seed"]["current_score"]["score"]
    band = founder["founder_score_seed"]["current_score"]["confidence_band"]
    components = founder["founder_score_seed"]["current_score"]["component_scores"]

    sections: list[str] = []

    if is_cold:
        sections.append(
            "> ⚠️ Cold-start founder — no external signal sources could be located. "
            "All claims below are deck- or application-derived."
        )

    sections.append(f"# {founder['company_name']} — Investment Memo")
    sections.append("")
    sections.append(f"**Founder:** {founder['name']}")
    sections.append(f"**Sector:** {founder['sector']}")
    sections.append(f"**Stage:** {founder['stage']}")
    sections.append(f"**Geography:** {founder['geography']}")
    sections.append("")

    # Problem & Product
    sections.append("## Problem & Product")
    sections.append(founder["deck_summary"])
    sections.append("")

    # Traction & KPIs
    sections.append("## Traction & KPIs")
    traction_claims = [c for c in claims if c.kind == "traction"]
    if traction_claims:
        for c in traction_claims:
            sections.append(f"- {c.text} [^{c.id}]")
    else:
        sections.append("- No traction claims disclosed.")
    sections.append("")

    # Team & History
    sections.append("## Team & History")
    sections.append(founder["prior_experience"])
    edu = founder["education"]
    sections.append(f"Education: {edu['degree']}, {edu['university']} ({edu['year']}).")
    sections.append("")

    # Technology & Defensibility
    sections.append("## Technology & Defensibility")
    tech_claims = [c for c in claims if c.kind == "technical_depth"]
    if tech_claims:
        for c in tech_claims:
            sections.append(f"- {c.text} [^{c.id}]")
    else:
        sections.append("- No GitHub / arXiv / patent signal available (cold-start).")
    sections.append("")

    # Market Sizing
    sections.append("## Market Sizing")
    market_claims = [c for c in claims if c.kind in ("market_size", "market_trend")]
    if market_claims:
        for c in market_claims:
            sections.append(f"- {c.text} [^{c.id}]")
    else:
        sections.append("- Market sizing not provided.")
    sections.append("")

    # Financials & Round Structure
    sections.append("## Financials & Round Structure")
    fin_claims = [c for c in claims if c.kind == "financial"]
    if fin_claims:
        for c in fin_claims:
            sections.append(f"- {c.text} [^{c.id}]")
    elif is_missing:
        sections.append("- **Not disclosed.** Founder has not provided cap table or financials.")
    else:
        sections.append("- Pre-revenue, no funding round publicly disclosed.")
    sections.append("")

    # Cap Table
    sections.append("## Cap Table")
    if is_missing:
        sections.append("- Cap table not disclosed in application or deck.")
    else:
        sections.append("- Founder retains majority ownership; no external cap table provided.")
    sections.append("")

    # Due Diligence Log (markdown table — MemoView renders these)
    sections.append("## Due Diligence Log")
    sections.append("")
    sections.append("| Claim | Status | Confidence | Source |")
    sections.append("|---|---|---|---|")
    for c in claims[:8]:  # cap at 8 rows for readability
        status = "unverified"
        src_kind = c.source.get("kind", "?")
        src_ref = c.source.get("ref", "?")[:30]
        sections.append(
            f"| {c.text[:60]}{'…' if len(c.text) > 60 else ''} [^{c.id}] "
            f"| {status} | {c.confidence:.2f} | {src_kind}:{src_ref} |"
        )
    sections.append("")

    # Recommendation
    sections.append("## Recommendation")
    if is_cold:
        rec = "deep_dive"
        rec_text = ("Cold-start profile — too little external signal to fast-pass. "
                    "Recommend a deep-dive call to validate founder background and product wedge.")
    elif is_contra:
        rec = "deep_dive"
        rec_text = ("Open contradictions between deck and external sources. "
                    "Resolve contradictions before any pass recommendation.")
    elif is_missing:
        rec = "deep_dive"
        rec_text = ("Missing required disclosures (cap table / financials). "
                    "Deep-dive required to fill gaps before any pass decision.")
    elif is_rich:
        rec = "fast_pass"
        rec_text = ("Rich external signal corroboration. Fast-pass to partner meeting.")
    else:
        rec = "deep_dive"
        rec_text = "Standard deep-dive — sufficient signal to warrant a partner call."
    sections.append(rec_text)
    sections.append("")
    sections.append(f"**Conviction:** {score:.1f}/100  "
                    f"(confidence band {band[0]:.1f}–{band[1]:.1f})")
    sections.append(f"**Components:** technical={components.get('technical', 0):.0f}, "
                    f"market_fit={components.get('market_fit', 0):.0f}, "
                    f"network={components.get('network', 0):.0f}, "
                    f"momentum={components.get('momentum', 0):.0f}")
    sections.append("")

    return "\n".join(sections)


def _open_contradictions(founder: dict, claims: list[ClaimORM]) -> list[str]:
    """Synthesize the list of open contradiction strings for contradicted founders."""
    out = []
    if "contradicted" not in founder["categories"]:
        return out
    # Group claims by kind; if there are 2+ of the same kind, mark as contradiction
    by_kind: dict[str, list[ClaimORM]] = {}
    for c in claims:
        by_kind.setdefault(c.kind, []).append(c)
    for kind, group in by_kind.items():
        if len(group) >= 2:
            out.append(
                f"Two '{kind}' claims disagree: "
                f"\"{group[0].text[:60]}…\" vs \"{group[1].text[:60]}…\""
            )
    return out


def _missing_sections(founder: dict, claims: list[ClaimORM]) -> tuple[list[str], list[str]]:
    """Determine which memo sections are missing for this founder."""
    have = {c.kind for c in claims}
    required = ["financial", "team", "market_size", "traction", "product"]
    optional = ["competitive", "founder_network"]
    missing_req = [k for k in required if k not in have]
    missing_opt = [k for k in optional if k not in have]
    # For missing_data founders, financial + team are always missing
    if "missing_data" in founder["categories"]:
        for k in ("financial", "team"):
            if k not in missing_req:
                missing_req.append(k)
    return missing_req, missing_opt


def _next_actions(founder: dict) -> list[str]:
    is_cold = "cold_start" in founder["categories"]
    is_contra = "contradicted" in founder["categories"]
    is_missing = "missing_data" in founder["categories"]
    is_rich = "rich_signal" in founder["categories"]
    actions = []
    if is_cold:
        actions.append("Schedule founder interview to validate background claims.")
        actions.append("Request access to GitHub (if any) and product demo.")
    if is_contra:
        actions.append("Resolve open contradictions with founder before next round.")
        actions.append("Cross-reference Crunchbase / LinkedIn for ground truth.")
    if is_missing:
        actions.append("Request cap table and latest financials from founder.")
        actions.append("Ask for team roster and any external validation.")
    if is_rich:
        actions.append("Fast-track to partner meeting within 7 days.")
        actions.append("Run technical reference call with prior colleagues.")
    if not actions:
        actions.append("Standard deep-dive interview.")
    return actions


# ============================================================
# Thesis seed (so thesis_fit_score has a reference)
# ============================================================
async def seed_thesis(session: AsyncSession) -> uuid.UUID:
    thesis = default_maschmeyer_thesis()
    existing = await session.execute(select(ThesisConfig).where(ThesisConfig.name == thesis.name))
    row = existing.scalars().first()
    if row:
        row.active = True
        return row.id
    row = ThesisConfig(
        id=thesis.id,
        name=thesis.name,
        sectors=thesis.sectors,
        stage=thesis.stage,
        geography=thesis.geography,
        check_size_usd=thesis.check_size_usd,
        ownership_target_pct=thesis.ownership_target_pct,
        risk_appetite=thesis.risk_appetite.model_dump(),
        active=True,
    )
    session.add(row)
    return thesis.id


# ============================================================
# Insert one founder
# ============================================================
async def insert_founder(session: AsyncSession, founder: dict) -> None:
    founder_id = uuid.UUID(founder["founder_id"])
    company_id = uuid.UUID(founder["company_id"])
    application_id = uuid.UUID(founder["application_id"])

    # 1. Founder row — bio_text carries the demo metadata as JSON
    f = Founder(
        id=founder_id,
        name=founder["name"],
        email=f"founder+{founder['founder_id'][:8]}@{founder['company_name'].lower()}.example",
        bio_text=_bio_text_json(founder),
    )
    session.add(f)

    # 2. Company row
    session.add(Company(
        id=company_id,
        founder_id=founder_id,
        name=founder["company_name"],
        website_url=f"https://{founder['company_name'].lower()}.example",
        hq_country=founder["geography"],
        sector_self_reported=founder["sector"],
    ))

    # 3. Application row — minimal raw_payload mirroring ApplicationCreate
    raw_payload = {
        "founder_name": founder["name"],
        "founder_email": f.email,
        "founder_bio_text": founder["prior_experience"],
        "company_name": founder["company_name"],
        "company_website_url": f"https://{founder['company_name'].lower()}.example",
        "deck_url": None,
        "github_repo_slugs": ([founder["github_profile"]["top_repo"]]
                              if founder["github_profile"] else []),
        "accelerator": None,
        "hq_country": founder["geography"],
        "sector_self_reported": founder["sector"],
    }
    app = ApplicationORM(
        id=application_id,
        founder_id=founder_id,
        company_id=company_id,
        received_at=datetime.utcnow(),
        status="screened",  # so the inbox doesn't show "pending" everywhere
        raw_payload=raw_payload,
        trace_id=f"seed-{founder['founder_id'][:8]}",
        ingestion_complete_at=datetime.utcnow(),
        validator_complete_at=datetime.utcnow(),
        scoring_complete_at=datetime.utcnow(),
        aggregator_complete_at=datetime.utcnow(),
    )
    session.add(app)

    # 4. Claims
    claim_orms: list[ClaimORM] = []
    for c in founder["claims"]:
        claim = ClaimORM(
            id=uuid.UUID(c["id"]),
            founder_id=founder_id,
            company_id=company_id,
            application_id=application_id,
            kind=c["kind"],
            text=c["text"],
            source=c["source"],
            confidence=c["confidence"],
            flags=c["flags"],
            embedding=None,
            created_at=datetime.utcnow(),
            superseded_by=None,
        )
        session.add(claim)
        claim_orms.append(claim)

    # 5. Founder score (aggregate) + snapshot (SQL-queryable history)
    snap_dict = founder["founder_score_seed"]["current_score"]
    snap_id = uuid.uuid4()
    snap = FounderScoreSnapshot(
        id=snap_id,
        founder_id=founder_id,
        score=snap_dict["score"],
        confidence_band_low=snap_dict["confidence_band"][0],
        confidence_band_high=snap_dict["confidence_band"][1],
        trend=snap_dict["trend"],
        trigger=snap_dict["trigger"],
        evidence_claim_ids=[c["id"] for c in founder["claims"]],
        component_scores=snap_dict["component_scores"],
        cold_start=snap_dict["cold_start"],
        application_id=application_id,
        computed_at=datetime.utcnow(),
    )
    session.add(snap)

    score = FounderScoreORM(
        founder_id=founder_id,
        score_history=[snap_dict],
        current_score=snap_dict,
        trend=founder["founder_score_seed"]["trend"],
        applications=[{
            "application_id": founder["application_id"],
            "received_at": datetime.utcnow().isoformat(),
            "outcome": "pending",
        }],
        first_seen_at=datetime.utcnow(),
        last_updated_at=datetime.utcnow(),
    )
    session.add(score)

    # 6. Minimal aggregator output — enough for /founders/{id}/memo to render.
    # Real pipeline runs produce a full memo_markdown + axes; we synthesize a
    # reasonable approximation from the seed data.
    missing_req, missing_opt = _missing_sections(founder, claim_orms)
    axes = {
        "founder": snap_dict["score"],
        "market": 50.0 if founder["sector"] in ("AI infra", "DevTools", "Fintech") else 40.0,
        "idea_vs_market": snap_dict["component_scores"].get("market_fit", 50.0),
    }
    axes_trends = {
        "founder": snap_dict["trend"],
        "market": "stable",
        "idea_vs_market": "stable",
    }
    is_cold = "cold_start" in founder["categories"]
    is_rich = "rich_signal" in founder["categories"]
    is_contra = "contradicted" in founder["categories"]

    if is_rich:
        rec = "fast_pass"
        conviction = min(95.0, snap_dict["score"] + 5)
    elif is_cold:
        rec = "deep_dive"
        conviction = max(40.0, snap_dict["score"] - 5)
    elif is_contra:
        rec = "deep_dive"
        conviction = max(35.0, snap_dict["score"] - 10)
    else:
        rec = "deep_dive"
        conviction = snap_dict["score"]

    open_contras = _open_contradictions(founder, claim_orms)

    # Thesis fit: simple heuristic
    thesis_sectors = ["AI infra", "DevTools", "Climate", "Fintech", "Healthtech", "Consumer"]
    thesis_geo = ["DE", "US", "PK", "SG", "GB", "FR", "IN"]
    thesis_fit = 80.0 if (founder["sector"] in thesis_sectors and
                          founder["geography"] in thesis_geo) else 50.0

    evidence_coverage = min(1.0, len(claim_orms) / 8.0)

    session.add(AggregatorOutputORM(
        id=uuid.uuid4(),
        application_id=application_id,
        founder_id=founder_id,
        company_id=company_id,
        overall_recommendation=rec,
        overall_conviction=conviction,
        axes=axes,
        axes_trends=axes_trends,
        thesis_fit_score=thesis_fit,
        evidence_coverage=evidence_coverage,
        open_contradictions=open_contras,
        missing_required_sections=missing_req,
        missing_optional_sections=missing_opt,
        memo_markdown=_build_memo_markdown(founder, claim_orms),
        next_actions=_next_actions(founder),
        computed_at=datetime.utcnow(),
        trace_id=f"seed-{founder['founder_id'][:8]}",
    ))


# ============================================================
# Cleanup
# ============================================================
async def reset_seed(session: AsyncSession, founder_ids: list[uuid.UUID] = None) -> None:
    """Delete every seeded row.

    If `founder_ids` is provided, only deletes founders in that set (idempotent
    re-seed of the same dataset). If None, truncates all 7 seed-managed tables
    (used when the founder_id set changes between runs).
    """
    if founder_ids:
        # Delete only the specified founders
        await session.execute(delete(AggregatorOutputORM).where(AggregatorOutputORM.founder_id.in_(founder_ids)))
        await session.execute(delete(FounderScoreSnapshot).where(FounderScoreSnapshot.founder_id.in_(founder_ids)))
        await session.execute(delete(FounderScoreORM).where(FounderScoreORM.founder_id.in_(founder_ids)))
        await session.execute(delete(FounderSignalORM).where(FounderSignalORM.founder_id.in_(founder_ids)))
        await session.execute(delete(ClaimORM).where(ClaimORM.founder_id.in_(founder_ids)))
        await session.execute(delete(ApplicationORM).where(ApplicationORM.founder_id.in_(founder_ids)))
        await session.execute(text(
            "DELETE FROM companies WHERE founder_id = ANY(:ids)"
        ).bindparams(ids=list(founder_ids)))
        await session.execute(delete(Founder).where(Founder.id.in_(founder_ids)))
    else:
        # Full truncate — all seed-managed tables. Preserves thesis_configs,
        # github_etag_cache, dedupe_cache, langgraph_*, alembic_version.
        await session.execute(text("DELETE FROM aggregator_outputs"))
        await session.execute(text("DELETE FROM founder_score_snapshots"))
        await session.execute(text("DELETE FROM founder_scores"))
        await session.execute(text("DELETE FROM founder_signals"))
        await session.execute(text("DELETE FROM claims"))
        await session.execute(text("DELETE FROM applications"))
        await session.execute(text("DELETE FROM companies"))
        await session.execute(text("DELETE FROM founders"))
    await session.commit()


# ============================================================
# Main
# ============================================================
async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true",
                        help="Truncate all 50 seed rows before re-inserting (idempotent).")
    args = parser.parse_args()

    founders = _load_founders()
    print(f"Loaded {len(founders)} founder records from {FOUNDERS_DIR}")

    # Ensure tables exist (idempotent — uses alembic if migrations not applied yet)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    founder_ids = [uuid.UUID(f["founder_id"]) for f in founders]

    async with async_session() as session:
        # 1. Thesis
        thesis_id = await seed_thesis(session)
        await session.commit()
        print(f"Thesis ready: {thesis_id}")

        # 2. Optional reset — full truncate so re-seeds with different IDs work
        if args.reset:
            print("Resetting: truncating all seed-managed tables...")
            await reset_seed(session, founder_ids=None)
            print("  Done.")

        # 3. Insert founders one-by-one (commits per founder for resumability)
        print(f"Inserting {len(founders)} founders + claims + scores + aggregator outputs...")
        for i, f in enumerate(founders):
            try:
                await insert_founder(session, f)
                await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"  ✗ FAIL [{i+1}/50] {f['name']}: {e}")
                raise
            print(f"  ✓ [{i+1:2d}/50] {f['name']:25s} [{','.join(f['categories']):14s}]")

    # 4. Verify counts
    async with async_session() as session:
        for table_name, model in [
            ("founders", Founder),
            ("companies", Company),
            ("applications", ApplicationORM),
            ("claims", ClaimORM),
            ("founder_scores", FounderScoreORM),
            ("founder_score_snapshots", FounderScoreSnapshot),
            ("aggregator_outputs", AggregatorOutputORM),
        ]:
            r = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = r.scalar()
            print(f"  {table_name:30s} {count:5d} rows")

    print("\nDone. Run scripts/verify_dataset.py to confirm via API.")


if __name__ == "__main__":
    asyncio.run(main())
