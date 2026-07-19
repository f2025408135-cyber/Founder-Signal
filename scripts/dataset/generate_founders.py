#!/usr/bin/env python3
"""Generate 50 synthetic founder profiles for the Founder-Signal demo.

Per docs/BUILD_SPEC.md §3.1 (Claim) and §3.2 (FounderScore) schemas.
Produces:
  dataset/founders/{founder_id}.json   — one file per founder
  dataset/index.json                   — summary with category tags + image-source flags
  dataset/README.md                    — final distribution + 4 demo fixture recommendations
  dataset/assets/*.svg                 — local-fallback avatars + university icons

Distribution target (with overlap allowed):
  ~10 cold_start     — zero external signal, only deck-derived claims
  ~12 rich_signal    — GitHub + arXiv|HackerNews|ProductHunt + accelerator
  ~10 contradicted   — at least one claim conflicts with another claim / plausible reality
  ~8  missing_data   — no disclosed cap table / financials / team
  ~10 mixed          — normal-signal remainder
Sectors:   AI infra, DevTools, Fintech, Healthtech, Climate, Consumer   (6 ≥ 5 required)
Geographies: US, DE, GB, SG, IN, FR, PK                                (7 ≥ 4 required)

Image sourcing (offline-safe):
  Photos:      randomuser.me/api/           (free, designed for fake profile data)
  Universities: Wikimedia Commons API        (CC-licensed campus photos)
  Fallback:    Local deterministic SVG (initials avatar + generic campus icon)
  The script logs clearly which founders got real fetched images vs. local fallback.

Usage:
  python scripts/dataset/generate_founders.py [--no-fetch] [--seed 42]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import httpx

# Make the backend importable so we can validate against the real Pydantic schemas
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.schemas.claim import Claim, ClaimKind, Source, SourceKind  # noqa: E402
from app.schemas.founder_score import FounderScore, ScoreSnapshot, Trend  # noqa: E402
from app.utils.hashing import hash_json  # noqa: E402

OUTPUT_DIR = REPO_ROOT / "dataset"
FOUNDERS_DIR = OUTPUT_DIR / "founders"
ASSETS_DIR = OUTPUT_DIR / "assets"

# ============================================================
# DATA POOLS — diverse across gender / ethnicity / geography
# ============================================================
SECTORS = ["AI infra", "DevTools", "Fintech", "Healthtech", "Climate", "Consumer"]
STAGES = ["pre-seed", "seed", "series-a"]
GEOGRAPHIES = ["US", "DE", "GB", "SG", "IN", "FR", "PK"]

FIRST_NAMES = [
    "Aisha", "Marcus", "Yuki", "Priya", "Dmitri", "Fatima", "Lars", "Ngozi",
    "Hiroshi", "Elena", "Kwame", "Mei", "Sven", "Ananya", "Rafael", "Ingrid",
    "Oluwaseun", "Yelena", "Arjun", "Sofia", "Kenji", "Amara", "Viktor", "Leila",
    "Tobias", "Zara", "Nikolai", "Adeola", "Ravi", "Camila", "Erik", "Hana",
    "Joaquin", "Nadia", "Stefan", "Yara", "Dario", "Linnea", "Omar", "Saanvi",
    "Pavel", "Jasmine", "Mikael", "Adaeze", "Henrik", "Rina", "Cyril", "Kavya",
    "Bastian", "Olamide",
]
LAST_NAMES = [
    "Chen", "Patel", "Müller", "Okafor", "Tanaka", "Silva", "Andersson", "Khan",
    "Novak", "O'Brien", "Yamamoto", "Rossi", "Schmidt", "Adebayo", "Volkov",
    "García", "Larsen", "Sharma", "Park", "Dubois", "Kowalski", "Mwangi",
    "Bergström", "Fernández", "Ivanov", "Nakamura", "Becker", "Almeida",
    "Petrov", "Singh", "Lindqvist", "Costa", "Hassan", "Reyes",
    "Schneider", "Watanabe", "Bauer", "Ibrahim", "Ali", "Nguyen",
]

# University → country mapping (country code is informational)
UNIVERSITIES = [
    {"name": "MIT",                          "country": "US"},
    {"name": "Stanford University",          "country": "US"},
    {"name": "ETH Zurich",                   "country": "CH"},
    {"name": "University of Cambridge",      "country": "GB"},
    {"name": "TU Munich",                    "country": "DE"},
    {"name": "IIT Bombay",                   "country": "IN"},
    {"name": "NUS Singapore",                "country": "SG"},
    {"name": "Tsinghua University",          "country": "CN"},
    {"name": "University of Toronto",        "country": "CA"},
    {"name": "Imperial College London",      "country": "GB"},
    {"name": "EPFL",                         "country": "CH"},
    {"name": "Carnegie Mellon University",   "country": "US"},
    {"name": "University of Oxford",         "country": "GB"},
    {"name": "TU Berlin",                    "country": "DE"},
    {"name": "LUMS",                         "country": "PK"},
    {"name": "National University of Singapore", "country": "SG"},
    {"name": "HEC Paris",                    "country": "FR"},
    {"name": "University of Lagos",          "country": "NG"},
]

DEGREES = [
    "BSc Computer Science", "MSc Electrical Engineering", "BSc Mathematics",
    "PhD Artificial Intelligence", "MSc Data Science", "BEng Software Engineering",
    "MBA", "MSc Robotics", "BSc Physics", "PhD Machine Learning",
]

COMPANY_PREFIXES = [
    "Nexus", "Vertex", "Quantum", "Helix", "Apex", "Lumen", "Cipher",
    "Forge", "Prism", "Atlas", "Orbit", "Flux", "Echo", "Drift",
    "Pulse", "Strata", "Nova", "Zenith", "Volt", "Mesh",
]
COMPANY_SUFFIXES = [
    "AI", "Labs", "Tech", "Systems", "Health", "Finance", "Climate",
    "Tools", "Cloud", "Data", "Robotics", "Bio", "Energy", "Stack",
]

DECK_PROBLEMS = [
    "LLM evaluation lacks standardized benchmarks for regulated industries.",
    "Developer onboarding takes 3+ weeks; existing tools don't integrate with CI/CD.",
    "Cross-border payments remain slow and expensive for SMBs.",
    "Clinical trial recruitment is bottlenecked by manual patient matching.",
    "Carbon accounting for supply chains is fragmented and error-prone.",
    "Consumer app discovery is broken; app store optimization is guesswork.",
    "AI model deployment lacks observability; teams fly blind in production.",
    "Data privacy compliance (GDPR/CCPA) is manual and error-prone.",
    "Battery lifecycle optimization for EV fleets is unsolved at scale.",
    "Code review for ML pipelines lacks tooling; bugs ship to production.",
    "Legacy hospital records are siloed and impossible to query in bulk.",
    "Grid operators lack real-time forecasting for distributed solar.",
]
DECK_SOLUTIONS = [
    "An open-source evaluation harness with auditable test suites.",
    "A CI/CD-native onboarding platform that reduces ramp time to 3 days.",
    "A real-time payment rail optimized for SMB cross-border transactions.",
    "An AI-powered patient matching engine for clinical trials.",
    "A supply chain carbon ledger with automated Scope 3 emissions tracking.",
    "A discovery platform using behavioral signals instead of ASO keywords.",
    "A model observability platform with drift detection and alerting.",
    "An automated privacy compliance scanner for codebases.",
    "A battery optimization platform using reinforcement learning.",
    "A code review tool specialized for ML pipeline correctness.",
    "A federated query layer that unifies EHR systems without data movement.",
    "A solar forecasting model trained on satellite imagery.",
]

GITHUB_LANGUAGES = ["Python", "TypeScript", "Rust", "Go", "JavaScript", "C++", "Julia"]
ACCELERATORS = ["YC W24", "YC S23", "Techstars", "Seedcamp", "Antler", "500 Global", "EWOR"]
PRIOR_COMPANIES = [
    "Google", "DeepMind", "Meta", "Stripe", "Anthropic", "OpenAI",
    "Microsoft", "Amazon", "Tesla", "Nvidia", "ByteDance", "Shopify",
    "a Series B startup", "a stealth AI startup", "a fintech unicorn",
    "a climate-tech scale-up", "a national research lab",
]

# Colors used for initials-avatar fallback
AVATAR_COLORS = [
    ("#1f4e79", "#ffffff"),  # navy / white
    ("#7b2d26", "#ffffff"),  # dark red / white
    ("#2d5f3f", "#ffffff"),  # forest / white
    ("#5d3a8e", "#ffffff"),  # purple / white
    ("#a85c00", "#ffffff"),  # amber / white
    ("#1e6e6e", "#ffffff"),  # teal / white
    ("#444444", "#ffffff"),  # dark gray / white
    ("#8a1c5b", "#ffffff"),  # magenta / white
]

# ============================================================
# HELPERS
# ============================================================
def make_source(kind: str, ref: str, retrieved_by: str = "dataset_generator",
                payload: Any = None) -> Source:
    return Source(
        kind=SourceKind(kind),
        ref=ref,
        ingested_at=datetime.utcnow(),
        raw_payload_hash=hash_json(payload or {"ref": ref}),
        retrieved_by=retrieved_by,
    )


def make_claim(founder_id: uuid.UUID, company_id: uuid.UUID,
               application_id: Optional[uuid.UUID],
               kind: str, text: str, source_kind: str, source_ref: str,
               payload: Any = None) -> Claim:
    """Construct one Claim per spec §3.1.

    confidence is left at default 0.5; flags is left empty — these get filled
    by the real Validator Agent when the pipeline runs.
    """
    return Claim(
        founder_id=founder_id,
        company_id=company_id,
        application_id=application_id,
        kind=ClaimKind(kind),
        text=text,
        source=make_source(source_kind, source_ref, payload=payload),
        confidence=0.5,
        flags=[],
    )


def make_founder_score(founder_id: uuid.UUID, score: float, cold_start: bool,
                       component_scores: dict, trigger: str = "application") -> FounderScore:
    band_widen = 30 if cold_start else 20
    snap = ScoreSnapshot(
        founder_id=founder_id,
        score=score,
        confidence_band=(max(0.0, score - band_widen), min(100.0, score + band_widen)),
        trend=Trend.INSUFFICIENT_DATA,
        computed_at=datetime.utcnow(),
        trigger=trigger,
        evidence_claim_ids=[],
        component_scores=component_scores,
        cold_start=cold_start,
    )
    return FounderScore(
        founder_id=founder_id,
        score_history=[snap],
        current_score=snap,
        trend=Trend.INSUFFICIENT_DATA,
        applications=[],
        first_seen_at=datetime.utcnow(),
        last_updated_at=datetime.utcnow(),
    )


# ============================================================
# IMAGE SOURCING — randomuser.me + Wikimedia Commons, with offline fallback
# ============================================================
USER_AGENT = "FounderSignalBot/1.0 (founder-signal-test@example.com)"
WIKI_CACHE: dict[str, Optional[str]] = {}


def fetch_photo(client: httpx.Client, gender_hint: Optional[str] = None) -> tuple[Optional[str], str]:
    """Try randomuser.me. Return (url_or_None, source_tag).

    source_tag is "randomuser.me" on success, "fallback" on failure.
    """
    try:
        url = "https://randomuser.me/api/?inc=picture,gender"
        if gender_hint == "female":
            url += "&gender=female"
        elif gender_hint == "male":
            url += "&gender=male"
        r = client.get(url, timeout=8.0)
        if r.status_code == 200:
            data = r.json()
            results = data.get("results") or []
            if results:
                pic = results[0].get("picture", {})
                return (pic.get("large") or pic.get("medium")), "randomuser.me"
    except Exception as e:
        print(f"    [warn] randomuser.me fetch failed: {e}")
    return None, "fallback"


def fetch_university_image(client: httpx.Client, university_name: str) -> tuple[Optional[str], str]:
    """Search Wikimedia Commons for a CC-licensed photo of the named university.

    Returns (image_url_or_None, source_tag) where source_tag is "wikimedia" or "fallback".
    """
    if university_name in WIKI_CACHE:
        url = WIKI_CACHE[university_name]
        return (url, "wikimedia") if url else (None, "fallback")

    headers = {"User-Agent": USER_AGENT}
    try:
        # Step 1: search for files matching the university name + "campus" or "building"
        for suffix in (" campus", " building", " logo", ""):
            search = f"{university_name}{suffix}".strip()
            r = client.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": search,
                    "gsrnamespace": 6,           # File: namespace
                    "gsrlimit": 5,
                    "prop": "imageinfo",
                    "iiprop": "url|extmetadata|mime",
                },
                headers=headers,
                timeout=10.0,
            )
            if r.status_code != 200:
                continue
            data = r.json()
            pages = (data.get("query") or {}).get("pages") or {}
            for _pid, page in pages.items():
                ii_list = page.get("imageinfo") or []
                if not ii_list:
                    continue
                ii = ii_list[0]
                img_url = ii.get("url")
                mime = ii.get("mime", "")
                # Prefer raster images that browsers render inline (svg also OK)
                if not img_url:
                    continue
                if mime and not any(mime.startswith(t) for t in ("image/jpeg", "image/png", "image/svg", "image/gif")):
                    continue
                ext = ii.get("extmetadata") or {}
                license_name = (ext.get("LicenseShortName") or {}).get("value", "")
                # Only accept CC-licensed or public-domain images
                ok_licenses = {"CC BY 2.0", "CC BY 2.5", "CC BY 3.0", "CC BY 4.0",
                               "CC BY-SA 2.0", "CC BY-SA 2.5", "CC BY-SA 3.0", "CC BY-SA 4.0",
                               "CC0", "Public domain", "Public Domain"}
                if license_name not in ok_licenses:
                    continue
                WIKI_CACHE[university_name] = img_url
                return img_url, "wikimedia"
    except Exception as e:
        print(f"    [warn] wikimedia fetch failed for {university_name!r}: {e}")

    WIKI_CACHE[university_name] = None
    return None, "fallback"


# ============================================================
# LOCAL FALLBACK SVG GENERATORS (no external call required)
# ============================================================
def initials_avatar_svg(name: str, founder_id: str) -> str:
    """Deterministic colored-circle avatar with founder initials.

    Saves an SVG file under dataset/assets/avatars/{founder_id}.svg and returns
    a relative path that the FastAPI app can serve as a static asset.
    """
    parts = name.split()
    initials = "".join(p[0].upper() for p in parts[:2]) if len(parts) >= 2 else name[:2].upper()
    # Deterministic color pick from founder_id
    h = int(hashlib.sha256(founder_id.encode()).hexdigest(), 16)
    bg, fg = AVATAR_COLORS[h % len(AVATAR_COLORS)]
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <rect width="256" height="256" fill="{bg}"/>
  <text x="128" y="128" font-family="Inter, 'Noto Sans', Arial, sans-serif" font-size="120"
        font-weight="700" fill="{fg}" text-anchor="middle" dominant-baseline="central">{initials}</text>
</svg>
"""
    ASSETS_DIR.joinpath("avatars").mkdir(parents=True, exist_ok=True)
    out = ASSETS_DIR / "avatars" / f"{founder_id}.svg"
    out.write_text(svg, encoding="utf-8")
    return f"/dataset/assets/avatars/{founder_id}.svg"


