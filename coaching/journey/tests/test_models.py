"""S84.2 task 1: the journey model and its evidence rules (synthetic data)."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from coaching.journey.interview import Answer, interview_step
from coaching.journey.models import (
    Journey,
    JourneyEvidence,
    JourneyStage,
    StageCount,
    from_draft,
    heard_from_customers,
)

TODAY = date(2026, 10, 1)


def _stages() -> list[JourneyStage]:
    return [
        JourneyStage(stage=stage)
        for stage in ("se_entera", "pregunta", "compra", "recibe", "regresa")
    ]


def test_customers_said_needs_when_and_how_many() -> None:
    with pytest.raises(ValidationError):
        JourneyEvidence(origin="clientes_dijeron", text="tardas en contestar")
    item = JourneyEvidence(
        origin="clientes_dijeron",
        text="tardas en contestar",
        asked_on=date(2026, 9, 20),
        asked_count=5,
    )
    assert item.asked_count == 5


def test_data_needs_local_source_and_period() -> None:
    with pytest.raises(ValidationError):
        JourneyEvidence(origin="dato_con_periodo", text="120 mensajes")
    with pytest.raises(ValidationError):
        JourneyEvidence(
            origin="dato_con_periodo",
            text="120",
            source="https://ejemplo.com",
            period="2026-09",
        )
    ok = JourneyEvidence(
        origin="dato_con_periodo",
        text="120",
        source="WhatsApp Business",
        period="2026-09",
    )
    assert ok.period == "2026-09"


def test_count_needs_period_and_local_source() -> None:
    with pytest.raises(ValidationError):
        StageCount(value=5, period="septiembre", source="cuaderno", origin="dueño_dice")
    with pytest.raises(ValidationError):
        StageCount(value=5, period="2026-09", source="www.x.com", origin="dueño_dice")
    count = StageCount(
        value=18, period="2026-09", source="tu cuaderno", origin="dato_con_periodo"
    )
    assert count.value == 18


def test_high_confidence_needs_first_hand_evidence() -> None:
    with pytest.raises(ValidationError):
        JourneyStage(
            stage="pregunta",
            confidence="alta",
            evidence=[JourneyEvidence(origin="dueño_dice", text="tardo")],
        )
    stage = JourneyStage(
        stage="pregunta",
        confidence="alta",
        evidence=[
            JourneyEvidence(
                origin="clientes_dijeron",
                text="tardas",
                asked_on=date(2026, 9, 20),
                asked_count=3,
            )
        ],
    )
    assert stage.confidence == "alta"


def test_journey_has_the_five_fixed_stages_in_order() -> None:
    with pytest.raises(ValidationError):
        Journey(built_on=TODAY, stages=_stages()[:4])
    with pytest.raises(ValidationError):
        Journey(built_on=TODAY, stages=list(reversed(_stages())))
    assert len(Journey(built_on=TODAY, stages=_stages()).stages) == 5


def test_heard_from_customers_only_with_customer_evidence() -> None:
    journey = Journey(built_on=TODAY, stages=_stages())
    assert heard_from_customers(journey) is False


def test_from_draft_keeps_owner_origin_and_never_fills_gaps() -> None:
    answers = [
        Answer(stage="se_entera", field="paso", answer="por Facebook, unos 300"),
        Answer(stage="pregunta", field="paso", answer="por WhatsApp, 120"),
        Answer(stage="compra", field="paso", answer="pagan al recoger, 18"),
        Answer(stage="recibe", field="paso", answer="pasan a la tienda, 18"),
        Answer(stage="regresa", field="paso", answer="no sé"),
        Answer(stage="compra", field="friccion", answer="tardo en contestar"),
    ]
    draft = interview_step(answers, TODAY).draft
    journey = from_draft(draft, TODAY)
    se_entera, pregunta, compra, _, regresa = journey.stages
    assert se_entera.count is not None and se_entera.count.origin == "supuesto"
    assert pregunta.count is not None and pregunta.count.origin == "dueño_dice"
    assert pregunta.count.period == "2026-09"
    assert pregunta.touchpoint == "por WhatsApp, 120"
    assert regresa.count is None and regresa.touchpoint is None
    assert compra.friction == "tardo en contestar"
    assert [item.origin for item in compra.evidence] == ["dueño_dice"]
    assert compra.confidence == "baja"
    assert heard_from_customers(journey) is False
