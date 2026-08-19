"""Local Markdown and JSON export for the E49 diagnostic result."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from coaching.core import ensure_dir
from coaching.diagnose import DiagnosticIntake, score_diagnostic
from coaching.diagnose.models import DiagnosticResult
from coaching.diagnose.result import build_diagnostic_result


def _percent(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "—"
    return f"{numerator / denominator:.0%}"


def render_diagnostic_result(result: DiagnosticResult) -> str:
    """Render all explainability fields needed for a user-facing result."""
    diagnosis = result.diagnosis
    lines = [
        "# Diagnóstico de Escala",
        "",
        f"**Generado:** {result.generated_at}",
        f"**Foco:** {diagnosis.focus or 'Pendiente de evidencia'}",
        f"**Regla:** {diagnosis.selection_rule}",
        "",
        "## Scorecard",
        "",
        "| Decisión | Score | Cobertura | Confianza | Evidencia | N/A |",
        "|---|---:|---:|---|---:|---:|",
    ]
    for decision, score in diagnosis.scores.items():
        value = "—" if score.score is None else f"{score.score:.1f}/5"
        lines.append(
            f"| {decision} | {value} | {score.coverage:.0%} | {score.confidence} | "
            f"{len(score.evidence_ids)} | {score.excluded} |"
        )

    lines.extend(["", "## Evidencia del foco", ""])
    if diagnosis.focus_evidence_ids:
        lines.extend(
            f"- `{evidence_id}`" for evidence_id in diagnosis.focus_evidence_ids
        )
    else:
        lines.append("No hay evidencia suficiente para explicar un foco.")

    if result.funnel is not None:
        funnel = result.funnel
        lines.extend(
            [
                "",
                "## Funnel del periodo",
                "",
                "| Etapa | Cantidad | Conversión |",
                "|---|---:|---:|",
                f"| Prospectos | {funnel.prospects if funnel.prospects is not None else '—'} | — |",
                f"| Conversaciones | {funnel.conversations if funnel.conversations is not None else '—'} | {_percent(funnel.conversations or 0, funnel.prospects or 0)} |",
                f"| Propuestas | {funnel.proposals if funnel.proposals is not None else '—'} | {_percent(funnel.proposals or 0, funnel.conversations or 0)} |",
                f"| Cierres | {funnel.wins if funnel.wins is not None else '—'} | {_percent(funnel.wins or 0, funnel.proposals or 0)} |",
            ]
        )

    lines.extend(
        [
            "",
            "## Ruta de 90 días",
            "",
            "| Trimestre | Decisión | Acción | Dueño | Métrica |",
            "|---|---|---|---|---|",
        ]
    )
    for action in result.route:
        lines.append(
            f"| {action.quarter} | {action.decision} | {action.action} | "
            f"{action.owner or 'Por confirmar'} | {action.metric or 'Por confirmar'} |"
        )
    lines.append("")
    return "\n".join(lines)


def run_diagnostic(context: Mapping[str, Any]) -> dict[str, Any]:
    """Validate intake, build result, and write local Markdown/JSON artifacts."""
    raw_intake = context.get("intake")
    if raw_intake is None:
        return {"output": "", "artifacts": {}, "errors": ["intake is required"]}
    try:
        intake = (
            raw_intake
            if isinstance(raw_intake, DiagnosticIntake)
            else DiagnosticIntake.model_validate(raw_intake)
        )
        diagnosis = score_diagnostic(intake)
        result = build_diagnostic_result(
            intake,
            diagnosis,
            route=context.get("route"),
            generated_at=context.get("generated_at"),
        )
    except (TypeError, ValueError) as exc:
        return {"output": "", "artifacts": {}, "errors": [str(exc)]}

    base = Path(str(context.get("base_path", ".")))
    generated = result.generated_at.isoformat()
    export_dir = ensure_dir(base / ".escala" / "my-company" / "exports")
    markdown_path = export_dir / f"{generated}-diagnostic.md"
    json_path = export_dir / f"{generated}-diagnostic.json"
    markdown_path.write_text(render_diagnostic_result(result), encoding="utf-8")
    json_path.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "output": f"Diagnostic generated: {markdown_path}",
        "artifacts": {
            "diagnostic_path": str(markdown_path),
            "diagnostic_json_path": str(json_path),
            "result": result.model_dump(mode="json"),
        },
        "errors": [],
    }
