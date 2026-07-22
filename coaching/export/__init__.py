"""
Export module — Action Plan Export.

Reads 5 data sources from .escala/my-company/ and assembles a dated
5-section markdown document at .escala/my-company/exports/YYYY-MM-DD-action-plan.md.
"""

import datetime
from pathlib import Path

from ..core import read_yaml, ensure_dir

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCORE_LEVEL_SHORT = {
    1: "No iniciado",
    2: "Ad hoc",
    3: "Emergente",
    4: "Establecido",
    5: "Optimizado",
}

PRIORITY_ORDER = ["people", "strategy", "execution", "cash"]

DECISION_LABELS = {
    "people": "People",
    "strategy": "Strategy",
    "execution": "Execution",
    "cash": "Cash",
}

ROUTING_RULES = {
    "people": "/escala-people",
    "strategy": "/escala-strategy",
    "execution": "/escala-execution",
    "cash": "/escala-cash",
}

PLACEHOLDER = "> Not configured yet. Run /escala-welcome."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_md(path: Path) -> tuple[str, bool]:
    """Return (content, found). If file missing, return placeholder."""
    if path.exists():
        return path.read_text(encoding="utf-8"), True
    return PLACEHOLDER, False


def _read_scores(base: Path) -> dict:
    """Return diagnosis scores from company-profile.yaml, or empty dict."""
    yaml_path = base / ".escala" / "agent" / "memory" / "company-profile.yaml"
    profile = read_yaml(yaml_path)
    return profile.get("scores", {})


def _scores_table(scores: dict) -> str:
    """Render scores as a markdown table."""
    lines = [
        "| Decision  | Score | Level          |",
        "|-----------|-------|----------------|",
    ]
    for key in PRIORITY_ORDER:
        score = scores.get(key)
        if score is not None:
            level = SCORE_LEVEL_SHORT.get(score, "—")
            label = DECISION_LABELS.get(key, key.title())
            lines.append(f"| {label:<9} | {score}     | {level:<14} |")
    return "\n".join(lines)


def _detect_priority(scores: dict) -> str | None:
    """Return decision key with the lowest score (tiebroken by PRIORITY_ORDER)."""
    valid = {k: v for k, v in scores.items() if isinstance(v, int) and v > 0}
    if not valid:
        return None
    lowest = min(valid.values())
    for key in PRIORITY_ORDER:
        if key in valid and valid[key] == lowest:
            return key
    return None


def _build_next_steps(scores: dict) -> str:
    """Generate next steps section from priority decision routing."""
    priority = _detect_priority(scores)
    lines = []
    if priority:
        label = DECISION_LABELS.get(priority, priority.title())
        cmd = ROUTING_RULES.get(priority, f"/escala-{priority}")
        lines.append(f"**Priority Focus:** {label} — `{cmd}`")
        lines.append("")
        lines.append(f"Your lowest score is in **{label}**. Start there with `{cmd}`.")
        lines.append("")
        lines.append("**Suggested sequence:**")
        lines.append("")
        others = [
            k for k in PRIORITY_ORDER if k != priority and k in scores and scores[k]
        ]
        others_sorted = sorted(others, key=lambda k: scores.get(k, 99))
        for key in others_sorted:
            score = scores.get(key, "—")
            cmd_other = ROUTING_RULES.get(key, f"/escala-{key}")
            lbl = DECISION_LABELS.get(key, key.title())
            lines.append(f"- `{cmd_other}` — {lbl} (score: {score})")
    else:
        lines.append(
            "Run `/escala-diagnose` to complete your assessment and get personalized next steps."
        )
    lines.append("")
    lines.append("> To re-evaluate: `/escala-diagnose`")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core run function
# ---------------------------------------------------------------------------


def run(context: dict) -> dict:
    """
    Generate Action Plan Export.

    Context keys:
        - base_path: str (default ".")

    Returns:
        dict with output (str), artifacts (dict), errors (list[str])
    """
    base = Path(context.get("base_path", "."))
    today = datetime.date.today().isoformat()
    filename = f"{today}-action-plan.md"

    company_dir = base / ".escala" / "my-company"
    exports_dir = company_dir / "exports"
    ensure_dir(exports_dir)
    export_path = exports_dir / filename

    missing_optional: list[str] = []

    # --- Read all 5 data sources ---
    scores = _read_scores(base)

    profile_content, profile_found = _read_md(company_dir / "profile.md")
    if not profile_found:
        missing_optional.append("profile.md")

    goal_content, goal_found = _read_md(company_dir / "annual-goal.md")
    if not goal_found:
        missing_optional.append("annual-goal.md")

    priorities_content, priorities_found = _read_md(company_dir / "quarterly-focus.md")
    if not priorities_found:
        missing_optional.append("quarterly-focus.md")

    tasks_content, tasks_found = _read_md(company_dir / "tasks.md")
    if not tasks_found:
        missing_optional.append("tasks.md")

    # --- Extract company name from YAML profile if available ---
    yaml_path = base / ".escala" / "agent" / "memory" / "company-profile.yaml"
    yaml_profile = read_yaml(yaml_path)
    company_name = yaml_profile.get("company", {}).get("name", "My Company")

    # --- Build scores section ---
    if scores:
        scores_body = _scores_table(scores)
        priority = _detect_priority(scores)
        if priority:
            priority_label = DECISION_LABELS.get(priority, priority.title())
            priority_cmd = ROUTING_RULES.get(priority, f"/escala-{priority}")
            scores_body += (
                f"\n\n**Priority focus:** {priority_label} — `{priority_cmd}`"
            )
    else:
        scores_body = "> No diagnosis scores found. Run `/escala-diagnose` first."

    # --- Build next steps ---
    next_steps_body = _build_next_steps(scores)

    # --- Assemble markdown document ---
    doc_lines = [
        "# Action Plan Export",
        "",
        f"**Company:** {company_name}",
        f"**Date:** {today}",
        "**Generated by:** ESCALA Coach",
        "",
        "---",
        "",
        "## 1. Diagnosis Scores",
        "",
        scores_body,
        "",
        "---",
        "",
        "## 2. Annual Goal",
        "",
        goal_content,
        "",
        "---",
        "",
        "## 3. Active Priorities (Current Quarter)",
        "",
        priorities_content,
        "",
        "---",
        "",
        "## 4. Open Tasks & Commitments",
        "",
        tasks_content,
        "",
        "---",
        "",
        "## 5. Next Steps",
        "",
        next_steps_body,
        "",
        "---",
        "",
        f"*Exported: {today} | ESCALA Coach*",
    ]

    markdown = "\n".join(doc_lines)
    export_path.write_text(markdown, encoding="utf-8")

    export_path_str = str(export_path)

    return {
        "output": f"Export generated: {export_path_str}",
        "artifacts": {
            "export_path": export_path_str,
            "sections_included": [
                "scores",
                "goal",
                "priorities",
                "tasks",
                "next_steps",
            ],
            "missing_optional": missing_optional,
        },
        "errors": [],
    }
