"""Outbound scan script — spec §10 B9.

Pulls:
- GitHub trending repos (last N hours) — uses GitHub search API sorted by stars
- Recent arxiv papers (last N hours) — sorted by submittedDate
- Recent Product Hunt launches (last N days) — GraphQL search
- Top Hacker News stories — Firebase topstories

For each discovery:
1. Create a Founder + Company row (if not already present) — flagged as outbound-sourced
2. Insert a FounderSignal row with conviction_delta estimate
3. If conviction_delta > 5, trigger the pipeline to compute a fresh score
4. New founders appear in /outbound page with sourcing_channel badge

Usage:
    python scripts/run_outbound_scan.py [--lookback-hours 1]
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Ensure backend/ is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sqlalchemy import desc, select

from app.config import settings
from app.db.models import (
    Application as ApplicationORM,
    Company,
    Founder,
    FounderSignalORM,
    ThesisConfig,
)
from app.db.session import async_session
from app.ingestion.arxiv import fetch_arxiv_papers
from app.ingestion.github import fetch_github_signals
from app.ingestion.hackernews import fetch_hn_item, fetch_hn_topstories
from app.ingestion.producthunt import fetch_ph_launches
from app.schemas.claim import Source, SourceKind
from app.schemas.thesis import RiskAppetite, Thesis, expand_market_descriptors
from app.utils.hashing import hash_json, hash_text

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


async def run_outbound_scan(*, lookback_hours: int = 1, scan_id: uuid.UUID | None = None) -> dict:
    """Run a single outbound scan pass. Returns a summary dict."""
    scan_id = scan_id or uuid.uuid4()
    started_at = datetime.utcnow()
    logger.info("Outbound scan %s started (lookback=%dh)", scan_id, lookback_hours)

    summary = {
        "scan_id": str(scan_id),
        "started_at": started_at.isoformat(),
        "lookback_hours": lookback_hours,
        "signals_detected": 0,
        "founders_created": 0,
        "pipelines_triggered": 0,
        "by_channel": {
            "github": 0,
            "arxiv": 0,
            "ph": 0,
            "hn": 0,
        },
    }

    # Load the active thesis (so we know what sectors/geographies to filter by)
    async with async_session() as s:
        thesis_q = select(ThesisConfig).where(ThesisConfig.active == True).limit(1)
        thesis_row = (await s.execute(thesis_q)).scalars().first()
        if thesis_row is None:
            logger.error("No active thesis found — aborting scan")
            summary["error"] = "no_active_thesis"
            summary["finished_at"] = datetime.utcnow().isoformat()
            return summary

    # ---- 1. GitHub: search for repos created in the last `lookback_hours` with high growth ----
    try:
        gh_signals = await _scan_github_trending(thesis_row, lookback_hours)
        summary["by_channel"]["github"] = len(gh_signals)
        for sig in gh_signals:
            await _record_signal(sig, "new_github_repo_high_growth", summary)
    except Exception as e:
        logger.warning("GitHub scan failed: %s", e)

    # ---- 2. arxiv: recent papers in thesis-relevant categories ----
    try:
        arxiv_signals = await _scan_arxiv_recent(thesis_row, lookback_hours)
        summary["by_channel"]["arxiv"] = len(arxiv_signals)
        for sig in arxiv_signals:
            await _record_signal(sig, "new_arxiv_paper", summary)
    except Exception as e:
        logger.warning("arxiv scan failed: %s", e)

    # ---- 3. ProductHunt: recent launches in thesis sectors ----
    try:
        ph_signals = await _scan_producthunt_recent(thesis_row)
        summary["by_channel"]["ph"] = len(ph_signals)
        for sig in ph_signals:
            await _record_signal(sig, "new_ph_launch", summary)
    except Exception as e:
        logger.warning("ProductHunt scan failed: %s", e)

    # ---- 4. Hacker News: top stories, look for high-points posts ----
    try:
        hn_signals = await _scan_hackernews_top()
        summary["by_channel"]["hn"] = len(hn_signals)
        for sig in hn_signals:
            await _record_signal(sig, "new_hn_post_above_threshold", summary)
    except Exception as e:
        logger.warning("Hacker News scan failed: %s", e)

    summary["signals_detected"] = sum(summary["by_channel"].values())
    summary["finished_at"] = datetime.utcnow().isoformat()
    summary["duration_seconds"] = (datetime.utcnow() - started_at).total_seconds()
    logger.info(
        "Outbound scan %s finished: %d signals, %d founders created, %d pipelines triggered (took %.1fs)",
        scan_id,
        summary["signals_detected"],
        summary["founders_created"],
        summary["pipelines_triggered"],
        summary["duration_seconds"],
    )
    return summary


# ---- Channel scanners ----


async def _scan_github_trending(thesis_row: ThesisConfig, lookback_hours: int) -> list[dict]:
    """Search GitHub for repos created in the lookback window with >10 stars.

    Uses GitHub search API: GET /search/repositories?q=created:>YYYY-MM-DD stars:>10
    """
    import httpx

    if not settings.github_token:
        logger.info("GITHUB_TOKEN not set — skipping GitHub scan")
        return []

    cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)
    cutoff_str = cutoff.strftime("%Y-%m-%d")
    # Build query from thesis sectors — pick the first sector as the keyword
    sector_keyword = thesis_row.sectors[0] if thesis_row.sectors else "AI"
    # Sanitize — GitHub search dislikes spaces
    sector_keyword = sector_keyword.replace(" ", "+")

    url = "https://api.github.com/search/repositories"
    params = {
        "q": f"{sector_keyword}+created:>{cutoff_str}+stars:>10",
        "sort": "stars",
        "order": "desc",
        "per_page": 10,
    }
    headers = {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "VC-Brain-Outbound-Scan",
    }

    async with httpx.AsyncClient(timeout=15, headers=headers) as c:
        r = await c.get(url, params=params)
        if r.status_code != 200:
            logger.warning("GitHub search returned %d: %s", r.status_code, r.text[:200])
            return []
        items = r.json().get("items", [])

    out: list[dict] = []
    for item in items[:5]:  # top 5 only
        slug = item.get("full_name", "")
        stars = item.get("stargazers_count", 0)
        if not slug or stars < 10:
            continue
        out.append({
            "founder_name": item.get("owner", {}).get("login", "unknown"),
            "company_name": item.get("name", slug.split("/")[-1]),
            "source_ref": slug,
            "stars": stars,
            "description": item.get("description", ""),
            "hq_country": "US",  # GitHub doesn't expose this; default
            "sector_self_reported": sector_keyword.replace("+", " "),
            "payload": {"slug": slug, "stars": stars, "description": item.get("description")},
            "conviction_delta": min(15.0, stars / 10.0),  # rough heuristic: 1 point per 10 stars, capped at 15
        })
    return out


async def _scan_arxiv_recent(thesis_row: ThesisConfig, lookback_hours: int) -> list[dict]:
    """Search arxiv for recent papers in thesis-relevant categories."""
    # Map thesis sectors to arxiv categories
    sector_to_arxiv_cat = {
        "AI infra": "cs.AI",
        "DevTools": "cs.SE",
        "Climate": "physics.ao-ph",
        "Robotics": "cs.RO",
    }
    cats = [sector_to_arxiv_cat[s] for s in thesis_row.sectors if s in sector_to_arxiv_cat]
    if not cats:
        cats = ["cs.AI"]

    # Build query: cat:cs.AI OR cat:cs.SE
    query = " OR ".join(f"cat:{c}" for c in cats)
    papers = await fetch_arxiv_papers(query, max_results=10)

    out: list[dict] = []
    cutoff = datetime.utcnow() - timedelta(hours=lookback_hours * 24)  # arxiv papers may be older
    for p in papers:
        content = p["content"]
        published_str = content.get("published", "")
        try:
            published = datetime.fromisoformat(published_str.replace("Z", "+00:00")).replace(tzinfo=None)
            if published < cutoff:
                continue
        except (ValueError, AttributeError):
            continue

        authors = content.get("authors", [])
        if not authors:
            continue
        first_author = authors[0]

        out.append({
            "founder_name": first_author,
            "company_name": content.get("title", "arxiv paper")[:80],
            "source_ref": content.get("arxiv_id", ""),
            "description": content.get("summary", "")[:200],
            "hq_country": "US",
            "sector_self_reported": "AI infra",
            "payload": content,
            "conviction_delta": 6.0,  # arxiv paper = modest conviction boost
        })
    return out


async def _scan_producthunt_recent(thesis_row: ThesisConfig) -> list[dict]:
    """Search ProductHunt for recent launches matching thesis sectors."""
    sector_keyword = thesis_row.sectors[0] if thesis_row.sectors else "AI"
    launches = await fetch_ph_launches(sector_keyword, lookback_days=7, max_pages=2)

    out: list[dict] = []
    for entry in launches[:5]:
        content = entry["content"]
        votes = content.get("votesCount", 0)
        if votes < 50:
            continue
        makers = content.get("makers", [])
        first_maker = makers[0].get("name") if makers else "unknown"

        out.append({
            "founder_name": first_maker,
            "company_name": content.get("name", "PH launch"),
            "source_ref": content.get("id", ""),
            "description": content.get("tagline", ""),
            "hq_country": "US",
            "sector_self_reported": sector_keyword,
            "payload": content,
            "conviction_delta": min(15.0, votes / 20.0),  # 1 point per 20 votes, cap 15
        })
    return out


async def _scan_hackernews_top() -> list[dict]:
    """Fetch top HN stories, keep those with >100 points."""
    top_ids = await fetch_hn_topstories()
    if not top_ids:
        return []

    out: list[dict] = []
    # Fetch up to 10 items (Firebase is rate-limit-friendly but we still cap)
    for item_id in top_ids[:10]:
        item = await fetch_hn_item(item_id)
        if not item:
            continue
        points = item.get("score", 0)
        if points < 100:
            continue
        title = item.get("title", "")
        by = item.get("by", "unknown")

        out.append({
            "founder_name": by,
            "company_name": title[:80],
            "source_ref": f"item:{item_id}",
            "description": title,
            "hq_country": "US",
            "sector_self_reported": "general",
            "payload": item,
            "conviction_delta": min(15.0, points / 20.0),
        })
    return out


async def _record_signal(signal: dict, signal_type: str, summary: dict) -> None:
    """Record a signal: create founder/company if new, insert FounderSignal, trigger pipeline if delta > 5."""
    try:
        async with async_session() as s:
            # Check if founder already exists by name + email-ish pattern
            founder_q = select(Founder).where(Founder.name == signal["founder_name"]).limit(1)
            founder = (await s.execute(founder_q)).scalars().first()

            if founder is None:
                founder = Founder(
                    id=uuid.uuid4(),
                    name=signal["founder_name"],
                    email=f"outbound+{signal['founder_name'].lower().replace(' ', '.')}@unknown.local",  # placeholder
                    bio_text=signal.get("description", "")[:500],
                )
                s.add(founder)
                await s.flush()
                summary["founders_created"] += 1

            # Create a Company row for the outbound source (always new — different from any inbound app)
            company = Company(
                id=uuid.uuid4(),
                founder_id=founder.id,
                name=signal["company_name"],
                hq_country=signal.get("hq_country", "US"),
                sector_self_reported=signal.get("sector_self_reported"),
            )
            s.add(company)
            await s.flush()

            # Insert the FounderSignal row
            payload_hash = hash_json(signal["payload"])
            sig = FounderSignalORM(
                id=uuid.uuid4(),
                founder_id=founder.id,
                signal_type=signal_type,
                detected_at=datetime.utcnow(),
                conviction_delta=signal["conviction_delta"],
                payload_hash=payload_hash,
                payload=signal["payload"],
            )
            s.add(sig)
            await s.commit()

            # If conviction_delta > 5, trigger the pipeline (background)
            if signal["conviction_delta"] > 5:
                asyncio.create_task(
                    _trigger_pipeline_for_outbound(
                        founder_id=founder.id,
                        company_id=company.id,
                        signal=signal,
                        signal_type=signal_type,
                    )
                )
                summary["pipelines_triggered"] += 1
    except Exception as e:
        logger.exception("Failed to record signal %r: %s", signal, e)


async def _trigger_pipeline_for_outbound(
    *,
    founder_id: uuid.UUID,
    company_id: uuid.UUID,
    signal: dict,
    signal_type: str,
) -> None:
    """Run the pipeline for an outbound-sourced founder."""
    from app.graph.pipeline import build_pipeline
    from app.schemas.thesis import RiskAppetite

    async with async_session() as s:
        thesis_q = select(ThesisConfig).where(ThesisConfig.active == True).limit(1)
        thesis_row = (await s.execute(thesis_q)).scalars().first()
        if thesis_row is None:
            logger.error("No active thesis — cannot run outbound pipeline for %s", founder_id)
            return

    thesis = Thesis(
        id=thesis_row.id,
        name=thesis_row.name,
        sectors=thesis_row.sectors,
        stage=thesis_row.stage,
        geography=thesis_row.geography,
        check_size_usd=thesis_row.check_size_usd,
        ownership_target_pct=thesis_row.ownership_target_pct,
        risk_appetite=RiskAppetite(**thesis_row.risk_appetite),
        created_at=thesis_row.created_at,
        updated_at=thesis_row.updated_at,
        active=thesis_row.active,
    )
    market_descriptors = expand_market_descriptors(thesis)

    # Build a single raw_input from the signal payload
    source_kind = _signal_type_to_source_kind(signal_type)
    source = Source(
        kind=source_kind,
        ref=signal["source_ref"],
        ingested_at=datetime.utcnow(),
        raw_payload_hash=hash_json(signal["payload"]),
        retrieved_by=f"outbound_scan.{signal_type}",
    )
    raw_inputs = [{"source": source, "content": signal["payload"]}]

    try:
        pipeline = build_pipeline(checkpointer=None)
        state = await pipeline.ainvoke(
            {
                "founder_id": founder_id,
                "company_id": company_id,
                "application_id": None,
                "thesis": thesis,
                "raw_inputs": raw_inputs,
                "prior_founder_score": None,
                "market_descriptors": market_descriptors,
                "validator_outputs": [],
                "errors": [],
            }
        )
        agg = state.get("aggregator_output")
        if agg:
            logger.info(
                "Outbound pipeline complete for founder %s: recommendation=%s conviction=%.1f",
                founder_id, agg.overall_recommendation, agg.overall_conviction,
            )
            # Update the cache so the card view serves fresh data immediately
            from app.triggers.rescore import write_cached_aggregator
            await write_cached_aggregator(founder_id, agg.model_dump(mode="json"))
    except Exception as e:
        logger.exception("Outbound pipeline failed for founder %s: %s", founder_id, e)


def _signal_type_to_source_kind(signal_type: str) -> SourceKind:
    """Map outbound signal_type to a SourceKind for the raw_input."""
    if "github" in signal_type:
        return SourceKind.GITHUB
    if "arxiv" in signal_type:
        return SourceKind.ARXIV
    if "ph" in signal_type or "producthunt" in signal_type:
        return SourceKind.PRODUCTHUNT
    if "hn" in signal_type or "hackernews" in signal_type:
        return SourceKind.HACKERNEWS
    return SourceKind.EXTERNAL_DB


def main():
    parser = argparse.ArgumentParser(description="Run an outbound scan pass.")
    parser.add_argument("--lookback-hours", type=int, default=1, help="Look back this many hours (default: 1)")
    args = parser.parse_args()

    summary = asyncio.run(run_outbound_scan(lookback_hours=args.lookback_hours))
    print("\n--- Scan summary ---")
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
