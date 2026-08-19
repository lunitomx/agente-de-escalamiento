"""Tests for E49 explainable scoring."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from coaching.diagnose import DiagnosticEvidence, DiagnosticIntake
from coaching.diagnose.explainable import score_diagnostic


def _evidence(
    evidence_id: str,
    decision: str,
    value: Any,
    **overrides: Any,
) -> DiagnosticEvidence:
    data: dict[str, Any] = {
        "evidence_id": evidence_id,
        "question_id": evidence_id,
        "decision": decision,
        "value": value,
        "applicability": "applicable",
        "answer_status": "fact",
        "source_kind": "conversation",
        "source_ref": "conversation:welcome",
        "captured_at": date(2026, 8, 19),
        "freshness": "current",
        "confidence": "high",
        "rationale": f"Evidencia {evidence_id}.",
    }
    data.update(overrides)
    return DiagnosticEvidence(**data)


def test_score_excludes_not_applicable_from_denominator() -> None:
    intake = DiagnosticIntake(
        evidence=[
            _evidence("commercial_q1", "commercial", 5),
            _evidence(
                "commercial_q6",
                "commercial",
                None,
                applicability="not_applicable",
                answer_status="unanswered",
                confidence="high",
                rationale="No hay vendedores.",
            ),
        ]
    )

    result = score_diagnostic(intake)

    commercial = result.scores["commercial"]
    assert commercial.score == 5.0
    assert commercial.applicable == 1
    assert commercial.excluded == 1
    assert "commercial_q6" in commercial.excluded_evidence_ids


def test_focus_contains_supporting_evidence_and_coverage() -> None:
    intake = DiagnosticIntake(
        evidence=[
            _evidence("people_q1", "people", 5),
            _evidence("execution_q1", "execution", 2),
            _evidence("execution_q2", "execution", 3),
            _evidence("cash_q1", "cash", 4),
        ]
    )

    result = score_diagnostic(intake)

    assert result.focus == "execution"
    assert result.focus_evidence_ids == ["execution_q1", "execution_q2"]
    assert result.scores["execution"].coverage == 1.0
    assert result.selection_rule == "lowest_score_then_decision_order"


def test_invalid_applicable_value_fails_closed() -> None:
    intake = DiagnosticIntake(evidence=[_evidence("cash_q1", "cash", 7)])

    with pytest.raises(ValueError, match="cash_q1"):
        score_diagnostic(intake)


def test_empty_intake_has_no_focus() -> None:
    result = score_diagnostic(DiagnosticIntake())

    assert result.focus is None
    assert result.focus_evidence_ids == []
