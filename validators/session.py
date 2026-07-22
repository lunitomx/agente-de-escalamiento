"""Quality gate validators for session lifecycle pipeline.

Code-based validation (ADR-5) — the LLM never evaluates its own output.
"""

from __future__ import annotations

import pathlib
import re
from datetime import date
from typing import Any

try:
    import yaml
except ImportError as e:
    raise ImportError("PyYAML required: pip install pyyaml") from e


_REQUIRED_FRONTMATTER = {"date", "duration_minutes", "decision_focus"}
_VALID_DECISIONS = {"people", "strategy", "execution", "cash"}
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.+?)\n---", re.DOTALL)


def validate_session_log(log_path: pathlib.Path) -> list[str]:
    """Validate a session log file. Returns list of errors (empty = valid)."""
    errors: list[str] = []

    if not log_path.exists():
        return [f"File not found: {log_path}"]

    text = log_path.read_text(encoding="utf-8")

    match = _FRONTMATTER_RE.match(text)
    if not match:
        return ["No YAML frontmatter found (must start with ---)"]

    try:
        frontmatter: dict[str, Any] = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return [f"Invalid YAML in frontmatter: {exc}"]

    if not isinstance(frontmatter, dict):
        return ["Frontmatter is not a mapping"]

    missing = _REQUIRED_FRONTMATTER - frontmatter.keys()
    if missing:
        errors.append(f"Missing required keys: {', '.join(sorted(missing))}")

    if "date" in frontmatter:
        d = frontmatter["date"]
        if not isinstance(d, date):
            errors.append(f"'date' must be a valid date, got: {d!r}")

    if "duration_minutes" in frontmatter:
        dur = frontmatter["duration_minutes"]
        if not isinstance(dur, int) or dur <= 0:
            errors.append(
                f"'duration_minutes' must be a positive integer, got: {dur!r}"
            )

    if "decision_focus" in frontmatter:
        focus = frontmatter["decision_focus"]
        if focus not in _VALID_DECISIONS:
            errors.append(
                f"'decision_focus' must be one of {_VALID_DECISIONS}, got: {focus!r}"
            )

    return errors


def validate_context_bundle(profile_path: pathlib.Path) -> list[str]:
    """Validate that company profile has minimum required data.

    Returns list of errors (empty = valid).
    """
    errors: list[str] = []

    if not profile_path.exists():
        return [f"Profile not found: {profile_path}"]

    try:
        data: dict[str, Any] = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"Invalid YAML: {exc}"]

    if not isinstance(data, dict):
        return ["Profile is not a mapping"]

    company = data.get("company", {})
    if not company.get("name"):
        errors.append("Company name is empty — run /escala-welcome first")

    scores = data.get("scores", {})
    for key in ("people", "strategy", "execution", "cash"):
        val = scores.get(key)
        if val is not None and not isinstance(val, (int, float)):
            errors.append(f"Score '{key}' must be numeric, got: {val!r}")

    return errors
