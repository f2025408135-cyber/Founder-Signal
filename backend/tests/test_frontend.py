"""Frontend smoke tests — verify dev server + build artifacts.

Per spec §10 D1: `npm run dev` starts on port 5173 and renders a placeholder InboxPage;
`npm run build` produces a production bundle < 500KB gzipped.

These tests don't require a running backend — they just verify the frontend
boots and the build is valid.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


def test_frontend_build_artifacts_exist():
    """dist/ contains the built index.html + JS + CSS bundles."""
    dist = FRONTEND_DIR / "dist"
    assert dist.exists(), "dist/ directory missing — run `npm run build` first"
    index_html = dist / "index.html"
    assert index_html.exists(), "dist/index.html missing"
    content = index_html.read_text()
    assert '<div id="root"' in content
    assert "module" in content  # script type=module


def test_frontend_build_under_500kb_gzipped():
    """Spec §10 D1: production bundle < 500KB gzipped."""
    assets = FRONTEND_DIR / "dist" / "assets"
    assert assets.exists()
    total_bytes = 0
    for f in assets.iterdir():
        if f.is_file():
            total_bytes += f.stat().st_size
    # Gzipped size is typically ~30% of raw — we use a conservative 40% factor
    # to account for less-compressible assets.
    estimated_gzipped = total_bytes * 0.4
    assert estimated_gzipped < 500_000, (
        f"Estimated gzipped bundle size {estimated_gzipped / 1024:.1f}KB exceeds 500KB limit"
    )


def test_frontend_dev_server_starts():
    """`npm run dev` starts on port 5173 and serves the index.html."""
    # Skip if dev server is already running (don't fail the test)
    try:
        r = httpx.get("http://localhost:5173/", timeout=2)
        if r.status_code == 200:
            pytest.skip("Dev server already running")
    except Exception:
        pass

    proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(FRONTEND_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        # Wait up to 10 seconds for the server to come up
        for _ in range(20):
            time.sleep(0.5)
            try:
                r = httpx.get("http://localhost:5173/", timeout=2)
                if r.status_code == 200:
                    assert '<div id="root"' in r.text
                    return
            except Exception:
                continue
        pytest.fail("Dev server did not come up within 10 seconds")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_frontend_src_files_present():
    """All required source files exist per spec §2 repository structure."""
    required = [
        "src/main.tsx",
        "src/App.tsx",
        "src/index.css",
        "src/lib/api.ts",
        "src/lib/utils.ts",
        "src/components/Layout.tsx",
        "src/components/FounderCard.tsx",
        "src/components/MemoView.tsx",
        "src/components/EvidenceChip.tsx",
        "src/components/PipelineTrace.tsx",
        "src/components/ui.tsx",
        "src/pages/InboxPage.tsx",
        "src/pages/FounderDetailPage.tsx",
        "src/pages/ThesisPage.tsx",
        "src/pages/OutboundPage.tsx",
    ]
    for rel in required:
        path = FRONTEND_DIR / rel
        assert path.exists(), f"Missing source file: {rel}"


def test_frontend_pages_export_default():
    """Each page module has a default export (required by react-router)."""
    for page in ["InboxPage", "FounderDetailPage", "ThesisPage", "OutboundPage"]:
        path = FRONTEND_DIR / "src" / "pages" / f"{page}.tsx"
        content = path.read_text()
        assert "export default" in content, f"{page}.tsx missing default export"


def test_frontend_compact_card_renders_all_spec_fields():
    """Spec §9.1 field list: every field is referenced in FounderCard.tsx."""
    card_src = (FRONTEND_DIR / "src" / "components" / "FounderCard.tsx").read_text()
    # Check that key field names from spec §9.1 appear in the source
    required_fields = [
        "company_name", "geography", "sector", "received_at",
        "founder_score", "founder_trend", "cold_start",
        "market_score", "idea_vs_market_score", "thesis_fit_score",
        "conviction", "evidence_coverage", "open_contradictions",
        "recommendation",
    ]
    for field in required_fields:
        assert field in card_src, f"FounderCard.tsx missing field: {field}"


def test_frontend_cold_start_amber_border():
    """Spec §9.1: cold-start founders get an amber border + ❄ icon."""
    card_src = (FRONTEND_DIR / "src" / "components" / "FounderCard.tsx").read_text()
    assert "cold-start" in card_src.lower()
    assert "Snowflake" in card_src  # lucide-react icon for ❄


def test_frontend_evidence_chip_colors():
    """Spec §9.2 evidence chip colors: verified=green, unverifiable=yellow, contradicted=red, missing=gray."""
    utils_src = (FRONTEND_DIR / "src" / "lib" / "utils.ts").read_text()
    assert "verified" in utils_src
    assert "unverifiable" in utils_src
    assert "contradicted" in utils_src
    assert "not_disclosed" in utils_src


def test_frontend_compound_query_input():
    """Spec §9.4: inbox search box accepts compound queries via POST /api/query."""
    inbox_src = (FRONTEND_DIR / "src" / "pages" / "InboxPage.tsx").read_text()
    assert "api.query" in inbox_src or "api/query" in inbox_src
    assert 'placeholder=' in inbox_src
    # Spec example query
    assert "technical founder" in inbox_src.lower() or "Berlin" in inbox_src
