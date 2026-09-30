"""The journey interview: 5 stages, one question per message, "no sé" is valid."""

from __future__ import annotations

from datetime import date

import pytest

from coaching.journey.interview import (
    FIELDS,
    STAGES,
    Answer,
    interview_step,
    is_dont_know,
    last_month,
    parse_count,
)

TODAY = date(2026, 10, 2)


def _answer(stage: str, field: str, answer: str) -> Answer:
    return Answer.model_validate({"stage": stage, "field": field, "answer": answer})


def _full_stage(stage: str, count: str = "120") -> list[Answer]:
    return [
        _answer(stage, "necesidad", "Saber si tengo pan de muerto"),
        _answer(stage, "donde", "WhatsApp"),
        _answer(stage, "friccion", "Tardo en contestar"),
        _answer(stage, "como_lo_sabe", "Lo veo yo"),
        _answer(stage, "conteo", count),
        _answer(stage, "fuente_conteo", "Mi WhatsApp Business"),
    ]


def test_five_fixed_stages_in_order() -> None:
    assert STAGES == ("se_entera", "pregunta", "compra", "recibe", "regresa")
    assert FIELDS == (
        "necesidad",
        "donde",
        "friccion",
        "como_lo_sabe",
        "conteo",
        "fuente_conteo",
    )


def test_first_question_opens_step_one_and_says_no_se_is_fine() -> None:
    step = interview_step([], TODAY)

    assert step.done is False
    assert (step.stage, step.field) == ("se_entera", "necesidad")
    assert "1 de 5" in step.message
    assert "no sé" in step.message
    assert step.draft.saved is False


def test_every_question_is_exactly_one_plain_question() -> None:
    answers: list[Answer] = []
    seen = 0
    while True:
        step = interview_step(answers, TODAY)
        if step.done:
            break
        seen += 1
        assert step.message.count("?") == 1, step.message
        assert step.message.count("¿") == 1, step.message
        lowered = step.message.lower()
        for jargon in ("journey", "embudo", "funnel", "/escala", "módulo"):
            assert jargon not in lowered
        assert step.stage is not None and step.field is not None
        answers.append(
            _answer(step.stage, step.field, "12" if step.field == "conteo" else "algo")
        )
    assert seen == 5 * 6


def test_count_question_names_last_month() -> None:
    answers = _full_stage("se_entera")[:4]

    step = interview_step(answers, TODAY)

    assert step.field == "conteo"
    assert "septiembre de 2026" in step.message


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
    [("120", 120), ("1,200", 1200), ("1.200", 1200), (" 18 ", 18), ("0", 0)],
)
def test_count_accepts_only_a_plain_number(text: str, value: int) -> None:
    assert parse_count(text) == value


@pytest.mark.parametrize(
    "text", ["unos 100", "como 50", "100-150", "muchos", "-3", "12.5", "1,20"]
)
def test_count_is_never_estimated(text: str) -> None:
    assert parse_count(text) is None


def test_dont_know_leaves_the_field_missing_and_skips_the_count_source() -> None:
    answers = [*_full_stage("se_entera")[:4], _answer("se_entera", "conteo", "no sé")]

    step = interview_step(answers, TODAY)
    first = step.draft.stages[0]

    assert first.conteo is None
    assert first.fuente_conteo is None
    assert (step.stage, step.field) == ("pregunta", "necesidad")
    assert "Se entera de ti: cuántos en septiembre de 2026" in step.draft.missing


def test_unparseable_count_asks_again_for_the_number() -> None:
    answers = [
        *_full_stage("se_entera")[:4],
        _answer("se_entera", "conteo", "unos 100"),
    ]

    step = interview_step(answers, TODAY)

    assert (step.stage, step.field, step.retry) == ("se_entera", "conteo", True)
    assert "sólo el número" in step.message.lower()
    assert step.draft.stages[0].conteo is None


def test_a_count_without_source_keeps_the_gap_visible() -> None:
    answers = [
        *_full_stage("se_entera")[:5],
        _answer("se_entera", "fuente_conteo", "no sé"),
    ]

    step = interview_step(answers, TODAY)

    assert step.draft.stages[0].conteo == 120
    assert "Se entera de ti: de dónde sale el número" in step.draft.missing


def test_complete_interview_returns_a_draft_that_is_not_saved() -> None:
    answers = [
        answer
        for stage in STAGES
        for answer in _full_stage(stage, "no sé" if stage == "regresa" else "18")
    ]

    step = interview_step(answers, TODAY)

    assert step.done is True
    assert step.stage is None and step.field is None
    assert step.draft.saved is False
    assert step.draft.period == "2026-09"
    assert [s.stage for s in step.draft.stages] == list(STAGES)
    assert step.draft.stages[2].conteo == 18
    assert step.draft.missing == ["Regresa a comprar: cuántos en septiembre de 2026"]
    assert "todavía no se guarda" in step.message


def test_the_last_answer_for_a_field_wins() -> None:
    answers = [
        _answer("se_entera", "necesidad", "primera"),
        _answer("se_entera", "necesidad", "corregida"),
    ]

    step = interview_step(answers, TODAY)

    assert step.draft.stages[0].necesidad == "corregida"
    assert step.field == "donde"
