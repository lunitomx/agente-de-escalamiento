"""Deterministic local visual evidence for E38 S38.4."""

from __future__ import annotations

import hashlib
import html
import json
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from escala_server.workspace.authority import WorkspaceConfig, validate_workspace

from .cash_decision import CashDecision


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CashReportArtifact(_StrictModel):
    schema_version: int = 1
    report_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: str = Field(min_length=1, max_length=20)
    html_path: str = Field(
        pattern=r"^\.escala-cash-reports/[0-9a-f]{64}/cash-report\.html$"
    )
    markdown_path: str = Field(
        pattern=r"^\.escala-cash-reports/[0-9a-f]{64}/cash-report\.md$"
    )
    json_path: str = Field(
        pattern=r"^\.escala-cash-reports/[0-9a-f]{64}/cash-report\.json$"
    )
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def write_cash_report(
    config: WorkspaceConfig,
    decision: CashDecision,
) -> CashReportArtifact:
    """Write a self-contained local report under installer-machine data_root."""

    if validate_workspace(config).status != "pass":
        raise ValueError("workspace_invalid")
    payload = decision.model_dump(mode="json")
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    report_id = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    relative_dir = Path(".escala-cash-reports") / report_id
    output_dir = config.data_root.expanduser().resolve(strict=False) / relative_dir
    html_path = relative_dir / "cash-report.html"
    markdown_path = relative_dir / "cash-report.md"
    json_path = relative_dir / "cash-report.json"
    html_content = _render_html(decision)
    markdown_content = _render_markdown(decision)
    json_content = (
        json.dumps(
            {"schema_version": 1, "report_id": report_id, "decision": payload},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    _atomic_write(output_dir / html_path.name, html_content)
    _atomic_write(output_dir / markdown_path.name, markdown_content)
    _atomic_write(output_dir / json_path.name, json_content)
    artifact_sha256 = hashlib.sha256(
        (html_content + markdown_content + json_content).encode("utf-8")
    ).hexdigest()
    return CashReportArtifact(
        report_id=report_id,
        status=decision.status,
        html_path=html_path.as_posix(),
        markdown_path=markdown_path.as_posix(),
        json_path=json_path.as_posix(),
        artifact_sha256=artifact_sha256,
    )


def render_cash_report_receipt_json(artifact: CashReportArtifact) -> str:
    """Render artifact metadata only; values remain in the local report."""

    return json.dumps(
        {
            "schema_version": artifact.schema_version,
            "report_id": artifact.report_id,
            "status": artifact.status,
            "html_path": artifact.html_path,
            "markdown_path": artifact.markdown_path,
            "json_path": artifact.json_path,
            "artifact_sha256": artifact.artifact_sha256,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def render_cash_report_receipt_markdown(artifact: CashReportArtifact) -> str:
    """Render a bounded local artifact receipt."""

    return "\n".join(
        [
            "# Cash Report Artifact Receipt",
            "",
            f"- report_id: {artifact.report_id}",
            f"- status: {artifact.status}",
            f"- html_path: {artifact.html_path}",
            f"- markdown_path: {artifact.markdown_path}",
            f"- json_path: {artifact.json_path}",
            f"- artifact_sha256: {artifact.artifact_sha256}",
            "",
        ]
    )


def _render_html(decision: CashDecision) -> str:
    title = "ESCALA — Evidencia de Cash"
    status = html.escape(decision.status)
    sections: list[str] = [
        "<!doctype html>",
        '<html lang="es"><head><meta charset="utf-8">',
        f"<title>{title}</title>",
        "<style>body{font-family:system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#17202a}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:1rem}"
        ".card{border:1px solid #d8dee4;border-radius:10px;padding:1rem;background:#fff}"
        ".ok{color:#087f5b}.blocked{color:#b42318}.muted{color:#667085}"
        "table{width:100%;border-collapse:collapse;margin:1rem 0}th,td{border-bottom:1px solid #eaecf0;text-align:left;padding:.55rem}"
        "code{font-size:.9em}body{background:#f8fafc}</style></head><body>",
        f"<h1>{title}</h1><p class='{status}'><strong>Estado: {status}</strong></p>",
    ]
    if decision.baseline is not None and decision.assumptions is not None:
        metrics = decision.baseline.metrics
        sections.append(
            "<h2>Ciclo de Conversión de Efectivo</h2><h3>Panorama</h3><div class='grid'>"
        )
        for key, label in (
            ("ccc_days", "CCC (días)"),
            ("dso_days", "DSO"),
            ("dio_days", "DIO"),
            ("dpo_days", "DPO"),
            ("profit_margin_pct", "Margen neto (%)"),
        ):
            if key in metrics:
                sections.append(
                    f"<div class='card'><div class='muted'>{label}</div><strong>{html.escape(str(round(metrics[key], 2)))}</strong></div>"
                )
        sections.append("</div>")
        sections.append(
            "<p class='muted'>Supuestos: "
            f"{decision.assumptions.days_per_year} días/año; factor de anualización "
            f"{decision.assumptions.annualization_factor}; periodo "
            f"{html.escape(decision.assumptions.period)}; moneda "
            f"{html.escape(decision.assumptions.currency)}; unidad "
            f"{html.escape(decision.assumptions.unit)}.</p>"
        )
    sections.append("<h2>Escenarios</h2>")
    if decision.scenarios:
        sections.append(
            "<table><thead><tr><th>Escenario</th><th>Impacto cash</th><th>Impacto EBIT</th><th>Ajustes</th></tr></thead><tbody>"
        )
        for scenario in decision.scenarios:
            adjustments = (
                ", ".join(
                    f"{html.escape(key)}={value}"
                    for key, value in scenario.adjustments.items()
                )
                or "baseline"
            )
            sections.append(
                f"<tr><td>{html.escape(scenario.scenario_id)}</td><td>{scenario.combined_cash_impact:,.2f}</td>"
                f"<td>{scenario.combined_ebit_impact:,.2f}</td><td>{adjustments}</td></tr>"
            )
        sections.append("</tbody></table>")
    else:
        sections.append(
            "<p class='muted'>No hay escenarios calculables con la evidencia actual.</p>"
        )
    sections.append("<h2>Hallazgos y preguntas</h2>")
    if decision.findings:
        sections.append(
            "<ul>"
            + "".join(
                f"<li>{html.escape(finding)}</li>" for finding in decision.findings
            )
            + "</ul>"
        )
    else:
        sections.append("<p class='ok'>Sin hallazgos bloqueantes.</p>")
    if decision.questions:
        sections.append(
            "<ul>"
            + "".join(
                f"<li>{html.escape(question.prompt)} — opciones: {html.escape(', '.join(question.options))}</li>"
                for question in decision.questions
            )
            + "</ul>"
        )
    if decision.recommendations:
        sections.append(
            "<h2>Recomendaciones de escenario</h2><ul>"
            + "".join(
                f"<li>{html.escape(recommendation)}</li>"
                for recommendation in decision.recommendations
            )
            + "</ul>"
        )
    else:
        sections.append(
            "<p class='blocked'>No hay recomendaciones disponibles con la evidencia actual.</p>"
        )
    sections.append("<h2>Evidencia de inputs</h2>")
    if decision.validated_inputs is not None:
        sections.append(
            "<table><thead><tr><th>Hoja</th><th>Rango</th><th>Periodo</th><th>Transformación</th></tr></thead><tbody>"
        )
        for provenance in decision.validated_inputs.provenance:
            sections.append(
                f"<tr><td>{html.escape(provenance.sheet)}</td><td><code>{html.escape(provenance.cell_range)}</code></td>"
                f"<td>{html.escape(provenance.period)}</td><td>{html.escape(provenance.transformation)}</td></tr>"
            )
        sections.append("</tbody></table>")
    else:
        sections.append(
            "<p class='muted'>No hay inputs validados; revisar preguntas y hallazgos.</p>"
        )
    sections.extend(
        [
            "<footer class='muted'>Generado localmente por ESCALA; no es asesoría financiera.</footer>",
            "</body></html>",
        ]
    )
    return "".join(sections)


def _render_markdown(decision: CashDecision) -> str:
    lines = [
        "# ESCALA — Evidencia de Cash",
        "",
        f"- Estado: `{decision.status}`",
        f"- Hallazgos: {', '.join(decision.findings) or 'ninguno'}",
        "",
        "## Escenarios",
    ]
    if decision.scenarios:
        lines.extend(
            f"- `{scenario.scenario_id}`: cash={scenario.combined_cash_impact:.2f}, EBIT={scenario.combined_ebit_impact:.2f}"
            for scenario in decision.scenarios
        )
    else:
        lines.append("- No hay escenarios calculables con la evidencia actual.")
    lines.extend(["", "## Preguntas"])
    if decision.questions:
        lines.extend(
            f"- {question.prompt} ({', '.join(question.options)})"
            for question in decision.questions
        )
    else:
        lines.append("- Ninguna")
    lines.extend(["", "## Recomendaciones"])
    lines.extend(f"- {recommendation}" for recommendation in decision.recommendations)
    if not decision.recommendations:
        lines.append("- No hay recomendaciones disponibles con la evidencia actual.")
    lines.extend(["", "## Evidencia"])
    if decision.validated_inputs is not None:
        lines.extend(
            f"- `{provenance.sheet}` `{provenance.cell_range}` — {provenance.period}; {provenance.transformation}"
            for provenance in decision.validated_inputs.provenance
        )
    else:
        lines.append("- No hay inputs validados.")
    return "\n".join(lines) + "\n"


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)
