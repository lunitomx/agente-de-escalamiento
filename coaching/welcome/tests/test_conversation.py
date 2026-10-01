"""Behavior tests for the E49 conversational welcome."""

from __future__ import annotations

from coaching.evidence.dashboard import MetricRequirement
from coaching.evidence.facts import Fact, save_fact
from coaching.welcome.conversation import (
    MaturityProfile,
    WelcomeState,
    begin_welcome,
    respond_to_welcome,
    respond_to_welcome_with_evidence,
    respond_to_welcome_from_local_evidence,
)


def test_opening_requirements_cover_each_decision() -> None:
    from coaching.welcome.conversation import default_onboarding_requirements

    assert {
        requirement.decision for requirement in default_onboarding_requirements()
    } == {
        "people",
        "strategy",
        "execution",
        "cash",
    }


def test_first_contact_asks_one_concern_question_without_commands() -> None:
    turn = begin_welcome()

    assert turn.state.phase == "concern"
    assert turn.question.count("?") == 1
    assert "/" not in turn.question
    assert "skill" not in turn.question.lower()


def test_vague_concern_narrows_to_one_question() -> None:
    turn = respond_to_welcome(
        WelcomeState(phase="concern"), "Todo está mal y no sé por dónde empezar."
    )

    assert turn.state.profile == MaturityProfile.EXPLORER
    assert turn.state.phase == "narrow"
    assert turn.state.area is None
    assert turn.question.count("?") == 1


def test_specific_pain_routes_and_asks_for_source_context() -> None:
    turn = respond_to_welcome(
        WelcomeState(phase="concern"), "Mis ventas bajaron y no sé cuánto cash tengo."
    )

    assert turn.state.profile == MaturityProfile.SPECIFIC
    assert turn.state.area == "cash"
    assert turn.state.phase == "source"
    assert turn.state.next_action == "evidence"
    assert turn.question.count("?") == 1
    assert "/" not in turn.question


def test_directed_request_routes_without_a_tour() -> None:
    turn = respond_to_welcome(
        WelcomeState(phase="concern"), "Necesito calcular mi CCC este trimestre."
    )

    assert turn.state.profile == MaturityProfile.DIRECTED
    assert turn.state.area == "cash"
    assert turn.state.next_action == "direct"


def test_returning_user_gets_continuity_prompt() -> None:
    turn = begin_welcome(returning=True, previous_focus="execution")

    assert turn.state.phase == "continuity"
    assert "tu día a día" in turn.question.lower()  # S86.2: área en español
    assert turn.question.count("?") == 1


def test_evidence_aware_welcome_skips_known_fact_and_asks_next_gap() -> None:
    turn = respond_to_welcome_with_evidence(
        WelcomeState(phase="concern"),
        "Necesito entender mi cash.",
        facts=[
            Fact(
                metric_definition="Ingreso",
                period="2026-07",
                source="ERP",
                confidence="high",
                value=100,
                decision="cash",
            )
        ],
        requirements=[
            MetricRequirement(
                metric_definition="Ingreso",
                decision="cash",
                question="¿Cuál fue el ingreso?",
            ),
            MetricRequirement(
                metric_definition="Cobros",
                decision="cash",
                question="¿Cuánto cobraste realmente?",
            ),
        ],
    )

    assert turn.question == "¿Cuánto cobraste realmente?"
    assert turn.question.count("?") == 1
    assert turn.state.next_action == "evidence"


def test_evidence_aware_welcome_explains_noncomparable_fact() -> None:
    turn = respond_to_welcome_with_evidence(
        WelcomeState(phase="concern"),
        "Necesito entender mi cash.",
        facts=[
            Fact(
                metric_definition="Cobros",
                period="2026-07",
                source="reporte parcial",
                confidence="medium",
                value=20,
                comparable=False,
                decision="cash",
            )
        ],
        requirements=[
            MetricRequirement(
                metric_definition="Cobros",
                decision="cash",
                question="¿Qué periodo cubre exactamente?",
            )
        ],
    )

    assert "no es comparable" in turn.question
    assert turn.question.count("?") == 1


def test_evidence_aware_welcome_proceeds_when_all_requirements_are_known() -> None:
    turn = respond_to_welcome_with_evidence(
        WelcomeState(phase="concern"),
        "Necesito entender mi cash.",
        facts=[
            Fact(
                metric_definition="Cobros",
                period="2026-07",
                source="ERP",
                confidence="high",
                value=20,
                decision="cash",
            )
        ],
        requirements=[
            MetricRequirement(
                metric_definition="Cobros",
                decision="cash",
                question="¿Cuánto cobraste?",
            )
        ],
    )

    assert turn.state.next_action == "direct"
    assert turn.question.count("?") == 1


def test_evidence_aware_welcome_loads_only_local_facts(tmp_path) -> None:
    save_fact(
        tmp_path,
        Fact(
            metric_definition="Cobros",
            period="2026-07",
            source="ERP",
            confidence="high",
            value=20,
            decision="cash",
        ),
    )
    turn = respond_to_welcome_from_local_evidence(
        WelcomeState(phase="concern"),
        "Necesito entender mi cash.",
        base_path=tmp_path,
        requirements=[
            MetricRequirement(
                metric_definition="Cobros",
                decision="cash",
                question="¿Cuánto cobraste?",
            )
        ],
    )

    assert turn.state.next_action == "direct"
