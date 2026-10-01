# pyright: strict
"""What the owner reads about his journey (E84 S84.2), in plain Spanish.

- A missing value says "falta"; nothing is estimated.
- "Dónde se pierden más" compares only two consecutive stages counted in the
  same month; otherwise it says it cannot be known yet.
- A friction without ``clientes_dijeron`` evidence says it is what the owner
  believes and that customers were not asked.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict

from coaching.diagnose.models import FunnelMetrics
from coaching.journey.interview import STAGE_LABEL, Stage
from coaching.journey.models import Journey, JourneyStage, StageCount

_MONTHS = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)
# Stage -> FunnelMetrics field; "recibe" and "regresa" have no funnel field.
_FUNNEL: dict[Stage, str] = {
    "se_entera": "prospects",
    "pregunta": "conversations",
    "compra": "wins",
}
NOT_ASKED = "Esto es lo que tú crees: no se lo hemos preguntado a clientes."
LOSS_UNKNOWN = (
    "Todavía no se puede saber dónde se pierden más: falta contar dos pasos "
    "seguidos en el mismo mes."
)


class Loss(BaseModel):
    """The biggest loss between two consecutive stages of the same month."""

    model_config = ConfigDict(extra="forbid")

    from_stage: Stage
    to_stage: Stage
    high: StageCount
    low: StageCount


def period_label(period: str) -> str:
    """``"2026-09"`` -> ``"septiembre de 2026"``."""
    year, month = period.split("-")
    return f"{_MONTHS[int(month) - 1]} de {year}"


def spanish_date(value: date) -> str:
    return f"{value.day} de {_MONTHS[value.month - 1]} de {value.year}"


def spoken(count: StageCount) -> str:
    if count.upper is not None:
        return f"entre {count.value} y {count.upper}"
    return f"unos {count.value}" if count.origin == "supuesto" else str(count.value)


def _middle(count: StageCount) -> float:
    """Only to rank losses; never shown or stored as the owner's number."""
    return count.value if count.upper is None else (count.value + count.upper) / 2


def biggest_loss(journey: Journey) -> Loss | None:
    """The biggest drop between consecutive stages counted in the same month."""
    best: tuple[float, Loss] | None = None
    for high_stage, low_stage in zip(journey.stages, journey.stages[1:], strict=False):
        high, low = high_stage.count, low_stage.count
        if high is None or low is None or high.period != low.period:
            continue
        if _middle(high) <= 0:
            continue
        lost = (_middle(high) - _middle(low)) / _middle(high)
        if lost > 0 and (best is None or lost > best[0]):
            best = (
                lost,
                Loss(
                    from_stage=high_stage.stage,
                    to_stage=low_stage.stage,
                    high=high,
                    low=low,
                ),
            )
    return None if best is None else best[1]


def loss_line(journey: Journey) -> str:
    loss = biggest_loss(journey)
    if loss is None:
        return LOSS_UNKNOWN
    return (
        f"Donde más se pierden es entre «{STAGE_LABEL[loss.from_stage]}» y "
        f"«{STAGE_LABEL[loss.to_stage]}»: de {spoken(loss.high)} a "
        f"{spoken(loss.low)} en {period_label(loss.high.period)}."
    )


def _common_period(journey: Journey) -> str | None:
    periods = {item.count.period for item in journey.stages if item.count is not None}
    return next(iter(periods)) if len(periods) == 1 else None


def missing_lines(journey: Journey) -> list[str]:
    """Every gap, as "<etapa>: falta ...". Never a guessed value."""
    period = _common_period(journey)
    when = f" en {period_label(period)}" if period else ""
    lines: list[str] = []
    for item in journey.stages:
        label = STAGE_LABEL[item.stage]
        if item.touchpoint is None:
            lines.append(f"{label}: falta qué pasa.")
        if item.count is None:
            lines.append(f"{label}: falta cuántos{when}.")
    return lines


def _friction_note(item: JourneyStage) -> str:
    heard = [ev for ev in item.evidence if ev.origin == "clientes_dijeron"]
    if not heard:
        return NOT_ASKED
    first = heard[0]
    if first.asked_on is None or first.asked_count is None:
        return NOT_ASKED
    return (
        f"Se lo preguntaste a {first.asked_count} clientes el "
        f"{spanish_date(first.asked_on)}."
    )


def _count_line(item: JourneyStage) -> str | None:
    count = item.count
    if count is None:
        return None
    source = (
        count.source if count.origin != "supuesto" else f"aproximado, {count.source}"
    )
    return (
        f"{STAGE_LABEL[item.stage]}: {spoken(count)} en "
        f"{period_label(count.period)} ({source})."
    )


def summary(journey: Journey) -> str:
    """The journey in a few short lines: counts, gaps, frictions, the loss."""
    lines = [line for item in journey.stages if (line := _count_line(item))]
    lines += missing_lines(journey)
    for item in journey.stages:
        if item.friction:
            lines.append(
                f"Lo que frena en «{STAGE_LABEL[item.stage]}»: {item.friction}. "
                f"{_friction_note(item)}"
            )
    lines.append(loss_line(journey))
    return "\n".join(f"- {line}" for line in lines)


def to_funnel(journey: Journey) -> FunnelMetrics | None:
    """Exact counts of one same month as ``FunnelMetrics``; else ``None``.

    Approximate counts (``supuesto``) stay out: they are not the owner's data.
    """
    if _common_period(journey) is None:
        return None
    values = {
        _FUNNEL[item.stage]: item.count.value
        for item in journey.stages
        if item.stage in _FUNNEL
        and item.count is not None
        and item.count.origin != "supuesto"
        and item.count.upper is None
    }
    return FunnelMetrics.model_validate(values) if values else None