def generic_campus_svg(university_name: str, slug: str) -> str:
    """Deterministic generic 'campus building' SVG used when Wikimedia fetch fails.

    Saves an SVG file under dataset/assets/campuses/{slug}.svg and returns a
    relative path that the FastAPI app can serve.
    """
    h = int(hashlib.sha256(slug.encode()).hexdigest(), 16)
    building_color = ["#3b4252", "#434c5e", "#4c566a", "#5a6478"][h % 4]
    roof_color = ["#8a4a3b", "#8a5a3b", "#7a4a4a", "#6a4a6a"][h % 4]
    label = university_name[:32]
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="320" height="200" viewBox="0 0 320 200">
  <rect width="320" height="200" fill="#e9ecef"/>
  <polygon points="60,80 160,30 260,80" fill="{roof_color}"/>
  <rect x="70" y="80" width="180" height="100" fill="{building_color}"/>
  <rect x="90"  y="100" width="20" height="30" fill="#f9f9f9" opacity="0.85"/>
  <rect x="120" y="100" width="20" height="30" fill="#f9f9f9" opacity="0.85"/>
  <rect x="180" y="100" width="20" height="30" fill="#f9f9f9" opacity="0.85"/>
  <rect x="210" y="100" width="20" height="30" fill="#f9f9f9" opacity="0.85"/>
  <rect x="148" y="140" width="24" height="40" fill="#2e3440"/>
  <text x="160" y="190" font-family="Inter, 'Noto Sans', Arial, sans-serif" font-size="11"
        fill="#2e3440" text-anchor="middle">{label}</text>
