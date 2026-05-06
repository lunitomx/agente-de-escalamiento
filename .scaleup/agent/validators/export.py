"""
Quality gate: validate Action Plan Export file.

Checks that all 5 required section headers are present in the generated file.

Usage:
    python .scaleup/agent/validators/export.py <path-to-export-file>

Exit codes:
    0 — file is valid
    1 — one or more required sections are missing
"""
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "## 1. Diagnosis Scores",
    "## 2. Annual Goal",
    "## 3. Active Priorities",
    "## 4. Open Tasks",
    "## 5. Next Steps",
]


def validate_export(file_path: Path) -> list[str]:
    """
    Validate that the export file contains all required section headers.
    Returns list of errors (empty = valid).
    """
    errors: list[str] = []

    if not file_path.exists():
        return [f"Export file not found: {file_path}"]

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"Could not read export file: {e}"]

    for section in REQUIRED_SECTIONS:
        if section not in content:
            errors.append(f"Missing required section: {section}")

    return errors


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export.py <path-to-export-file>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    errors = validate_export(path)

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)
    else:
        print("VALIDATION PASSED")
        sys.exit(0)
