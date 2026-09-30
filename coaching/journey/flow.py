# pyright: strict
"""Steps the journey procedure drives: ``python -m coaching.journey``.

Actions (JSON on stdin, like ``coaching.research``):

- ``check``: ``signals`` (see ``JourneySignals``; ``today`` defaults to the
  top-level ``today``). When not given, ``last_declined_on`` comes from
  ``asks.yaml``, ``journey_review_by`` from a saved ``journey.yaml`` and the
  funnel gaps from ``funnel`` (``FunnelMetrics``). Returns the decision and,
  only when asking, the one question. Never writes.
- ``record``: the owner's answer to that question (``outcome`` si / despues /
  no, ``reason`` = the trigger code). Writes one line to ``asks.yaml``. With
  "si" it also returns the interview's first question.
- ``interview``: ``answers`` so far -> next single question and the draft.
  Never writes: the journey is decided and saved in S84.2.

Everything is written under ``<base_path>/.escala/my-company/journey/``.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import cast

import yaml
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from coaching.diagnose.models import FunnelMetrics
from coaching.journey import messages
from coaching.journey.asks import (
    JOURNEY_DIR,
    AskRecord,
    last_declined_on,
    load_asks,
    record_ask,
)
from coaching.journey.interview import Answer, InterviewStep, interview_step
from coaching.journey.triggers import (
    AskDecision,
    JourneySignals,
    funnel_gaps,
    should_ask_journey,
)

_ANSWERS = TypeAdapter(list[Answer])
JOURNEY_NAME = "journey.yaml"


class FlowResult(BaseModel):
    """Everything the flow hands back to the conversation."""

    action: str
    message: str = ""
    decision: AskDecision | None = None
    step: InterviewStep | None = None
    saved_to: str | None = None
    errors: list[str] = Field(default_factory=list[str])


def _text(context: Mapping[str, object], key: str) -> str | None:
    value = context.get(key)
    return value.strip() or None if isinstance(value, str) else None


def _today(context: Mapping[str, object]) -> date:
    raw = _text(context, "today")
    return date.fromisoformat(raw) if raw else date.today()


def _base(context: Mapping[str, object]) -> Path:
    return Path(_text(context, "base_path") or ".")


def _review_by(base: Path) -> date | None:
    """``review_by`` of a saved journey, if any; unreadable means none."""
    path = base / JOURNEY_DIR / JOURNEY_NAME
    try:
        raw: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(raw, dict):
        return None
    value = cast(dict[str, object], raw).get("review_by")
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def _check(context: Mapping[str, object]) -> FlowResult:
    raw = context.get("signals", {})
    given: dict[str, object] = (
        dict(cast(Mapping[str, object], raw)) if isinstance(raw, Mapping) else {}
    )
    base = _base(context)
    given.setdefault("today", _today(context))
    if "last_declined_on" not in given:
        given["last_declined_on"] = last_declined_on(load_asks(base))
    if "journey_review_by" not in given:
        given["journey_review_by"] = _review_by(base)
    if "funnel" in context and not ({"funnel_known", "funnel_missing"} & given.keys()):
        known, missing = funnel_gaps(FunnelMetrics.model_validate(context["funnel"]))
        given["funnel_known"], given["funnel_missing"] = known, missing
    decision = should_ask_journey(JourneySignals.model_validate(given))
    return FlowResult(action="check", decision=decision, message=decision.message or "")


def _record(context: Mapping[str, object]) -> FlowResult:
    today = _today(context)
    record = AskRecord.model_validate(
        {
            "asked_on": today,
            "outcome": context.get("outcome"),
            "reason": context.get("reason"),
        }
    )
    base = _base(context)
    path = record_ask(base, record)
    saved_to = path.relative_to(base).as_posix()
    if record.outcome != "si":
        return FlowResult(action="record", saved_to=saved_to, message=messages.LATER)
    step = interview_step([], today)
    return FlowResult(
        action="record", saved_to=saved_to, step=step, message=step.message
    )


def _interview(context: Mapping[str, object]) -> FlowResult:
    answers = _ANSWERS.validate_python(context.get("answers", []))
    step = interview_step(answers, _today(context))
    return FlowResult(action="interview", step=step, message=step.message)


_ACTIONS = {"check": _check, "record": _record, "interview": _interview}


def _validation_codes(exc: ValidationError) -> list[str]:
    codes: list[str] = []
    for error in exc.errors():
        where = ".".join(str(part) for part in cast(tuple[object, ...], error["loc"]))
        codes.append(f"invalid:{where}" if where else "invalid")
    return codes


def run(context: Mapping[str, object]) -> FlowResult:
    """Run one step of the journey procedure."""
    action = _text(context, "action") or ""
    step = _ACTIONS.get(action)
    if step is None:
        return FlowResult(action=action, errors=["unknown_action"])
    try:
        return step(context)
    except ValidationError as exc:
        return FlowResult(action=action, errors=_validation_codes(exc))
    except ValueError as exc:
        return FlowResult(action=action, errors=[str(exc)])
