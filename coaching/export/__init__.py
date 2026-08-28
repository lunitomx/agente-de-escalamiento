"""
Export module — Action Plan Export.

Reads 5 data sources from .escala/my-company/ and assembles a dated
5-section markdown document at .escala/my-company/exports/YYYY-MM-DD-action-plan.md.
"""

import datetime
from pathlib import Path

from ..core import read_yaml, ensure_dir
from .diagnostic import run_diagnostic

__all__ = ["run", "run_diagnostic"]

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
    """Return optional legacy diagnosis scores from company-profile.yaml."""
    yaml_path = base / ".escala" / "agent" / "memory" / "company-profile.yaml"
    profile = read_yaml(yaml_path)
    scores = profile.get("scores", {})
    return scores if isinstance(scores, dict) else {}


def _read_assessment(base: Path) -> dict:
    """Return the latest narrative assessment, if the user authorized one."""
    yaml_path = base / ".escala" / "agent" / "memory" / "company-profile.yaml"
    profile = read_yaml(yaml_path)
    assessment = profile.get("narrative_assessment", {})
    return assessment if isinstance(assessment, dict) else {}


def _assessment_body(assessment: dict) -> str:
    """Render an assessment without silently converting it into a score."""
    if not assessment:
        return (
            "> Aún no hay assessment narrativo. Ejecuta `/escala-diagnose` para "
            "explicar el contexto antes de elegir un foco."
        )
    lines: list[str] = []
    summary = assessment.get("company_summary")
    if isinstance(summary, str) and summary.strip():
        lines.append(summary.strip())
    lines.extend(
        ["", f"**Estado:** {assessment.get('confirmation_status', 'pending')}"]
    )
    understanding = assessment.get("company_understanding", {})
    if isinstance(understanding, dict):
        labels = {
            "industry": "Industria",
            "offering": "Oferta",
            "target_customer": "Cliente objetivo",
            "business_model": "Modelo de negocio",
            "primary_challenge": "Reto actual",
        }
        for field, label in labels.items():
            value = understanding.get(field)
            if isinstance(value, str) and value.strip():
                lines.append(f"- **{label}:** {value.strip()}")
    focuses = assessment.get("proposed_focuses", [])
    if isinstance(focuses, list) and focuses:
        lines.extend(["", "**Focos propuestos:**"])
        for focus in focuses[:2]:
            if isinstance(focus, dict) and isinstance(focus.get("decision"), str):
                lines.append(
                    f"- **{focus['decision'].title()}** — "
                    f"{focus.get('rationale', 'sin razón registrada')}"
                )
    return "\n".join(lines)


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


def _build_next_steps(scores: dict, assessment: dict) -> str:
    """Generate next steps from optional scores or a confirmed narrative focus."""
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
        status = assessment.get("confirmation_status")
        focuses = assessment.get("proposed_focuses", [])
        focus = focuses[0] if isinstance(focuses, list) and focuses else None
        if status in {"confirmed", "corrected"} and isinstance(focus, dict):
            decision = focus.get("decision")
            rationale = focus.get("rationale", "sin razón registrada")
            if decision in PRIORITY_ORDER:
                lines.append(f"**Foco confirmado:** {decision.title()} — {rationale}")
                lines.append("")
                lines.append(
                    "Pide la evidencia detallada sólo cuando el procedimiento "
                    "correspondiente esté disponible."
                )
            else:
                lines.append(
                    "Confirma el foco del assessment antes de pedir información detallada."
                )
        elif assessment:
            lines.append("Confirma o corrige el assessment antes de elegir un foco.")
        else:
            lines.append(
                "Ejecuta `/escala-diagnose` para construir un assessment narrativo "
                "antes de elegir próximos pasos."
            )
    lines.append("")
    lines.append(
        "> Revisa el assessment con `/escala-diagnose` cuando cambie el contexto."
    )
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
    assessment = _read_assessment(base)

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

    # --- Build diagnosis / assessment section ---
    if scores:
        scores_body = _scores_table(scores)
        diagnosis_heading = "## 1. Diagnosis Scores"
        priority = _detect_priority(scores)
        if priority:
            priority_label = DECISION_LABELS.get(priority, priority.title())
            priority_cmd = ROUTING_RULES.get(priority, f"/escala-{priority}")
            scores_body += (
                f"\n\n**Priority focus:** {priority_label} — `{priority_cmd}`"
            )
    else:
        scores_body = _assessment_body(assessment)
        diagnosis_heading = "## 1. Diagnosis & Assessment"

    # --- Build next steps ---
    next_steps_body = _build_next_steps(scores, assessment)

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
        diagnosis_heading,
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
                "assessment" if not scores else "scores",
                "goal",
                "priorities",
                "tasks",
                "next_steps",
            ],
            "missing_optional": missing_optional,
        },
        "errors": [],
    }
