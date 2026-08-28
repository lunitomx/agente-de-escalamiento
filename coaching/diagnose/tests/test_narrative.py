"""Acceptance tests for the E75 narrative-first diagnostic contract."""

from __future__ import annotations

import pytest

from coaching.core import read_yaml
from coaching.diagnose import (
    DiagnosticEvidence,
    build_diagnostic_intake,
    build_narrative_assessment,
    run,
)


def _evidence() -> DiagnosticEvidence:
    return DiagnosticEvidence(
        evidence_id="welcome.cash.1",
        question_id="cash-open-1",
        decision="cash",
        value="Cobramos normalmente sesenta días después de entregar.",
        source_kind="conversation",
        source_ref="conversation:welcome",
        rationale="Respuesta detallada de la persona dueña.",
        freshness="current",
        confidence="medium",
    )


def _company_understanding(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "industry": "Alimentos",
        "offering": "Alimentos preparados",
        "target_customer": "Tiendas independientes",
        "business_model": "Venta B2B recurrente",
        "primary_challenge": "Crecer sin tensionar caja",
        "unknown_fields": [],
    }
    value.update(overrides)
    return value


def _context(**overrides: object) -> dict[str, object]:
    context: dict[str, object] = {
        "action": "narrative_assessment",
        "company": {"name": "Nopal Foods"},
        "company_summary": "Nopal Foods vende alimentos y busca crecer sin tensionar caja.",
        "company_understanding": _company_understanding(),
        "evidence": [_evidence().model_dump(mode="json")],
        "findings": [
            {
                "decision": "cash",
                "statement": "El desfase entre entrega y cobro parece tensionar caja",
                "evidence_ids": ["welcome.cash.1"],
                "status": "hypothesis",
                "confidence": "medium",
                "implication": "Conviene confirmar periodo, cobros y obligaciones.",
            }
        ],
        "proposed_focuses": [
            {
                "decision": "cash",
                "rationale": "Es la señal con mayor impacto declarado por la dueña.",
                "evidence_ids": ["welcome.cash.1"],
            }
        ],
        "open_questions": ["¿Qué periodo cubren esos sesenta días?"],
        "confirmation_status": "pending",
    }
    context.update(overrides)
    return context


def test_narrative_assessment_renders_evidence_and_unknowns_without_score() -> None:
    result = run(_context())

    assert result["errors"] == []
    output = result["output"]
    assert "## Esto es lo que entendí" in output
    assert "Lo que todavía necesito entender" in output
    assert "Score" not in output
    assert (
        result["artifacts"]["assessment"]["proposed_focuses"][0]["decision"] == "cash"
    )


def test_company_understanding_makes_missing_fields_explicit() -> None:
    result = run(
        _context(
            company_understanding={
                "industry": "Alimentos",
                "offering": None,
                "target_customer": None,
                "business_model": None,
                "primary_challenge": "Crecer con caja estable",
                "unknown_fields": ["offering", "target_customer", "business_model"],
            }
        )
    )

    assert result["errors"] == []
    assert "**Oferta:** todavía no lo sé" in result["output"]


def test_company_understanding_rejects_silent_missing_field() -> None:
    result = run(
        _context(
            company_understanding={
                "industry": "Alimentos",
                "offering": None,
                "target_customer": "Tiendas",
                "business_model": "B2B",
                "primary_challenge": "Caja",
                "unknown_fields": [],
            }
        )
    )

    assert result["errors"]
    assert "must mark missing fields unknown" in result["errors"][0]


def test_narrative_assessment_rejects_unknown_evidence_reference() -> None:
    intake = build_diagnostic_intake(evidence=[_evidence()])

    with pytest.raises(ValueError, match="unknown evidence"):
        build_narrative_assessment(
            intake,
            company_summary="Empresa con una tensión conocida.",
            company_understanding=_company_understanding(),
            findings=[
                {
                    "decision": "cash",
                    "statement": "La cobranza parece lenta.",
                    "evidence_ids": ["missing.evidence"],
                    "implication": "Hay que confirmar el periodo.",
                }
            ],
        )


def test_narrative_assessment_rejects_cross_decision_evidence() -> None:
    intake = build_diagnostic_intake(evidence=[_evidence()])

    with pytest.raises(ValueError, match="crosses decision"):
        build_narrative_assessment(
            intake,
            company_summary="Empresa con una tensión conocida.",
            company_understanding=_company_understanding(),
            findings=[
                {
                    "decision": "people",
                    "statement": "El equipo parece sobrecargado.",
                    "evidence_ids": ["welcome.cash.1"],
                    "implication": "Hay que confirmar responsables.",
                }
            ],
        )


def test_unknown_only_decision_cannot_be_proposed_as_focus() -> None:
    result = run(
        _context(
            findings=[
                {
                    "decision": "cash",
                    "statement": "No sabemos todavía cómo se cobra.",
                    "evidence_ids": ["welcome.cash.1"],
                    "status": "unknown",
                    "implication": "Hace falta entender el ciclo.",
                }
            ]
        )
    )

    assert result["errors"]
    assert "unknown-only" in result["errors"][0]


def test_narrative_assessment_requires_confirmation_before_persistence(
    tmp_path,
) -> None:
    result = run(_context(base_path=str(tmp_path), persist_authorized=True))

    assert result["errors"] == [
        "El assessment requiere confirmación o corrección antes de guardarse."
    ]
    assert not (
        tmp_path / ".escala" / "agent" / "memory" / "company-profile.yaml"
    ).exists()


def test_confirmed_narrative_assessment_persists_only_when_authorized(tmp_path) -> None:
    result = run(
        _context(
            base_path=str(tmp_path),
            confirmation_status="corrected",
            persist_authorized=True,
        )
    )

    assert result["errors"] == []
    profile = read_yaml(
        tmp_path / ".escala" / "agent" / "memory" / "company-profile.yaml"
    )
    assert profile["narrative_assessments"][0]["confirmation_status"] == "corrected"
    assert profile["narrative_assessment"]["company_understanding"]["offering"] == (
        "Alimentos preparados"
    )
