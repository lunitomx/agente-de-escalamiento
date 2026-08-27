from __future__ import annotations

from datetime import date

import pytest

from escala_server.handlers import OutcomeLearningHandler
from escala_server.outcome_learning import (
    OutcomeLearningError,
    OutcomeLearningLedger,
    render_learning_cockpit_html,
)


def _accepted(ledger: OutcomeLearningLedger, area: str = "cash") -> dict:
    return ledger.register_decision(
        recommendation="Revisar el ciclo de cobro.",
        decision="Reducir días de cobranza.",
        area=area,
        status="accepted",
        decided_by="Dueño",
        reason="Es el cuello de botella actual.",
        evidence_ids=("source-001",),
        today=date(2026, 8, 27),
    )


def test_full_cycle_separates_observation_interpretation_and_learning(tmp_path) -> None:
    ledger = OutcomeLearningLedger(tmp_path, "acme")
    cycle = _accepted(ledger)
    action = ledger.add_action(
        cycle["id"],
        description="Contactar cuentas vencidas.",
        owner="Ana",
        review_on=date(2026, 9, 3),
        cadence="weekly",
        expected_result="Reducir cuentas vencidas.",
        metric="días de cobranza",
    )
    assert ledger.reviews_due(date(2026, 9, 2)) == []
    assert ledger.reviews_due(date(2026, 9, 3))[0]["owner"] == "Ana"
    result = ledger.record_result(
        cycle["id"],
        action["id"],
        status="observed",
        observed="Bajaron 3 días.",
        evidence_ids=("cash-report-1",),
        interpretation="La cobranza mejoró.",
    )
    assert result["causality"] == "unconfirmed"
    learning = ledger.confirm_learning(
        cycle["id"],
        result["id"],
        statement="Las llamadas semanales ayudan a detectar cobros bloqueados.",
        status="confirmed",
        confirmed_by="Dueño",
        confidence=80,
    )
    assert learning["causality"] == "not_claimed"
    assert len(ledger.reusable_learnings(date(2026, 9, 4))) == 1


def test_rejected_or_deferred_decisions_cannot_create_actions(tmp_path) -> None:
    ledger = OutcomeLearningLedger(tmp_path, "acme")
    decision = ledger.register_decision(
        recommendation="Cambiar precios.",
        decision="Esperar.",
        area="strategy",
        status="deferred",
        decided_by="Dueño",
        reason="Falta evidencia.",
    )
    with pytest.raises(OutcomeLearningError, match="accepted"):
        ledger.add_action(
            decision["id"],
            description="Cambiar lista.",
            owner="Ana",
            review_on=date(2026, 9, 1),
            cadence="monthly",
            expected_result="Mejor margen.",
        )


def test_no_result_is_valid_and_does_not_create_a_false_failure(tmp_path) -> None:
    ledger = OutcomeLearningLedger(tmp_path, "acme")
    cycle = _accepted(ledger, "execution")
    action = ledger.add_action(
        cycle["id"],
        description="Instalar WWW.",
        owner="Luis",
        review_on=date(2026, 8, 28),
        cadence="daily",
        expected_result="Compromisos claros.",
    )
    result = ledger.record_result(
        cycle["id"], action["id"], status="no_result_yet", observed=None
    )
    assert result["status"] == "no_result_yet"
    assert ledger.cockpit(date(2026, 8, 28))["learnings_pending"] == 1


