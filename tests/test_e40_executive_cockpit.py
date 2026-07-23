from __future__ import annotations

import pytest
from pydantic import ValidationError

from escala_server.executive import (
    DiagnosticAnswer,
    EvidenceItem,
    ProfileAnswer,
    build_company_profile,
    build_diagnostic,
)
from escala_server.executive.models import Decision


def test_profile_preserves_unknowns_and_material_questions() -> None:
    result = build_company_profile(
        (
            ProfileAnswer(key="company_name", value="Nopal Foods", status="fact"),
            ProfileAnswer(key="industry", value="alimentos", status="fact"),
            ProfileAnswer(key="employees", value=28, status="fact"),
            ProfileAnswer(key="critical_number", value=None, status="unknown"),
            ProfileAnswer(
                key="stage",
                value="regional",
                status="inference",
                question="¿Es regional?",
            ),
        )
    )

    assert result.status == "needs_clarification"
    assert result.profile.field("company_name").value == "Nopal Foods"
    assert result.profile.field("critical_number").status == "unknown"
    assert result.unresolved_fields == ("stage", "critical_number")
    assert result.questions[0].field == "stage"


def test_profile_is_ready_when_required_facts_are_supplied() -> None:
    result = build_company_profile(
        (
            ProfileAnswer(key="company_name", value="Nopal Foods", status="fact"),
            ProfileAnswer(key="industry", value="alimentos", status="fact"),
            ProfileAnswer(key="stage", value="regional", status="fact"),
            ProfileAnswer(key="employees", value=28, status="fact"),
            ProfileAnswer(key="critical_number", value="margen bruto", status="fact"),
        )
    )

    assert result.status == "ready"
    assert result.unresolved_fields == ()
    assert [field.key for field in result.profile.fields] == [
        "company_name",
        "industry",
        "stage",
        "employees",
        "critical_number",
    ]


def test_diagnostic_emits_four_evidence_backed_0_to_100_assessments() -> None:
    scores: tuple[tuple[Decision, int], ...] = (
        ("people", 64),
        ("strategy", 51),
        ("execution", 73),
        ("cash", 42),
    )
    answers = tuple(
        DiagnosticAnswer(
            decision=decision, score=score, source_ids=(f"src-{decision}",)
        )
        for decision, score in scores
    )

    diagnostic = build_diagnostic(answers)

    assert [item.decision for item in diagnostic.assessments] == [
        "people",
        "strategy",
        "execution",
        "cash",
    ]
    assert diagnostic.assessment_for("cash").score == 42
    assert diagnostic.assessment_for("cash").evidence_status == "supported"
    assert diagnostic.assessment_for("cash").evidence_count == 1
    assert diagnostic.overall_score == 58


def test_diagnostic_keeps_missing_decision_evidence_limited() -> None:
    diagnostic = build_diagnostic(
        (DiagnosticAnswer(decision="people", score=80, source_ids=("people-1",)),)
    )

    cash = diagnostic.assessment_for("cash")
    assert cash.score is None
    assert cash.evidence_status == "evidence_limited"
    assert cash.questions == (
        "Necesito evidencia o una respuesta del dueño para Cash.",
    )
    assert diagnostic.status == "evidence_limited"


def test_owner_input_is_an_explicit_supported_attribution() -> None:
    diagnostic = build_diagnostic(
        (DiagnosticAnswer(decision="strategy", score=67, attribution="owner_input"),)
    )

    assessment = diagnostic.assessment_for("strategy")
    assert assessment.evidence_status == "supported"
    assert assessment.attribution == ("owner_input",)


def test_invalid_score_and_path_bearing_evidence_fail_closed() -> None:
    with pytest.raises(ValidationError):
        DiagnosticAnswer(decision="cash", score=101, source_ids=("cash-1",))

    with pytest.raises(ValidationError):
        EvidenceItem(source_id="cash-1", locator="/Users/private/transcript.txt")


def test_closed_models_reject_arbitrary_fields() -> None:
    with pytest.raises(ValidationError):
        ProfileAnswer.model_validate(
            {"key": "industry", "value": "alimentos", "status": "fact", "leaked": "no"}
        )
