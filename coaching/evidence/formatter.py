"""coaching.evidence.formatter — markdown renderer and structured summary builder.

No I/O. Accepts an EvidencePackage and returns user-facing markdown plus a
structured summary for downstream modules.
"""

from __future__ import annotations

from typing import Any

from coaching.core import DECISION_LABELS

from .models import EvidencePackage, EvidenceSource


def _format_source(source: EvidenceSource) -> str:
    """Format a single source as a markdown bullet."""
    confidence_label = {
        "high": "Alta",
        "medium": "Media",
        "low": "Baja",
    }.get(source.confidence, source.confidence)
    period = f" ({source.period})" if source.period else ""
    return (
        f"- **{source.title}**{period} — confianza {confidence_label}: {source.reason}"
    )


def format_package(package: EvidencePackage) -> str:
    """Render an evidence package as user-facing markdown."""
    area_label = DECISION_LABELS.get(
        package.decision_ref.area, package.decision_ref.area.title()
    )
    lines = [
        f"## Paquete de evidencia para: {package.decision_ref.decision}",
        "",
        f"**Área:** {area_label}  ",
        f"**Horizonte:** {package.decision_ref.horizon}  ",
        f"**Resultado esperado:** {package.decision_ref.outcome}",
        "",
    ]

    if package.sources:
        lines.append("### Fuentes disponibles")
        lines.append("")
        for source in package.sources:
            lines.append(_format_source(source))
        lines.append("")

    if package.not_trustworthy:
        lines.append("### Fuentes no confiables todavía")
        lines.append("")
        for source in package.not_trustworthy:
            lines.append(_format_source(source))
        lines.append("")

    if package.missing:
        lines.append("### Evidencia ausente")
        lines.append("")
        for source in package.missing:
            lines.append(_format_source(source))
        lines.append("")

    if package.questions:
        lines.append("### Preguntas para completar el análisis")
        lines.append("")
        for question in package.questions:
            lines.append(f"- {question}")
        lines.append("")

    if not package.sources and not package.missing and not package.not_trustworthy:
        lines.append("No se encontró evidencia local para esta decisión.")
        lines.append("")

    return "\n".join(lines)


def package_summary(package: EvidencePackage) -> dict[str, Any]:
    """Return a structured summary for S43.3."""
    return {
        "decision_ref": package.decision_ref.model_dump(),
        "source_count": len(package.sources),
        "missing_count": len(package.missing),
        "not_trustworthy_count": len(package.not_trustworthy),
        "questions": package.questions,
        "ready_for_analysis": len(package.sources) > 0 and len(package.missing) == 0,
    }