</svg>
"""
    ASSETS_DIR.joinpath("campuses").mkdir(parents=True, exist_ok=True)
    out = ASSETS_DIR / "campuses" / f"{slug}.svg"
    out.write_text(svg, encoding="utf-8")
    return f"/dataset/assets/campuses/{slug}.svg"


def slugify(s: str) -> str:
    out = []
    for c in s.lower():
        if c.isalnum():
            out.append(c)
        elif c in (" ", "-", "_"):
            out.append("-")
    slug = "".join(out).strip("-")
    return slug or "campus"


# ============================================================
# FOUNDER GENERATORS BY CATEGORY
# ============================================================
def _common_header(rng: random.Random) -> dict:
    """Fields shared by every founder (caller fills in categories/claims)."""
    first = rng.choice(FIRST_NAMES)
    last = rng.choice(LAST_NAMES)
    name = f"{first} {last}"
    # Crude gender hint to align avatar with name (used only when fallback kicks in
    # and to bias randomuser.me results; not stored on the record).
    female_names = {"Aisha", "Priya", "Fatima", "Yuki", "Elena", "Mei", "Ananya",
                    "Ingrid", "Yelena", "Sofia", "Amara", "Leila", "Zara", "Nadia",
                    "Yara", "Linnea", "Hana", "Saanvi", "Jasmine", "Adaeze", "Rina",
                    "Kavya", "Camila"}
    gender_hint = "female" if first in female_names else "male"
    return {
        "name": name,
        "first": first,
        "last": last,
        "gender_hint": gender_hint,
        "sector": rng.choice(SECTORS),
        "geo": rng.choice(GEOGRAPHIES),
        "stage": rng.choice(STAGES),
        "company_name": f"{rng.choice(COMPANY_PREFIXES)}{rng.choice(COMPANY_SUFFIXES)}",
        "university": rng.choice(UNIVERSITIES),
        "degree": rng.choice(DEGREES),
        "grad_year": rng.randint(2012, 2024),
        "prior_co": rng.choice(PRIOR_COMPANIES),
        "problem": rng.choice(DECK_PROBLEMS),
        "solution": rng.choice(DECK_SOLUTIONS),
    }


def _founder_id() -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    return uuid.uuid4(), uuid.uuid4(), uuid.uuid4()


def generate_cold_start_founder(rng: random.Random) -> dict:
    h = _common_header(rng)
    founder_id, company_id, application_id = _founder_id()

    claims = [
        make_claim(founder_id, company_id, application_id, "founder_background",
                   f"Founder {h['name']} holds a {h['degree']} from {h['university']['name']}, graduating in {h['grad_year']}.",
                   "application_form", f"app:{application_id}"),
        make_claim(founder_id, company_id, application_id, "founder_background",
                   f"Founder {h['name']} previously worked at {h['prior_co']}.",
                   "deck", f"deck#slide=1"),
        make_claim(founder_id, company_id, application_id, "product",
                   f"{h['company_name']} addresses: {h['problem']}",
                   "deck", "deck#slide=2"),
        make_claim(founder_id, company_id, application_id, "product",
                   f"Solution: {h['solution']}",
                   "deck", "deck#slide=3"),
        make_claim(founder_id, company_id, application_id, "market_size",
                   f"The {h['sector']} market is projected to reach $2B by 2028.",
                   "deck", "deck#slide=4"),
        make_claim(founder_id, company_id, application_id, "cold_start_inferred",
                   f"Cold-start founder with no GitHub, arXiv, Product Hunt, or accelerator signals.",
                   "application_form", f"app:{application_id}"),
    ]

    score = rng.uniform(45, 65)
    return _wrap(founder_id, company_id, application_id, h,
                 categories=["cold_start"], github_profile=None,
                 claims=claims, score=score, cold_start=True,
                 components={"technical": score * 0.8, "market_fit": score * 0.7,
                             "network": 0.0, "momentum": 0.0})


def generate_rich_signal_founder(rng: random.Random) -> dict:
    h = _common_header(rng)
    founder_id, company_id, application_id = _founder_id()

    github_username = (h["name"].lower().replace(" ", "") + str(rng.randint(10, 99)))[:15]
    repo_name = f"{github_username}/{h['company_name'].lower()}-core"
    stars = rng.randint(80, 1400)
    commits_30d = rng.randint(8, 60)
    contributor_count = rng.randint(4, 28)
    primary_lang = rng.choice(GITHUB_LANGUAGES)
    accelerator = rng.choice(ACCELERATORS)

    claims = [
        make_claim(founder_id, company_id, application_id, "founder_background",
                   f"Founder {h['name']} holds a {h['degree']} from {h['university']['name']}, graduating in {h['grad_year']}.",
                   "application_form", f"app:{application_id}"),
        make_claim(founder_id, company_id, application_id, "technical_depth",
                   f"Repository {repo_name} has {stars} stars on GitHub.",
                   "github", repo_name),
        make_claim(founder_id, company_id, application_id, "technical_depth",
                   f"Repository {repo_name} received {commits_30d} commits in the last 30 days.",
                   "github", f"{repo_name}/commits"),
        make_claim(founder_id, company_id, application_id, "founder_network",
                   f"Repository {repo_name} has {contributor_count} contributors.",
                   "github", f"{repo_name}/contributors"),
    ]

    signal_type = rng.choice(["arxiv", "ph", "hn", "patent"])
    if signal_type == "arxiv":
        arxiv_id = f"{rng.randint(2301, 2601)}.{rng.randint(10000, 99999)}"
        claims.append(make_claim(founder_id, company_id, application_id, "technical_depth",
                                 f"Founder authored arXiv paper {arxiv_id} on {h['sector']} techniques.",
                                 "arxiv", arxiv_id))
    elif signal_type == "ph":
        ph_votes = rng.randint(80, 600)
        claims.append(make_claim(founder_id, company_id, application_id, "traction",
                                 f"Product Hunt launch '{h['company_name']}' received {ph_votes} upvotes.",
                                 "producthunt", f"post:{uuid.uuid4().hex[:8]}"))
    elif signal_type == "hn":
        hn_points = rng.randint(60, 350)
        claims.append(make_claim(founder_id, company_id, application_id, "traction",
                                 f"Hacker News post about {h['company_name']} received {hn_points} points.",
                                 "hackernews", f"item:{rng.randint(38000000, 42000000)}"))
    else:
        patent_id = f"US{rng.randint(10000000, 11999999)}B2"
        claims.append(make_claim(founder_id, company_id, application_id, "technical_depth",
                                 f"Founder is listed as inventor on patent {patent_id} covering {h['sector']} methods.",
                                 "external_db", f"uspto:{patent_id}"))

    claims.append(make_claim(founder_id, company_id, application_id, "founder_network",
                             f"Founder is a member of the {accelerator} accelerator cohort.",
                             "accelerator_cohort", f"accelerator:{accelerator.replace(' ', ':')}"))
    claims.append(make_claim(founder_id, company_id, application_id, "market_trend",
                             f"The {h['sector']} market is growing at 25% CAGR.",
                             "external_db", f"crunchbase:{h['sector']}-market"))
    claims.append(make_claim(founder_id, company_id, application_id, "product",
                             f"{h['company_name']} addresses: {h['problem']}",
                             "deck", "deck#slide=1"))

    score = rng.uniform(68, 90)
    github_profile = {
        "username": github_username,
        "repo_count": rng.randint(5, 30),
        "primary_language": primary_lang,
        "commit_activity": f"{commits_30d} commits in last 30 days",
        "stars": stars,
        "top_repo": repo_name,
        "contributors": contributor_count,
    }
    return _wrap(founder_id, company_id, application_id, h,
                 categories=["rich_signal"], github_profile=github_profile,
                 claims=claims, score=score, cold_start=False,
                 components={"technical": score * 0.92, "market_fit": score * 0.82,
                             "network": score * 0.78, "momentum": score * 0.72})


def generate_contradicted_founder(rng: random.Random) -> dict:
    h = _common_header(rng)
    founder_id, company_id, application_id = _founder_id()

    claims = [
        make_claim(founder_id, company_id, application_id, "founder_background",
                   f"Founder {h['name']} holds a {h['degree']} from {h['university']['name']}, graduating in {h['grad_year']}.",
                   "application_form", f"app:{application_id}"),
        make_claim(founder_id, company_id, application_id, "product",
                   f"{h['company_name']} addresses: {h['problem']}",
                   "deck", "deck#slide=1"),
    ]

    contradiction_type = rng.choice(["market_size", "traction", "financial", "team"])
    if contradiction_type == "market_size":
        claims.append(make_claim(founder_id, company_id, application_id, "market_size",
                                 f"The {h['sector']} market is $5B in 2026.",
                                 "deck", "deck#slide=3"))
        claims.append(make_claim(founder_id, company_id, application_id, "market_size",
                                 f"The {h['sector']} market is $500M in 2026.",
                                 "external_db", f"crunchbase:{h['sector']}-market"))
    elif contradiction_type == "traction":
        claims.append(make_claim(founder_id, company_id, application_id, "traction",
                                 f"{h['company_name']} has 50 paying enterprise customers.",
                                 "deck", "deck#slide=4"))
        claims.append(make_claim(founder_id, company_id, application_id, "traction",
                                 f"{h['company_name']} has 3 active pilot deployments and no public customer logos.",
                                 "external_db", f"crunchbase:{h['company_name']}"))
    elif contradiction_type == "financial":
        claims.append(make_claim(founder_id, company_id, application_id, "financial",
                                 f"{h['company_name']} raised a $5M seed round in 2025.",
                                 "deck", "deck#slide=5"))
        claims.append(make_claim(founder_id, company_id, application_id, "financial",
                                 f"No public record of funding for {h['company_name']} as of 2026-07.",
                                 "external_db", f"crunchbase:{h['company_name']}-funding"))
    else:  # team
        claims.append(make_claim(founder_id, company_id, application_id, "team",
                                 f"{h['company_name']} has 25 employees across two offices.",
                                 "deck", "deck#slide=6"))
        claims.append(make_claim(founder_id, company_id, application_id, "team",
                                 f"LinkedIn lists 4 employees at {h['company_name']}.",
                                 "external_db", f"linkedin:{h['company_name']}"))

    # Add a GitHub signal too — contradiction + rich-signal overlap
    github_username = (h["name"].lower().replace(" ", "") + str(rng.randint(10, 99)))[:15]
    repo_name = f"{github_username}/{h['company_name'].lower()}-core"
    stars = rng.randint(40, 500)
    claims.append(make_claim(founder_id, company_id, application_id, "technical_depth",
                             f"Repository {repo_name} has {stars} stars on GitHub.",
                             "github", repo_name))

    score = rng.uniform(40, 65)
    github_profile = {
        "username": github_username,
        "repo_count": rng.randint(3, 15),
        "primary_language": rng.choice(GITHUB_LANGUAGES),
        "commit_activity": f"{rng.randint(5, 20)} commits in last 30 days",
        "stars": stars,
        "top_repo": repo_name,
        "contributors": rng.randint(2, 8),
    }
    return _wrap(founder_id, company_id, application_id, h,
                 categories=["contradicted"], github_profile=github_profile,
                 claims=claims, score=score, cold_start=False,
                 components={"technical": score * 0.8, "market_fit": score * 0.5,
                             "network": score * 0.6, "momentum": score * 0.5})


def generate_missing_data_founder(rng: random.Random) -> dict:
    h = _common_header(rng)
    founder_id, company_id, application_id = _founder_id()

    claims = [
        make_claim(founder_id, company_id, application_id, "founder_background",
                   f"Founder {h['name']} holds a {h['degree']} from {h['university']['name']}, graduating in {h['grad_year']}.",
                   "application_form", f"app:{application_id}"),
        make_claim(founder_id, company_id, application_id, "product",
                   f"{h['company_name']} addresses: {h['problem']}",
                   "deck", "deck#slide=1"),
        make_claim(founder_id, company_id, application_id, "product",
                   f"Solution: {h['solution']}",
                   "deck", "deck#slide=2"),
        make_claim(founder_id, company_id, application_id, "market_trend",
                   f"The {h['sector']} sector is seeing increased VC interest.",
                   "external_db", f"crunchbase:{h['sector']}-trend"),
        # Deliberately NO financial / cap_table / team claims — Validator will mark these
        # as not_disclosed. This is the "explicit missing data" pattern.
    ]

    # Sometimes has GitHub, sometimes not — overlap with cold-start
    if rng.random() > 0.4:
        github_username = (h["name"].lower().replace(" ", "") + str(rng.randint(10, 99)))[:15]
        repo_name = f"{github_username}/{h['company_name'].lower()}-core"
        stars = rng.randint(20, 200)
        claims.append(make_claim(founder_id, company_id, application_id, "technical_depth",
                                 f"Repository {repo_name} has {stars} stars on GitHub.",
                                 "github", repo_name))
        github_profile = {
            "username": github_username,
            "repo_count": rng.randint(2, 10),
            "primary_language": rng.choice(GITHUB_LANGUAGES),
            "commit_activity": f"{rng.randint(3, 15)} commits in last 30 days",
            "stars": stars,
            "top_repo": repo_name,
            "contributors": rng.randint(2, 6),
        }
    else:
        github_profile = None

    score = rng.uniform(50, 70)
    return _wrap(founder_id, company_id, application_id, h,
                 categories=["missing_data"], github_profile=github_profile,
                 claims=claims, score=score, cold_start=False,
                 components={"technical": score * 0.75, "market_fit": score * 0.6,
                             "network": score * 0.4, "momentum": score * 0.5})


def generate_mixed_founder(rng: random.Random) -> dict:
    h = _common_header(rng)
    founder_id, company_id, application_id = _founder_id()

    claims = [
        make_claim(founder_id, company_id, application_id, "founder_background",
                   f"Founder {h['name']} holds a {h['degree']} from {h['university']['name']}, graduating in {h['grad_year']}.",
                   "application_form", f"app:{application_id}"),
        make_claim(founder_id, company_id, application_id, "product",
                   f"{h['company_name']} addresses: {h['problem']}",
                   "deck", "deck#slide=1"),
        make_claim(founder_id, company_id, application_id, "product",
                   f"Solution: {h['solution']}",
                   "deck", "deck#slide=2"),
    ]

    has_github = rng.random() > 0.3
    if has_github:
        github_username = (h["name"].lower().replace(" ", "") + str(rng.randint(10, 99)))[:15]
        repo_name = f"{github_username}/{h['company_name'].lower()}-core"
        stars = rng.randint(10, 350)
        claims.append(make_claim(founder_id, company_id, application_id, "technical_depth",
                                 f"Repository {repo_name} has {stars} stars on GitHub.",
                                 "github", repo_name))
        github_profile = {
            "username": github_username,
            "repo_count": rng.randint(2, 12),
            "primary_language": rng.choice(GITHUB_LANGUAGES),
            "commit_activity": f"{rng.randint(2, 25)} commits in last 30 days",
            "stars": stars,
            "top_repo": repo_name,
            "contributors": rng.randint(2, 10),
        }
    else:
        github_profile = None

    if rng.random() > 0.55:
        claims.append(make_claim(founder_id, company_id, application_id, "market_trend",
                                 f"The {h['sector']} market is growing at {rng.randint(15, 35)}% CAGR.",
                                 "external_db", f"crunchbase:{h['sector']}-market"))
    if rng.random() > 0.7:
        claims.append(make_claim(founder_id, company_id, application_id, "traction",
                                 f"{h['company_name']} has {rng.randint(100, 5000)} active users.",
                                 "deck", "deck#slide=3"))
    if rng.random() > 0.8:
        accelerator = rng.choice(ACCELERATORS)
        claims.append(make_claim(founder_id, company_id, application_id, "founder_network",
                                 f"Founder participated in {accelerator} cohort.",
                                 "accelerator_cohort", f"accelerator:{accelerator.replace(' ', ':')}"))

    score = rng.uniform(50, 80)
    return _wrap(founder_id, company_id, application_id, h,
                 categories=["mixed"], github_profile=github_profile,
                 claims=claims, score=score, cold_start=False,
                 components={"technical": score * 0.8, "market_fit": score * 0.7,
                             "network": score * 0.5, "momentum": score * 0.6})


def _wrap(founder_id: uuid.UUID, company_id: uuid.UUID, application_id: uuid.UUID,
          h: dict, categories: list[str], github_profile: Optional[dict],
          claims: list[Claim], score: float, cold_start: bool,
          components: dict[str, float]) -> dict:
    return {
        "founder_id": str(founder_id),
        "company_id": str(company_id),
        "application_id": str(application_id),
        "name": h["name"],
        "company_name": h["company_name"],
        "sector": h["sector"],
        "stage": h["stage"],
        "geography": h["geo"],
        "categories": categories,
        "education": {
            "university": h["university"]["name"],
            "university_country": h["university"]["country"],
            "degree": h["degree"],
            "year": h["grad_year"],
        },
        "prior_experience": f"Previously worked at {h['prior_co']}, focusing on {h['sector'].lower()} problems.",
        "github_profile": github_profile,
        "deck_summary": f"{h['company_name']} is building {h['solution']} The problem: {h['problem']}",
        "claims": [c.model_dump(mode="json") for c in claims],
        "founder_score_seed": make_founder_score(
            founder_id, score, cold_start=cold_start, component_scores=components,
        ).model_dump(mode="json"),
        # image fields filled in by main() below
        "photo_url": None,
        "university_image_url": None,
        "image_source": {"photo": "pending", "university": "pending"},
    }


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-fetch", action="store_true",
                        help="Skip all network calls; use local SVG fallback for every image.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FOUNDERS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    # 10 + 12 + 10 + 8 + 10 = 50
    plan = (
        [generate_cold_start_founder]     * 10 +
        [generate_rich_signal_founder]    * 12 +
        [generate_contradicted_founder]   * 10 +
        [generate_missing_data_founder]   * 8  +
        [generate_mixed_founder]          * 10
    )
    rng.shuffle(plan)  # mix the categories so file order is realistic

    founders: list[dict] = []
    index_entries: list[dict] = []

    print(f"Generating {len(plan)} founders → {OUTPUT_DIR}")
    fetch_enabled = not args.no_fetch

    # Reuse HTTP client for connection pooling
    transport = httpx.HTTPTransport(retries=2) if fetch_enabled else None
    client = httpx.Client(transport=transport, timeout=15.0) if fetch_enabled else None

    try:
        for i, gen_fn in enumerate(plan):
            f = gen_fn(rng)

            # --- Photo ---
            photo_url, photo_src = (None, "fallback")
            if fetch_enabled:
                photo_url, photo_src = fetch_photo(client, f.get("gender_hint"))
                # gender_hint is just for fetch bias — not stored on the record
            if photo_url is None:
                photo_url = initials_avatar_svg(f["name"], f["founder_id"])
                photo_src = "fallback"
            f["photo_url"] = photo_url
            f["image_source"]["photo"] = photo_src

            # --- University image ---
            uni_url, uni_src = (None, "fallback")
            if fetch_enabled:
                uni_url, uni_src = fetch_university_image(client, f["education"]["university"])
            if uni_url is None:
                slug = slugify(f["education"]["university"])
                uni_url = generic_campus_svg(f["education"]["university"], slug)
                uni_src = "fallback"
            f["university_image_url"] = uni_url
            f["image_source"]["university"] = uni_src

            f.pop("gender_hint", None)  # not part of the founder record

            # --- Write per-founder JSON ---
            out_path = FOUNDERS_DIR / f"{f['founder_id']}.json"
            with open(out_path, "w", encoding="utf-8") as fp:
                json.dump(f, fp, indent=2, default=str)

            founders.append(f)
            index_entries.append({
                "founder_id": f["founder_id"],
                "name": f["name"],
                "company_name": f["company_name"],
                "categories": f["categories"],
                "sector": f["sector"],
                "geography": f["geography"],
                "stage": f["stage"],
                "image_source": f["image_source"],
            })

            print(f"  [{i+1:2d}/{len(plan)}] {f['name']:25s} "
                  f"[{','.join(f['categories']):14s}] "
                  f"photo={photo_src:12s} uni={uni_src}")
            # gentle rate limit for randomuser.me (~50 req — well within their limit)
            if fetch_enabled and (i + 1) % 10 == 0:
                time.sleep(0.5)
    finally:
        if client:
            client.close()

    # --- index.json ---
    with open(OUTPUT_DIR / "index.json", "w", encoding="utf-8") as fp:
        json.dump({
            "total": len(founders),
            "generated_at": datetime.utcnow().isoformat(),
            "sectors": SECTORS,
            "geographies": GEOGRAPHIES,
            "founders": index_entries,
        }, fp, indent=2, default=str)

    # --- README.md ---
    write_readme(founders, index_entries, fetch_enabled)

    # --- Summary ---
    cat_counts: dict[str, int] = {}
    sector_counts: dict[str, int] = {}
    geo_counts: dict[str, int] = {}
    photo_real = sum(1 for f in founders if f["image_source"]["photo"] == "randomuser.me")
    photo_fallback = len(founders) - photo_real
    uni_real = sum(1 for f in founders if f["image_source"]["university"] == "wikimedia")
    uni_fallback = len(founders) - uni_real
    for f in founders:
        for c in f["categories"]:
            cat_counts[c] = cat_counts.get(c, 0) + 1
        sector_counts[f["sector"]] = sector_counts.get(f["sector"], 0) + 1
        geo_counts[f["geography"]] = geo_counts.get(f["geography"], 0) + 1

    print(f"\n=== Generation complete ===")
    print(f"Total founders: {len(founders)}")
    print(f"Categories: {cat_counts}")
    print(f"Sectors: {sector_counts}")
    print(f"Geographies: {geo_counts}")
    print(f"Photos: {photo_real} real, {photo_fallback} fallback")
    print(f"University images: {uni_real} real, {uni_fallback} fallback")
    print(f"Output: {OUTPUT_DIR}")


def write_readme(founders: list[dict], index_entries: list[dict], fetch_enabled: bool):
    cat_counts: dict[str, int] = {}
    sector_counts: dict[str, int] = {}
    geo_counts: dict[str, int] = {}
    photo_real = sum(1 for f in founders if f["image_source"]["photo"] == "randomuser.me")
    uni_real = sum(1 for f in founders if f["image_source"]["university"] == "wikimedia")
    for f in founders:
        for c in f["categories"]:
            cat_counts[c] = cat_counts.get(c, 0) + 1
        sector_counts[f["sector"]] = sector_counts.get(f["sector"], 0) + 1
        geo_counts[f["geography"]] = geo_counts.get(f["geography"], 0) + 1

    # Pick one demo fixture per category (the highest-scoring in each)
    def best_in(cat: str) -> Optional[dict]:
        matches = [f for f in founders if cat in f["categories"]]
        if not matches:
            return None
        return max(matches, key=lambda f: f["founder_score_seed"]["current_score"]["score"])

    cold = best_in("cold_start")
    rich = best_in("rich_signal")
    contra = best_in("contradicted")
    miss = best_in("missing_data")

    def row(f: Optional[dict]) -> str:
        if not f:
            return "| N/A | N/A | N/A | N/A |"
        return (f"| `{f['founder_id']}` | {f['name']} | {f['company_name']} "
                f"| {f['sector']} / {f['geography']} |")

    def fixture_row(label: str, f: Optional[dict]) -> str:
        if not f:
            return f"| {label} | N/A | N/A | N/A | N/A |"
        return (f"| {label} | `{f['founder_id']}` | {f['name']} | "
                f"{f['company_name']} | {f['sector']} / {f['geography']} |")

    readme = f"""# Synthetic Founder Dataset

