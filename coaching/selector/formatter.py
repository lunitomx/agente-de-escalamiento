"""coaching.selector.formatter — markdown renderer for tool selection receipts.

No I/O. Accepts a SelectionReceipt plus the original EvidencePackage and returns
user-facing markdown matching the design examples.
"""

from __future__ import annotations

from coaching.core import owner_area_name
from coaching.evidence.models import EvidencePackage, EvidenceSource

from .models import SelectionReceipt

_AREA_HINTS: dict[str, str] = {
    "cash": "tus números recientes (ventas, cobros y pagos de un mes)",
    "execution": "notas de tus reuniones o tus prioridades recientes",
    "people": "quién hace qué en tu equipo",
    "strategy": "a quién le vendes y por qué te eligen",
}

# S86.2: the next step is a plain question; the procedure ids stay internal
# in ``receipt.skills`` and are never shown to the owner.
_AREA_NEXT_STEP: dict[str, str] = {
    "cash": "¿Vemos cuántos días tardas en cobrar y cuánto dinero liberas si cobras antes?",
    "execution": "¿Revisamos tus prioridades y cómo las sigues cada semana?",
    "people": "¿Revisamos quién es responsable de cada tarea clave en tu equipo?",
    "strategy": "¿Revisamos quiénes son tus mejores clientes y por qué te eligen?",
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
    area_label = owner_area_name(receipt.area, capital=True)
    used = _used_sources(receipt, package)
    evidence_line = ", ".join(_source_display(source) for source in used) or "—"

    lines = [
        f"## Lo que vamos a revisar: {owner_area_name(receipt.area)}",
        "",
        f"**Área:** {area_label}  ",
        f"**Decisión:** {receipt.decision}  ",
        f"**Evidencia usada:** {evidence_line}  ",
        f"**Razón:** {receipt.reason}  ",
        "",
    ]

    if receipt.skills:
        detail = _AREA_NEXT_STEP.get(receipt.area, "¿Seguimos con el análisis?")
        lines.append(f"Próximo paso: {detail}")
        lines.append("")

    return "\n".join(lines)


def format_clarify(
    receipt: SelectionReceipt,
    questions: list[str],
    package: EvidencePackage,  # noqa: ARG001 — kept for API symmetry
) -> str:
    """Render a clarify request when minimum evidence is missing."""
    area_label = owner_area_name(receipt.area)
    hint = _AREA_HINTS.get(receipt.area, "un dato reciente de tu negocio")

    lines = [
        "## Falta información",
        "",
        f"Para revisar **{area_label}** necesito al menos {hint}.",
        "",
    ]

    if questions:
        lines.append(questions[0])
        lines.append("")

    return "\n".join(lines)
