# pyright: strict
"""The journey ends in one decision, saved only after the owner's yes (S84.2).

Options reuse research's ``DecisionOption`` (2-3 of them, one recommended):

- with a known loss and an experiment: "work stage N for 7-14 days" (A);
- always "todavía no": the missing data and a date (default: 14 days);
- with no loss to work on: "no hacer nada por ahora" instead of A.

``save_journey`` refuses without a chosen option and writes, atomically,
``.escala/my-company/journey/journey.yaml`` (with ``review_by`` at 90 days,
read by ``check`` for blocker N1) and ``AAAA-MM-DD-journey.md``.
"""

from __future__ import annotations

import os
import tempfile
from datetime import date, timedelta
from pathlib import Path
from typing import Self, cast

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from coaching.journey.asks import JOURNEY_DIR
from coaching.journey.interview import STAGE_LABEL
from coaching.journey.models import Journey
from coaching.journey.view import biggest_loss, period_label, spanish_date, summary
from coaching.research.models import DecisionOption

JOURNEY_NAME = "journey.yaml"
REVIEW_DAYS = 90
WAIT_DAYS = 14
_LABELS = ("A", "B", "C")
_NO_LOSS_DATA = "contar dos pasos seguidos en el mismo mes"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class JourneyDecision(_Strict):
    """2-3 options, the recommended one, and the one the owner chose."""

    options: list[DecisionOption] = Field(min_length=2, max_length=3)
    recommendation: str
    reason: str
    chosen: str | None = None

    @model_validator(mode="after")
    def _labels_are_options(self) -> Self:
        labels = {option.label for option in self.options}
        if self.recommendation not in labels:
            raise ValueError("recommendation_must_be_an_option")
        if self.chosen is not None and self.chosen not in labels:
            raise ValueError("chosen_must_be_an_option")
        return self


class SavedJourney(_Strict):
    """What ``journey.yaml`` holds."""

    saved_on: date
    review_by: date
    reference: str
    journey: Journey
    decision: JourneyDecision


def _first_missing_count(journey: Journey) -> str | None:
    periods = {item.count.period for item in journey.stages if item.count is not None}
    when = f" en {period_label(next(iter(periods)))}" if len(periods) == 1 else ""
    for item in journey.stages:
        if item.count is None:
            return f"cuántos en «{STAGE_LABEL[item.stage]}»{when}"
    return None


def propose(
    journey: Journey,
    today: date,
    experiment: str | None,
    days: int = 14,
    by_date: date | None = None,
) -> JourneyDecision:
    """The options the journey closes with; nothing is chosen yet."""
    if not 7 <= days <= 14:
        raise ValueError("experiment_days_7_to_14")
    loss = biggest_loss(journey)
    missing = _first_missing_count(journey) or (_NO_LOSS_DATA if loss is None else None)
    texts: list[tuple[str, dict[str, object]]] = []
    if loss is not None and experiment and experiment.strip():
        stage = STAGE_LABEL[loss.to_stage]
        texts.append(
            (
                f"Durante {days} días en «{stage}»: {experiment.strip()}, y luego "
                "contar de nuevo",
                {"kind": "decidir"},
            )
        )
    else:
        texts.append(("No hacer nada con esto por ahora", {"kind": "decidir"}))
    if missing is not None:
        texts.append(
            (
                "Todavía no: primero consigo el dato que falta",
                {
                    "kind": "esperar",
                    "missing_data": missing,
                    "by_date": by_date or today + timedelta(days=WAIT_DAYS),
                },
            )
        )
    else:
        texts.append(("Dejarlo así y revisarlo en 90 días", {"kind": "decidir"}))
    options = [
        DecisionOption.model_validate({"label": label, "text": text, **extra})
        for label, (text, extra) in zip(_LABELS, texts, strict=False)
    ]
    works_a_stage = loss is not None and bool(experiment and experiment.strip())
    if works_a_stage:
        recommended, reason = "A", "ahí se pierden más clientes"
    else:
        wait = next((o for o in options if o.kind == "esperar"), options[-1])
        recommended, reason = wait.label, "sin ese dato no se sabe dónde actuar"
    return JourneyDecision(options=options, recommendation=recommended, reason=reason)


def choose(decision: JourneyDecision, label: str) -> JourneyDecision:
    """The owner's choice (``a`` or ``A``); an unknown label is refused."""
    wanted = label.strip().upper()
    if wanted not in {option.label for option in decision.options}:
        raise ValueError("chosen_must_be_an_option")
    return decision.model_copy(update={"chosen": wanted})


def option_text(option: DecisionOption) -> str:
    text = f"{option.label}) {option.text}"
    if option.kind == "esperar" and option.missing_data and option.by_date:
        text += f": {option.missing_data}, para el {spanish_date(option.by_date)}"
    return text + "."


def decision_lines(decision: JourneyDecision) -> list[str]:
    lines = [option_text(option) for option in decision.options]
    lines.append(f"Te recomiendo la {decision.recommendation}: {decision.reason}.")
    return lines


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, tmp = tempfile.mkstemp(dir=path.parent, prefix=".journey-", suffix=".tmp")
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(text)
    Path(tmp).replace(path)


def _markdown(journey: Journey, decision: JourneyDecision, saved_on: date) -> str:
    chosen = next(o for o in decision.options if o.label == decision.chosen)
    return "\n".join(
        [
            f"# Cómo llega un cliente hasta que te compra ({spanish_date(saved_on)})",
            "",
            summary(journey),
            "",
            "## Decisión",
            "",
            *[f"- {line}" for line in decision_lines(decision)],
            "",
            f"Elegiste: {option_text(chosen)}",
            "",
        ]
    )


def save_journey(
    base: Path, journey: Journey, decision: JourneyDecision, today: date
) -> list[Path]:
    """Save the journey and the chosen decision; refused without a choice."""
    if decision.chosen is None:
        raise ValueError("needs_chosen_option")
    folder = base / JOURNEY_DIR
    markdown = folder / f"{today.isoformat()}-journey.md"
    saved = SavedJourney(
        saved_on=today,
        review_by=today + timedelta(days=REVIEW_DAYS),
        reference=markdown.relative_to(base).as_posix(),
        journey=journey,
        decision=decision,
    )
    _write(markdown, _markdown(journey, decision, today))
    data = folder / JOURNEY_NAME
    _write(
        data,
        yaml.safe_dump(
            saved.model_dump(mode="json"), allow_unicode=True, sort_keys=False
        ),
    )
    return [markdown, data]


def load_saved(base: Path) -> SavedJourney | None:
    """The saved journey, or ``None`` when missing or unreadable."""
    path = base / JOURNEY_DIR / JOURNEY_NAME
    try:
        raw: object = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return None
        return SavedJourney.model_validate(cast(dict[str, object], raw))
    except (OSError, yaml.YAMLError, ValidationError):
        return None