Generated: {datetime.utcnow().isoformat()}

This dataset is the **canonical reference copy** of the 50 fictional founder records
used by the Founder-Signal demo. The source of truth at runtime is the Postgres
database (see `scripts/seed_dataset.py`); this folder exists for version control
and inspection.

## Distribution actually generated

| Category | Count |
|---|---|
| cold_start    | {cat_counts.get('cold_start', 0)} |
| rich_signal   | {cat_counts.get('rich_signal', 0)} |
| contradicted  | {cat_counts.get('contradicted', 0)} |
| missing_data  | {cat_counts.get('missing_data', 0)} |
| mixed         | {cat_counts.get('mixed', 0)} |
| **Total**     | **{len(founders)}** |

> Categories can overlap (e.g. a founder can be both `rich_signal` and `contradicted`).
> Above counts are per-tag, so they may sum to more than 50.

## Sectors ({len(sector_counts)} ≥ 5 required)

{chr(10).join(f"- {s}: {c}" for s, c in sorted(sector_counts.items(), key=lambda x: -x[1]))}

## Geographies ({len(geo_counts)} ≥ 4 required, ISO-3166 alpha-2)

{chr(10).join(f"- {g}: {c}" for g, c in sorted(geo_counts.items(), key=lambda x: -x[1]))}

