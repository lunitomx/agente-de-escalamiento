# pyright: strict
"""Steps the board procedure drives: ``python -m coaching.dashboard.boards``.

Actions (JSON on stdin, like ``coaching.journey``):

- ``recommend``: ``request`` (the owner's words), optional ``decision`` (the
  answer to "¿qué quieres decidir?"), ``area``, ``decision_asked`` and
  ``facts`` (else read from local memory). Looks for what already exists
  (cash report, tracker, research) and the decision memory. When a sales
  board lacks stage counts it consults the journey trigger (T4) with
  ``asked_this_conversation``, ``other_flow_active`` and ``cash_emergency``
  as given; the question comes back apart, never inside ``message``. Never
  writes.
- ``decide``: ``board_id`` and ``outcome`` (construir / esperar / no; esperar
  needs ``review_on``). Writes one line to ``tableros/index.yaml``; a corrupt
  one is first kept as ``index.yaml.bak`` and reported in ``notes``.

Generating the board file is S84.4.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import cast

from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from coaching.dashboard.boards.memory import (
    BoardDecision,
    declined_boards,
    record_decision,
)
from coaching.dashboard.boards.models import Recommendation
from coaching.dashboard.boards.recommend import (
    BoardRequest,
    Existing,
    recommend_boards,
)
from coaching.evidence.facts import Fact, load_facts
from coaching.journey import flow as journey_flow
from coaching.journey.triggers import AskDecision

_FACTS = TypeAdapter(list[Fact])
CASH_REPORTS = ".escala-cash-reports"
TRACKER = ".escala/my-company/tracker.yaml"
RESEARCH = ".escala/my-company/research/index.yaml"
_JOURNEY_FLAGS = ("asked_this_conversation", "other_flow_active", "cash_emergency")

DECIDED = {
    "construir": (
        "Anotado: lo armamos con tus datos, y lo que falte se verá como «Falta». "
        "El archivo sólo queda en tu computadora; no se publica."
    ),
    "esperar": (
        "Va, lo dejamos para cuando tengas los datos. Cuando los tengas, sólo dime."
    ),
    "no": "Va, no te lo vuelvo a proponer en un mes. Si antes lo quieres, sólo dime.",
}


class FlowResult(BaseModel):
    """Everything the flow hands back to the conversation."""

    action: str
    message: str = ""
    recommendation: Recommendation | None = None
    journey: AskDecision | None = None
    journey_question: str | None = None
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


def _existing(base: Path) -> Existing:
    reports = base / CASH_REPORTS
    has_report = reports.is_dir() and any(reports.rglob("cash-report.*"))
    return Existing(
        cash_report=f"{CASH_REPORTS}/" if has_report else None,
        tracker=TRACKER if (base / TRACKER).is_file() else None,
        research=RESEARCH if (base / RESEARCH).is_file() else None,
    )


def _facts(context: Mapping[str, object], base: Path) -> list[Fact]:
    if "facts" in context:
        return _FACTS.validate_python(context["facts"])
    return load_facts(base)


def _journey(
    context: Mapping[str, object], base: Path, today: date
) -> AskDecision | None:
    signals: dict[str, object] = {"board_needs_stages": True}
    for flag in _JOURNEY_FLAGS:
        if isinstance(context.get(flag), bool):
            signals[flag] = context[flag]
    checked = journey_flow.run(
        {
            "action": "check",
            "base_path": str(base),
            "today": today.isoformat(),
            "signals": signals,
        }
    )
    return checked.decision


def _recommend(context: Mapping[str, object]) -> FlowResult:
    base, today = _base(context), _today(context)
    request = BoardRequest.model_validate(
        {
            "request": _text(context, "request") or "",
            "decision": _text(context, "decision") or "",
            "area": context.get("area"),
            "decision_asked": context.get("decision_asked") is True,
            "today": today,
        }
    )
    recommendation = recommend_boards(
        request,
        facts=_facts(context, base),
        existing=_existing(base),
        declined=declined_boards(base),
    )
    journey = (
        _journey(context, base, today) if recommendation.needs_journey_stages else None
    )
    return FlowResult(
        action="recommend",
        recommendation=recommendation,
        journey=journey,
        journey_question=journey.message if journey and journey.ask else None,
        message=recommendation.message,
    )


def _decide(context: Mapping[str, object]) -> FlowResult:
    base = _base(context)
    decision = BoardDecision.model_validate(
        {
            "decided_on": _today(context),
            "board_id": context.get("board_id"),
            "outcome": context.get("outcome"),
            "review_on": context.get("review_on"),
        }
    )
    path, backup = record_decision(base, decision)
    notes = (
        []
        if backup is None
        else [f"index_corrupt_backed_up:{backup.relative_to(base).as_posix()}"]
    )
    return FlowResult(
        action="decide",
        saved_to=path.relative_to(base).as_posix(),
        notes=notes,
        message=DECIDED[decision.outcome],
    )


_ACTIONS = {"recommend": _recommend, "decide": _decide}


def _validation_codes(exc: ValidationError) -> list[str]:
    codes: list[str] = []
    for error in exc.errors():
        where = ".".join(str(part) for part in cast(tuple[object, ...], error["loc"]))
        codes.append(f"invalid:{where}" if where else "invalid")
    return codes


def run(context: Mapping[str, object]) -> FlowResult:
    """Run one step of the board procedure."""
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
