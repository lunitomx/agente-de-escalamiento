"""Behavior tests for the E49 conversational welcome."""

from __future__ import annotations

from coaching.welcome.conversation import (
    MaturityProfile,
    WelcomeState,
    begin_welcome,
    respond_to_welcome,
)


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
    assert "execution" in turn.question.lower()
    assert turn.question.count("?") == 1
