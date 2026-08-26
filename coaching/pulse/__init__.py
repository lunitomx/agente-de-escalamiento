"""
Pulse module — Quarterly Pulse Check.

Reads answer dict from context (each decision: -1, 0, or 1),
maps answers to trends (regressing/stalling/improving),
persists entry to pulse-history.yaml, generates course corrections
for regressing decisions, and returns formatted markdown output.
"""

import datetime
from pathlib import Path

from ..core import (
    DECISION_LABELS,
    ROUTING_RULES,
    load_context,
    read_yaml,
    write_yaml,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DECISIONS = ["people", "strategy", "execution", "cash", "overall"]
VALID_ANSWER_VALUES = {-1, 0, 1}
HISTORY_REL_PATH = ".scaleup/my-company/pulse-history.yaml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _trend(answer: int) -> str:
    """Map a single pulse answer to a trend label."""
    if answer > 0:
        return "improving"
    if answer < 0:
        return "regressing"
    return "stalling"


def _validate_answers(answers: dict) -> list[str]:
    """Return list of error strings for missing or invalid answer values."""
    errors = []
    for decision in DECISIONS:
        val = answers.get(decision)
        if val is None:
            errors.append(f"Missing answer for '{decision}'. Must be -1, 0, or 1.")
        elif val not in VALID_ANSWER_VALUES:
            errors.append(
                f"Invalid answer for '{decision}': {val!r}. Must be -1, 0, or 1."
            )
    return errors


def _build_course_corrections(trends: dict) -> list[str]:
    """Build list of course correction strings for regressing decisions."""
    corrections = []
    for decision in DECISIONS:
        if trends.get(decision) == "regressing":
            label = DECISION_LABELS.get(decision, decision.title())
            cmd = ROUTING_RULES.get(decision, f"/scaleup-{decision}")
            corrections.append(f"{label} regressing → run {cmd}")
    return corrections


def _format_answer(val: int) -> str:
    """Format answer as +1, 0, or -1."""
    if val > 0:
        return f"+{val}"
    return str(val)


def _build_output(
    today: str, answers: dict, trends: dict, course_corrections: list[str]
) -> str:
    """Assemble the markdown output."""
    overall_trend = trends.get("overall", "stalling")

    lines = [
        f"## Pulse — {today}",
        "",
        f"**Overall trend:** {overall_trend}",
        "",
        "| Decision  | Answer | Trend      |",
        "|-----------|--------|------------|",
    ]

    for decision in DECISIONS:
        label = DECISION_LABELS.get(decision, decision.title())
        val = answers.get(decision, 0)
        trend = trends.get(decision, "stalling")
        lines.append(f"| {label:<9} | {_format_answer(val):<6} | {trend:<10} |")

    if course_corrections:
        lines.append("")
        lines.append("**Course corrections:**")
        for correction in course_corrections:
            lines.append(f"- {correction}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core run function
# ---------------------------------------------------------------------------


def run(context: dict) -> dict:
    """
    Run a quarterly pulse check.

    Context keys:
        - answers: dict with keys people, strategy, execution, cash, overall
                   Values must be -1 (regressing), 0 (stalling), or 1 (improving)
        - base_path: str (default ".")

    Returns:
        dict with success (bool), output (str), artifacts (dict), errors (list[str])
    """
    base = Path(context.get("base_path", "."))
    answers = context.get("answers", {})
    today = datetime.date.today().isoformat()

    # --- Validate answers ---
    errors = _validate_answers(answers)
    if errors:
        return {
            "success": False,
            "output": "",
            "artifacts": {
                "trends": {},
                "course_corrections": [],
                "history_path": str(base / HISTORY_REL_PATH),
                "pulse_date": today,
                "prior_pulse_date": None,
            },
            "errors": errors,
        }

    # --- Compute trends ---
    trends = {d: _trend(answers.get(d, 0)) for d in DECISIONS}

    # --- Load history for prior_pulse_date ---
    history_path = base / HISTORY_REL_PATH
    history_data = read_yaml(history_path)
    pulses = history_data.get("pulses", [])
    prior_pulse_date = pulses[-1]["date"] if pulses else None

    # --- Build course corrections ---
    course_corrections = _build_course_corrections(trends)

    # --- Build new entry ---
    new_entry = {
        "date": today,
        "answers": dict(answers),
        "trends": dict(trends),
        "course_corrections": course_corrections,
    }

    # --- Append and persist ---
    pulses.append(new_entry)
    write_yaml(history_path, {"pulses": pulses})

    # --- Build output markdown ---
    output = _build_output(today, answers, trends, course_corrections)

    return {
        "success": True,
        "output": output,
        "artifacts": {
            "pulse_date": today,
            "trends": trends,
            "course_corrections": course_corrections,
            "history_path": str(history_path),
            "prior_pulse_date": prior_pulse_date,
        },
        "errors": [],
    }
