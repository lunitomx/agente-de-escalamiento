"""E83 S83.1: research is an internal strategy procedure reached only via ESCALA."""

from __future__ import annotations

import json
from pathlib import Path

from coaching.research.messages import SEARCH_OFF
from escala_server.capabilities import load_capability_catalog, public_install_skills
from escala_server.specialist_team import SPECIALIST_CONTRACTS

ROOT = Path(__file__).resolve().parents[1]
PROCEDURE = ROOT / "escala-skills" / "escala-strategy-research" / "SKILL.md"


def _procedure() -> str:
    return PROCEDURE.read_text(encoding="utf-8")


def test_research_is_an_internal_strategy_procedure() -> None:
    catalog = load_capability_catalog(ROOT / "escala-skills" / "catalog.yaml")

    capability = catalog.capability("escala-strategy-research")
    assert capability.visibility == "internal"
    assert capability.owner == "strategy"
    assert "escala-strategy-research" not in public_install_skills(catalog)


def test_procedure_declares_its_name_and_drives_the_flow_module() -> None:
    text = _procedure()

    assert text.startswith("---\n")
    assert "name: escala-strategy-research" in text
    assert "python3 -m coaching.research" in text
    for action in ("frame", "grade", "report", "save"):
        assert f'"action": "{action}"' in text


def test_procedure_carries_the_search_rules_and_the_search_off_line() -> None:
    text = _procedure()

    assert SEARCH_OFF in text
    assert "no el nombre de la plataforma" in text
    assert "abriste la página" in text
    assert "cita literal" in text
    assert "Lo que recuerdas no es fuente" in text
    assert "user_confirmed" in text
    assert "¿Qué decisión quieres tomar con esto?" in text
    assert "ChatGPT" in text  # only to say it is not promised (E85)


def test_strategy_specialist_offers_research_from_its_next_step_table() -> None:
    text = (ROOT / "escala-skills" / "escala-strategy" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "escala-strategy-research" in text


def test_strategy_trigger_is_unchanged() -> None:
    trigger = SPECIALIST_CONTRACTS["strategy"].trigger
    contract = json.loads(
        (ROOT / "adapters/specialists/contract.json").read_text(encoding="utf-8")
    )
    strategy = next(
        s for s in contract["specialists"] if s["decision_area"] == "strategy"
    )

    assert strategy["trigger"] == trigger
    assert "research" not in trigger.lower()


def test_mvp_capability_catalog_is_unchanged_by_research() -> None:
    catalog = (ROOT / "capabilities/mvp/catalog.json").read_text(encoding="utf-8")

    assert "research" not in catalog
