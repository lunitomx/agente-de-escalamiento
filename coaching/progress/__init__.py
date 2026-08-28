"""Progress dashboard that accepts narrative assessment or legacy optional scores."""

from __future__ import annotations

from pathlib import Path

from ..core import read_yaml

DECISIONS = ["people", "strategy", "execution", "cash"]

DECISION_LABELS = {
    "people": "People — Personas",
    "strategy": "Strategy — Estrategia",
    "execution": "Execution — Ejecución",
    "cash": "Cash — Efectivo",
}

DECISION_ORDER = ["people", "strategy", "execution", "cash"]
_CONFIRMED_ASSESSMENTS = {"confirmed", "corrected"}


def _get_worksheets(base_path: Path) -> tuple[list[dict], dict[str, dict]]:
    """Load all worksheets and completed ones."""
    registry_path = base_path / ".escala" / "knowledge" / "registry" / "worksheets.yaml"
    registry = read_yaml(registry_path)
    all_ws = registry.get("worksheets", [])

    wdir = base_path / ".escala" / "my-company" / "worksheets"
    completed = {}
    if wdir.exists():
        for file_path in wdir.glob("*.yaml"):
            data = read_yaml(file_path)
            worksheet_id = data.get("worksheet_id") if data else file_path.stem
            if data and data.get("status") == "completed":
                completed[worksheet_id] = data

    return all_ws, completed


def _narrative_context(profile: dict) -> tuple[dict | None, str | None]:
    """Return the approved narrative assessment and its selected focus, if any."""
    assessment = profile.get("narrative_assessment")
    if not isinstance(assessment, dict):
        return None, None
    status = assessment.get("confirmation_status")
    focuses = assessment.get("proposed_focuses")
    if status not in _CONFIRMED_ASSESSMENTS or not isinstance(focuses, list):
        return assessment, None
    for focus in focuses:
        if isinstance(focus, dict) and focus.get("decision") in DECISION_ORDER:
            return assessment, focus["decision"]
    return assessment, None


def _append_narrative_summary(lines: list[str], assessment: dict | None) -> None:
    """Render a compact narrative context without inventing a numeric score."""
    lines.extend(["### Assessment narrativo", ""])
    if assessment is None:
        lines.append(
            "Aún no hay un assessment. Cuéntame qué está pasando y construiremos "
            "uno antes de pedir datos detallados."
        )
        return
    summary = assessment.get("company_summary")
    if isinstance(summary, str) and summary.strip():
        lines.append(summary.strip())
    status = assessment.get("confirmation_status", "pending")
    lines.append(f"- Estado de confirmación: **{status}**")
    for focus in assessment.get("proposed_focuses", []):
        if isinstance(focus, dict) and focus.get("decision") in DECISION_ORDER:
            rationale = focus.get("rationale", "sin razón registrada")
            lines.append(
                f"- Foco propuesto: **{focus['decision'].title()}** — {rationale}"
            )


