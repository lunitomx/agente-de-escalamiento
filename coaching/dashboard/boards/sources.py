# pyright: strict
"""Where board numbers come from (E84 S84.4): local facts plus the journey.

The journey saved by S84.2 (``.escala/my-company/journey/journey.yaml``) holds
stage counts, each with its month and local source. They become board facts:

- "pregunta" -> "Personas que preguntan", "compra" -> "Clientes que compran",
  "regresa" -> "Clientes que volvieron a comprar";
- a guess (``supuesto``) or a range (``upper``) is kept but marked not
  comparable, so it is never shown as a number;
- "de cada 10" ratios only when both counts are comparable, from the same
  month and the first is not zero.

An explicit local fact for the same metric wins over the journey.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from coaching.evidence.facts import Fact
from coaching.journey.decision import load_saved
from coaching.journey.models import Journey, StageCount
from coaching.journey.view import period_label

STAGE_METRIC: dict[str, str] = {
    "pregunta": "Personas que preguntan",
    "compra": "Clientes que compran",
    "regresa": "Clientes que volvieron a comprar",
}
RATIOS: tuple[tuple[str, str, str], ...] = (
    ("pregunta", "compra", "De cada 10 que preguntan, cuántos compran"),
    ("compra", "regresa", "De cada 10 clientes, cuántos regresan"),
)
JOURNEY_NOTE = "recorrido del cliente"


def _comparable(count: StageCount) -> bool:
    return count.origin != "supuesto" and count.upper is None


def _fact(name: str, count: StageCount) -> Fact:
    return Fact(
        metric_definition=name,
        period=period_label(count.period),
        source=count.source,
        confidence="high" if count.origin == "dato_con_periodo" else "medium",
        comparable=_comparable(count),
        value=count.value,
        notes=JOURNEY_NOTE,
    )


def journey_facts(journey: Journey) -> list[Fact]:
    """Board facts from the journey's stage counts; nothing is estimated."""
    counts = {s.stage: s.count for s in journey.stages if s.count is not None}
    facts = [
        _fact(name, counts[stage])
        for stage, name in STAGE_METRIC.items()
        if stage in counts
    ]
    for first, second, name in RATIOS:
        top, bottom = counts.get(first), counts.get(second)
        if (
            top is None
            or bottom is None
            or not (_comparable(top) and _comparable(bottom))
            or top.period != bottom.period
            or top.value == 0
        ):
            continue
        facts.append(
            Fact(
                metric_definition=name,
                period=period_label(top.period),
                source=f"{STAGE_METRIC[first]} y {STAGE_METRIC[second]}",
                confidence="medium",
                value=round(bottom.value * 10 / top.value, 1),
                notes=JOURNEY_NOTE,
            )
        )
    return facts


def metric_facts(base: Path, explicit: Sequence[Fact]) -> list[Fact]:
    """Explicit facts plus the saved journey's, explicit first for each metric."""
    saved = load_saved(base)
    if saved is None:
        return list(explicit)
    taken = {fact.metric_definition.casefold() for fact in explicit}
    extra = [
        fact
        for fact in journey_facts(saved.journey)
        if fact.metric_definition.casefold() not in taken
    ]
    return [*explicit, *extra]
