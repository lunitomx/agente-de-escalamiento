"""Render a Execution Habits assessment into markdown."""

from __future__ import annotations

from .engine import HABITS, MISSING, ExecutionAssessment


def render_markdown(
    assessment: ExecutionAssessment,
    company_name: str = "",
    action_plan: list[str] | None = None,
) -> str:
    """Render the assessment using the same structure as the template."""
    score_by_id = {s.habit_id: s for s in assessment.scores}

    lines = [
        "# 10 Execution Habits — Evaluación",
        "",
    ]
    if company_name:
        lines.append(f"> Empresa: {company_name}")
        lines.append("")

    lines.extend(
        [
            "| # | Hábito | Score (1-5) | Notas |",
            "|---|--------|-------------|-------|",
        ]
    )

    for i, habit in enumerate(HABITS, 1):
        score_obj = score_by_id.get(habit["id"])
        score_str = (
            str(score_obj.score)
            if score_obj and score_obj.score is not None
            else MISSING
        )
        notes = score_obj.notes if score_obj and score_obj.notes else ""
        lines.append(f"| {i} | {habit['name']} | {score_str} | {notes} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Próximos pasos")
    lines.append("")
    if action_plan:
        for item in action_plan:
            lines.append(f"- {item}")
    else:
        lines.append("_Completa la evaluación y revisa los 3 hábitos más débiles._")

    return "\n".join(lines)
