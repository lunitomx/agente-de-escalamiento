# pyright: strict
"""Steps the research procedure drives: ``python -m coaching.research``.

Actions (JSON on stdin, like ``coaching.tracker``):

- ``frame``: the owner's concern as a frame. With web search, 2-3 searches
  from the frame's public fields (or the agent's proposals), checked against
  ``private`` (company names, people, figures; required), plus the one
  permission message. Without search (``search_mode: "sin_busqueda"``), the
  one-line notice and the ask for the owner's sources. In ``mercado``
  without a segment or geography no size is searched and
  ``missing_question`` says what to ask (S83.3).
- ``grade``: grade ``claims`` against ``sources`` (``today`` = reference date).
- ``comparables`` (benchmark): the businesses found, checked against the frame
  and ``sources`` (required ``private``: the own company is never one), and
  the message asking which candidates look like the owner's business.
- ``report``: the graded report and the short result that ends in the
  decision question. Nothing is saved. Needs ``frame.confirmed``. In
  ``mercado`` it takes ``market_size`` (a range with method, assumptions and
  sources, or "not estimable yet" with what is missing).
- ``save``: same input plus ``chosen`` (option label) and
  ``user_confirmed: true``; writes under ``.escala/my-company/research/``.
- ``diagnosis``: the saved research as input for the next diagnosis (the
  owner's decisions as local facts, outside findings as assumptions, gaps as
  open questions) and, for a report past its review date, the offer to
  refresh it. ``base_path`` and ``today``.
- ``check_sources``: a sample of a saved report's web sources (``reference``
  = its local path, as in ``index.yaml``; ``limit``, default 3). Without
  ``pages`` it returns the links to open; with ``pages`` ({source_id: page
  text}) it says, per source, whether the quoted excerpt is on the page.

The private specialist never writes state; this module does.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import cast

from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from coaching.research import messages
from coaching.research.diagnosis import (
    DiagnosticInputs,
    load_diagnostic_inputs,
    misfits,
)
from coaching.research.engine import (
    RejectedQuery,
    build_queries,
    check_queries,
    grade_claim,
    is_own_company,
)
from coaching.research.sampling import SAMPLE_SIZE, SourceCheck, check_sources
from coaching.research.models import (
    Comparable,
    DecisionOption,
    MarketSize,
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
    load_index,
    load_saved_report,
    report_message,
    save_report,
)

_SOURCES = TypeAdapter(list[SourceRecord])
_CLAIMS = TypeAdapter(list[ResearchClaim])
_OPTIONS = TypeAdapter(list[DecisionOption])
_COMPARABLES = TypeAdapter(list[Comparable])
_TEXTS = TypeAdapter(list[str])
_SIZE: TypeAdapter[MarketSize | None] = TypeAdapter(MarketSize | None)


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
    missing_question: str | None = None
    diagnostic_inputs: DiagnosticInputs | None = None
    source_checks: list[SourceCheck] = Field(default_factory=list[SourceCheck])
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


def _missing_question(frame: ResearchFrame) -> str | None:
    """In ``mercado``, what the owner must say before his market is sized."""
    if frame.mode != "mercado":
        return None
    return messages.missing_question(
        not (frame.segment and frame.segment.strip()),
        not (frame.geography and frame.geography.strip()),
    )


def _frame(context: Mapping[str, object]) -> FlowResult:
    frame = ResearchFrame.model_validate(context.get("frame"))
    missing = _missing_question(frame)
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
        ask = f"\n\n{messages.size_blocked(missing)}" if missing else ""
        return FlowResult(
            action="frame",
            frame=frame.model_copy(update={"queries": [], "confirmed": False}),
            missing_question=missing,
            message=(
                f"{messages.SEARCH_OFF}{ask}\n\nLo que quieres decidir: "
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
        missing_question=missing,
        message=messages.frame_message(
            frame.decision_informed, checked.accepted, missing
        ),
    )


def _must_fit(
    *,
    as_of: date,
    claims: list[ResearchClaim] | None = None,
    comparables: list[Comparable] | None = None,
    not_found: list[str] | None = None,
    options: list[DecisionOption] | None = None,
    market_size: MarketSize | None = None,
) -> None:
    """Every text must reach the next diagnosis whole; none is ever cut."""
    bad = misfits(
        claims=claims or [],
        comparables=comparables or [],
        not_found=not_found or [],
        options=options or [],
        as_of=as_of,
        market_size=market_size,
    )
    if bad:
        raise _Refusal("finding_too_long", messages.finding_too_long(bad))


def _grade(context: Mapping[str, object]) -> FlowResult:
    sources = _SOURCES.validate_python(context.get("sources", []))
    claims = _CLAIMS.validate_python(context.get("claims", []))
    _must_fit(as_of=_today(context), claims=claims)
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
    _must_fit(as_of=_today(context), comparables=comparables)
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
    claims = _CLAIMS.validate_python(context.get("claims", []))
    options = _OPTIONS.validate_python(context.get("options", []))
    not_found = _TEXTS.validate_python(context.get("not_found", []))
    _must_fit(
        as_of=_today(context),
        claims=claims,
        comparables=comparables,
        not_found=not_found,
        options=options,
    )
    report = build_report(
        frame=frame,
        researched_on=_today(context),
        sources=_SOURCES.validate_python(context.get("sources", [])),
        claims=claims,
        options=options,
        recommendation=_text(context, "recommendation") or "",
        recommendation_reason=_text(context, "recommendation_reason") or "",
        not_found=not_found,
        limits=_TEXTS.validate_python(context.get("limits", [])),
        chosen=chosen,
        comparables=comparables,
        market_size=_SIZE.validate_python(context.get("market_size")),
    )
    # The size as graded (or "not estimable yet") must also reach it whole.
    _must_fit(as_of=_today(context), market_size=report.market_size)
    return report


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


_PAGES = TypeAdapter(dict[str, str])


def _check_sources(context: Mapping[str, object]) -> FlowResult:
    """Sample a saved report's sources and check their quotes (E83 S83.5)."""
    base = Path(_text(context, "base_path") or ".")
    reference = _text(context, "reference")
    entry = next(
        (item for item in load_index(base) if item.reference == reference), None
    )
    if entry is None:
        raise _Refusal("unknown_report")
    report = load_saved_report(base, entry)
    if report is None:
        raise _Refusal("detail_unreadable", messages.DETAIL_UNREADABLE)
    raw_limit = context.get("limit", SAMPLE_SIZE)
    limit = raw_limit if isinstance(raw_limit, int) and raw_limit > 0 else SAMPLE_SIZE
    raw_pages = context.get("pages")
    pages = {} if raw_pages is None else _PAGES.validate_python(raw_pages)
    checks = check_sources(report, pages, limit)
    if raw_pages is None:
        message = messages.sources_to_open(len(checks))
    else:
        count = {
            result: sum(item.result == result for item in checks)
            for result in ("aparece", "no_aparece", "sin_revisar")
        }
        message = messages.sources_checked(
            count["aparece"], count["no_aparece"], count["sin_revisar"]
        )
    return FlowResult(action="check_sources", source_checks=checks, message=message)


_ACTIONS = {
    "frame": _frame,
    "grade": _grade,
    "comparables": _comparables,
    "report": _report,
    "save": _save,
    "diagnosis": _diagnosis,
    "check_sources": _check_sources,
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
