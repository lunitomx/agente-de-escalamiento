"""E82 S82.3: the tracker is an internal procedure reached only through ESCALA."""

from __future__ import annotations

import json
from pathlib import Path

from coaching.tracker.messages import DRIVE_NOTICE
from escala_server.capabilities import load_capability_catalog, public_install_skills
from escala_server.specialist_team import SPECIALIST_CONTRACTS

ROOT = Path(__file__).resolve().parents[1]
PROCEDURE = ROOT / "escala-skills" / "escala-execution-tracker" / "SKILL.md"
TRIGGER = "tracker de accountability / hoja del grupo"


def _procedure() -> str:
    return PROCEDURE.read_text(encoding="utf-8")


def test_tracker_is_an_internal_execution_procedure() -> None:
    catalog = load_capability_catalog(ROOT / "escala-skills" / "catalog.yaml")

    capability = catalog.capability("escala-execution-tracker")
    assert capability.visibility == "internal"
    assert capability.owner == "execution"
    assert "escala-execution-tracker" not in public_install_skills(catalog)


def test_procedure_declares_its_name_and_drives_the_flow_module() -> None:
    text = _procedure()

    assert text.startswith("---\n")
    assert "name: escala-execution-tracker" in text
    assert "python3 -m coaching.tracker" in text
    for action in ("connect", "candidates", "confirm", "load"):
        assert f'"action": "{action}"' in text


def test_procedure_carries_the_owner_drive_notice_and_privacy_rules() -> None:
    text = _procedure()

    assert DRIVE_NOTICE in text
    assert "START HERE" in text
    assert "user_confirmed" in text
    assert "ChatGPT" in text  # only to say it is not promised (E85)


def test_execution_specialist_recognizes_the_group_sheet() -> None:
    assert TRIGGER in SPECIALIST_CONTRACTS["execution"].trigger
    contract = json.loads(
        (ROOT / "adapters/specialists/contract.json").read_text(encoding="utf-8")
    )
    execution = next(
        s for s in contract["specialists"] if s["decision_area"] == "execution"
    )
    assert TRIGGER in execution["trigger"]
    for agent in (
        ROOT / "adapters/claude/agents/escala-execution.md",
        ROOT / "adapters/codex/agents/escala-execution.toml",
    ):
        assert TRIGGER in agent.read_text(encoding="utf-8")


def test_quarterly_priority_procedures_offer_the_group_sheet() -> None:
    for name in ("escala-execution-prioridad", "escala-execution-priorities"):
        text = (ROOT / "escala-skills" / name / "SKILL.md").read_text(encoding="utf-8")
        assert "escala-execution-tracker" in text
        assert "¿Las pasamos a tu hoja del grupo?" in text


def test_mvp_capability_catalog_is_unchanged_by_the_tracker() -> None:
    catalog = (ROOT / "capabilities/mvp/catalog.json").read_text(encoding="utf-8")

    assert "tracker" not in catalog


def test_procedure_proposes_rows_and_never_writes_them() -> None:
    """S82.4: paste-ready rows only (S82.6 found no verified write path)."""
    text = _procedure()

    assert '"action": "propose"' in text
    assert "drive_notice_shown" in text
    assert "Ctrl+Z" in text
    assert "Restaurar esta versión" in text  # only as what never to suggest
    assert "Nunca escribas" in text
    assert "Critical Number" in text


def test_procedure_prepares_the_meeting_without_moving_anything() -> None:
    """S82.5: before the meeting ESCALA only suggests; the owner decides."""
    text = _procedure()

    assert '"action": "prepare"' in text
    assert '"today"' in text
    assert "Antes de tu reunión" in text
    assert "por confirmar" in text
    assert "Nunca muevas" in text


def test_procedure_fills_rocks_for_the_quarter_the_sheet_declares() -> None:
    """S82.7: same propose action; the quarter is never guessed."""
    text = _procedure()

    assert '"table": "rocks"' in text
    assert '"quarter"' in text
    assert "Quarterly Goals" in text
    assert "Nunca adivines el trimestre" in text


def test_procedure_reviews_rocks_apart_and_reads_dates_by_the_sheet() -> None:
    """S82.7: prepare also reviews Rocks; swappable dates follow the tab."""
    text = _procedure()

    assert "Rocks del trimestre" in text
    assert "día/mes" in text
    assert "no la adivines" in text
