"""Guided flow: name -> Drive or paste -> own tab confirmed -> remembered (S82.3).

Includes the red-team privacy test: a synthetic multi-tab workbook where each
tab carries a unique marker; no other tab's marker may reach an ESCALA message,
a flow output or a file under ``.escala/my-company/``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from coaching.tracker.flow import FlowResult, run
from coaching.tracker.messages import (
    ASK_NAME,
    DRIVE_NOTICE,
    candidates_message,
    confirmed_message,
    connect_message,
)
from coaching.tracker.identity import rank_candidates

ROOT = Path(__file__).resolve().parents[3]

MARKERS = {
    "START HERE": "MARCA-START-91",
    "Ana": "MARCA-ANA-17",
    "Beto": "MARCA-BETO-42",
    "Name 6": "MARCA-N6-63",
}


def _tab(name: str, participant: str, marker: str) -> str:
    return f"""\
### Sheet Name: {name}
### Table Range: A1:C3
| | | |
|---|---|---|
| Participant Name | | {participant} |
| Business Name | | Negocio {marker} |
| Critical Number | | {marker} ventas |

### Table Range: A5:E7
| | | | | |
|---|---|---|---|---|
| Monthly Commitments | | | | |
| | Focus Area | Priorities | KPIs | Due Dates |
| | Cash | Cobrar {marker} | 90% {marker} | 30/10/2026 |
"""


def _workbook() -> str:
    return "\n".join(
        [
            "### Sheet Name: START HERE\n### Table Range: A1:B1\n| | |\n|---|---|\n"
            f"| Grupo | {MARKERS['START HERE']} |\n",
            _tab("Ana", "Ana Demo", MARKERS["Ana"]),
            _tab("Beto", "Beto Otro", MARKERS["Beto"]),
            _tab("Name 6", "Name 6", MARKERS["Name 6"]),
        ]
    )


def _foreign(own_tab: str) -> list[str]:
    return [marker for tab, marker in MARKERS.items() if tab != own_tab]


def _company_files(base: Path) -> str:
    folder = base / ".escala" / "my-company"
    return "\n".join(
        path.read_text(encoding="utf-8") for path in folder.rglob("*") if path.is_file()
    )


def _dump(result: FlowResult) -> str:
    return result.model_dump_json()


def test_connect_message_carries_the_owner_notice_verbatim() -> None:
    message = connect_message()

    assert (
        "Ojo: al conectarlo, el asistente puede ver todo el archivo compartido del "
        "grupo; ESCALA sólo usa tu pestaña." in message
    )
    assert DRIVE_NOTICE in message
    assert "Configuración → Conectores" in message
    assert "cópiala y pégala aquí" in message
    assert "ChatGPT" not in message


def test_single_match_asks_if_it_is_yours() -> None:
    message = candidates_message(rank_candidates(["Ana", "Beto"], "Ana"), None)

    assert message == "Veo una pestaña que se llama **Ana**. ¿Es la tuya?"


def test_tie_asks_for_the_business_only_then() -> None:
    ranked = rank_candidates(["Ana López", "Ana Ruiz", "Beto"], "Ana")

    message = candidates_message(ranked, None)

    assert "**Ana López**" in message and "**Ana Ruiz**" in message
    assert "negocio" in message
    assert "Beto" not in message


def test_no_match_lists_tab_names_and_marks_placeholders() -> None:
    ranked = rank_candidates(["START HERE", "Beto", "Name 6"], "Ana")

    message = candidates_message(ranked, None)

    assert "**Beto**" in message
    assert "**Name 6** (todavía sin nombre)" in message
    assert "START HERE" not in message
    assert message.endswith("¿Cuál es la tuya?")


def test_confirmed_placeholder_cell_warns_after_the_yes() -> None:
    message = confirmed_message("Name 6", "Name 6")

    assert (
        "Tu pestaña dice 'Name 6' en vez de tu nombre; puedo trabajar igual, y "
        "conviene avisar al grupo para que llene START HERE" in message
    )


def test_user_messages_have_no_internal_jargon() -> None:
    ranked = rank_candidates(["Ana López", "Ana Ruiz"], "Ana")
    messages = [
        ASK_NAME,
        connect_message(),
        candidates_message(ranked, None),
        candidates_message(rank_candidates(["Beto"], "Ana"), None),
        confirmed_message("Ana", "Ana Demo"),
        confirmed_message("Ana", None),
    ]
    banned = [
        "tracker",
        "TSV",
        "MCP",
        "escala-",
        "skill",
        "procedimiento",
        "grid",
        "yaml",
    ]

    for message in messages:
        for word in banned:
            assert word.lower() not in message.lower(), (word, message)


def test_confirm_without_the_users_yes_reads_nothing(tmp_path: Path) -> None:
    result = run(
        {
            "action": "confirm",
            "base_path": str(tmp_path),
            "tab_name": "Ana",
            "connector_text": _workbook(),
        }
    )

    assert result.errors == ["needs_confirmation"]
    assert result.sheet is None
    assert not (tmp_path / ".escala").exists()
    assert all(marker not in _dump(result) for marker in MARKERS.values())


def test_start_here_can_never_be_confirmed(tmp_path: Path) -> None:
    result = run(
        {
            "action": "confirm",
            "base_path": str(tmp_path),
            "user_confirmed": True,
            "tab_name": "START HERE",
            "connector_text": _workbook(),
        }
    )

    assert result.errors == ["start_here"]
    assert MARKERS["START HERE"] not in _dump(result)


def test_privacy_other_tabs_never_reach_messages_or_files(tmp_path: Path) -> None:
    """Red-team blind spot: only the confirmed tab's cells survive the flow."""
    base = str(tmp_path)
    workbook = _workbook()
    common = {"base_path": base, "file_title": "Tracker del grupo", "file_id": "f-1"}

    steps = [
        run({"action": "connect"}),
        run(
            {"action": "candidates", "connector_text": workbook, "name": "Ana"} | common
        ),
    ]
    before_yes = "\n".join(_dump(step) for step in steps)
    assert all(marker not in before_yes for marker in MARKERS.values())
    assert steps[1].message == "Veo una pestaña que se llama **Ana**. ¿Es la tuya?"

    confirmed = run(
        {
            "action": "confirm",
            "user_confirmed": True,
            "tab_name": "Ana",
            "connector_text": workbook,
        }
        | common
    )
    again = run(
        {"action": "candidates", "connector_text": workbook, "name": "Ana"} | common
    )
    loaded = run({"action": "load", "base_path": base})
    steps += [confirmed, again, loaded]

    outputs = "\n".join(_dump(step) for step in steps)
    files = _company_files(tmp_path)
    for marker in _foreign("Ana"):
        assert marker not in outputs, marker
        assert marker not in files, marker
    assert MARKERS["Ana"] not in files  # the link is a reference, not content
    assert confirmed.sheet is not None
    assert MARKERS["Ana"] in (confirmed.sheet.critical_number or "")
    assert again.message == "Uso tu pestaña **Ana**, como la otra vez."
    assert loaded.link is not None and loaded.link.tab_name == "Ana"


