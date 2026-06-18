"""
Quality gate: validate Progress Dashboard output file.

Checks that all 4 required section headers are present in the dashboard output.

Usage:
    python .scaleup/agent/validators/dashboard.py <path-to-dashboard-file>

Exit codes:
    0 — file is valid
    1 — one or more required sections are missing
"""

import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "## Current Scores",
    "## Pulse History",
    "## Wins",
    "## Attention Areas",
]


def validate_dashboard(file_path: Path) -> list[str]:
    """
    Validate that the dashboard file contains all required section headers.
    Returns list of errors (empty = valid).
    """
    errors: list[str] = []

    if not file_path.exists():
        return [f"Dashboard file not found: {file_path}"]

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"Could not read dashboard file: {e}"]

    for section in REQUIRED_SECTIONS:
        if section not in content:
            errors.append(f"Missing required section: {section}")

    return errors


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dashboard.py <path-to-dashboard-file>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    errors = validate_dashboard(path)

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)
    else:
        print("VALIDATION PASSED")
        sys.exit(0)
