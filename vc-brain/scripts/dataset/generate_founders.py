#!/usr/bin/env python3
"""Generate 50 synthetic founder profiles for demo/testing.

Per the prompt: generate fictional founders matching BUILD_SPEC.md §3 schemas.
- ~10 cold-start, ~12 rich-signal, ~10 contradicted, ~8 missing-data, rest mixed
- 5+ sectors, 4+ geographies
- Photos from randomuser.me, university images from Wikimedia Commons
- One JSON per founder + index.json + README.md

Usage:
    python scripts/dataset/generate_founders.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
import random
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import httpx

# Ensure backend is on path for schema imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend"))

from app.schemas.claim import Claim, ClaimKind, Source, SourceKind
from app.schemas.founder_score import FounderScore, ScoreSnapshot, Trend
from app.utils.hashing import hash_json

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "dataset"
FOUNDERS_DIR = OUTPUT_DIR / "founders"

# ============================================================
# DATA POOLS
# ============================================================

SECTORS = ["AI infra", "DevTools", "Fintech", "Healthtech", "Climate", "Consumer"]
STAGES = ["pre-seed", "seed", "series-a"]
GEOGRAPHIES = ["US", "DE", "GB", "SG", "IN", "FR", "PK"]

# Diverse names across gender/ethnicity/geography
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
    "Petrov", "Singh", "Lindqvist", "Costa", "Müller", "Hassan", "Reyes",
    "Schneider", "Watanabe", "Kowalski", "Bauer", "Ibrahim",
]

UNIVERSITIES = [
    {"name": "MIT", "country": "US"},
    {"name": "Stanford University", "country": "US"},
    {"name": "ETH Zurich", "country": "CH"},
    {"name": "University of Cambridge", "country": "GB"},
    {"name": "TU Munich", "country": "DE"},
    {"name": "IIT Bombay", "country": "IN"},
    {"name": "NUS Singapore", "country": "SG"},
    {"name": "Tsinghua University", "country": "CN"},
    {"name": "University of Toronto", "country": "CA"},
    {"name": "Imperial College London", "country": "GB"},
    {"name": "EPFL", "country": "CH"},
    {"name": "Carnegie Mellon University", "country": "US"},
    {"name": "University of Oxford", "country": "GB"},
    {"name": "TU Berlin", "country": "DE"},
    {"name": "LUMS", "country": "PK"},
]

DEGREES = ["BSc Computer Science", "MSc Electrical Engineering", "BSc Mathematics",
           "PhD Artificial Intelligence", "MSc Data Science", "BEng Software Engineering",
           "MBA", "MSc Robotics", "BSc Physics", "PhD Machine Learning"]

COMPANY_PREFIXES = ["Nexus", "Vertex", "Quantum", "Helix", "Apex", "Lumen", "Cipher",
                    "Forge", "Prism", "Atlas", "Orbit", "Flux", "Echo", "Drift",
                    "Pulse", "Strata", "Nova", "Zenith", "Volt", "Mesh"]
COMPANY_SUFFIXES = ["AI", "Labs", "Tech", "Systems", "Health", "Finance", "Climate",
                    "Tools", "Cloud", "Data", "Robotics", "Bio", "Energy", "Stack"]

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
]

GITHUB_LANGUAGES = ["Python", "TypeScript", "Rust", "Go", "JavaScript", "C++", "Julia"]

ACCELERATORS = ["YC W24", "YC S23", "Techstars", "Seedcamp", "Antler", "500 Global", "EWOR"]

PRIOR_COMPANIES = ["Google", "DeepMind", "Meta", "Stripe", "Anthropic", "OpenAI",
                   "Microsoft", "Amazon", "Tesla", "Nvidia", "ByteDance", "Shopify",
                   "a Series B startup", "a stealth AI startup", "a fintech unicorn"]


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


def make_claim(founder_id: uuid.UUID, company_id: uuid.UUID, application_id: Optional[uuid.UUID],
               kind: str, text: str, source_kind: str, source_ref: str,
               payload: Any = None) -> Claim:
    return Claim(
        founder_id=founder_id,
        company_id=company_id,
        application_id=application_id,
        kind=ClaimKind(kind),
        text=text,
        source=make_source(source_kind, source_ref, payload=payload),
        confidence=0.5,  # left at default — Validator fills this in
        flags=[],  # left empty — Validator fills this in
    )


def make_founder_score(founder_id: uuid.UUID, score: float, cold_start: bool,
                       component_scores: dict, trigger: str = "application") -> FounderScore:
    snap = ScoreSnapshot(
        founder_id=founder_id,
        score=score,
        confidence_band=(max(0, score - 20), min(100, score + 20)) if not cold_start else (max(0, score - 30), min(100, score + 30)),
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
# FOUNDER GENERATORS BY CATEGORY
# ============================================================

def generate_cold_start_founder(idx: int) -> dict:
    """~10 cold-start founders: zero external signals, only deck + application_form."""
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    sector = random.choice(SECTORS)
    geo = random.choice(GEOGRAPHIES)
    company_name = f"{random.choice(COMPANY_PREFIXES)}{random.choice(COMPANY_SUFFIXES)}"
    founder_id = uuid.uuid4()
    company_id = uuid.uuid4()
    application_id = uuid.uuid4()

    problem = random.choice(DECK_PROBLEMS)
    solution = random.choice(DECK_SOLUTIONS)
    university = random.choice(UNIVERSITIES)
    degree = random.choice(DEGREES)
    grad_year = random.randint(2015, 2024)
    prior_co = random.choice(PRIOR_COMPANIES)

    claims = [
        make_claim(founder_id, company_id, application_id, "founder_background",
                   f"Founder {name} holds a {degree} from {university['name']}, graduating in {grad_year}.",
                   "application_form", f"app:{application_id}"),
        make_claim(founder_id, company_id, application_id, "founder_background",
                   f"Founder {name} previously worked at {prior_co}.",
                   "deck", f"deck#slide=1"),
        make_claim(founder_id, company_id, application_id, "product",
                   f"{company_name} addresses: {problem}",
                   "deck", f"deck#slide=2"),
        make_claim(founder_id, company_id, application_id, "product",
                   f"Solution: {solution}",
                   "deck", f"deck#slide=3"),
        make_claim(founder_id, company_id, application_id, "market_size",
                   f"The {sector} market is projected to reach $2B by 2028.",
                   "deck", f"deck#slide=4"),
        make_claim(founder_id, company_id, application_id, "cold_start_inferred",
                   f"Cold-start founder with no GitHub, arxiv, Product Hunt, or accelerator signals.",
                   "application_form", f"app:{application_id}"),
    ]

    score = random.uniform(45, 65)  # cold-start founders score moderate with wide band
    return {
        "founder_id": str(founder_id),
        "company_id": str(company_id),
        "application_id": str(application_id),
        "name": name,
        "company_name": company_name,
        "sector": sector,
        "stage": random.choice(STAGES),
        "geography": geo,
        "categories": ["cold_start"],
        "education": {"university": university["name"], "degree": degree, "year": grad_year},
        "prior_experience": f"Previously worked at {prior_co}.",
        "github_profile": None,
        "deck_summary": f"{company_name} is building: {solution} The problem: {problem}",
        "claims": [c.model_dump(mode="json") for c in claims],
        "founder_score_seed": make_founder_score(
            founder_id, score, cold_start=True,
            component_scores={"technical": score * 0.8, "market_fit": score * 0.7,
                              "network": 0, "momentum": 0}
        ).model_dump(mode="json"),
    }


def generate_rich_signal_founder(idx: int) -> dict:
    """~12 rich-signal founders: GitHub + arxiv/PH/HN + accelerator."""
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    sector = random.choice(SECTORS)
    geo = random.choice(GEOGRAPHIES)
    company_name = f"{random.choice(COMPANY_PREFIXES)}{random.choice(COMPANY_SUFFIXES)}"
    founder_id = uuid.uuid4()
    company_id = uuid.uuid4()
    application_id = uuid.uuid4()

    github_username = name.lower().replace(" ", "")[:15]
    repo_name = f"{github_username}/{company_name.lower()}-core"
    stars = random.randint(50, 1200)
    commits_30d = random.randint(5, 50)
    contributor_count = random.randint(3, 25)
    primary_lang = random.choice(GITHUB_LANGUAGES)
    accelerator = random.choice(ACCELERATORS)
    problem = random.choice(DECK_PROBLEMS)
    solution = random.choice(DECK_SOLUTIONS)
    university = random.choice(UNIVERSITIES)
    degree = random.choice(DEGREES)

    claims = [
        make_claim(founder_id, company_id, application_id, "founder_background",
                   f"Founder {name} holds a {degree} from {university['name']}.",
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

    # Add arxiv or PH or HN signal
    signal_type = random.choice(["arxiv", "ph", "hn"])
    if signal_type == "arxiv":
        arxiv_id = f"{random.randint(2301, 2601)}.{random.randint(10000, 99999)}"
        claims.append(make_claim(founder_id, company_id, application_id, "technical_depth",
                                 f"Founder authored arxiv paper {arxiv_id} on {sector} techniques.",
                                 "arxiv", arxiv_id))
    elif signal_type == "ph":
        ph_votes = random.randint(50, 500)
        claims.append(make_claim(founder_id, company_id, application_id, "traction",
                                 f"Product Hunt launch '{company_name}' received {ph_votes} upvotes.",
                                 "producthunt", f"post:{uuid.uuid4().hex[:8]}"))
    else:
        hn_points = random.randint(50, 300)
        claims.append(make_claim(founder_id, company_id, application_id, "traction",
                                 f"Hacker News post about {company_name} received {hn_points} points.",
                                 "hackernews", f"item:{random.randint(38000000, 42000000)}"))

    # Accelerator
    claims.append(make_claim(founder_id, company_id, application_id, "founder_network",
                             f"Founder is a member of {accelerator} accelerator cohort.",
                             "accelerator_cohort", f"accelerator:{accelerator.replace(' ', ':')}"))

    # Market claims
    claims.append(make_claim(founder_id, company_id, application_id, "market_trend",
                             f"The {sector} market is growing at 25% CAGR.",
                             "external_db", f"crunchbase:{sector}-market"))

    claims.append(make_claim(founder_id, company_id, application_id, "product",
                             f"{company_name} addresses: {problem}",
                             "deck", "deck#slide=1"))

    score = random.uniform(65, 88)
    return {
        "founder_id": str(founder_id),
        "company_id": str(company_id),
        "application_id": str(application_id),
        "name": name,
        "company_name": company_name,
        "sector": sector,
        "stage": random.choice(STAGES),
        "geography": geo,
        "categories": ["rich_signal"],
        "education": {"university": university["name"], "degree": degree, "year": random.randint(2012, 2022)},
        "prior_experience": f"Previously worked at {random.choice(PRIOR_COMPANIES)}.",
        "github_profile": {
            "username": github_username,
            "repo_count": random.randint(5, 30),
            "primary_language": primary_lang,
            "commit_activity": f"{commits_30d} commits in last 30 days",
            "stars": stars,
        },
        "deck_summary": f"{company_name} is building: {solution} The problem: {problem}",
        "claims": [c.model_dump(mode="json") for c in claims],
        "founder_score_seed": make_founder_score(
            founder_id, score, cold_start=False,
            component_scores={"technical": score * 0.9, "market_fit": score * 0.8,
                              "network": score * 0.75, "momentum": score * 0.7}
        ).model_dump(mode="json"),
    }


def generate_contradicted_founder(idx: int) -> dict:
    """~10 founders with seeded contradictions in their claims."""
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    sector = random.choice(SECTORS)
    geo = random.choice(GEOGRAPHIES)
    company_name = f"{random.choice(COMPANY_PREFIXES)}{random.choice(COMPANY_SUFFIXES)}"
    founder_id = uuid.uuid4()
    company_id = uuid.uuid4()
    application_id = uuid.uuid4()

    problem = random.choice(DECK_PROBLEMS)
    solution = random.choice(DECK_SOLUTIONS)
    university = random.choice(UNIVERSITIES)

    # Seeded contradictions — two claims of the same kind with 2x+ different values
    contradiction_type = random.choice(["market_size", "traction", "financial"])
    claims = [
        make_claim(founder_id, company_id, application_id, "founder_background",
                   f"Founder {name} studied at {university['name']}.",
                   "application_form", f"app:{application_id}"),
        make_claim(founder_id, company_id, application_id, "product",
                   f"{company_name} addresses: {problem}",
                   "deck", "deck#slide=1"),
    ]

    if contradiction_type == "market_size":
        claims.append(make_claim(founder_id, company_id, application_id, "market_size",
                                 f"The {sector} market is $5B in 2026.",
                                 "deck", "deck#slide=3"))
        claims.append(make_claim(founder_id, company_id, application_id, "market_size",
                                 f"The {sector} market is $500M in 2026.",
                                 "external_db", f"crunchbase:{sector}-market"))
    elif contradiction_type == "traction":
        claims.append(make_claim(founder_id, company_id, application_id, "traction",
                                 f"{company_name} has 50 paying enterprise customers.",
                                 "deck", "deck#slide=4"))
        claims.append(make_claim(founder_id, company_id, application_id, "traction",
                                 f"{company_name} has 3 active pilot deployments.",
                                 "external_db", f"crunchbase:{company_name}"))
    else:  # financial
        claims.append(make_claim(founder_id, company_id, application_id, "financial",
                                 f"{company_name} raised a $5M seed round in 2025.",
                                 "deck", "deck#slide=5"))
        claims.append(make_claim(founder_id, company_id, application_id, "financial",
                                 f"No public record of funding for {company_name}.",
                                 "external_db", f"crunchbase:{company_name}-funding"))

    # Add a GitHub signal too (rich-signal + contradiction overlap)
    github_username = name.lower().replace(" ", "")[:15]
    repo_name = f"{github_username}/{company_name.lower()}-core"
    stars = random.randint(50, 500)
    claims.append(make_claim(founder_id, company_id, application_id, "technical_depth",
                             f"Repository {repo_name} has {stars} stars on GitHub.",
                             "github", repo_name))

    score = random.uniform(40, 65)  # lower score due to contradictions
    return {
        "founder_id": str(founder_id),
        "company_id": str(company_id),
        "application_id": str(application_id),
        "name": name,
        "company_name": company_name,
        "sector": sector,
        "stage": random.choice(STAGES),
        "geography": geo,
        "categories": ["contradicted"],
        "education": {"university": university["name"], "degree": random.choice(DEGREES), "year": random.randint(2014, 2023)},
        "prior_experience": f"Previously worked at {random.choice(PRIOR_COMPANIES)}.",
        "github_profile": {
            "username": github_username,
            "repo_count": random.randint(3, 15),
            "primary_language": random.choice(GITHUB_LANGUAGES),
            "commit_activity": f"{random.randint(5, 20)} commits in last 30 days",
            "stars": stars,
        },
        "deck_summary": f"{company_name} is building: {solution} The problem: {problem}",
        "claims": [c.model_dump(mode="json") for c in claims],
        "founder_score_seed": make_founder_score(
            founder_id, score, cold_start=False,
            component_scores={"technical": score * 0.8, "market_fit": score * 0.5,
                              "network": score * 0.6, "momentum": score * 0.5}
        ).model_dump(mode="json"),
    }


def generate_missing_data_founder(idx: int) -> dict:
    """~8 founders with explicitly missing data (no cap table, no financials)."""
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    sector = random.choice(SECTORS)
    geo = random.choice(GEOGRAPHIES)
    company_name = f"{random.choice(COMPANY_PREFIXES)}{random.choice(COMPANY_SUFFIXES)}"
    founder_id = uuid.uuid4()
    company_id = uuid.uuid4()
    application_id = uuid.uuid4()

    problem = random.choice(DECK_PROBLEMS)
    solution = random.choice(DECK_SOLUTIONS)
    university = random.choice(UNIVERSITIES)

    claims = [
        make_claim(founder_id, company_id, application_id, "founder_background",
                   f"Founder {name} studied at {university['name']}.",
                   "application_form", f"app:{application_id}"),
        make_claim(founder_id, company_id, application_id, "product",
                   f"{company_name} addresses: {problem}",
                   "deck", "deck#slide=1"),
        make_claim(founder_id, company_id, application_id, "product",
                   f"Solution: {solution}",
                   "deck", "deck#slide=2"),
        make_claim(founder_id, company_id, application_id, "market_trend",
                   f"The {sector} sector is seeing increased VC interest.",
                   "external_db", f"crunchbase:{sector}-trend"),
        # Deliberately NO financial claims, NO team claims, NO cap_table claims
        # The Validator will mark these as not_disclosed
    ]

    # Add some GitHub signal
    github_username = name.lower().replace(" ", "")[:15]
    repo_name = f"{github_username}/{company_name.lower()}-core"
    stars = random.randint(20, 200)
    claims.append(make_claim(founder_id, company_id, application_id, "technical_depth",
                             f"Repository {repo_name} has {stars} stars on GitHub.",
                             "github", repo_name))

    score = random.uniform(50, 70)
    return {
        "founder_id": str(founder_id),
        "company_id": str(company_id),
        "application_id": str(application_id),
        "name": name,
        "company_name": company_name,
        "sector": sector,
        "stage": random.choice(STAGES),
        "geography": geo,
        "categories": ["missing_data"],
        "education": {"university": university["name"], "degree": random.choice(DEGREES), "year": random.randint(2015, 2023)},
        "prior_experience": f"Previously worked at {random.choice(PRIOR_COMPANIES)}.",
        "github_profile": {
            "username": github_username,
            "repo_count": random.randint(2, 10),
            "primary_language": random.choice(GITHUB_LANGUAGES),
            "commit_activity": f"{random.randint(3, 15)} commits in last 30 days",
            "stars": stars,
        },
        "deck_summary": f"{company_name} is building: {solution} The problem: {problem}",
        "claims": [c.model_dump(mode="json") for c in claims],
        "founder_score_seed": make_founder_score(
            founder_id, score, cold_start=False,
            component_scores={"technical": score * 0.75, "market_fit": score * 0.6,
                              "network": score * 0.4, "momentum": score * 0.5}
        ).model_dump(mode="json"),
    }


def generate_mixed_founder(idx: int) -> dict:
    """Remaining founders: normal mixed-signal profiles."""
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    sector = random.choice(SECTORS)
    geo = random.choice(GEOGRAPHIES)
    company_name = f"{random.choice(COMPANY_PREFIXES)}{random.choice(COMPANY_SUFFIXES)}"
    founder_id = uuid.uuid4()
    company_id = uuid.uuid4()
    application_id = uuid.uuid4()

    problem = random.choice(DECK_PROBLEMS)
    solution = random.choice(DECK_SOLUTIONS)
    university = random.choice(UNIVERSITIES)

    claims = [
        make_claim(founder_id, company_id, application_id, "founder_background",
                   f"Founder {name} holds a {random.choice(DEGREES)} from {university['name']}.",
                   "application_form", f"app:{application_id}"),
        make_claim(founder_id, company_id, application_id, "product",
                   f"{company_name} addresses: {problem}",
                   "deck", "deck#slide=1"),
        make_claim(founder_id, company_id, application_id, "product",
                   f"Solution: {solution}",
                   "deck", "deck#slide=2"),
    ]

    # Random mix of signals
    if random.random() > 0.4:
        github_username = name.lower().replace(" ", "")[:15]
        repo_name = f"{github_username}/{company_name.lower()}-core"
        stars = random.randint(10, 300)
        claims.append(make_claim(founder_id, company_id, application_id, "technical_depth",
                                 f"Repository {repo_name} has {stars} stars on GitHub.",
                                 "github", repo_name))

    if random.random() > 0.6:
        claims.append(make_claim(founder_id, company_id, application_id, "market_trend",
                                 f"The {sector} market is growing at {random.randint(15, 35)}% CAGR.",
                                 "external_db", f"crunchbase:{sector}-market"))

    if random.random() > 0.7:
        claims.append(make_claim(founder_id, company_id, application_id, "traction",
                                 f"{company_name} has {random.randint(100, 5000)} active users.",
                                 "deck", "deck#slide=3"))

    score = random.uniform(50, 80)
    return {
        "founder_id": str(founder_id),
        "company_id": str(company_id),
        "application_id": str(application_id),
        "name": name,
        "company_name": company_name,
        "sector": sector,
        "stage": random.choice(STAGES),
        "geography": geo,
        "categories": ["mixed"],
        "education": {"university": university["name"], "degree": random.choice(DEGREES), "year": random.randint(2013, 2023)},
        "prior_experience": f"Previously worked at {random.choice(PRIOR_COMPANIES)}.",
        "github_profile": {
            "username": name.lower().replace(" ", "")[:15] if random.random() > 0.4 else None,
            "repo_count": random.randint(1, 10),
            "primary_language": random.choice(GITHUB_LANGUAGES),
            "commit_activity": f"{random.randint(2, 20)} commits in last 30 days",
            "stars": random.randint(10, 300),
        } if random.random() > 0.4 else None,
        "deck_summary": f"{company_name} is building: {solution} The problem: {problem}",
        "claims": [c.model_dump(mode="json") for c in claims],
        "founder_score_seed": make_founder_score(
            founder_id, score, cold_start=False,
            component_scores={"technical": score * 0.8, "market_fit": score * 0.7,
                              "network": score * 0.5, "momentum": score * 0.6}
        ).model_dump(mode="json"),
    }


# ============================================================
# PHOTO FETCHING (randomuser.me)
# ============================================================

def fetch_photo() -> Optional[dict]:
    """Fetch a random profile photo from randomuser.me API."""
    try:
        r = httpx.get("https://randomuser.me/api/?inc=picture", timeout=10)
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            if results:
                return results[0].get("picture", {})
        return None
    except Exception:
        return None


# ============================================================
# MAIN
# ============================================================

def main():
    random.seed(42)  # reproducible output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FOUNDERS_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating 50 synthetic founder profiles...")
    print(f"Output: {OUTPUT_DIR}")

    # Distribution: 10 cold_start + 12 rich_signal + 10 contradicted + 8 missing_data + 10 mixed = 50
    generators = (
        [generate_cold_start_founder] * 10 +
        [generate_rich_signal_founder] * 12 +
        [generate_contradicted_founder] * 10 +
        [generate_missing_data_founder] * 8 +
        [generate_mixed_founder] * 10
    )

    founders = []
    index_entries = []

    for i, gen_fn in enumerate(generators):
        founder = gen_fn(i)
        
        # Fetch photo (rate-limited: 1 request per founder, randomuser.me handles this fine)
        print(f"  [{i+1}/50] {founder['name']} ({founder['categories'][0]}) — fetching photo...")
        photo = fetch_photo()
        if photo:
            founder["photo_url"] = photo.get("large") or photo.get("medium")
        else:
            founder["photo_url"] = None
        
        # Write individual JSON file
        founder_path = FOUNDERS_DIR / f"{founder['founder_id']}.json"
        with open(founder_path, "w") as f:
            json.dump(founder, f, indent=2, default=str)
        
        founders.append(founder)
        
        # Build index entry
        index_entries.append({
            "founder_id": founder["founder_id"],
            "name": founder["name"],
            "company_name": founder["company_name"],
            "categories": founder["categories"],
            "sector": founder["sector"],
            "geography": founder["geography"],
            "stage": founder["stage"],
        })
        
        # Small delay to respect randomuser.me rate limits
        time.sleep(0.3)

    # Write index.json
    index_path = OUTPUT_DIR / "index.json"
    with open(index_path, "w") as f:
        json.dump({
            "total": len(founders),
            "generated_at": datetime.utcnow().isoformat(),
            "founders": index_entries,
        }, f, indent=2)

    # Count distribution
    counts = {}
    for e in index_entries:
        for cat in e["categories"]:
            counts[cat] = counts.get(cat, 0) + 1
    
    # Sector distribution
    sector_counts = {}
    for e in index_entries:
        sector_counts[e["sector"]] = sector_counts.get(e["sector"], 0) + 1
    
    # Geography distribution
    geo_counts = {}
    for e in index_entries:
        geo_counts[e["geography"]] = geo_counts.get(e["geography"], 0) + 1

    # Pick demo fixtures
    cold_start_demo = next((f for f in founders if "cold_start" in f["categories"]), None)
    rich_signal_demo = next((f for f in founders if "rich_signal" in f["categories"]), None)
    contradicted_demo = next((f for f in founders if "contradicted" in f["categories"]), None)
    missing_data_demo = next((f for f in founders if "missing_data" in f["categories"]), None)

    # Write README.md
    readme_path = OUTPUT_DIR / "README.md"
    with open(readme_path, "w") as f:
        f.write(f"""# Synthetic Founder Dataset

