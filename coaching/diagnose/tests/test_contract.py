"""Contract tests for E49 diagnostic evidence."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from pydantic import ValidationError

from coaching.diagnose.models import DiagnosticEvidence, DiagnosticIntake


def _evidence(**overrides: object) -> DiagnosticEvidence:
    data: dict[str, Any] = {
        "evidence_id": "execution_q2",
        "question_id": "execution_q2",
        "value": 2,
        "applicability": "applicable",
        "answer_status": "fact",
        "source_kind": "conversation",
        "source_ref": "conversation:welcome",
        "captured_at": date(2026, 8, 19),
        "freshness": "current",
        "confidence": "high",
        "rationale": "El equipo no revisa un KPI semanal visible.",
    }
    data.update(overrides)
    return DiagnosticEvidence(**data)


def test_valid_evidence_serializes_with_stable_id() -> None:
    evidence = _evidence()

    assert evidence.evidence_id == "execution_q2"
    assert evidence.included_in_score is True
    assert evidence.model_dump(mode="json")["source_ref"] == "conversation:welcome"


def test_not_applicable_is_not_a_zero_score() -> None:
    evidence = _evidence(
        evidence_id="commercial_q6",
        question_id="commercial_q6",
        value=None,
        applicability="not_applicable",
        answer_status="unanswered",
        source_kind="conversation",
        confidence="high",
        rationale="La empresa no tiene vendedores.",
    )

    assert evidence.value is None
    assert evidence.included_in_score is False


def test_unknown_or_unanswered_is_not_included() -> None:
    evidence = _evidence(
        value=None,
        applicability="unknown",
        answer_status="unanswered",
        confidence="low",
    )

    assert evidence.included_in_score is False


@pytest.mark.parametrize(
    "source_ref",
    ["/Users/private.csv", "https://example.com/data.csv", "../../outside.csv"],
)
def test_unsafe_source_reference_fails_closed(source_ref: str) -> None:
    with pytest.raises(ValidationError, match="source_ref"):
        _evidence(source_ref=source_ref)


def test_intake_requires_a_local_or_redacted_source_for_answers() -> None:
    intake = DiagnosticIntake(
        company={"name": "Demo", "employees": 6},
        evidence=[_evidence()],
        funnel={"prospects": 10, "conversations": 4},
        open_context={"obstacle": "Falta de ritmo"},
    )

    assert intake.evidence[0].evidence_id == "execution_q2"
    assert intake.funnel["prospects"] == 10