def run(context: dict) -> dict:
    """Generate a progress dashboard without requiring a numeric baseline."""
    base = Path(context.get("base_path", "."))
    profile_path = base / ".escala" / "agent" / "memory" / "company-profile.yaml"
    profile = read_yaml(profile_path)
    scores = context.get("scores", profile.get("scores", {}))
    if not isinstance(scores, dict):
        scores = {}
    assessment, narrative_focus = _narrative_context(profile)

    all_ws, completed = _get_worksheets(base)
    if not all_ws:
        return {
            "output": "No hay worksheets registrados en la ontología. Verifica E6.",
            "artifacts": {},
            "errors": ["Empty worksheet registry"],
        }

    lines = ["## 📊 Dashboard de Progreso", ""]
    if scores:
        lines.extend(["### Calificación cuantitativa opcional", ""])
        lines.extend(["| Decisión | Score | Nivel |", "|----------|-------|-------|"])
        level_labels = {
            1: "🔴 No iniciado",
            2: "🟠 Ad hoc",
            3: "🟡 Emergente",
            4: "🟢 Establecido",
            5: "⭐ Optimizado",
        }
        for decision in DECISION_ORDER:
            score = scores.get(decision, 0)
            lines.append(
                f"| {DECISION_LABELS.get(decision, decision)} | {score} | "
                f"{level_labels.get(score, '—')} |"
            )
        lines.append("")
    else:
        _append_narrative_summary(lines, assessment)
        lines.append("")

    lines.extend(["### Worksheets por Decisión", ""])
    for decision in DECISION_ORDER:
        decision_worksheets = [
            worksheet for worksheet in all_ws if worksheet.get("decision") == decision
        ]
        total = len(decision_worksheets)
        done = sum(
            1 for worksheet in decision_worksheets if worksheet["id"] in completed
        )
        percentage = round((done / total * 100)) if total > 0 else 0
        lines.extend(
            [
                f"**{DECISION_LABELS.get(decision, decision)}:** {done}/{total} ({percentage}%)",
                "",
            ]
        )
        for worksheet in decision_worksheets:
            lines.append(
                f"- {'✅' if worksheet['id'] in completed else '⬜'} {worksheet['name']}"
            )
        lines.append("")

    lowest_score_focus = min(
        [decision for decision in DECISION_ORDER if scores.get(decision, 0) > 0],
        key=lambda decision: scores.get(decision, 0),
        default=None,
    )
    focus = lowest_score_focus or narrative_focus
    if focus:
        focus_worksheets = [
            worksheet
            for worksheet in all_ws
            if worksheet.get("decision") == focus and worksheet["id"] not in completed
        ]
        if focus_worksheets:
            next_worksheet = focus_worksheets[0]
            source = (
                "calificación opcional"
                if lowest_score_focus
                else "assessment confirmado"
            )
            lines.extend(
                [
                    "### Siguiente Sugerido",
                    f"- {next_worksheet['name']} (`{next_worksheet['id']}`) en {DECISION_LABELS[focus]}",
                    f"- Fuente del foco: {source}",
                    f"- Dificultad: {next_worksheet.get('difficulty', '—')} | Tiempo: {next_worksheet.get('time_estimate', '—')}",
                    f"- Usa `/escala-worksheet {next_worksheet['id']}` para empezar",
                    "",
                ]
            )

    if scores:
        lines.append(
            "> Puedes revisar la calificación opcional con `/escala-diagnose`; "
            "la conversación y la evidencia siguen siendo la fuente principal."
        )
    elif assessment and narrative_focus is None:
        lines.append(
            "> Confirma o corrige el assessment antes de elegir dónde profundizar."
        )

    total_all = sum(
        len(
            [worksheet for worksheet in all_ws if worksheet.get("decision") == decision]
        )
        for decision in DECISION_ORDER
    )
    done_all = sum(1 for worksheet in all_ws if worksheet["id"] in completed)
    overall_percentage = round((done_all / total_all * 100)) if total_all > 0 else 0

    return {
        "output": "\n".join(lines),
        "artifacts": {
            "total_worksheets": total_all,
            "completed_worksheets": done_all,
            "completion_pct": overall_percentage,
            "assessment_status": assessment.get("confirmation_status")
            if assessment
            else None,
            "focus_source": (
                "score"
                if lowest_score_focus
                else "narrative"
                if narrative_focus
                else None
            ),
            "per_decision": {
                decision: {
                    "score": scores.get(decision),
                    "total": len(
                        [
                            worksheet
                            for worksheet in all_ws
                            if worksheet.get("decision") == decision
                        ]
                    ),
                    "completed": sum(
                        1
                        for worksheet in all_ws
                        if worksheet.get("decision") == decision
                        and worksheet["id"] in completed
                    ),
                }
                for decision in DECISION_ORDER
            },
        },
        "errors": [],
    }


def _main() -> None:
    """Minimal module entry point for ``python -m coaching.progress``."""
    result = run({})
    if result.get("output"):
        print(result["output"])
    for error in result.get("errors", []):
        print(error)
