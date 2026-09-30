"""``should_ask_journey``: blockers N1-N6 first, then triggers T1-T5 (E84 S84.1)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from coaching.diagnose.models import FunnelMetrics
from coaching.journey import messages
from coaching.journey.triggers import (
    SALES_LEXICON,
    JourneySignals,
    funnel_gaps,
    has_sales_words,
    should_ask_journey,
)

TODAY = date(2026, 9, 30)
PAN_RICO = "Mucha gente pregunta por WhatsApp pero pocos compran."


def _signals(**fields: object) -> JourneySignals:
    base: dict[str, object] = {"today": TODAY}
    base.update(fields)
    return JourneySignals.model_validate(base)


# --- Triggers -------------------------------------------------------------


def test_pan_rico_phrase_fires_t1_with_one_plain_question() -> None:
    decision = should_ask_journey(_signals(owner_text=PAN_RICO))

    assert decision.ask is True
    assert decision.reason == "T1"
    assert decision.offer == "nuevo"
    assert decision.message == messages.ASK_NEW


@pytest.mark.parametrize(
    "text",
    [
        "Pocos compran, la verdad",
        "Mis clientes no regresan",
        "Siento que se me van a la competencia",
        "Este mes no vendo nada",
        "Necesito ayuda con el MARKETING",
        "¿Cómo consigo más prospectos?",
        "No me llegan clientes nuevos",
        "Ya no vuelven después de la primera compra",
    ],
)
def test_sales_marketing_and_retention_words_fire_t1(text: str) -> None:
    decision = should_ask_journey(_signals(owner_text=text))

    assert (decision.ask, decision.reason) == (True, "T1")


@pytest.mark.parametrize(
    "text",
    [
        "Mi equipo no sabe quién decide",
        "Quiero ordenar mis reuniones",
        "No tengo efectivo para la nómina",
        "Tengo un problema con el proveedor de harina",
        "",
    ],
)
def test_words_outside_the_closed_lexicon_do_not_fire_t1(text: str) -> None:
    assert has_sales_words(text) is False
    assert should_ask_journey(_signals(owner_text=text)).reason == "sin_disparador"


def test_lexicon_is_closed_and_matches_whole_words() -> None:
    assert "pocos compran" in SALES_LEXICON
    assert "marketing" in SALES_LEXICON
    # A lexicon phrase inside a longer word is not a match.
    assert has_sales_words("remarketingxyz") is False


@pytest.mark.parametrize(
    ("area", "topic", "asks"),
    [
        ("strategy", None, True),
        ("cash", "ventas", True),
        ("cash", "precio", True),
        ("cash", "liquidez", False),
        ("cash", "cobranza", False),
        ("cash", None, False),
    ],
)
def test_t2_strategy_or_cash_only_by_sales_or_price(
    area: str, topic: str | None, asks: bool
) -> None:
    decision = should_ask_journey(_signals(constraint_area=area, cash_topic=topic))

    assert decision.ask is asks
    assert decision.reason == ("T2" if asks else "sin_disparador")


def test_t3_funnel_with_some_counts_and_some_gaps() -> None:
    partial = should_ask_journey(
        _signals(funnel_known=["prospects"], funnel_missing=["wins"])
    )
    complete = should_ask_journey(_signals(funnel_known=["prospects", "wins"]))
    empty = should_ask_journey(_signals(funnel_missing=["prospects", "wins"]))

    assert (partial.ask, partial.reason) == (True, "T3")
    assert complete.ask is False
    assert empty.ask is False


def test_funnel_gaps_reads_funnel_metrics_without_estimating() -> None:
    known, missing = funnel_gaps(FunnelMetrics(prospects=120, wins=18))

    assert known == ["prospects", "wins"]
    assert missing == ["conversations", "proposals"]
    assert funnel_gaps(None) == (
        [],
        ["prospects", "conversations", "proposals", "wins"],
    )


def test_t4_board_needs_journey_stages() -> None:
    decision = should_ask_journey(_signals(board_needs_stages=True))

    assert (decision.ask, decision.reason) == (True, "T4")


def test_t5_research_decision_about_acquisition_or_channel() -> None:
    decision = should_ask_journey(_signals(research_topic_acquisition=True))

    assert (decision.ask, decision.reason) == (True, "T5")


def test_no_trigger_no_question() -> None:
    decision = should_ask_journey(_signals())

    assert decision.ask is False
    assert decision.reason == "sin_disparador"
    assert decision.message is None


# --- Blockers (evaluated before triggers) ---------------------------------

ALL_TRIGGERS: dict[str, object] = {
    "owner_text": PAN_RICO,
    "constraint_area": "strategy",
    "funnel_known": ["prospects"],
    "funnel_missing": ["wins"],
    "board_needs_stages": True,
    "research_topic_acquisition": True,
}


def test_n1_current_journey_blocks_every_trigger() -> None:
    decision = should_ask_journey(
        _signals(**ALL_TRIGGERS, journey_review_by=TODAY + timedelta(days=10))
    )
    on_the_day = should_ask_journey(_signals(**ALL_TRIGGERS, journey_review_by=TODAY))

    assert (decision.ask, decision.reason, decision.message) == (False, "N1", None)
    assert on_the_day.reason == "N1"


def test_n1_expired_journey_offers_an_update_not_a_new_one() -> None:
    decision = should_ask_journey(
        _signals(owner_text=PAN_RICO, journey_review_by=TODAY - timedelta(days=1))
    )

    assert (decision.ask, decision.reason) == (True, "T1")
    assert decision.offer == "actualizar"
    assert decision.message == messages.ASK_UPDATE


def test_expired_journey_without_trigger_is_not_offered() -> None:
    decision = should_ask_journey(_signals(journey_review_by=TODAY - timedelta(days=1)))

    assert decision.ask is False


@pytest.mark.parametrize("days_ago", [0, 1, 15, 29, 30])
def test_n2_thirty_days_of_silence_after_no_or_later(days_ago: int) -> None:
    decision = should_ask_journey(
        _signals(**ALL_TRIGGERS, last_declined_on=TODAY - timedelta(days=days_ago))
    )

    assert (decision.ask, decision.reason) == (False, "N2")


def test_n2_ends_after_thirty_full_days() -> None:
    decision = should_ask_journey(
        _signals(owner_text=PAN_RICO, last_declined_on=TODAY - timedelta(days=31))
    )

    assert (decision.ask, decision.reason) == (True, "T1")


def test_n2_decline_dated_in_the_future_still_blocks() -> None:
    decision = should_ask_journey(
        _signals(owner_text=PAN_RICO, last_declined_on=TODAY + timedelta(days=3))
    )

    assert decision.reason == "N2"


def test_n3_at_most_one_ask_per_conversation() -> None:
    decision = should_ask_journey(
        _signals(**ALL_TRIGGERS, asked_this_conversation=True)
    )

    assert (decision.ask, decision.reason) == (False, "N3")


@pytest.mark.parametrize("area", ["people", "execution"])
def test_n4_people_or_execution_without_sales_signal(area: str) -> None:
    decision = should_ask_journey(
        _signals(
            constraint_area=area,
            owner_text="Mi equipo no sabe quién decide",
            funnel_known=["prospects"],
            funnel_missing=["wins"],
        )
    )

    assert (decision.ask, decision.reason) == (False, "N4")


@pytest.mark.parametrize(
    ("fields", "reason"),
    [
        ({"owner_text": PAN_RICO}, "T1"),
        ({"board_needs_stages": True}, "T4"),
        ({"research_topic_acquisition": True}, "T5"),
    ],
)
def test_people_constraint_with_a_sales_signal_still_asks(
    fields: dict[str, object], reason: str
) -> None:
    decision = should_ask_journey(_signals(constraint_area="people", **fields))

    assert (decision.ask, decision.reason) == (True, reason)


def test_n5_other_flow_in_progress_waits() -> None:
    decision = should_ask_journey(_signals(**ALL_TRIGGERS, other_flow_active=True))

    assert (decision.ask, decision.reason) == (False, "N5")


def test_n6_cash_or_payroll_emergency_never_asks() -> None:
    decision = should_ask_journey(_signals(**ALL_TRIGGERS, cash_emergency=True))

    assert (decision.ask, decision.reason) == (False, "N6")


def test_emergency_wins_over_every_other_blocker() -> None:
    decision = should_ask_journey(
        _signals(
            **ALL_TRIGGERS,
            cash_emergency=True,
            other_flow_active=True,
            asked_this_conversation=True,
            last_declined_on=TODAY,
            journey_review_by=TODAY,
        )
    )

    assert decision.reason == "N6"


# --- Message ---------------------------------------------------------------


@pytest.mark.parametrize("message", [messages.ASK_NEW, messages.ASK_UPDATE])
def test_ask_message_is_one_plain_question_with_a_way_out(message: str) -> None:
    lowered = message.lower()

    assert message.count("?") == 1
    assert message.count("¿") == 1
    assert "después" in lowered
    for jargon in ("journey", "funnel", "embudo", "/escala", "escala-", "módulo"):
        assert jargon not in lowered
