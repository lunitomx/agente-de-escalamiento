# pyright: strict
"""Board recommender (E84 S84.3): at most 2 proposals, rules in order.

1. No redundancy: if something that exists answers the request (cash report,
   tracker, progress summary, research), point to it and propose nothing.
2. Start from a decision: without one, ask **one** question.
3. Closed catalogue of patterns by area (``patterns``).
4. Each metric's state comes from ``build_evidence_dashboard``.
5. Sales boards flag ``needs_journey_stages`` so the flow consults
   ``should_ask_journey`` (T4).

Pure: disk lookups (facts, existing artifacts, decision memory) happen in
``flow``. Boards declined or postponed in the last 30 days are not proposed.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from pydantic import BaseModel, ConfigDict

from coaching.dashboard.boards import messages
from coaching.dashboard.boards.models import (
    MAX_PROPOSALS,
    Area,
    BoardMetric,
    BoardProposal,
    Feasibility,
    Recommendation,
)
from coaching.dashboard.boards.patterns import BoardPattern, detect_area, patterns_for
from coaching.evidence.dashboard import MetricRequirement, build_evidence_dashboard
from coaching.evidence.facts import Fact

NO_REPROPOSE_DAYS = 30


class BoardRequest(BaseModel):
    """What the owner asked, plus the answer to the decision question if any."""

    model_config = ConfigDict(extra="forbid")

    request: str = ""
    decision: str = ""
    area: Area | None = None
    decision_asked: bool = False
    today: date


class Existing(BaseModel):
    """Local artifacts that already answer a request (paths relative to base)."""

    model_config = ConfigDict(extra="forbid")

    cash_report: str | None = None
    tracker: str | None = None
    research: str | None = None


def _pointer(area: Area, existing: Existing) -> Recommendation | None:
    if area == "caja":
        text = messages.CASH_REPORT if existing.cash_report else messages.CASH_NO_REPORT
        return Recommendation(
            outcome="existe",
            area=area,
            points_to_existing=existing.cash_report,
            message=text,
        )
    if area == "ejecucion":
        text = messages.TRACKER if existing.tracker else messages.TRACKER_MISSING
        return Recommendation(
            outcome="existe",
            area=area,
            points_to_existing=existing.tracker,
            message=text,
        )
    if area == "progreso":
        return Recommendation(outcome="existe", area=area, message=messages.PROGRESS)
    if area == "mercado":
        if existing.research:
            return Recommendation(
                outcome="existe",
                area=area,
                points_to_existing=existing.research,
                message=messages.RESEARCH,
            )
        return Recommendation(
            outcome="sin_patron", area=area, message=messages.NO_PATTERN
        )
    return None


def _metric_states(
    metrics: Sequence[BoardMetric], facts: Sequence[Fact]
) -> list[BoardMetric]:
    requirements = [
        MetricRequirement(
            metric_definition=m.metric_definition,
            question=m.how_to_get or m.metric_definition,
        )
        for m in metrics
    ]
    board = build_evidence_dashboard(facts, requirements)
    known = {fact.metric_definition.casefold(): fact for fact in board.known}
    blocked = {fact.metric_definition.casefold() for fact in board.not_comparable}
    result: list[BoardMetric] = []
    for metric in metrics:
        key = metric.metric_definition.casefold()
        fact = known.get(key)
        if fact is not None:
            result.append(
                metric.model_copy(
                    update={
                        "status": "conocido",
                        "source": fact.source,
                        "period": fact.period,
                    }
                )
            )
        elif key in blocked:
            result.append(metric.model_copy(update={"status": "no_comparable"}))
        else:
            result.append(metric.model_copy(update={"status": "falta"}))
    return result


def _feasibility(metrics: Sequence[BoardMetric]) -> Feasibility:
    known = sum(metric.status == "conocido" for metric in metrics)
    if known == len(metrics):
        return "se_puede_hoy"
    return "necesita_datos" if known else "no_ahora"


def _proposal(pattern: BoardPattern, facts: Sequence[Fact]) -> BoardProposal:
    metrics = _metric_states(pattern.metrics, facts)
    return BoardProposal(
        board_id=pattern.board_id,
        title=pattern.title,
        decision=pattern.decision,
        audience=pattern.audience,
        cadence=pattern.cadence,
        metrics=metrics,
        feasibility=_feasibility(metrics),
        missing=[m.metric_definition for m in metrics if m.status != "conocido"],
    )


def _recently_declined(
    board_id: str, declined: Mapping[str, date], today: date
) -> bool:
    day = declined.get(board_id)
    return day is not None and (today - day).days <= NO_REPROPOSE_DAYS


def recommend_boards(
    request: BoardRequest,
    *,
    facts: Sequence[Fact],
    existing: Existing,
    declined: Mapping[str, date] | None = None,
) -> Recommendation:
    """Apply the rules in order and end in a pointer, one question or a decision."""
    area = request.area or detect_area(f"{request.request} {request.decision}")
    if area is None:
        if request.decision_asked:
            return Recommendation(outcome="sin_patron", message=messages.NO_PATTERN)
        return Recommendation(
            outcome="pregunta_decision", message=messages.ASK_DECISION
        )
    pointer = _pointer(area, existing)
    if pointer is not None:
        return pointer
    candidates = patterns_for(area)
    if not candidates:
        return Recommendation(
            outcome="sin_patron", area=area, message=messages.NO_PATTERN
        )
    memory = declined or {}
    open_patterns = [
        p
        for p in candidates
        if not _recently_declined(p.board_id, memory, request.today)
    ][:MAX_PROPOSALS]
    if not open_patterns:
        return Recommendation(
            outcome="pospuesto", area=area, message=messages.POSTPONED
        )
    proposals = [_proposal(p, facts) for p in open_patterns]
    needs_stages = any(
        pattern.needs_journey_stages and proposal.missing
        for pattern, proposal in zip(open_patterns, proposals, strict=True)
    )
    buildable = any(p.feasibility != "no_ahora" for p in proposals)
    return Recommendation(
        outcome="propuestas",
        area=area,
        proposals=proposals,
        needs_journey_stages=needs_stages,
        options=list(messages.OPTIONS),
        recommended="construir" if buildable else "esperar",
        message=messages.proposals_text(proposals),
    )
