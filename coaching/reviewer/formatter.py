"""coaching.reviewer.formatter — markdown renderer for review reports.

No I/O. Accepts a ReviewReport and returns user-facing markdown that matches
the executive tone of the coaching loop.
"""

from __future__ import annotations

from coaching.core import DECISION_LABELS

from .models import ReviewFinding, ReviewReport

_SEVERITY_ICON = {
    "info": "✅",
    "warning": "⚠️",
    "critical": "❌",
}


def _format_finding(finding: ReviewFinding) -> str:
    icon = _SEVERITY_ICON.get(finding.severity, "•")
    return f"- {icon} {finding.message}"


def format_report(report: ReviewReport) -> str:
    """Render a review report as markdown, choosing the right section tone."""
    has_critical = any(finding.severity == "critical" for finding in report.findings)
    has_warning = any(finding.severity == "warning" for finding in report.findings)

    if has_critical:
        return _format_blocked(report)
    if has_warning:
        return _format_clarify(report)
    return _format_reviewed(report)


def _header_lines(report: ReviewReport) -> list[str]:
    area_label = DECISION_LABELS.get(report.area, report.area.title())
    tool_label = report.tool or "Ninguna"
    return [
        f"**Decisión:** {report.decision}  ",
        f"**Área:** {area_label}  ",
        f"**Herramienta:** {tool_label}  ",
        "",
    ]


def _findings_section(findings: list[ReviewFinding]) -> list[str]:
    if not findings:
        return []
    lines = ["### Hallazgos", ""]
    lines.extend(_format_finding(finding) for finding in findings)
    lines.append("")
    return lines


def _format_reviewed(report: ReviewReport) -> str:
    lines = [
        "## Revisión de calidad",
        "",
        "La recomendación puede avanzar.",
        "",
    ]
    lines.extend(_header_lines(report))
    lines.extend(_findings_section(report.findings))
    if not report.findings:
        lines.append("No hay advertencias críticas.")
        lines.append("")
    return "\n".join(lines)


def _format_clarify(report: ReviewReport) -> str:
    lines = [
        "## Revisión de calidad: falta información",
        "",
        "Se encontraron advertencias que deben resolverse antes de responder.",
        "",
    ]
    lines.extend(_header_lines(report))
    lines.extend(_findings_section(report.findings))
    if report.critical_questions:
        lines.append("### Próximo paso")
        lines.append("")
        lines.append(f"- {report.critical_questions[0]}")
        lines.append("")
    return "\n".join(lines)


def _format_blocked(report: ReviewReport) -> str:
    lines = [
        "## Revisión de calidad: bloqueada",
        "",
        "Se detectó un problema crítico que impide generar una recomendación segura.",
        "",
    ]
    lines.extend(_header_lines(report))
    lines.extend(_findings_section(report.findings))
    return "\n".join(lines)
