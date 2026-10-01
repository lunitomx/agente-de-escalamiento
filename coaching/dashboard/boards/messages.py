# pyright: strict
"""Owner-facing text of the board recommender (plain Spanish, no commands)."""

from __future__ import annotations

from coaching.dashboard.boards.models import (
    BoardProposal,
    DecisionOption,
    Feasibility,
    MetricStatus,
)

ASK_DECISION = (
    "¿Qué quieres decidir con ese tablero? Por ejemplo: en qué paso se te van "
    "los clientes, o si tu equipo puede con lo que tiene."
)

NO_PATTERN = (
    "Para eso todavía no tengo un tablero que te sirva de verdad, y no quiero "
    "inventarte uno. Si me dices qué quieres decidir, vemos qué datos ya tienes."
)

CASH_REPORT = (
    "Para tu dinero ya tienes tu reporte de caja: ahí ves lo que entra, lo que "
    "sale y lo que te queda. Te lo muestro en lugar de hacer otro tablero."
)
CASH_NO_REPORT = (
    "Para tu dinero ya existe el reporte de caja; todavía no lo has armado. "
    "Lo hacemos con tus números de caja, sin un tablero nuevo."
)
TRACKER = (
    "Tus prioridades y compromisos ya viven en tu lista de seguimiento. Te la "
    "muestro en lugar de hacer otro tablero."
)
TRACKER_MISSING = (
    "Tus prioridades se siguen en tu lista de seguimiento; todavía no la tienes. "
    "La armamos primero, sin un tablero nuevo."
)
PROGRESS = (
    "Para ver cómo vas ya tienes tu resumen de avance. Te lo muestro en lugar de "
    "hacer otro tablero."
)
RESEARCH = (
    "Lo que averiguamos de tu mercado ya está en tus reportes de investigación. "
    "Te los muestro en lugar de hacer otro tablero."
)
POSTPONED = (
    "Esos tableros me dijiste hace poco que no o que después. No te los vuelvo a "
    "proponer en un mes; si antes los quieres, sólo dime."
)

OPTIONS: tuple[DecisionOption, ...] = (
    DecisionOption(code="construir", label="Sí, ármalo."),
    DecisionOption(
        code="esperar",
        label="Todavía no: primero junto los datos que faltan (dime para qué fecha).",
    ),
    DecisionOption(code="no", label="No lo necesito."),
)

_STATUS: dict[MetricStatus, str] = {
    "conocido": "ya lo tienes",
    "no_comparable": "lo tienes, pero todavía no se puede comparar",
    "falta": "falta",
}


def _feasibility(kind: Feasibility, missing: list[str]) -> str:
    gaps = ", ".join(missing)
    if kind == "se_puede_hoy":
        return "Se puede hoy: ya tienes todos los datos."
    if kind == "necesita_datos":
        return f"Se puede con lo que tienes; lo demás se verá como «Falta»: {gaps}."
    return f"Todavía no: no hay ningún dato. Falta: {gaps}."


def proposals_text(proposals: list[BoardProposal]) -> str:
    """The proposals in chat, one block each, ending in the owner's choice."""
    count = "un tablero" if len(proposals) == 1 else "dos tableros"
    lines = [f"Te propongo {count}. Cada uno sirve para decidir algo concreto.", ""]
    for number, proposal in enumerate(proposals, start=1):
        lines += [
            f"**{number}. {proposal.title}**",
            f"- Te ayuda a decidir: {proposal.decision}",
            f"- Lo mira: {proposal.audience}. {proposal.cadence}.",
            "- Qué muestra:",
        ]
        for metric in proposal.metrics:
            lines.append(
                f"  - {metric.metric_definition}: de {metric.source}; "
                f"{metric.period.lower()}; {_STATUS[metric.status]}."
            )
        lines += [f"- {_feasibility(proposal.feasibility, proposal.missing)}", ""]
    lines.append("¿Qué hacemos?")
    lines += [f"- {option.label}" for option in OPTIONS]
    return "\n".join(lines)
