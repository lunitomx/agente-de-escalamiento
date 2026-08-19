"""Tests for the local diagnostic result contract."""

from __future__ import annotations

from datetime import date
from typing import Any

from coaching.diagnose import (
    DiagnosticEvidence,
    DiagnosticIntake,
    FunnelMetrics,
    score_diagnostic,
)
from coaching.diagnose.result import build_diagnostic_result


def _evidence(evidence_id: str, decision: str, value: Any) -> DiagnosticEvidence:
    return DiagnosticEvidence(
        evidence_id=evidence_id,
        question_id=evidence_id,
        decision=decision,
        value=value,
        source_kind="conversation",
        source_ref="conversation:welcome",
        captured_at=date(2026, 8, 19),
        freshness="current",
        confidence="high",
        rationale="Respuesta de prueba.",
    )


def test_result_contains_focus_and_bounded_route() -> None:
    intake = DiagnosticIntake(
        company={"name": "Demo"},
        evidence=[
            _evidence("people_q1", "people", 5),
            _evidence("execution_q1", "execution", 2),
        ],
        funnel=FunnelMetrics(prospects=10, conversations=4, proposals=2, wins=1),
    )
    diagnosis = score_diagnostic(intake)

    result = build_diagnostic_result(intake, diagnosis, generated_at="2026-08-19")

    assert result.diagnosis.focus == "execution"
    assert result.diagnosis.focus_evidence_ids == ["execution_q1"]
    assert len(result.route) <= 2
    assert result.route[0].decision == "execution"
    assert result.funnel is not None
    assert result.funnel.total_prospects == 10


def test_result_keeps_explicit_route_when_provided() -> None:
    intake = DiagnosticIntake(evidence=[_evidence("cash_q1", "cash", 2)])
    diagnosis = score_diagnostic(intake)
    route = [{"quarter": "Q1", "decision": "cash", "action": "Revisar CCC"}]

    result = build_diagnostic_result(intake, diagnosis, route=route)

    assert len(result.route) == 1
    assert result.route[0].action == "Revisar CCC"
