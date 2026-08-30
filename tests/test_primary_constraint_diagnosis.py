"""S65.3 acceptance tests for the narrative primary-constraint runtime."""

from __future__ import annotations

import pytest

from coaching.diagnose.primary_constraint import (
    PrimaryConstraintRequest,
    diagnose_primary_constraint,
)


def _company() -> dict[str, object]:
    return {
        "industry": "Servicios B2B",
        "offering": "Implementación y soporte",
        "target_customer": "Empresas medianas",
        "business_model": "Proyectos recurrentes",
        "primary_challenge": "Cobrar antes sin afectar servicio",
        "unknown_fields": [],
    }


def _request(**overrides: object) -> PrimaryConstraintRequest:
    payload: dict[str, object] = {
        "company_summary": "La empresa vende servicios B2B y busca mejorar su ciclo de cobro.",
        "company_understanding": _company(),
        "evidence": [
            {
                "evidence_id": "conversation.cash.1",
                "question_id": "cash-detail",
                "decision": "cash",
                "value": "Entregamos antes de facturar y cobramos alrededor de sesenta días después.",
                "source_kind": "conversation",
                "source_ref": "conversation:welcome",
                "rationale": "Respuesta detallada de la dirección.",
                "freshness": "current",
                "confidence": "medium",
            }
        ],
        "decision_assessments": [
            {
                "decision": "people",
                "status": "unknown",
                "rationale": "Aún no hay detalle del equipo de liderazgo.",
                "evidence_ids": [],
            },
            {
                "decision": "strategy",
                "status": "unknown",
                "rationale": "Aún no hay detalle de la propuesta de valor.",
                "evidence_ids": [],
            },
            {
                "decision": "execution",
                "status": "unknown",
                "rationale": "Aún no hay detalle de prioridades y cadencias.",
                "evidence_ids": [],
            },
            {
                "decision": "cash",
                "status": "hypothesis",
                "rationale": "El desfase entre entrega y cobro puede limitar el avance.",
                "evidence_ids": ["conversation.cash.1"],
            },
        ],
        "requested_primary_decision": "cash",
        "open_questions": [
            "¿Qué monto y periodo representan las cuentas por cobrar actuales?"
        ],
    }
    payload.update(overrides)
    return PrimaryConstraintRequest.model_validate(payload)


def test_selects_one_requested_supported_constraint_without_a_score() -> None:
    result = diagnose_primary_constraint(_request())

    assert result.primary_constraint is not None
    assert result.primary_constraint.decision == "cash"
    assert result.missing_evidence == []
    assert result.persistence_status == "proposed_not_persisted"
    assert result.output_contract.artifact.status == "unknown"
    assert result.output_contract.owner.status == "unknown"
    assert result.output_contract.kpi.status == "unknown"
    assert result.output_contract.who_what_when.status == "unknown"
    assert result.output_contract.review_cadence.status == "unknown"
    assert "score" not in result.model_dump_json().lower()
    assert len(result.decision_explanations) == 4
    assert all(item.priority_reason for item in result.decision_explanations)


def test_unknown_requested_decision_returns_evidence_gap_not_an_invented_focus() -> (
    None
):
    result = diagnose_primary_constraint(_request(requested_primary_decision="people"))

    assert result.primary_constraint is None
    assert result.missing_evidence == ["people"]
    assert result.persistence_status == "proposed_not_persisted"
    assert "People" in result.confirmation_prompt


def test_rejects_untraced_evidence_and_cross_decision_assessment() -> None:
    with pytest.raises(ValueError, match="crosses decision evidence"):
        diagnose_primary_constraint(
            _request(
                decision_assessments=[
                    {
                        "decision": "people",
                        "status": "hypothesis",
                        "rationale": "El equipo parece saturado.",
                        "evidence_ids": ["conversation.cash.1"],
                    },
                    *_request().decision_assessments[1:],
                ]
            )
        )


def test_fail_closed_never_persists_known_or_confirmed_company_data(tmp_path) -> None:
    result = diagnose_primary_constraint(
        _request(), persistence_requested=True, state_root=tmp_path
    )

    assert result.persistence_status == "proposed_not_persisted"
    assert not list(tmp_path.rglob("*.yaml"))
    assert "E52" in result.persistence_reason


def test_rejects_multiple_assessments_for_one_decision() -> None:
    payload = _request().model_dump(mode="python")
    payload["decision_assessments"].append(payload["decision_assessments"][0])

    with pytest.raises(ValueError, match="exactly once"):
        PrimaryConstraintRequest.model_validate(payload)
