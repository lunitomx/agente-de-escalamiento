"""Tests for the optional evidence pack and funnel intake."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from pydantic import ValidationError

from coaching.diagnose import DiagnosticEvidence
from coaching.diagnose.intake import build_diagnostic_intake


def _answer(evidence_id: str, **overrides: Any) -> DiagnosticEvidence:
    data: dict[str, Any] = {
        "evidence_id": evidence_id,
        "question_id": evidence_id,
        "value": 3,
        "applicability": "applicable",
        "answer_status": "fact",
        "source_kind": "conversation",
        "source_ref": "conversation:welcome",
        "captured_at": date(2026, 8, 19),
        "freshness": "current",
        "confidence": "high",
        "rationale": "Respuesta aportada durante la conversación.",
    }
    data.update(overrides)
    return DiagnosticEvidence(**data)


def test_build_intake_preserves_mixed_source_status() -> None:
    intake = build_diagnostic_intake(
        company={"name": "Demo"},
        evidence=[
            _answer("execution_q1"),
            _answer(
                "funnel_prospects",
                value=40,
                answer_status="estimate",
                source_kind="estimate",
                source_ref="estimate:user",
                confidence="medium",
            ),
        ],
        funnel={"prospects": 40, "conversations": 12, "proposals": 6, "wins": 3},
        open_context={"obstacle": "Falta de ritmo"},
    )

    assert intake.evidence[1].answer_status == "estimate"
    assert intake.funnel is not None
    assert intake.funnel.total_prospects == 40
    assert intake.open_context["obstacle"] == "Falta de ritmo"


def test_optional_average_sale_stays_absent() -> None:
    intake = build_diagnostic_intake(
        company={}, evidence=[], funnel={"prospects": 5, "average_sale": None}
    )

    assert intake.funnel is not None
    assert intake.funnel.average_sale is None


def test_negative_funnel_count_fails_before_consumers() -> None:
    with pytest.raises(ValidationError, match="prospects"):
        build_diagnostic_intake(company={}, evidence=[], funnel={"prospects": -1})


def test_not_applicable_evidence_survives_intake() -> None:
    intake = build_diagnostic_intake(
        company={},
        evidence=[
            _answer(
                "commercial_q6",
                value=None,
                applicability="not_applicable",
                answer_status="unanswered",
                rationale="No hay vendedores.",
            )
        ],
    )

    assert intake.evidence[0].applicability == "not_applicable"
    assert intake.evidence[0].included_in_score is False
