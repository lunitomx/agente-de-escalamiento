# pyright: strict
"""Steps the journey procedure drives: ``python -m coaching.journey``.

Actions (JSON on stdin, like ``coaching.research``):

- ``check``: ``signals`` (see ``JourneySignals``; ``today`` defaults to the
  top-level ``today``). When not given, ``last_declined_on`` comes from
  ``asks.yaml`` (the latest of both wins; a corrupt file counts as declined
  on the day it last changed), ``journey_review_by`` from a saved ``journey.yaml`` and the
  funnel gaps from ``funnel`` (``FunnelMetrics``). Returns the decision and,
  only when asking, the one question. Never writes.
- ``record``: the owner's answer to that question (``outcome`` si / despues /
  no, ``reason`` = the trigger code). Writes one line to ``asks.yaml``; a
  corrupt one is first kept as ``asks.yaml.bak`` and reported in ``notes``. With
  "si" it also returns the interview's first question.
- ``interview``: ``answers`` so far -> next single question and the draft.
  Never writes.
- ``build`` (S84.2): ``answers`` plus what the agent knows from the
  conversation (``counts`` per stage with period and local source,
  ``evidence`` per stage with its origin, ``experiment``) -> the journey, its
  plain summary and 2-3 options with one recommended. Never writes.
- ``save``: the same plus ``chosen`` (the owner's option). Refused without
  it. Writes ``journey.yaml`` and ``AAAA-MM-DD-journey.md``.
- ``diagnosis``: the saved decision as input for the next diagnosis.

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
from coaching.journey.decision import (
    JourneyDecision,
    choose,
    decision_lines,
    propose,
    save_journey,
)
from coaching.journey.diagnosis import load_diagnostic_inputs
from coaching.journey.models import Journey, JourneyEvidence, StageCount, from_draft
from coaching.journey.view import summary
from coaching.research.diagnosis import DiagnosticInputs
from coaching.journey.asks import (
    JOURNEY_DIR,
    AskRecord,
    declined_on,
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
    journey: Journey | None = None
    options: JourneyDecision | None = None
    diagnostic_inputs: DiagnosticInputs | None = None
    saved_to: str | None = None
    notes: list[str] = Field(default_factory=list[str])
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
    if "funnel" in context and not ({"funnel_known", "funnel_missing"} & given.keys()):
        known, missing = funnel_gaps(FunnelMetrics.model_validate(context["funnel"]))
        given["funnel_known"], given["funnel_missing"] = known, missing
    signals = JourneySignals.model_validate(given)
    # What the disk remembers is never masked by a missing or older value.
    declines = [
        day for day in (signals.last_declined_on, declined_on(base)) if day is not None
    ]
    signals = signals.model_copy(
        update={
            "last_declined_on": max(declines, default=None),
            "journey_review_by": signals.journey_review_by or _review_by(base),
        }
    )
    decision = should_ask_journey(signals)
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
    path, backup = record_ask(base, record)
    saved_to = path.relative_to(base).as_posix()
    notes = (
        []
        if backup is None
        else [f"asks_corrupt_backed_up:{backup.relative_to(base).as_posix()}"]
    )
    if record.outcome != "si":
        return FlowResult(
            action="record", saved_to=saved_to, notes=notes, message=messages.LATER
        )
    step = interview_step([], today)
    return FlowResult(
        action="record",
        saved_to=saved_to,
        notes=notes,
        step=step,
        message=step.message,
    )


def _interview(context: Mapping[str, object]) -> FlowResult:
    answers = _ANSWERS.validate_python(context.get("answers", []))
    step = interview_step(answers, _today(context))
    return FlowResult(action="interview", step=step, message=step.message)


_COUNTS = TypeAdapter(dict[str, StageCount])
_EVIDENCE = TypeAdapter(list[dict[str, object]])


def _journey(context: Mapping[str, object], today: date) -> Journey:
    """The interview's draft plus what the agent knows, as a journey."""
    answers = _ANSWERS.validate_python(context.get("answers", []))
    journey = from_draft(interview_step(answers, today).draft, today)
    counts = _COUNTS.validate_python(context.get("counts", {}))
    extra: dict[str, list[JourneyEvidence]] = {}
    for item in _EVIDENCE.validate_python(context.get("evidence", [])):
        fields = {key: value for key, value in item.items() if key != "stage"}
        extra.setdefault(str(item.get("stage")), []).append(
            JourneyEvidence.model_validate(fields)
        )
    known = {stage.stage for stage in journey.stages}
    if unknown := (set(counts) | set(extra)) - known:
        raise ValueError(f"unknown_stage:{','.join(sorted(unknown))}")
    stages = [
        stage.model_copy(
            update={
                "count": counts.get(stage.stage, stage.count),
                "evidence": [*stage.evidence, *extra.get(stage.stage, [])],
            }
        )
        for stage in journey.stages
    ]
    return Journey.model_validate(
        {"built_on": today, "stages": [s.model_dump() for s in stages]}
    )


def _decision(
    context: Mapping[str, object], journey: Journey, today: date
) -> JourneyDecision:
    days = context.get("days", 14)
    by_date = _text(context, "by_date")
    return propose(
        journey,
        today,
        experiment=_text(context, "experiment"),
        days=days if isinstance(days, int) else 14,
        by_date=date.fromisoformat(by_date) if by_date else None,
    )


def _build(context: Mapping[str, object]) -> FlowResult:
    today = _today(context)
    journey = _journey(context, today)
    decision = _decision(context, journey, today)
    message = "\n".join(
        [
            summary(journey),
            "",
            messages.DECIDE,
            *[f"- {line}" for line in decision_lines(decision)],
            messages.NOT_SAVED_YET,
        ]
    )
    return FlowResult(
        action="build", journey=journey, options=decision, message=message
    )


def _save(context: Mapping[str, object]) -> FlowResult:
    today = _today(context)
    chosen = _text(context, "chosen")
    if chosen is None:
        raise ValueError("needs_chosen_option")
    journey = _journey(context, today)
    decision = choose(_decision(context, journey, today), chosen)
    base = _base(context)
    markdown, _ = save_journey(base, journey, decision, today)
    return FlowResult(
        action="save",
        journey=journey,
        options=decision,
        saved_to=markdown.relative_to(base).as_posix(),
        message=messages.SAVED,
    )


def _diagnosis(context: Mapping[str, object]) -> FlowResult:
    inputs = load_diagnostic_inputs(_base(context), _today(context))
    return FlowResult(action="diagnosis", diagnostic_inputs=inputs)


_ACTIONS = {
    "check": _check,
    "record": _record,
    "interview": _interview,
    "build": _build,
    "save": _save,
    "diagnosis": _diagnosis,
}


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
