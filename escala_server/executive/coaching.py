"""Strategy/OPSP composition and four-decision coaching routing."""

from __future__ import annotations

from collections.abc import Iterable

from .models import (
    CoachingRequest,
    CoachingRoute,
    DECISIONS,
    ExecutiveDiagnostic,
    StrategyAnswer,
    StrategyPlan,
)


STRATEGY_FIELDS: tuple[str, ...] = (
    "vision",
    "purpose",
    "bhag",
    "sandbox",
    "brand_promise",
    "profit_per_x",
    "annual_goal",
    "critical_number",
)
SKILL_COMMANDS = {
    "people": "/escala-people",
    "strategy": "/escala-strategy",
    "execution": "/escala-execution",
    "cash": "/escala-cash",
}


def build_strategy_plan(answers: Iterable[StrategyAnswer]) -> StrategyPlan:
    """Build a partial OPSP, preserving unresolved strategic decisions."""

    answer_map: dict[str, StrategyAnswer] = {}
    for answer in answers:
        answer_map[answer.key] = answer

    values: dict[str, str | None] = {}
    unresolved: list[str] = []
    questions: list[str] = []
    source_ids: set[str] = set()
    for key in STRATEGY_FIELDS:
        answer = answer_map.get(key)
        if answer is not None:
            source_ids.update(answer.source_ids)
        if answer is None or answer.status != "fact" or answer.value is None:
            values[key] = None
            unresolved.append(key)
            questions.append(
                answer.question
                if answer is not None and answer.question
                else f"¿Cuál es la definición de {key} ({key.replace('_', ' ')})?"
            )
            continue
        values[key] = str(answer.value)

    return StrategyPlan(
        vision=values["vision"],
        purpose=values["purpose"],
        bhag=values["bhag"],
        sandbox=values["sandbox"],
        brand_promise=values["brand_promise"],
        profit_per_x=values["profit_per_x"],
        annual_goal=values["annual_goal"],
        critical_number=values["critical_number"],
        source_ids=tuple(sorted(source_ids)),
        unresolved=tuple(unresolved),
        questions=tuple(questions),
        status="ready" if not unresolved else "needs_clarification",
    )


def route_coaching(
    request: CoachingRequest,
    diagnostic: ExecutiveDiagnostic,
) -> CoachingRoute:
    """Route explicit requests first, then the lowest supported decision."""

    if request.decision is not None:
        target = request.decision
        rationale = "Solicitud explícita del dueño; se conserva el contexto solicitado."
    else:
        supported = [
            item
            for item in diagnostic.assessments
            if item.score is not None and item.evidence_status == "supported"
        ]
        if supported:
            target = min(
                supported,
                key=lambda item: (
                    item.score if item.score is not None else 101,
                    DECISIONS.index(item.decision),
                ),
            ).decision
            rationale = "Se recomienda la decisión soportada con score más bajo."
        else:
            target = "strategy"
            rationale = "No hay una decisión soportada; se requiere aclarar antes de recomendar."

    assessment = diagnostic.assessment_for(target)
    supported = assessment.evidence_status == "supported"
    questions = assessment.questions if not supported else ()
    if not supported and not questions:
        questions = (
            f"Necesito evidencia o una respuesta del dueño para {target.title()}.",
        )
    return CoachingRoute(
        decision=target,
        skill=SKILL_COMMANDS[target],
        supported=supported,
        evidence_status=assessment.evidence_status,
        rationale=rationale,
        questions=questions,
    )