def test_people_learning_requires_consent_and_other_pillars_can_complete(
    tmp_path,
) -> None:
    ledger = OutcomeLearningLedger(tmp_path, "acme")
    for area in ("people", "strategy", "execution", "cash"):
        cycle = _accepted(ledger, area)
        action = ledger.add_action(
            cycle["id"],
            description="Acción concreta.",
            owner="Ana",
            review_on=date(2026, 8, 28),
            cadence="daily",
            expected_result="Resultado claro.",
        )
        result = ledger.record_result(
            cycle["id"], action["id"], status="observed", observed="Cambio medido."
        )
        if area == "people":
            with pytest.raises(OutcomeLearningError, match="consent"):
                ledger.confirm_learning(
                    cycle["id"],
                    result["id"],
                    statement="Lección.",
                    status="confirmed",
                    confirmed_by="Dueño",
                    confidence=70,
                )
            ledger.confirm_learning(
                cycle["id"],
                result["id"],
                statement="Lección.",
                status="confirmed",
                confirmed_by="Dueño",
                confidence=70,
                people_consent=True,
            )
        else:
            ledger.confirm_learning(
                cycle["id"],
                result["id"],
                statement="Lección.",
                status="confirmed",
                confirmed_by="Dueño",
                confidence=70,
            )
    assert len(ledger.reusable_learnings(date(2026, 8, 29))) == 4


def test_cockpit_is_company_scoped_and_exposes_next_review_only(tmp_path) -> None:
    first = OutcomeLearningLedger(tmp_path, "acme")
    second = OutcomeLearningLedger(tmp_path, "other")
    cycle = _accepted(first)
    first.add_action(
        cycle["id"],
        description="Cobrar.",
        owner="Ana",
        review_on=date(2026, 8, 27),
        cadence="weekly",
        expected_result="Cobrar antes.",
    )
    assert first.cockpit(date(2026, 8, 27))["reviews_due"] == 1
    assert second.cockpit(date(2026, 8, 27))["reviews_due"] == 0


def test_api_handler_exposes_human_decision_and_company_scoped_cockpit(
    tmp_path,
) -> None:
    handler = OutcomeLearningHandler(tmp_path)
    decision = handler.create_decision(
        "acme",
        {
            "recommendation": "Revisar cobertura.",
            "decision": "Cobrar semanalmente.",
            "area": "cash",
            "status": "accepted",
            "decided_by": "Dueño",
            "reason": "Hay evidencia suficiente.",
            "decided_on": "2026-08-27",
        },
    )
    assert decision["status"] == "ok"
    action = handler.create_action(
        "acme",
        decision["data"]["id"],
        {
            "description": "Llamar cartera vencida.",
            "owner": "Ana",
            "review_on": "2026-08-28",
            "cadence": "daily",
            "expected_result": "Cobros al día.",
        },
    )
    assert action["status"] == "ok"
    assert handler.cockpit("acme", on="2026-08-28")["data"]["reviews_due"] == 1
    assert handler.cockpit("other", on="2026-08-28")["data"]["reviews_due"] == 0


def test_owner_cockpit_hides_ids_and_renders_business_language(tmp_path) -> None:
    ledger = OutcomeLearningLedger(tmp_path, "acme")
    cycle = _accepted(ledger)
    ledger.add_action(
        cycle["id"],
        description="Cobrar.",
        owner="Ana",
        review_on=date(2026, 8, 27),
        cadence="weekly",
        expected_result="Cobrar antes.",
    )
    cockpit = ledger.cockpit(date(2026, 8, 27))
    assert "cycle_id" not in cockpit["next_review"]
    assert "action_id" not in cockpit["next_review"]
    page = render_learning_cockpit_html(cockpit)
    assert "Seguimiento de decisiones" in page
    assert cycle["id"] not in page


def test_runtime_rejects_unknown_states_and_unsafe_company_id(tmp_path) -> None:
    ledger = OutcomeLearningLedger(tmp_path, "acme")
    with pytest.raises(OutcomeLearningError, match="decision status"):
        ledger.register_decision(
            recommendation="Recomendación.",
            decision="Decisión.",
            area="cash",
            status="invented",  # type: ignore[arg-type]
            decided_by="Dueño",
            reason="Motivo.",
        )
    assert OutcomeLearningHandler(tmp_path).cockpit("../unsafe")["status"] == "error"
