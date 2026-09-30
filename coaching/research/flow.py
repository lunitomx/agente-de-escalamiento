# pyright: strict
"""Steps the research procedure drives: ``python -m coaching.research``.

Actions (JSON on stdin, like ``coaching.tracker``):

- ``frame``: the owner's concern as a frame. With web search, 2-3 searches
  from the frame's public fields (or the agent's proposals), checked against
  ``private`` (company names, people, figures; required), plus the one
  permission message. Without search (``search_mode: "sin_busqueda"``), the
  one-line notice and the ask for the owner's sources.
- ``grade``: grade ``claims`` against ``sources`` (``today`` = reference date).
- ``comparables`` (benchmark): the businesses found, checked against the frame
  and ``sources`` (required ``private``: the own company is never one), and
  the message asking which candidates look like the owner's business.
- ``report``: the graded report and the short result that ends in the
  decision question. Nothing is saved. Needs ``frame.confirmed``.
- ``save``: same input plus ``chosen`` (option label) and
  ``user_confirmed: true``; writes under ``.escala/my-company/research/``.
- ``diagnosis``: the saved research as input for the next diagnosis (the
  owner's decisions as local facts, outside findings as assumptions, gaps as
  open questions) and, for a report past its review date, the offer to
  refresh it. ``base_path`` and ``today``.

The private specialist never writes state; this module does.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import cast

from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from coaching.research import messages
from coaching.research.diagnosis import DiagnosticInputs, load_diagnostic_inputs
from coaching.research.engine import (
    RejectedQuery,
    build_queries,
    check_queries,
    grade_claim,
    is_own_company,
)
from coaching.research.models import (
    Comparable,
    DecisionOption,
    PrivateTerms,
    ResearchClaim,
    ResearchFrame,
    ResearchReport,
    SourceRecord,
    check_comparables,
)
from coaching.research.report import (
    build_report,
    comparables_message,
    report_message,
    save_report,
)

_SOURCES = TypeAdapter(list[SourceRecord])
_CLAIMS = TypeAdapter(list[ResearchClaim])
_OPTIONS = TypeAdapter(list[DecisionOption])
_COMPARABLES = TypeAdapter(list[Comparable])
_TEXTS = TypeAdapter(list[str])


class FlowResult(BaseModel):
    """Everything the flow hands back to the conversation."""

    action: str
    message: str = ""
    frame: ResearchFrame | None = None
    rejected: list[RejectedQuery] = Field(default_factory=list[RejectedQuery])
    claims: list[ResearchClaim] = Field(default_factory=list[ResearchClaim])
    comparables: list[Comparable] = Field(default_factory=list[Comparable])
    report: ResearchReport | None = None
    saved_to: str | None = None
    diagnostic_inputs: DiagnosticInputs | None = None
    errors: list[str] = Field(default_factory=list)


class _Refusal(Exception):
    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.message = message


def _text(context: Mapping[str, object], key: str) -> str | None:
    value = context.get(key)
    return value.strip() or None if isinstance(value, str) else None


def _today(context: Mapping[str, object]) -> date:
    raw = _text(context, "today")
    return date.fromisoformat(raw) if raw else date.today()


def _private(context: Mapping[str, object]) -> PrivateTerms | None:
    raw = context.get("private")
    return None if raw is None else PrivateTerms.model_validate(raw)


def _frame(context: Mapping[str, object]) -> FlowResult:
    frame = ResearchFrame.model_validate(context.get("frame"))
    private = _private(context)
    if private is None:
        raise _Refusal("needs_private_terms")
    if frame.mode == "benchmark":
        # Comparable = same confirmed offer and geography (S83.2).
        if not (frame.offer_category and frame.offer_category.strip()):
            raise _Refusal("needs_offer_category", messages.NEEDS_OFFER)
        if not (frame.geography and frame.geography.strip()):
            raise _Refusal("needs_geography", messages.NEEDS_OFFER)
    if frame.search_mode == "sin_busqueda":
        return FlowResult(
            action="frame",
            frame=frame.model_copy(update={"queries": [], "confirmed": False}),
            message=(
                f"{messages.SEARCH_OFF}\n\nLo que quieres decidir: "
                f"{frame.decision_informed}. ¿Es eso?"
            ),
        )
    if not frame.offer_category:
        raise _Refusal("needs_offer_category", messages.NEEDS_OFFER)
    proposed = frame.queries or build_queries(frame)
    checked = check_queries(frame.model_copy(update={"queries": proposed}), private)
    if not checked.accepted:
        return FlowResult(
            action="frame",
            message=messages.NO_SAFE_QUERY,
            rejected=checked.rejected,
            errors=["no_safe_query"],
        )
    return FlowResult(
        action="frame",
        frame=frame.model_copy(
            update={"queries": checked.accepted, "confirmed": False}
        ),
        rejected=checked.rejected,
        message=messages.frame_message(frame.decision_informed, checked.accepted),
    )


def _grade(context: Mapping[str, object]) -> FlowResult:
    sources = _SOURCES.validate_python(context.get("sources", []))
    claims = _CLAIMS.validate_python(context.get("claims", []))
    by_id = {source.source_id: source for source in sources}
    as_of = _today(context)
    return FlowResult(
        action="grade", claims=[grade_claim(claim, by_id, as_of) for claim in claims]
    )


def _no_own_company(
    frame: ResearchFrame, comparables: list[Comparable], private: PrivateTerms
) -> None:
    if any(is_own_company(item.name, frame, private) for item in comparables):
        raise _Refusal("own_company_as_comparable")


def _comparables(context: Mapping[str, object]) -> FlowResult:
    frame = ResearchFrame.model_validate(context.get("frame"))
    private = _private(context)
    if private is None:
        raise _Refusal("needs_private_terms")
    if not frame.confirmed:
        raise _Refusal("frame_not_confirmed")
    sources = _SOURCES.validate_python(context.get("sources", []))
    comparables = _COMPARABLES.validate_python(context.get("comparables", []))
    check_comparables(frame, sources, comparables)
    _no_own_company(frame, comparables, private)
    return FlowResult(
        action="comparables",
        comparables=comparables,
        message=comparables_message(frame, sources, comparables),
    )


def _build(context: Mapping[str, object], chosen: str | None) -> ResearchReport:
    frame = ResearchFrame.model_validate(context.get("frame"))
    private = _private(context)
    comparables = _COMPARABLES.validate_python(context.get("comparables", []))
    if private is not None:
        # The recorded searches must be exactly the text the check accepted.
        checked = check_queries(frame, private)
        if checked.rejected or checked.accepted != frame.queries:
            raise _Refusal("private_query", messages.NO_SAFE_QUERY)
        _no_own_company(frame, comparables, private)
    return build_report(
        frame=frame,
        researched_on=_today(context),
        sources=_SOURCES.validate_python(context.get("sources", [])),
        claims=_CLAIMS.validate_python(context.get("claims", [])),
        options=_OPTIONS.validate_python(context.get("options", [])),
        recommendation=_text(context, "recommendation") or "",
        recommendation_reason=_text(context, "recommendation_reason") or "",
        not_found=_TEXTS.validate_python(context.get("not_found", [])),
        limits=_TEXTS.validate_python(context.get("limits", [])),
        chosen=chosen,
        comparables=comparables,
    )


def _report(context: Mapping[str, object]) -> FlowResult:
    report = _build(context, None)
    return FlowResult(action="report", report=report, message=report_message(report))


def _save(context: Mapping[str, object]) -> FlowResult:
    if context.get("user_confirmed") is not True:
        raise _Refusal("needs_user_confirmation", messages.NEEDS_CHOICE)
    chosen = _text(context, "chosen")
    if chosen is None:
        raise _Refusal("needs_chosen_option", messages.NEEDS_CHOICE)
    report = _build(context, chosen)
    base = Path(_text(context, "base_path") or ".")
    path = save_report(report, base)
    return FlowResult(
        action="save",
        report=report,
        saved_to=path.relative_to(base).as_posix(),
        message=messages.saved_message(report.review_by),
    )


def _diagnosis(context: Mapping[str, object]) -> FlowResult:
    """Saved research as input for the next diagnosis (E83 S83.5)."""
    base = Path(_text(context, "base_path") or ".")
    inputs = load_diagnostic_inputs(base, _today(context))
    return FlowResult(
        action="diagnosis",
        diagnostic_inputs=inputs,
        message="\n\n".join(inputs.refresh_offers),
    )


_ACTIONS = {
    "frame": _frame,
    "grade": _grade,
    "comparables": _comparables,
    "report": _report,
    "save": _save,
    "diagnosis": _diagnosis,
}


def _validation_codes(exc: ValidationError) -> list[str]:
    codes: list[str] = []
    for error in exc.errors():
        text = str(error["msg"]).removeprefix("Value error, ")
        where = ".".join(str(part) for part in cast(tuple[object, ...], error["loc"]))
        codes.append(text if not where else f"invalid:{where}:{text}")
    return codes


def run(context: Mapping[str, object]) -> FlowResult:
    """Run one step of the research."""
    action = _text(context, "action") or ""
    step = _ACTIONS.get(action)
    if step is None:
        return FlowResult(action=action, errors=["unknown_action"])
    try:
        return step(context)
    except _Refusal as refusal:
        return FlowResult(action=action, message=refusal.message, errors=[refusal.code])
    except ValidationError as exc:
        return FlowResult(action=action, errors=_validation_codes(exc))
    except ValueError as exc:
        return FlowResult(action=action, errors=[str(exc)])
