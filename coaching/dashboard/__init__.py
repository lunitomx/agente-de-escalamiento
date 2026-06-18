"""
Dashboard module — Progress Dashboard.

Reads current scores from company-profile.yaml and pulse history from
pulse-history.yaml. Produces a 4-section markdown dashboard:
  1. Current Scores
  2. Pulse History
  3. Wins
  4. Attention Areas

Read-only — no file writes.
"""

from pathlib import Path

from ..core import (
    read_yaml,
    DECISION_LABELS,
    ROUTING_RULES,
    PRIORITY_ORDER,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCORE_LEVELS = {
    1: "No iniciado",
    2: "Ad hoc",
    3: "Emergente",
    4: "Establecido",
    5: "Optimizado",
}

HISTORY_REL_PATH = ".scaleup/my-company/pulse-history.yaml"


# ---------------------------------------------------------------------------
# Helpers — Scores
# ---------------------------------------------------------------------------


def _read_scores(base: Path) -> dict:
    """Return diagnosis scores from company-profile.yaml, or empty dict."""
    yaml_path = base / ".scaleup" / "agent" / "memory" / "company-profile.yaml"
    profile = read_yaml(yaml_path)
    return profile.get("scores") or {}


def _scores_table(scores: dict) -> str:
    """Render scores as a markdown table."""
    lines = [
        "| Decision  | Score | Level          |",
        "|-----------|-------|----------------|",
    ]
    for key in PRIORITY_ORDER:
        score = scores.get(key)
        if isinstance(score, int) and score > 0:
            level = SCORE_LEVELS.get(score, "—")
            label = DECISION_LABELS.get(key, key.title())
            lines.append(f"| {label:<9} | {score}/5   | {level:<14} |")
    return "\n".join(lines)


def _build_scores_section(base: Path) -> tuple[str, dict]:
    """Build the Current Scores section. Returns (markdown, scores_dict)."""
    scores = _read_scores(base)
    # Treat all-zero or empty scores as "no diagnosis yet"
    has_data = any(isinstance(v, int) and v > 0 for v in scores.values())
    if not has_data:
        body = "No diagnosis yet. Run /scaleup-diagnose first."
        return body, {}
    return _scores_table(scores), scores


# ---------------------------------------------------------------------------
# Helpers — Pulse History
# ---------------------------------------------------------------------------


def _read_pulse_history(base: Path) -> list[dict]:
    """Read pulse history from pulse-history.yaml. Returns list of pulses."""
    history_path = base / HISTORY_REL_PATH
    data = read_yaml(history_path)
    return data.get("pulses") or []


def _format_trend(trend: str) -> str:
    """Short display for trend column."""
    return trend if trend else "—"


def _build_history_table(pulses: list[dict]) -> str:
    """Build Pulse History table in reverse-chronological order."""
    lines = [
        "| Date       | People     | Strategy   | Execution  | Cash       | Overall    |",
        "|------------|------------|------------|------------|------------|------------|",
    ]
    for pulse in reversed(pulses):
        date = pulse.get("date", "—")
        trends = pulse.get("trends", {})
        row = (
            f"| {date:<10} "
            f"| {_format_trend(trends.get('people', '—')):<10} "
            f"| {_format_trend(trends.get('strategy', '—')):<10} "
            f"| {_format_trend(trends.get('execution', '—')):<10} "
            f"| {_format_trend(trends.get('cash', '—')):<10} "
            f"| {_format_trend(trends.get('overall', '—')):<10} |"
        )
        lines.append(row)
    return "\n".join(lines)


def _build_wins(last_pulse: dict) -> list[str]:
    """Return list of (decision_key, label) for improving trends in last pulse."""
    trends = last_pulse.get("trends", {})
    wins = []
    for decision in PRIORITY_ORDER:
        if trends.get(decision) == "improving":
            label = DECISION_LABELS.get(decision, decision.title())
            wins.append(label)
    return wins


def _build_attention(pulses: list[dict]) -> list[tuple[str, str, str]]:
    """
    Return list of (decision_key, label, reason) for attention areas.
    - regressing in last pulse → flagged (1 pulse sufficient)
    - stalling in last 2 consecutive pulses → flagged
    """
    if not pulses:
        return []
    last = pulses[-1]
    prev = pulses[-2] if len(pulses) >= 2 else None
    attention = []
    for decision in PRIORITY_ORDER:
        trend = last.get("trends", {}).get(decision)
        if trend == "regressing":
            label = DECISION_LABELS.get(decision, decision.title())
            cmd = ROUTING_RULES.get(decision, f"/scaleup-{decision}")
            attention.append((decision, label, f"regressing → run {cmd}"))
        elif trend == "stalling" and prev is not None:
            prev_trend = prev.get("trends", {}).get(decision)
            if prev_trend == "stalling":
                label = DECISION_LABELS.get(decision, decision.title())
                cmd = ROUTING_RULES.get(decision, f"/scaleup-{decision}")
                attention.append((decision, label, f"stalling 2+ pulses → run {cmd}"))
    return attention


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def _section_pulse_history(pulses: list[dict]) -> str:
    if not pulses:
        return "No pulse data yet. Run /scaleup-pulse to start tracking."
    return _build_history_table(pulses)


def _section_wins(pulses: list[dict]) -> str:
    if not pulses:
        return "No pulse data yet. Run /scaleup-pulse to start tracking."
    wins = _build_wins(pulses[-1])
    if not wins:
        return "No improving trends in the latest pulse."
    lines = []
    for label in wins:
        lines.append(f"- {label} improving since last pulse")
    return "\n".join(lines)


def _section_attention(pulses: list[dict]) -> str:
    if not pulses:
        return "No pulse data yet. Run /scaleup-pulse to start tracking."
    items = _build_attention(pulses)
    if not items:
        return "No attention areas detected. Keep up the momentum!"
    lines = []
    for _, label, reason in items:
        lines.append(f"- {label}: {reason}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core run function
# ---------------------------------------------------------------------------


def run(context: dict) -> dict:
    """
    Generate Progress Dashboard.

    Context keys:
        - base_path: str (default ".")

    Returns:
        dict with success (bool), output (str), artifacts (dict), errors (list[str])
    """
    base = Path(context.get("base_path", "."))

    # --- Build Section 1: Current Scores ---
    scores_body, scores = _build_scores_section(base)

    # --- Build Sections 2-4: Pulse ---
    pulses = _read_pulse_history(base)
    history_body = _section_pulse_history(pulses)
    wins_body = _section_wins(pulses)
    attention_body = _section_attention(pulses)

    # --- Assemble full dashboard ---
    sections = [
        "# ScaleUp Progress Dashboard",
        "",
        "## Current Scores",
        "",
        scores_body,
        "",
        "---",
        "",
        "## Pulse History",
        "",
        history_body,
        "",
        "---",
        "",
        "## Wins",
        "",
        wins_body,
        "",
        "---",
        "",
        "## Attention Areas",
        "",
        attention_body,
    ]
    output = "\n".join(sections)

    return {
        "success": True,
        "output": output,
        "artifacts": {
            "scores": scores,
            "pulse_count": len(pulses),
        },
        "errors": [],
    }
