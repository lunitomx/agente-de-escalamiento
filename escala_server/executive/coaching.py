"""Strategy/OPSP composition and four-decision coaching routing."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

from .models import (
    CoachingRequest,
    CoachingRoute,
    DECISIONS,
    ExecutiveDiagnostic,
    KeyCapability,
    OPSPAccountability,
    OPSPCell,
    OPSPColumn,
    OPSPRow,
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
LEGACY_FIELD_ALIASES = {
    "brand_promise": "brand_promises",
    "critical_number": "annual_critical_number",
}
OPSP_COLUMNS: tuple[tuple[str, bool], ...] = (
    ("Core Values and Purpose", False),
    ("BHAG and Key Capabilities", False),
    ("Brand Promises and Sandbox", False),
    ("Annual Plan", True),
    ("Q1", True),
    ("Q2", True),
    ("Q3", True),
)
OPSP_ROW_FIELDS: tuple[
    tuple[Literal["actions", "goals", "targets"], tuple[str, ...]], ...
] = (
    (
        "actions",
        (
            "core_values",
            "key_capabilities",
            "brand_promises",
            "annual_priorities",
            "q1_actions",
            "q2_actions",
            "q3_actions",
        ),
    ),
    (
        "goals",
        (
            "purpose",
            "bhag",
            "sandbox",
            "annual_goal",
            "q1_goals",
            "q2_goals",
            "q3_goals",
        ),
    ),
    (
        "targets",
        (
            "values_commitments",
            "three_to_five_year_targets",
            "profit_per_x",
            "annual_critical_number",
            "q1_critical_number",
            "q2_critical_number",
            "q3_critical_number",
        ),
    ),
)
OPSP_REQUIRED_FIELDS: tuple[str, ...] = ("vision",) + tuple(
    key for _, row_fields in OPSP_ROW_FIELDS for key in row_fields
)
SKILL_COMMANDS = {
    "people": "/escala-people",
    "strategy": "/escala-strategy",
    "execution": "/escala-execution",
    "cash": "/escala-cash",
}


def build_strategy_plan(answers: Iterable[StrategyAnswer]) -> StrategyPlan:
    """Build a complete OPSP structure, preserving every unresolved decision."""

    answer_map: dict[str, StrategyAnswer] = {}
    for answer in answers:
        answer_map[answer.key] = answer

    values: dict[str, str | None] = {}
    unresolved: list[str] = []
    questions: list[str] = []
    source_ids: set[str] = set()

    def unresolved_answer(key: str, answer: StrategyAnswer | None) -> None:
        unresolved.append(key)
        questions.append(
            answer.question
            if answer is not None and answer.question
            else f"¿Cuál es la definición de {key} ({key.replace('_', ' ')})?"
        )

    for key in STRATEGY_FIELDS:
        answer = answer_map.get(key)
        if answer is None and key in LEGACY_FIELD_ALIASES:
            answer = answer_map.get(LEGACY_FIELD_ALIASES[key])
        if answer is not None:
            source_ids.update(answer.source_ids)
        if answer is None or answer.status != "fact" or answer.value is None:
            values[key] = None
            continue
        values[key] = str(answer.value)

    rows: list[OPSPRow] = []
    for row_name, row_fields in OPSP_ROW_FIELDS:
        cells: list[OPSPCell] = []
        for column, key in enumerate(row_fields, start=1):
            answer = answer_map.get(key)
            if answer is not None:
                source_ids.update(answer.source_ids)
            is_fact = (
                answer is not None
                and answer.status == "fact"
                and answer.value is not None
            )
            if not is_fact:
                unresolved_answer(key, answer)
            value = str(answer.value) if is_fact and answer is not None else None
            accountability = (
                OPSPAccountability(person=answer.owner, responsibility=value)
                if is_fact
                and answer is not None
                and answer.owner is not None
                and value is not None
                else None
            )
            if is_fact and column >= 4 and accountability is None:
                unresolved.append(f"{key}_accountability")
                questions.append(
                    f"¿Quién asume la accountability de {key.replace('_', ' ')}?"
                )
            cells.append(
                OPSPCell(
                    key=key,
                    column=column,
                    value=value,
                    status=answer.status if answer is not None else "unknown",
                    question=answer.question if answer is not None else None,
                    accountability=accountability,
                )
            )
        rows.append(OPSPRow(name=row_name, cells=tuple(cells)))

    if (
        answer_map.get("vision") is None
        or answer_map["vision"].status != "fact"
        or answer_map["vision"].value is None
    ):
        unresolved_answer("vision", answer_map.get("vision"))

    capabilities_answer = answer_map.get("key_capabilities")
    key_capabilities = (
        (KeyCapability(description=str(capabilities_answer.value)),)
        if capabilities_answer is not None
        and capabilities_answer.status == "fact"
        and capabilities_answer.value is not None
        else ()
    )

    return StrategyPlan(
        vision=values["vision"],
        purpose=values["purpose"],
        bhag=values["bhag"],
        sandbox=values["sandbox"],
        brand_promise=values["brand_promise"],
        profit_per_x=values["profit_per_x"],
        annual_goal=values["annual_goal"],
        critical_number=values["critical_number"],
        columns=tuple(
            OPSPColumn(number=number, title=title, execution=execution)
            for number, (title, execution) in enumerate(OPSP_COLUMNS, start=1)
        ),
        rows=tuple(rows),
        key_capabilities=key_capabilities,
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
