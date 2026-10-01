# pyright: strict
"""Short, closed catalogue of board patterns by area (design S84.3 rule 3).

- ventas: conversion between stages, and customers who come back;
- caja: the existing cash report (no pattern here, see ``recommend``);
- equipo: load and progress **by area**, never an individual ranking;
- ejecucion: the existing tracker (no pattern here).

Area detection is a closed lexicon on whole words, accents and case removed.
"""

from __future__ import annotations

import re
import unicodedata

from pydantic import BaseModel, ConfigDict

from coaching.dashboard.boards.models import Area, BoardMetric

AREA_ORDER: tuple[Area, ...] = (
    "caja",
    "ventas",
    "equipo",
    "ejecucion",
    "progreso",
    "mercado",
)

AREA_WORDS: dict[Area, tuple[str, ...]] = {
    "caja": (
        "caja",
        "efectivo",
        "dinero",
        "flujo",
        "cobrar",
        "cobranza",
        "cobros",
        "pagos",
        "gastos",
        "margen",
        "nomina",
        "finanzas",
    ),
    "ventas": (
        "ventas",
        "venta",
        "vender",
        "vendo",
        "vendemos",
        "cliente",
        "clientes",
        "compran",
        "prospecto",
        "prospectos",
        "marketing",
        "pedidos",
        "cotizaciones",
    ),
    "equipo": ("equipo", "personas", "gente", "empleados", "colaboradores"),
    "ejecucion": (
        "prioridad",
        "prioridades",
        "pendientes",
        "tareas",
        "compromisos",
        "metas",
        "proyectos",
    ),
    "progreso": ("avance", "progreso", "como voy", "como vamos"),
    "mercado": ("mercado", "competencia", "competidor", "competidores"),
}


def normalize(text: str) -> str:
    """Lowercase, accents removed, only letters and digits, single spaces."""
    ascii_text = (
        unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    )
    return " ".join(re.sub(r"[^a-z0-9]+", " ", ascii_text.lower()).split())


def detect_area(text: str) -> Area | None:
    """First area (in ``AREA_ORDER``) whose words appear; ``None`` if none."""
    padded = f" {normalize(text)} "
    for area in AREA_ORDER:
        if any(f" {word} " in padded for word in AREA_WORDS[area]):
            return area
    return None


class BoardPattern(BaseModel):
    """A board the recommender may propose; metrics carry source and period."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    board_id: str
    area: Area
    title: str
    decision: str
    audience: str
    cadence: str
    metrics: tuple[BoardMetric, ...]
    needs_journey_stages: bool = False


_ASK = BoardMetric(
    metric_definition="Personas que preguntan",
    source="Tus mensajes o llamadas (por ejemplo, WhatsApp Business)",
    period="Por mes",
    how_to_get="Cuenta las conversaciones nuevas del mes.",
)
_BUY = BoardMetric(
    metric_definition="Clientes que compran",
    source="Tu registro de ventas o tu cuaderno",
    period="Por mes, el mismo mes",
    how_to_get="Cuenta las ventas del mes.",
)
_ASK_TO_BUY = BoardMetric(
    metric_definition="De cada 10 que preguntan, cuántos compran",
    source="Sale de las dos anteriores, del mismo mes",
    period="Por mes",
    how_to_get="Se calcula sólo si tienes las dos del mismo mes.",
)
_RETURN = BoardMetric(
    metric_definition="Clientes que volvieron a comprar",
    source="Tu registro de ventas o tu cuaderno",
    period="Por mes, el mismo mes",
    how_to_get="De los clientes del mes, cuenta los que ya te habían comprado.",
)
_RETURN_RATE = BoardMetric(
    metric_definition="De cada 10 clientes, cuántos regresan",
    source="Sale de las dos anteriores, del mismo mes",
    period="Por mes",
    how_to_get="Se calcula sólo si tienes las dos del mismo mes.",
)


def _by_area(name: str, how: str) -> BoardMetric:
    return BoardMetric(
        metric_definition=name,
        source="Tu lista de seguimiento de compromisos",
        period="Por semana",
        how_to_get=how,
    )


PATTERNS: dict[str, BoardPattern] = {
    pattern.board_id: pattern
    for pattern in (
        BoardPattern(
            board_id="ventas-etapas",
            area="ventas",
            title="Dónde se te van los clientes",
            decision=(
                "En qué paso trabajar primero para que más de los que preguntan "
                "terminen comprando."
            ),
            audience="Tú, como dueño",
            cadence="Cada semana",
            metrics=(_ASK, _BUY, _ASK_TO_BUY),
            needs_journey_stages=True,
        ),
        BoardPattern(
            board_id="ventas-regresan",
            area="ventas",
            title="Clientes que regresan",
            decision="Si vale la pena trabajar para que tus clientes vuelvan a comprar.",
            audience="Tú, como dueño",
            cadence="Cada mes",
            metrics=(_BUY, _RETURN, _RETURN_RATE),
            needs_journey_stages=True,
        ),
        BoardPattern(
            board_id="equipo-carga",
            area="equipo",
            title="Carga y avance del equipo, por área",
            decision=(
                "Si el equipo puede con lo que tiene o hay que repartir o pausar algo."
            ),
            audience="Tú y tus responsables de área",
            cadence="Cada semana",
            metrics=(
                _by_area(
                    "Compromisos abiertos por área",
                    "Cuenta los compromisos sin terminar de cada área.",
                ),
                _by_area(
                    "Compromisos cumplidos por área en la semana",
                    "Cuenta los que se terminaron esta semana en cada área.",
                ),
                _by_area(
                    "Compromisos atrasados por área",
                    "Cuenta los que pasaron su fecha sin terminarse en cada área.",
                ),
            ),
        ),
    )
}


def patterns_for(area: Area) -> list[BoardPattern]:
    """Patterns of one area, in catalogue order."""
    return [pattern for pattern in PATTERNS.values() if pattern.area == area]