## Image sourcing

| Asset | Real fetched | Local SVG fallback |
|---|---|---|
| Photos (randomuser.me)        | {photo_real} | {len(founders) - photo_real} |
| University images (Wikimedia) | {uni_real}  | {len(founders) - uni_real} |

- **Photos**: fetched from `https://randomuser.me/api/` (free, built for fake profile data).
  When the API is unreachable or `--no-fetch` is passed, the generator writes a
  deterministic initials-avatar SVG under `dataset/assets/avatars/<founder_id>.svg`
  and points `photo_url` at it.
- **University images**: searched via the Wikimedia Commons API (CC-licensed only —
  CC BY / CC BY-SA / CC0 / public domain). When no suitable image is found, the
  generator writes a generic campus-building SVG under
  `dataset/assets/campuses/<slug>.svg`.
- The `image_source` block on each founder record (and the same field in
  `index.json`) records which path was used, so the team can see at a glance
  which founders got real fetched images vs. local fallback placeholders before
  the demo.

## Recommended demo fixtures (one per category)

These four founder IDs should be referenced in `DEMO_SCRIPT.md` as the canonical
live-demo fixtures — each is the strongest-scoring example in its category so the
memo view has the richest content to render:

| Use case | founder_id | Name | Company | Sector / Geo |
|---|---|---|---|---|
{fixture_row("Cold-start example", cold)}
{fixture_row("Rich-signal example", rich)}
{fixture_row("Contradiction example", contra)}
{fixture_row("Missing-data example", miss)}

