"""
Quality gate: validate pulse-history.yaml.

Validates the last entry in pulse-history.yaml contains all required keys,
valid answer values, and valid trend values.

Usage:
    python3 .scaleup/agent/validators/pulse.py <path-to-pulse-history.yaml>

Exit codes:
    0 — file is valid (or pulses list is empty)
    1 — one or more validation errors found
"""
import sys
from pathlib import Path

REQUIRED_ENTRY_KEYS = ["date", "answers", "trends", "course_corrections"]
REQUIRED_DECISION_KEYS = ["people", "strategy", "execution", "cash", "overall"]
VALID_ANSWER_VALUES = {-1, 0, 1}
VALID_TREND_VALUES = {"improving", "stalling", "regressing"}


def validate_pulse_history(file_path: Path) -> list[str]:
    """
    Validate the last entry in pulse-history.yaml.
    Returns list of errors (empty = valid).
    """
    errors: list[str] = []

    if not file_path.exists():
        return [f"Pulse history file not found: {file_path}"]

    try:
        import yaml
        content = file_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content) or {}
    except Exception as e:
        return [f"Could not read pulse history file: {e}"]

    if not isinstance(data, dict):
        return ["pulse-history.yaml must be a mapping with a 'pulses' key"]

    pulses = data.get("pulses", [])

    if not isinstance(pulses, list):
        return ["'pulses' must be a list"]

    # Empty list is valid — no entries to check
    if len(pulses) == 0:
        return []

    last_entry = pulses[-1]

    # Check required top-level keys
    for key in REQUIRED_ENTRY_KEYS:
        if key not in last_entry:
            errors.append(f"Last entry missing required key: {key}")

    if errors:
        return errors

    # Check answers keys and values
    answers = last_entry.get("answers", {})
    for decision in REQUIRED_DECISION_KEYS:
        if decision not in answers:
            errors.append(f"Last entry answers missing decision: {decision}")
        else:
            val = answers[decision]
            if val not in VALID_ANSWER_VALUES:
                errors.append(
                    f"Last entry answers['{decision}'] = {val!r} is not valid. "
                    f"Must be one of {sorted(VALID_ANSWER_VALUES)}."
                )

    # Check trends keys and values
    trends = last_entry.get("trends", {})
    for decision in REQUIRED_DECISION_KEYS:
        if decision not in trends:
            errors.append(f"Last entry trends missing decision: {decision}")
        else:
            val = trends[decision]
            if val not in VALID_TREND_VALUES:
                errors.append(
                    f"Last entry trends['{decision}'] = {val!r} is not valid. "
                    f"Must be one of {sorted(VALID_TREND_VALUES)}."
                )

    # Check date is present and non-empty
    date_val = last_entry.get("date", "")
    if not date_val:
        errors.append("Last entry 'date' is empty or missing")

    return errors


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 pulse.py <path-to-pulse-history.yaml>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    errors = validate_pulse_history(path)

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)
    else:
        print("VALIDATION PASSED")
        sys.exit(0)
