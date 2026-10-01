"""S84.2 task 2: gaps, where most are lost (same period only), plain text."""

from __future__ import annotations

from datetime import date

from coaching.journey.models import (
    Journey,
    JourneyEvidence,
    JourneyStage,
    StageCount,
)
from coaching.journey.view import (
    NOT_ASKED,
    biggest_loss,
    loss_line,
    missing_lines,
    period_label,
    summary,
    to_funnel,
)

TODAY = date(2026, 10, 1)


def _count(
    value: int, period: str = "2026-09", origin: str = "dueño_dice"
) -> StageCount:
    return StageCount.model_validate(
        {"value": value, "period": period, "source": "tu cuaderno", "origin": origin}
    )


def _journey(
    counts: dict[str, StageCount | None], friction: JourneyEvidence | None = None
) -> Journey:
    stages: list[JourneyStage] = []
    for stage in ("se_entera", "pregunta", "compra", "recibe", "regresa"):
        extra: dict[str, object] = {}
        if stage == "compra" and friction is not None:
            extra = {"friction": friction.text, "evidence": [friction]}
        stages.append(
            JourneyStage.model_validate(
                {"stage": stage, "count": counts.get(stage), **extra}
            )
        )
    return Journey(built_on=TODAY, stages=stages)


def test_period_label_is_plain_spanish() -> None:
    assert period_label("2026-09") == "septiembre de 2026"


def test_loss_only_between_consecutive_stages_of_the_same_period() -> None:
    journey = _journey(
        {"se_entera": _count(300), "pregunta": _count(120), "compra": _count(18)}
    )
    loss = biggest_loss(journey)
    assert loss is not None
    assert (loss.from_stage, loss.to_stage) == ("pregunta", "compra")
    assert loss_line(journey) == (
        "Donde más se pierden es entre «Te pregunta» y «Te compra»: "
        "de 120 a 18 en septiembre de 2026."
    )


def test_different_periods_are_never_compared() -> None:
    journey = _journey(
        {"pregunta": _count(120, "2026-09"), "compra": _count(18, "2026-08")}
    )
    assert biggest_loss(journey) is None
    assert loss_line(journey) == (
        "Todavía no se puede saber dónde se pierden más: falta contar dos pasos "
        "seguidos en el mismo mes."
    )


def test_gap_between_counts_is_not_bridged() -> None:
    journey = _journey({"pregunta": _count(120), "recibe": _count(18)})
    assert biggest_loss(journey) is None


def test_missing_shows_falta_and_is_never_estimated() -> None:
    journey = _journey({"pregunta": _count(120), "compra": _count(18)})
    lines = missing_lines(journey)
    assert "Regresa a comprar: falta cuántos en septiembre de 2026." in lines
    assert "Se entera de ti: falta qué pasa." in lines
    assert all(line.split(": ", 1)[1].startswith("falta") for line in lines)


def test_owner_friction_says_customers_were_not_asked() -> None:
    owner = JourneyEvidence(origin="dueño_dice", text="tardo en contestar")
    text = summary(_journey({"compra": _count(18)}, owner))
    assert NOT_ASKED in text
    assert "entrevist" not in text.lower()


def test_customer_friction_says_when_and_how_many() -> None:
    heard = JourneyEvidence(
        origin="clientes_dijeron",
        text="tardas en contestar",
        asked_on=date(2026, 9, 20),
        asked_count=5,
    )
    text = summary(_journey({"compra": _count(18)}, heard))
    assert NOT_ASKED not in text
    assert "Se lo preguntaste a 5 clientes el 20 de septiembre de 2026." in text


def test_summary_counts_say_source_and_month() -> None:
    data = _count(120, origin="dato_con_periodo").model_copy(
        update={"source": "tu WhatsApp Business"}
    )
    text = summary(
        _journey({"pregunta": data, "se_entera": _count(300, origin="supuesto")})
    )
    assert "Te pregunta: 120 en septiembre de 2026 (tu WhatsApp Business)." in text
    assert "Se entera de ti: unos 300 en septiembre de 2026 (aproximado" in text


def test_funnel_only_with_one_period_and_exact_counts() -> None:
    same = _journey(
        {"se_entera": _count(300), "pregunta": _count(120), "compra": _count(18)}
    )
    funnel = to_funnel(same)
    assert funnel is not None
    assert (funnel.prospects, funnel.conversations, funnel.wins) == (300, 120, 18)
    assert funnel.proposals is None
    mixed = _journey(
        {"pregunta": _count(120, "2026-09"), "compra": _count(18, "2026-08")}
    )
    assert to_funnel(mixed) is None
    guessed = _journey(
        {"pregunta": _count(120, origin="supuesto"), "compra": _count(18)}
    )
    funnel = to_funnel(guessed)
    assert funnel is not None and funnel.conversations is None and funnel.wins == 18
