"""Explainable scoring for E49 diagnostic evidence."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .models import (
    Confidence,
    DecisionScore,
    DiagnosticEvidence,
    DiagnosticIntake,
    ExplainableDiagnosis,
)

DECISION_ORDER = ("people", "strategy", "execution", "cash")
REPORTING_ORDER = DECISION_ORDER + ("commercial",)
_CONFIDENCE_RANK: dict[Confidence, int] = {"low": 1, "medium": 2, "high": 3}


def _decision_for(item: DiagnosticEvidence) -> str:
    decision = item.decision or item.question_id.split("_", 1)[0]
    if decision not in REPORTING_ORDER:
        raise ValueError(f"{item.evidence_id}: unknown decision {decision!r}")
    return decision


def _confidence(items: list[DiagnosticEvidence]) -> Confidence:
    if not items:
        return "low"
    return min(items, key=lambda item: _CONFIDENCE_RANK[item.confidence]).confidence


def _numeric_value(item: DiagnosticEvidence) -> float:
    value: Any = item.value
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{item.evidence_id}: applicable answer must be numeric 1-5")
    if value < 1 or value > 5:
        raise ValueError(f"{item.evidence_id}: applicable answer must be numeric 1-5")
    return float(value)


def score_diagnostic(intake: DiagnosticIntake) -> ExplainableDiagnosis:
    """Score applicable answers and retain evidence for the selected focus."""
    grouped: dict[str, list[DiagnosticEvidence]] = defaultdict(list)
    for item in intake.evidence:
        grouped[_decision_for(item)].append(item)

    scores: dict[str, DecisionScore] = {}
    for decision in REPORTING_ORDER:
        items = grouped.get(decision, [])
        applicable_items = [
            item for item in items if item.applicability == "applicable"
        ]
        excluded_items = [
            item for item in items if item.applicability == "not_applicable"
        ]
        answered_items: list[DiagnosticEvidence] = []
        values: list[float] = []
        for item in applicable_items:
            if item.answer_status == "unanswered":
                continue
            values.append(_numeric_value(item))
            answered_items.append(item)
        score = round(sum(values) / len(values), 1) if values else None
        scores[decision] = DecisionScore(
            decision=decision,
            score=score,
            answered=len(answered_items),
            applicable=len(applicable_items),
            excluded=len(excluded_items),
            coverage=(len(answered_items) / len(applicable_items))
            if applicable_items
            else 0.0,
            confidence=_confidence(answered_items),
            evidence_ids=[item.evidence_id for item in answered_items],
            excluded_evidence_ids=[item.evidence_id for item in excluded_items],
        )

    scored = [
        scores[decision]
        for decision in DECISION_ORDER
        if scores[decision].score is not None
    ]
    if not scored:
        return ExplainableDiagnosis(scores=scores)

    focus = min(
        scored,
        key=lambda score: (score.score, DECISION_ORDER.index(score.decision)),
    )
    return ExplainableDiagnosis(
        scores=scores,
        focus=focus.decision,
        focus_evidence_ids=focus.evidence_ids,
    )
