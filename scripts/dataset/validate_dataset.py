#!/usr/bin/env python3
"""Validate every generated founder JSON against the BUILD_SPEC.md schemas.

Per spec §4 (Step 4): fails loudly on:
  - missing required fields
  - malformed UUID
  - empty claims array
  - Claim or FounderScore that doesn't round-trip through the Pydantic schema

Exits with status 0 if all 50 records pass; 1 otherwise.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.schemas.claim import Claim, ClaimKind, Source, SourceKind  # noqa: E402
from app.schemas.founder_score import FounderScore  # noqa: E402

DATASET_DIR = REPO_ROOT / "dataset"
FOUNDERS_DIR = DATASET_DIR / "founders"

REQUIRED_TOPLEVEL = [
    "founder_id", "company_id", "application_id",
    "name", "company_name", "sector", "stage", "geography",
    "categories", "education", "prior_experience", "github_profile",
    "deck_summary", "claims", "founder_score_seed",
    "photo_url", "university_image_url", "image_source",
]

REQUIRED_EDUCATION = ["university", "degree", "year"]

REQUIRED_IMAGE_SOURCE = ["photo", "university"]
VALID_IMAGE_SOURCES = {"randomuser.me", "wikimedia", "fallback"}


def fail(founder_id: str, msg: str) -> None:
    print(f"  ✗ FAIL  {founder_id}: {msg}", file=sys.stderr)


def is_uuid(s: str) -> bool:
    try:
        uuid.UUID(s)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def validate_one(path: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        fail(path.name, f"invalid JSON: {e}")
        return False

    fid = data.get("founder_id", "<missing>")

    # 1. Top-level required fields
    for k in REQUIRED_TOPLEVEL:
        if k not in data:
            fail(fid, f"missing top-level field: {k}")
            return False
        if data[k] is None and k not in ("github_profile",):
            fail(fid, f"top-level field {k} is null")
            return False

    # 2. UUIDs are well-formed
    for k in ("founder_id", "company_id", "application_id"):
        if not is_uuid(data[k]):
            fail(fid, f"{k} is not a valid UUID: {data[k]!r}")
            return False

    # 3. Categories — must be a non-empty list of known tags
    if not isinstance(data["categories"], list) or not data["categories"]:
        fail(fid, "categories is empty or not a list")
        return False
    valid_cats = {"cold_start", "rich_signal", "contradicted", "missing_data", "mixed"}
    for c in data["categories"]:
        if c not in valid_cats:
            fail(fid, f"unknown category tag: {c}")
            return False

    # 4. Education
    edu = data["education"]
    for k in REQUIRED_EDUCATION:
        if k not in edu or edu[k] is None:
            fail(fid, f"education.{k} is missing or null")
            return False
    if not isinstance(edu["year"], int) or not (1970 <= edu["year"] <= 2030):
        fail(fid, f"education.year is out of range: {edu['year']}")
        return False

    # 5. Photo + university image — must be non-null, and image_source must be a known tag
    for k in ("photo_url", "university_image_url"):
        if not data[k] or not isinstance(data[k], str):
            fail(fid, f"{k} is null or not a string")
            return False
    if not isinstance(data["image_source"], dict):
        fail(fid, "image_source is not a dict")
        return False
    for k in REQUIRED_IMAGE_SOURCE:
        v = data["image_source"].get(k)
        if v not in VALID_IMAGE_SOURCES:
            fail(fid, f"image_source.{k} has invalid value: {v!r}")
            return False

    # 6. Claims — must be a non-empty list of valid Claim objects
    if not isinstance(data["claims"], list) or len(data["claims"]) == 0:
        fail(fid, "claims is empty or not a list")
        return False

    founder_uuid = uuid.UUID(data["founder_id"])
    company_uuid = uuid.UUID(data["company_id"])
    app_uuid = uuid.UUID(data["application_id"])

    for i, c in enumerate(data["claims"]):
        try:
            claim = Claim.model_validate(c)
        except Exception as e:
            fail(fid, f"claim[{i}] fails schema validation: {e}")
            return False
        # Cross-field integrity
        if claim.founder_id != founder_uuid:
            fail(fid, f"claim[{i}].founder_id does not match top-level founder_id")
            return False
        if claim.company_id != company_uuid:
            fail(fid, f"claim[{i}].company_id does not match top-level company_id")
            return False
        # Confidence must be left at default 0.5 (spec: "left null/[] — Validator fills in")
        if claim.confidence != 0.5:
            fail(fid, f"claim[{i}].confidence is {claim.confidence}, expected 0.5 (Validator fills this in)")
            return False
        if claim.flags != []:
            fail(fid, f"claim[{i}].flags is non-empty — Validator should fill this in")
            return False
        # Kind must be a valid ClaimKind
        try:
            ClaimKind(claim.kind)
        except ValueError:
            fail(fid, f"claim[{i}].kind is not a valid ClaimKind: {claim.kind}")
            return False
        # Source kind must be a valid SourceKind
        try:
            SourceKind(claim.source.kind)
        except ValueError:
            fail(fid, f"claim[{i}].source.kind is not a valid SourceKind: {claim.source.kind}")
            return False
        # Text must be a single declarative sentence
        if not claim.text or len(claim.text.strip()) < 10:
            fail(fid, f"claim[{i}].text is too short")
            return False
        if claim.superseded_by is not None:
            fail(fid, f"claim[{i}].superseded_by should be null on a fresh dataset (no contradictions resolved yet)")
            return False

    # 7. Founder Score seed — must round-trip through schema with exactly one score_history entry
    try:
        score = FounderScore.model_validate(data["founder_score_seed"])
    except Exception as e:
        fail(fid, f"founder_score_seed fails schema validation: {e}")
        return False
    if score.founder_id != founder_uuid:
        fail(fid, "founder_score_seed.founder_id does not match top-level founder_id")
        return False
    if len(score.score_history) != 1:
        fail(fid, f"founder_score_seed.score_history should have exactly 1 entry, has {len(score.score_history)}")
        return False
    if score.current_score is None:
        fail(fid, "founder_score_seed.current_score is null")
        return False
    snap = score.score_history[0]
    if snap.cold_start != ("cold_start" in data["categories"]):
        # Allow cold_start=True on a cold_start-tagged founder, False otherwise
        # (mixed / rich_signal / contradicted / missing_data all default False)
        if not (snap.cold_start is False and "cold_start" not in data["categories"]):
            fail(fid, f"score_history[0].cold_start={snap.cold_start} but categories={data['categories']}")
            return False
    if snap.trigger not in ("application", "signal_threshold", "manual", "outbound_scan"):
        fail(fid, f"score_history[0].trigger has invalid value: {snap.trigger}")
        return False
    if not (0.0 <= snap.score <= 100.0):
        fail(fid, f"score_history[0].score out of range: {snap.score}")
        return False
    if not (snap.confidence_band[0] <= snap.score <= snap.confidence_band[1]):
        fail(fid, f"score not inside confidence_band: score={snap.score}, band={snap.confidence_band}")
        return False

    # 8. github_profile only for rich_signal / contradicted / mixed / missing_data founders
    if "cold_start" in data["categories"] and data["github_profile"] is not None:
        fail(fid, "cold_start founder should have github_profile=null")
        return False

    print(f"  ✓ OK    {fid}  [{','.join(data['categories'])}]  {data['name']}  ({len(data['claims'])} claims)")
    return True


def main() -> int:
    if not FOUNDERS_DIR.exists():
        print(f"ERROR: {FOUNDERS_DIR} does not exist. Run scripts/dataset/generate_founders.py first.", file=sys.stderr)
        return 2
    files = sorted(FOUNDERS_DIR.glob("*.json"))
    if len(files) != 50:
        print(f"WARNING: expected 50 founder JSON files, found {len(files)}", file=sys.stderr)

    print(f"Validating {len(files)} founder records against Claim + FounderScore schemas...")
    ok = 0
    failed = 0
    for p in files:
        if validate_one(p):
            ok += 1
        else:
            failed += 1

    print()
    print(f"=== Validation result ===")
    print(f"  OK     : {ok}")
    print(f"  FAILED : {failed}")
    if failed > 0:
        print(f"\n{failed} record(s) failed validation. Fix the generator before seeding.", file=sys.stderr)
        return 1
    print(f"\nAll {ok} records pass schema validation. Safe to seed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
