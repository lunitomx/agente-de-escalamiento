"""coaching.decision.formatter — pure markdown renderer for decision sheets.

No I/O. Accepts a structured draft dict, returns markdown string.
"""

from __future__ import annotations

from typing import Any

from coaching.core import owner_area_name


def format_draft(draft: dict[str, Any]) -> str:
    """Render a proposed decision sheet for user confirmation."""
    area_label = owner_area_name(draft.get("area"), capital=True)
    lines = [
        "## Ficha de decisión propuesta",
        "",
        f"**Decisión:** {draft.get('decision', '—')}",
        f"**Área:** {area_label}",
        f"**Horizonte:** {draft.get('horizon', '—')}",
        f"**Resultado esperado:** {draft.get('outcome', '—')}",
        "",
        "¿Confirmas que esta ficha refleja tu decisión? Responde **confirmar** "
        "o dime qué campo quieres corregir.",
        "",
    ]
    return "\n".join(lines)


def format_clarification(question: str) -> str:
    """Render a clarification question to the user."""
    return f"## Antes de continuar, necesito aclarar algo\n\n{question}\n"


def format_confirmed(draft: dict[str, Any]) -> str:
    """Render confirmation after persisting a decision sheet."""
    area_label = owner_area_name(draft.get("area"))
    lines = [
        "## Decisión confirmada",
        "",
        f"He registrado tu decisión en **{area_label}**:",
        "",
        f"- **Decisión:** {draft.get('decision', '—')}",
        f"- **Horizonte:** {draft.get('horizon', '—')}",
        f"- **Resultado esperado:** {draft.get('outcome', '—')}",
        "",
        "Ahora puedo armar el paquete de evidencia para ayudarte a avanzar.",
        "",
    ]
    return "\n".join(lines)
