"""Evidence-backed four-decision diagnostic for E40."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .models import (
    DECISIONS,
    DecisionAssessment,
    DiagnosticAnswer,
    ExecutiveDiagnostic,
    Freshness,
)


_MISSING_QUESTION = {
    "people": "Necesito evidencia o una respuesta del dueño para People.",
    "strategy": "Necesito evidencia o una respuesta del dueño para Strategy.",
    "execution": "Necesito evidencia o una respuesta del dueño para Execution.",
    "cash": "Necesito evidencia o una respuesta del dueño para Cash.",
}


def build_diagnostic(answers: Iterable[DiagnosticAnswer]) -> ExecutiveDiagnostic:
    """Aggregate answer scores deterministically and fail closed on missing data."""

    grouped: dict[str, list[DiagnosticAnswer]] = defaultdict(list)
    for answer in answers:
        grouped[answer.decision].append(answer)

    assessments: list[DecisionAssessment] = []
    supported_scores: list[int] = []
    for decision in DECISIONS:
        items = grouped.get(decision, [])
        source_ids = tuple(
            sorted({source_id for item in items for source_id in item.source_ids})
        )
        attribution = tuple(
            sorted(
                {
                    *(source_ids),
                    *(
                        "owner_input"
                        for item in items
                        if item.attribution == "owner_input"
                    ),
                }
            )
        )
        if not items or not attribution:
            assessments.append(
                DecisionAssessment(
                    decision=decision,
                    evidence_status="evidence_limited",
                    evidence_count=0,
                    questions=(_MISSING_QUESTION[decision],),
                )
            )
            continue

        score = round(sum(item.score for item in items) / len(items))
        freshness = _combine_freshness(item.freshness for item in items)
        blockers = tuple(
            sorted({item.blocker for item in items if item.blocker is not None})
        )
        assessments.append(
            DecisionAssessment(
                decision=decision,
                score=score,
                evidence_status="supported",
                evidence_count=len(items),
                source_ids=source_ids,
                attribution=attribution,
                freshness=freshness,
                blockers=blockers,
            )
        )
        supported_scores.append(score)

    status = (
        "supported" if len(supported_scores) == len(DECISIONS) else "evidence_limited"
    )
    return ExecutiveDiagnostic(
        assessments=tuple(assessments),
        overall_score=(
            round(sum(supported_scores) / len(supported_scores))
            if supported_scores
            else None
        ),
        status=status,
    )


def _combine_freshness(values: Iterable[Freshness]) -> Freshness:
    """Collapse freshness without treating an unknown input as stale."""

    states = set(values)
    if "stale" in states:
        return "stale"
    if states == {"fresh"}:
        return "fresh"
    return "unknown"
