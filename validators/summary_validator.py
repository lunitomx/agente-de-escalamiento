"""Quality gate: validate Session Summary section in session log file.

Checks that a '## Session Summary' section header is present as a
top-level markdown heading (anchored at start of line).

Usage:
    python .scaleup/agent/validators/summary_validator.py <path-to-session-log>

Exit codes:
    0 — file is valid (## Session Summary present)
    1 — section missing, file not found, or read error
"""
import re
import sys
from pathlib import Path

REQUIRED_SECTION = "## Session Summary"
_SECTION_RE = re.compile(r"^## Session Summary", re.MULTILINE)


def validate_summary(log_path: str) -> list[str]:
    """Validate that the session log file contains the Session Summary section.

    Args:
        log_path: Path to the session log file (str).

    Returns:
        List of error strings (empty = valid).
    """
    errors: list[str] = []
    path = Path(log_path)

    if not path.exists():
        return [f"File not found: {log_path}"]

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"Could not read file: {exc}"]

    if not _SECTION_RE.search(content):
        errors.append(f"Missing section: {REQUIRED_SECTION}")

    return errors


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python summary_validator.py <path-to-session-log>", file=sys.stderr)
        sys.exit(1)

    path_arg = sys.argv[1]
    errors = validate_summary(path_arg)

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)
    else:
        print("VALIDATION PASSED")
        sys.exit(0)
