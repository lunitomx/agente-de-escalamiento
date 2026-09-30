"""E84 S84.1: the journey is an internal strategy procedure reached only via ESCALA."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from coaching.journey import messages
from coaching.journey.triggers import JourneySignals, should_ask_journey
from escala_server.capabilities import (
    load_capability_catalog,
    public_install_skills,
    route_request,
)
from escala_server.specialist_team import SPECIALIST_CONTRACTS

ROOT = Path(__file__).resolve().parents[1]
PROCEDURE = ROOT / "escala-skills" / "escala-strategy-journey" / "SKILL.md"


def _procedure() -> str:
    return PROCEDURE.read_text(encoding="utf-8")


def test_journey_is_an_internal_strategy_procedure() -> None:
    catalog = load_capability_catalog(ROOT / "escala-skills" / "catalog.yaml")

    capability = catalog.capability("escala-strategy-journey")
    assert capability.visibility == "internal"
    assert capability.owner == "strategy"
    assert "escala-strategy-journey" not in public_install_skills(catalog)


def test_procedure_declares_its_name_and_drives_the_flow_module() -> None:
    text = _procedure()

    assert text.startswith("---\n")
    assert "name: escala-strategy-journey" in text
    assert "python3 -m coaching.journey" in text
    for action in ("check", "record", "interview"):
        assert f'"action": "{action}"' in text


def test_procedure_carries_the_no_insist_rules_and_the_exact_question() -> None:
    text = _procedure()

    assert messages.ASK_NEW in text
    assert "asked_this_conversation" in text
    assert "30 días" in text
    assert "una sola vez" in text
    assert '"No sé" es una respuesta válida' in text
    assert "no se guarda" in text
    assert ".escala/my-company/journey/" in text
    assert "facts.yaml" in text  # only to say counts never go there


def test_strategy_specialist_offers_the_journey_from_its_next_step_table() -> None:
    text = (ROOT / "escala-skills" / "escala-strategy" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "escala-strategy-journey" in text


def test_strategy_trigger_is_unchanged() -> None:
    trigger = SPECIALIST_CONTRACTS["strategy"].trigger
    contract = json.loads(
        (ROOT / "adapters/specialists/contract.json").read_text(encoding="utf-8")
    )
    strategy = next(
        s for s in contract["specialists"] if s["decision_area"] == "strategy"
    )

    assert strategy["trigger"] == trigger


def test_mvp_capability_catalog_is_unchanged_by_the_journey() -> None:
    catalog = (ROOT / "capabilities/mvp/catalog.json").read_text(encoding="utf-8")

    assert "escala-strategy-journey" not in catalog


@pytest.mark.parametrize(
    "phrase",
    [
        "Mucha gente pregunta por WhatsApp pero pocos compran",
        "Me preguntan mucho pero no me compran",
        "Nadie me compra",
        "Compran una vez y no regresan",
        "Se me van los clientes",
        "No vendo nada este mes",
        "Vendo poco",
    ],
)
def test_a_sales_pain_phrase_reaches_strategy_and_fires_the_check(
    phrase: str,
) -> None:
    """M1 demo: the front door routes it to Strategy, where check asks (T1)."""
    assert route_request(phrase).capability_id == "escala-strategy"
    decision = should_ask_journey(
        JourneySignals(owner_text=phrase, today=date(2026, 9, 30))
    )
    assert (decision.ask, decision.reason) == (True, "T1")
