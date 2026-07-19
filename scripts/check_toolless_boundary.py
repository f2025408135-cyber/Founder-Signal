"""Static analysis — verify the tool-less synthesizer boundary (spec §10 C5).

Per spec §5.4 + §10 C5:
- app/agents/aggregator.py MUST NOT contain any `bind_tools()` call
- app/agents/aggregator.py MUST NOT pass `tools=` as a kwarg to any LLM call
- The synthesizer's input is `AggregatorAgentInput` — no `raw_inputs`, no `external_evidence`, no URLs

This script runs as a pytest test (test_toolless_boundary.py) AND as a standalone
script (python scripts/check_toolless_boundary.py) so it can be wired into CI.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
AGGREGATOR_PATH = BACKEND_DIR / "app" / "agents" / "aggregator.py"

# Patterns that indicate tool binding — forbidden in aggregator.py
FORBIDDEN_PATTERNS = [
    (r"\bbind_tools\s*\(", "bind_tools() call"),
    (r"\btools\s*=\s*\[", "tools= list kwarg"),
    (r"\btools\s*=\s*[A-Za-z_]", "tools= variable kwarg"),
    (r"\btool_choice\s*=", "tool_choice= kwarg"),
    (r"\bfunction_call\s*=", "function_call= kwarg (deprecated)"),
    (r"\bfunctions\s*=", "functions= kwarg (deprecated)"),
]

# Required: the aggregator must NOT receive raw_inputs / external_evidence / URLs
# We check the run_aggregator_agent signature.
REQUIRED_ABSENT_IN_INPUT = [
    "raw_inputs",
    "external_evidence",
    "external_evidence_url",
    "website_url",
    "search_query",
]


def check_aggregator_no_tools() -> list[tuple[str, int, str]]:
    """Return a list of (pattern_name, line_number, line_content) violations.

    Skips comment lines (lines starting with # after stripping whitespace) and
    string literals (lines inside a triple-quoted docstring).
    """
    if not AGGREGATOR_PATH.exists():
        return [("file_missing", 0, str(AGGREGATOR_PATH))]

    violations: list[tuple[str, int, str]] = []
    in_docstring = False
    for line_no, line in enumerate(AGGREGATOR_PATH.read_text().splitlines(), start=1):
        stripped = line.strip()

        # Track triple-quoted docstrings — skip lines inside them
        triple_count = line.count('"""') + line.count("'''")
        if in_docstring:
            if triple_count % 2 == 1:
                in_docstring = False
            continue
        if triple_count % 2 == 1:
            in_docstring = True
            # The line itself might still have code before the docstring starts,
            # but for our purposes, we skip it.
            continue

        # Skip comment-only lines
        if stripped.startswith("#"):
            continue

        for pattern, name in FORBIDDEN_PATTERNS:
            if re.search(pattern, line):
                violations.append((name, line_no, line.strip()))
    return violations


def check_aggregator_input_signature() -> list[str]:
    """Verify run_aggregator_agent does NOT accept raw_inputs / external_evidence / URLs."""
    if not AGGREGATOR_PATH.exists():
        return [f"file missing: {AGGREGATOR_PATH}"]

    content = AGGREGATOR_PATH.read_text()
    # Extract the run_aggregator_agent function signature (potentially multi-line)
    m = re.search(
        r"async\s+def\s+run_aggregator_agent\s*\(([^)]*)\)",
        content,
        re.DOTALL,
    )
    if m is None:
        return ["run_aggregator_agent function not found"]

    sig = m.group(1)
    violations: list[str] = []
    for forbidden in REQUIRED_ABSENT_IN_INPUT:
        # Match the parameter as a word — not as a substring of another param name
        if re.search(rf"\b{forbidden}\b", sig):
            violations.append(f"forbidden parameter in input: {forbidden}")
    return violations


def main() -> int:
    """Run all checks. Returns 0 on success, 1 on violation."""
    print(f"Checking {AGGREGATOR_PATH}...")
    fail = False

    tool_violations = check_aggregator_no_tools()
    if tool_violations:
        print("\nTOOL BINDING VIOLATIONS (spec §10 C5):")
        for name, line_no, line in tool_violations:
            print(f"  line {line_no}: {name}")
            print(f"    {line}")
        fail = True
    else:
        print("  No tool-binding patterns found. OK.")

    input_violations = check_aggregator_input_signature()
    if input_violations:
        print("\nINPUT SIGNATURE VIOLATIONS (spec §5.4):")
        for v in input_violations:
            print(f"  {v}")
        fail = True
    else:
        print("  Input signature does not contain raw_inputs / external_evidence / URLs. OK.")

    if fail:
        print("\nFAIL: tool-less synthesizer boundary violated.")
        return 1
    print("\nPASS: tool-less synthesizer boundary enforced.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
