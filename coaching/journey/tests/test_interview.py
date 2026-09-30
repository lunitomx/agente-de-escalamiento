"""The journey interview: one question per stage, at most one follow-up.

Ultra simple: 5 questions (what happens + roughly how many last month), plus
at most one follow-up where the biggest drop is. "No sé" is valid; an
approximate count ("unos 100", "entre 80 y 120") is kept as a supuesto and
never asked again. Only an answer with no number at all gets one short retry.
"""

from __future__ import annotations

from datetime import date

import pytest

from coaching.journey import messages
from coaching.journey.interview import (
    OWNER_SOURCE,
    STAGES,
    Answer,
    InterviewStep,
    interview_step,
    is_dont_know,
    last_month,
    parse_count,
)

TODAY = date(2026, 10, 2)


def _answer(stage: str, field: str, answer: str) -> Answer:
    return Answer.model_validate({"stage": stage, "field": field, "answer": answer})


def _run(
    replies: dict[str, str], follow_up: str = "No les contesto rápido"
) -> tuple[InterviewStep, list[InterviewStep]]:
    """Answer every question until the end; returns the last step and all asked."""
    answers: list[Answer] = []
    asked: list[InterviewStep] = []
    while True:
        step = interview_step(answers, TODAY)
        if step.done:
            return step, asked
        asked.append(step)
        assert step.stage is not None and step.field is not None
        if step.field == "friccion":
            reply = follow_up
        elif step.field == "conteo":
            reply = "no sé"
        else:
            reply = replies[step.stage]
        answers.append(_answer(step.stage, step.field, reply))


PAN_RICO = {
    "se_entera": "Por Instagram, unos 300",
    "pregunta": "Me escriben por WhatsApp, como 120",
    "compra": "Pasan al local, 18",
    "recibe": "Se lo llevan ese día, 18",
    "regresa": "Regresan pocos, entre 5 y 9",
}


def test_five_fixed_stages_in_order() -> None:
    assert STAGES == ("se_entera", "pregunta", "compra", "recibe", "regresa")


def test_first_question_asks_what_happens_and_how_many_in_one_message() -> None:
    step = interview_step([], TODAY)

    assert step.done is False
    assert (step.stage, step.field) == ("se_entera", "paso")
    assert "1 de 5" in step.message
    assert "cuántos" in step.message
    assert "septiembre de 2026" in step.message
    assert "no sé" in step.message
    assert step.draft.saved is False


def test_whole_interview_is_at_most_six_questions() -> None:
    last, asked = _run(PAN_RICO)

    assert last.done is True
    assert len(asked) == 6
    assert [s.field for s in asked] == ["paso"] * 5 + ["friccion"]


def test_every_question_is_exactly_one_plain_question() -> None:
    _, asked = _run(PAN_RICO)

    for step in asked:
        assert step.message.count("?") == 1, step.message
        assert step.message.count("¿") == 1, step.message
        lowered = step.message.lower()
        for jargon in ("journey", "embudo", "funnel", "/escala", "módulo"):
            assert jargon not in lowered
        assert "de dónde sale" not in lowered


def test_the_follow_up_names_the_biggest_drop_once() -> None:
    last, asked = _run(PAN_RICO)

    follow_up = asked[-1]
    assert follow_up.stage == "compra"  # 120 -> 18 is the biggest drop
    assert "«Te pregunta»" in follow_up.message
    assert "«Te compra»" in follow_up.message
    assert last.draft.biggest_drop is not None
    assert last.draft.biggest_drop.from_stage == "pregunta"
    assert last.draft.biggest_drop.to_stage == "compra"
    assert last.draft.stages[2].friccion == "No les contesto rápido"


def test_no_follow_up_without_two_counts_to_compare() -> None:
    replies = {stage: "no sé" for stage in STAGES}

    last, asked = _run(replies)

    assert len(asked) == 5
    assert last.draft.biggest_drop is None


def test_ask_message_promises_the_real_length() -> None:
    for text in (messages.ASK_NEW, messages.ASK_UPDATE):
        assert f"{len(STAGES)} preguntas cortas" in text
        assert "minutos" not in text


def test_last_month_handles_january() -> None:
    assert last_month(date(2026, 1, 15)) == ("2025-12", "diciembre de 2025")
    assert last_month(TODAY) == ("2026-09", "septiembre de 2026")


@pytest.mark.parametrize(
    "text", ["no sé", "No se", "NO LO SÉ", "ni idea", "No tengo idea", "  ", "nose"]
)
def test_dont_know_is_a_valid_answer(text: str) -> None:
    assert is_dont_know(text) is True


@pytest.mark.parametrize("text", ["nada", "no lo anoto", "Sé que tardo"])
def test_real_answers_are_not_dont_know(text: str) -> None:
    assert is_dont_know(text) is False


