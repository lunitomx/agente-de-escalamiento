"""coaching.selector.formatter — markdown renderer for tool selection receipts.

No I/O. Accepts a SelectionReceipt plus the original EvidencePackage and returns
user-facing markdown matching the design examples.
"""

from __future__ import annotations

from coaching.core import DECISION_LABELS
from coaching.evidence.models import EvidencePackage, EvidenceSource

from .models import SelectionReceipt

_AREA_HINTS: dict[str, str] = {
    "cash": "una fuente financiera reciente (por ejemplo, el *Cash Conversion Cycle Worksheet*)",
    "execution": "registros de reuniones o prioridades recientes",
    "people": "worksheets de People completados",
    "strategy": "worksheets de Strategy como OPSP o 7 Strata",
}

_AREA_NEXT_STEP: dict[str, str] = {
    "cash": "profundizar en CCC, Power of One y aceleración de cash",
    "execution": "revisar ritmos, prioridades y Rockefeller Habits",
    "people": "revisar estructura, valores y talento",
    "strategy": "revisar OPSP, diferenciación y los 7 Strata",
}


def _source_display(source: EvidenceSource) -> str:
    """Format a source as 'Title (period)'."""
    period = f" ({source.period})" if source.period else ""
    return f"{source.title}{period}"


def _used_sources(
    receipt: SelectionReceipt, package: EvidencePackage
) -> list[EvidenceSource]:
    """Return the package sources whose ids appear in the receipt."""
    used_ids = set(receipt.evidence_used)
    return [source for source in package.sources if source.source_id in used_ids]


def format_selection(receipt: SelectionReceipt, package: EvidencePackage) -> str:
    """Render a tool-selected receipt as markdown."""
    area_label = DECISION_LABELS.get(receipt.area, receipt.area.title())
    used = _used_sources(receipt, package)
    evidence_line = ", ".join(_source_display(source) for source in used) or "—"

    lines = [
        f"## Herramienta seleccionada: {receipt.label}",
        "",
        f"**Área:** {area_label}  ",
        f"**Decisión:** {receipt.decision}  ",
        f"**Evidencia usada:** {evidence_line}  ",
        f"**Razón:** {receipt.reason}  ",
        "",
    ]

    if receipt.skills:
        primary_skill = receipt.skills[0]
        detail = _AREA_NEXT_STEP.get(receipt.area, "continuar el análisis")
        lines.append(f"Próximo paso: ejecutar `{primary_skill}` para {detail}.")
        lines.append("")

    return "\n".join(lines)


def format_clarify(
    receipt: SelectionReceipt,
    questions: list[str],
    package: EvidencePackage,  # noqa: ARG001 — kept for API symmetry
) -> str:
    """Render a clarify request when minimum evidence is missing."""
    area_label = DECISION_LABELS.get(receipt.area, receipt.area.title())
    hint = _AREA_HINTS.get(receipt.area, "evidencia relevante")

    lines = [
        "## Falta información para elegir una herramienta",
        "",
        f"Para analizar una decisión de **{area_label}** necesito al menos {hint}.",
        "",
    ]

    if questions:
        lines.append(questions[0])
        lines.append("")

    return "\n".join(lines)