Canonical IDs:

```text
cold_start:    {cold['founder_id'] if cold else 'N/A'}  ({cold['name'] if cold else 'N/A'} — {cold['company_name'] if cold else 'N/A'})
rich_signal:   {rich['founder_id'] if rich else 'N/A'}  ({rich['name'] if rich else 'N/A'} — {rich['company_name'] if rich else 'N/A'})
contradicted:  {contra['founder_id'] if contra else 'N/A'}  ({contra['name'] if contra else 'N/A'} — {contra['company_name'] if contra else 'N/A'})
missing_data:  {miss['founder_id'] if miss else 'N/A'}  ({miss['name'] if miss else 'N/A'} — {miss['company_name'] if miss else 'N/A'})
```

## Schema

Each founder JSON file validates against the BUILD_SPEC.md schemas:

- `claims[*]` matches **Claim** (§3.1). `confidence` is left at the default `0.5`
  and `flags` is left `[]` — the real Validator Agent fills these in when the
  pipeline runs.
- `founder_score_seed` matches **FounderScore** (§3.2) with a single starting
  `score_history` entry.
- `photo_url` and `university_image_url` are non-null on every record (real
  fetched URL or local SVG path).

## Reproducing

```bash
python scripts/dataset/generate_founders.py            # uses randomuser.me + Wikimedia
python scripts/dataset/generate_founders.py --no-fetch # offline-safe: every image is local SVG
python scripts/dataset/generate_founders.py --seed 42  # deterministic
```

Then validate + seed the database:

```bash
python scripts/dataset/validate_dataset.py
python scripts/seed_dataset.py
python scripts/verify_dataset.py
```
"""
    (OUTPUT_DIR / "README.md").write_text(readme, encoding="utf-8")


if __name__ == "__main__":
    main()