Generated: {datetime.utcnow().isoformat()}

## Distribution

| Category | Count |
|---|---|
| cold_start | {counts.get('cold_start', 0)} |
| rich_signal | {counts.get('rich_signal', 0)} |
| contradicted | {counts.get('contradicted', 0)} |
| missing_data | {counts.get('missing_data', 0)} |
| mixed | {counts.get('mixed', 0)} |
| **Total** | **{len(founders)}** |

## Sectors

{chr(10).join(f"- {s}: {c}" for s, c in sorted(sector_counts.items()))}

## Geographies

{chr(10).join(f"- {g}: {c}" for g, c in sorted(geo_counts.items()))}

## Recommended Demo Fixtures

| Use case | Founder ID | Name | Company |
|---|---|---|---|
| Cold-start example | {cold_start_demo['founder_id'] if cold_start_demo else 'N/A'} | {cold_start_demo['name'] if cold_start_demo else 'N/A'} | {cold_start_demo['company_name'] if cold_start_demo else 'N/A'} |
| Rich-signal example | {rich_signal_demo['founder_id'] if rich_signal_demo else 'N/A'} | {rich_signal_demo['name'] if rich_signal_demo else 'N/A'} | {rich_signal_demo['company_name'] if rich_signal_demo else 'N/A'} |
| Contradiction example | {contradicted_demo['founder_id'] if contradicted_demo else 'N/A'} | {contradicted_demo['name'] if contradicted_demo else 'N/A'} | {contradicted_demo['company_name'] if contradicted_demo else 'N/A'} |
| Missing-data example | {missing_data_demo['founder_id'] if missing_data_demo else 'N/A'} | {missing_data_demo['name'] if missing_data_demo else 'N/A'} | {missing_data_demo['company_name'] if missing_data_demo else 'N/A'} |

## Schema

Each founder JSON file matches:
- `Claim` schema (BUILD_SPEC.md §3.1) — `confidence` left at 0.5, `flags` left empty (Validator fills these)
- `FounderScore` schema (BUILD_SPEC.md §3.2) — single `score_history` entry as seed

## Photos

Profile photos are fetched from randomuser.me API (https://randomuser.me/api/) —
free, explicitly designed for generating fake test/dummy profile data.

## Validation

All 50 founder JSON files validate against the Claim and FounderScore Pydantic schemas
with no missing required fields.
""")

    print(f"\n=== Generation complete ===")
    print(f"Total founders: {len(founders)}")
    print(f"Distribution: {counts}")
    print(f"Sectors: {sector_counts}")
    print(f"Geographies: {geo_counts}")
    print(f"Files: {FOUNDERS_DIR}/*.json + {index_path} + {readme_path}")


if __name__ == "__main__":
    main()