@pytest.mark.parametrize(
    ("text", "value"),
    [
        ("120", 120),
        ("1,200", 1200),
        ("1.200", 1200),
        (" 18 ", 18),
        ("0", 0),
        ("Me escriben por WhatsApp, 45", 45),
    ],
)
def test_a_plain_number_is_an_exact_count(text: str, value: int) -> None:
    count = parse_count(text)

    assert count is not None
    assert (count.value, count.upper, count.supuesto) == (value, None, False)


@pytest.mark.parametrize(
    ("text", "value", "upper"),
    [
        ("unos 100", 100, None),
        ("como 100", 100, None),
        ("Como 50 por WhatsApp", 50, None),
        ("más o menos 30", 30, None),
        ("casi 200", 200, None),
        ("entre 80 y 120", 80, 120),
        ("de 120 a 80", 80, 120),
        ("100-150", 100, 150),
    ],
)
def test_an_approximation_is_kept_as_a_supuesto(
    text: str, value: int, upper: int | None
) -> None:
    count = parse_count(text)

    assert count is not None
    assert (count.value, count.upper, count.supuesto) == (value, upper, True)


@pytest.mark.parametrize(
    "text", ["muchos", "Me escriben por WhatsApp", "12.5", "3 y 40"]
)
def test_no_single_number_is_not_a_count(text: str) -> None:
    assert parse_count(text) is None


def test_approximation_is_not_asked_again_and_is_flagged() -> None:
    answers = [_answer("se_entera", "paso", "Por Instagram, unos 100")]

    step = interview_step(answers, TODAY)
    first = step.draft.stages[0]

    assert (step.stage, step.field) == ("pregunta", "paso")
    assert (first.conteo, first.conteo_supuesto) == (100, True)
    assert first.fuente_conteo == OWNER_SOURCE == "lo dijo el dueño"
    assert first.que_pasa == "Por Instagram, unos 100"


def test_a_range_keeps_both_ends() -> None:
    answers = [_answer("se_entera", "paso", "entre 80 y 120")]

    first = interview_step(answers, TODAY).draft.stages[0]

    assert (first.conteo, first.conteo_hasta, first.conteo_supuesto) == (80, 120, True)


def test_no_number_at_all_gets_one_short_retry_then_moves_on() -> None:
    answers = [_answer("se_entera", "paso", "Por Instagram")]

    retry = interview_step(answers, TODAY)
    assert (retry.stage, retry.field, retry.retry) == ("se_entera", "conteo", True)
    assert "cuántos" in retry.message
    assert "aproximado" in retry.message

    answers.append(_answer("se_entera", "conteo", "muchos"))
    after = interview_step(answers, TODAY)

    assert (after.stage, after.field) == ("pregunta", "paso")
    assert after.draft.stages[0].conteo is None
    assert "Se entera de ti: cuántos en septiembre de 2026" in after.draft.missing


def test_the_retry_accepts_an_approximation() -> None:
    answers = [
        _answer("se_entera", "paso", "Por Instagram"),
        _answer("se_entera", "conteo", "unos 300"),
    ]

    first = interview_step(answers, TODAY).draft.stages[0]

    assert (first.conteo, first.conteo_supuesto) == (300, True)
    assert first.que_pasa == "Por Instagram"


def test_saying_no_se_about_the_count_needs_no_retry() -> None:
    answers = [_answer("se_entera", "paso", "Por Instagram, pero no sé cuántos")]

    step = interview_step(answers, TODAY)

    assert (step.stage, step.field) == ("pregunta", "paso")
    assert step.draft.stages[0].conteo is None
    assert step.draft.stages[0].fuente_conteo is None


def test_no_se_for_the_whole_stage_leaves_both_missing() -> None:
    answers = [_answer("se_entera", "paso", "no sé")]

    step = interview_step(answers, TODAY)

    assert (step.stage, step.field) == ("pregunta", "paso")
    assert step.draft.missing[:2] == [
        "Se entera de ti: qué pasa",
        "Se entera de ti: cuántos en septiembre de 2026",
    ]


def test_complete_interview_returns_a_draft_that_is_not_saved() -> None:
    last, _ = _run(PAN_RICO)

    assert last.stage is None and last.field is None
    assert last.draft.saved is False
    assert last.draft.period == "2026-09"
    assert [s.stage for s in last.draft.stages] == list(STAGES)
    assert last.draft.stages[2].conteo == 18
    assert last.draft.stages[2].conteo_supuesto is False
    assert last.draft.missing == []
    assert "todavía no se guarda" in last.message


def test_the_last_answer_for_a_field_wins() -> None:
    answers = [
        _answer("se_entera", "paso", "primera, 10"),
        _answer("se_entera", "paso", "corregida, 20"),
    ]

    step = interview_step(answers, TODAY)

    assert step.draft.stages[0].que_pasa == "corregida, 20"
    assert step.draft.stages[0].conteo == 20