def test_privacy_placeholder_tab_confirmed_keeps_only_its_cells(
    tmp_path: Path,
) -> None:
    result = run(
        {
            "action": "confirm",
            "base_path": str(tmp_path),
            "user_confirmed": True,
            "tab_name": "Name 6",
            "connector_text": _workbook(),
        }
    )

    dump = _dump(result) + _company_files(tmp_path)
    assert all(marker not in dump for marker in _foreign("Name 6"))
    assert "Tu pestaña dice 'Name 6'" in result.message


def test_pasted_tab_path_reaches_the_sheet(tmp_path: Path) -> None:
    pasted = (
        "Participant Name\t\tAna Demo\n"
        "Critical Number\t\t10 clientes\n"
        "Monthly Commitments\n"
        "\tFocus Area\tPriorities\tKPIs\tDue Dates\n"
        "\tVentas\tLlamar 20 prospectos\t20 llamadas\t31/10/2026\n"
    )

    result = run(
        {
            "action": "confirm",
            "base_path": str(tmp_path),
            "user_confirmed": True,
            "tab_name": "Ana",
            "pasted_text": pasted,
        }
    )

    assert result.errors == []
    assert result.sheet is not None
    assert result.sheet.critical_number == "10 clientes"
    assert result.sheet.commitments[0].text == "Llamar 20 prospectos"
    assert result.link is not None and result.link.file_title is None
    assert "Llamar" not in _company_files(tmp_path)


def test_unknown_tab_asks_again(tmp_path: Path) -> None:
    result = run(
        {
            "action": "confirm",
            "base_path": str(tmp_path),
            "user_confirmed": True,
            "tab_name": "Carla",
            "connector_text": _workbook(),
        }
    )

    assert result.errors == ["tab_not_found"]
    assert "**Carla**" in result.message


def test_changed_file_asks_again(tmp_path: Path) -> None:
    base = str(tmp_path)
    run(
        {
            "action": "confirm",
            "base_path": base,
            "user_confirmed": True,
            "tab_name": "Ana",
            "file_title": "Tracker 2026",
            "connector_text": _workbook(),
        }
    )

    result = run(
        {
            "action": "candidates",
            "base_path": base,
            "file_title": "Tracker 2027",
            "connector_text": _workbook(),
            "name": "Ana",
        }
    )

    assert result.link is None
    assert result.message.startswith("Veo una pestaña")


@pytest.mark.parametrize("action", ["", "borrar"])
def test_unknown_action_is_an_error(action: str) -> None:
    assert run({"action": action}).errors == ["unknown_action"]


def test_module_runs_from_the_command_line(tmp_path: Path) -> None:
    payload = json.dumps({"action": "tabs", "connector_text": _workbook()})

    completed = subprocess.run(
        [sys.executable, "-m", "coaching.tracker"],
        input=payload,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    result = json.loads(completed.stdout)
    assert result["tab_names"] == ["START HERE", "Ana", "Beto", "Name 6"]
    assert all(marker not in completed.stdout for marker in MARKERS.values())
