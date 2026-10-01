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

### Table Range: A10:D12
| | | | |
|---|---|---|---|
| Quarterly Goals (Rocks) - Q4-2026 | | | |
| | Focus Area | Goals/Rock for this quarter | |
| | Cash | Rock {marker} | Vamos en 40% |
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


# --- S82.4: propose rows for the confirmed tab --------------------------------

_PLAN: dict[str, object] = {
    "quarter": "Q4-2026",
    "critical_number": "10 clientes nuevos",
    "priorities": [
        {"priority": "Contratar vendedor", "kpi": "1 contratado", "decision": "people"},
        {"priority": "Definir cliente ideal", "kpi": "1 documento"},
    ],
}


def _confirm_ana(base: str) -> FlowResult:
    return run(
        {
            "action": "confirm",
            "base_path": base,
            "user_confirmed": True,
            "tab_name": "Ana",
            "connector_text": _workbook(),
            "file_title": "Tracker del grupo",
            "file_id": "f-1",
        }
    )


def _propose(base: str, **extra: object) -> FlowResult:
    context: dict[str, object] = {
        "action": "propose",
        "base_path": base,
        "connector_text": _workbook(),
        "file_title": "Tracker del grupo",
        "file_id": "f-1",
        "plan": _PLAN,
        "month": "2026-10",
    }
    context.update(extra)
    return run(context)


def _files_snapshot(base: Path) -> dict[str, str]:
    folder = base / ".escala" / "my-company"
    return {
        str(path): path.read_text(encoding="utf-8")
        for path in folder.rglob("*")
        if path.is_file()
    }


def test_propose_needs_a_confirmed_tab_first(tmp_path: Path) -> None:
    result = _propose(str(tmp_path))

    assert result.errors == ["needs_confirmed_tab"]
    assert result.proposal is None
    assert all(marker not in _dump(result) for marker in MARKERS.values())


def test_propose_without_a_plan_asks_to_define_priorities(tmp_path: Path) -> None:
    _confirm_ana(str(tmp_path))

    result = _propose(str(tmp_path), plan=None)

    assert result.errors == ["needs_plan"]
    assert "prioridades" in result.message


def test_propose_reads_the_plan_saved_by_the_opsp(tmp_path: Path) -> None:
    _confirm_ana(str(tmp_path))
    opsp = tmp_path / ".escala" / "my-company" / "opsp.yaml"
    opsp.write_text(
        "quarterly_plan:\n  critical_number: 7 ventas\n"
        "  priorities:\n    - priority: Abrir sucursal\n      kpi: '1'\n",
        encoding="utf-8",
    )

    result = _propose(str(tmp_path), plan=None)

    assert result.proposal is not None
    assert [row.priority for row in result.proposal.rows] == ["Abrir sucursal"]


def test_propose_says_where_to_paste_and_how_to_undo(tmp_path: Path) -> None:
    _confirm_ana(str(tmp_path))

    result = _propose(str(tmp_path))

    assert result.errors == []
    assert result.proposal is not None
    assert len(result.proposal.rows) == 2
    assert result.paste_block.splitlines() == [
        "People\tContratar vendedor\t1 contratado\t2026-10-31",
        "\tDefinir cliente ideal\t1 documento\t2026-10-31",
    ]
    message = result.message
    assert "compromisos de octubre" in message
    assert "**B8**" in message  # first empty row under Monthly Commitments
    assert "Monthly Commitments" in message
    assert result.paste_block in message
    assert "START HERE" in message  # never paste over the linked name
    assert "Ctrl+Z" in message
    assert "Mostrar historial de ediciones" in message
    assert "No uses «Restaurar esta versión»" in message


def test_propose_points_out_a_different_critical_number(tmp_path: Path) -> None:
    _confirm_ana(str(tmp_path))

    result = _propose(str(tmp_path))

    assert result.proposal is not None
    assert result.proposal.critical_number == "different"
    assert "10 clientes nuevos" in result.message
    assert "10 clientes nuevos" not in result.paste_block
    assert "¿Cuál" in result.message


def test_propose_asks_to_make_room_when_rows_do_not_fit() -> None:
    from coaching.tracker.messages import proposal_message
    from coaching.tracker.parser import CommitmentsLayout
    from coaching.tracker.proposal import ProposedRow, RowProposal

    rows = [
        ProposedRow(focus_area="Cash", priority=f"P{i}", kpi=None, due="2026-10-31")
        for i in range(3)
    ]
    proposal = RowProposal(
        month="2026-10", month_name="octubre", rows=rows, critical_number="same"
    )
    layout = CommitmentsLayout(
        header_row=4,
        focus_col=1,
        headers=["Focus Area", "Priorities", "KPIs", "Due Dates"],
        fields=["focus", "text", "kpi", "due"],
        first_free_row=6,
        free_rows=1,
    )

    message = proposal_message(proposal, layout, "Ana", "x")

    assert "Insertar 1 fila arriba" in message
    assert "fila 8" in message
    assert "2 veces" in message


def test_propose_with_nothing_new_says_so(tmp_path: Path) -> None:
    _confirm_ana(str(tmp_path))
    plan = {"priorities": [{"priority": f"Cobrar {MARKERS['Ana']}"}]}

    result = _propose(str(tmp_path), plan=plan)

    assert result.proposal is not None and result.proposal.rows == []
    assert result.paste_block == ""
    assert "nada nuevo" in result.message


def test_propose_user_messages_have_no_internal_jargon(tmp_path: Path) -> None:
    _confirm_ana(str(tmp_path))

    message = _propose(str(tmp_path)).message

    for word in ["tracker", "TSV", "MCP", "escala-", "skill", "yaml", "grid"]:
        assert word.lower() not in message.lower(), word


def test_privacy_propose_keeps_other_tabs_out_and_writes_nothing(
    tmp_path: Path,
) -> None:
    _confirm_ana(str(tmp_path))
    before = _files_snapshot(tmp_path)

    result = _propose(str(tmp_path))

    dump = _dump(result)
    for marker in _foreign("Ana"):
        assert marker not in dump, marker
    assert _files_snapshot(tmp_path) == before  # ESCALA only proposes


def test_propose_on_a_different_file_asks_for_the_tab_again(tmp_path: Path) -> None:
    _confirm_ana(str(tmp_path))

    result = _propose(str(tmp_path), file_title="Otro archivo", file_id="f-2")

    assert result.errors == ["link_mismatch"]
    assert result.proposal is None


def test_propose_from_a_pasted_tab(tmp_path: Path) -> None:
    pasted = (
        "Participant Name\t\tAna Demo\n"
        "Monthly Commitments\n"
        "\tFocus Area\tPriorities\tKPIs\tDue Dates\n"
    )
    run(
        {
            "action": "confirm",
            "base_path": str(tmp_path),
            "user_confirmed": True,
            "tab_name": "Ana",
            "pasted_text": pasted,
        }
    )

    result = run(
        {
            "action": "propose",
            "base_path": str(tmp_path),
            "pasted_text": pasted,
            "plan": _PLAN,
            "month": "2026-10",
        }
    )

    assert result.errors == []
    assert "**B4**" in result.message
    assert result.proposal is not None
    assert result.proposal.critical_number == "add"


# --- S82.4 owner defaults -----------------------------------------------------


def test_drive_notice_is_said_once_on_the_first_link_even_if_connected(
    tmp_path: Path,
) -> None:
    first = _confirm_ana(str(tmp_path))
    second = _confirm_ana(str(tmp_path))

    assert DRIVE_NOTICE in first.message
    assert first.message.startswith("Listo: tu pestaña es **Ana**.")
    assert DRIVE_NOTICE not in second.message


def test_drive_notice_is_not_repeated_if_the_connect_message_said_it(
    tmp_path: Path,
) -> None:
    result = run(
        {
            "action": "confirm",
            "base_path": str(tmp_path),
            "user_confirmed": True,
            "tab_name": "Ana",
            "connector_text": _workbook(),
            "drive_notice_shown": True,
        }
    )

    assert result.errors == []
    assert DRIVE_NOTICE not in result.message


def test_pasted_tab_gets_no_drive_notice(tmp_path: Path) -> None:
    result = run(
        {
            "action": "confirm",
            "base_path": str(tmp_path),
            "user_confirmed": True,
            "tab_name": "Ana",
            "pasted_text": "Participant Name\t\tAna Demo\n",
        }
    )

    assert DRIVE_NOTICE not in result.message


def test_pasted_tab_without_tab_name_uses_the_name_already_given(
    tmp_path: Path,
) -> None:
    result = run(
        {
            "action": "confirm",
            "base_path": str(tmp_path),
            "user_confirmed": True,
            "name": "Ana",
            "pasted_text": "Participant Name\t\tAna Demo\n",
        }
    )

    assert result.errors == []
    assert result.link is not None and result.link.tab_name == "Ana"


def test_pasted_tab_without_any_name_asks_for_the_tab(tmp_path: Path) -> None:
    result = run(
        {
            "action": "confirm",
            "base_path": str(tmp_path),
            "user_confirmed": True,
            "pasted_text": "Participant Name\t\tAna Demo\n",
        }
    )

    assert result.errors == ["needs_tab_name"]


def test_connector_path_still_needs_the_confirmed_tab_name(tmp_path: Path) -> None:
    result = run(
        {
            "action": "confirm",
            "base_path": str(tmp_path),
            "user_confirmed": True,
            "name": "Ana",
            "connector_text": _workbook(),
        }
    )

    assert result.errors == ["needs_tab_name"]


# --- S82.5: before the group meeting (suggestions only) -----------------------

_PASTED_WITH_DONE = (
    "Participant Name\t\tAna Demo\n"
    "Monthly Commitments\n"
    "\tFocus Area\tPriorities\tKPIs\tDue Dates\n"
    "\tCash\tCobrar cartera\t90%\t30/10/2026\n"
    "\tPeople\tContratar gerente\t1\t15/10/2026\tHecho\n"
    "\tExecution\tLanzar curso\t\tfin de mes\n"
    "\n"
    "Done - record anything you want to keep track\n"
    "\tFocus Area\tGoals/Rock/Action\n"
    "\tStrategy\tDefinir cliente ideal\n"
)


def _prepare(base: str, **extra: object) -> FlowResult:
    context: dict[str, object] = {
        "action": "prepare",
        "base_path": base,
        "connector_text": _workbook(),
        "file_title": "Tracker del grupo",
        "file_id": "f-1",
        "today": "2026-11-02",
    }
    context.update(extra)
    return run(context)


def _confirm_pasted(base: str, pasted: str) -> None:
    run(
        {
            "action": "confirm",
            "base_path": base,
            "user_confirmed": True,
            "tab_name": "Ana",
            "pasted_text": pasted,
        }
    )


def test_prepare_needs_a_confirmed_tab_first(tmp_path: Path) -> None:
    result = _prepare(str(tmp_path))

    assert result.errors == ["needs_confirmed_tab"]
    assert result.prep is None
    assert all(marker not in _dump(result) for marker in MARKERS.values())


def test_prepare_lists_overdue_with_the_date_as_written(tmp_path: Path) -> None:
    _confirm_ana(str(tmp_path))

    result = _prepare(str(tmp_path))

    assert result.errors == []
    assert result.prep is not None
    assert [item.text for item in result.prep.overdue] == [f"Cobrar {MARKERS['Ana']}"]
    assert result.message.startswith("Antes de tu reunión: 1 compromiso vencido.")
    assert "30/10/2026" in result.message
    assert "No moví nada en tu hoja." in result.message
    assert result.message.endswith("?")
    assert result.paste_block == ""


def test_prepare_uses_the_injected_reference_date(tmp_path: Path) -> None:
    _confirm_ana(str(tmp_path))

    result = _prepare(str(tmp_path), today="2026-10-01")

    assert result.prep is not None and result.prep.overdue == []


def test_prepare_with_a_bad_date_asks_for_today(tmp_path: Path) -> None:
    _confirm_ana(str(tmp_path))

    result = _prepare(str(tmp_path), today="mañana")

    assert result.errors == ["bad_today"]
    assert result.prep is None


def test_prepare_suggests_done_with_block_cell_and_undo(tmp_path: Path) -> None:
    _confirm_pasted(str(tmp_path), _PASTED_WITH_DONE)
    before = _files_snapshot(tmp_path)

    result = _prepare(str(tmp_path), connector_text=None, pasted_text=_PASTED_WITH_DONE)

    assert result.errors == []
    assert result.paste_block == "People\tContratar gerente"
    message = result.message
    assert message.startswith(
        "Antes de tu reunión: 1 compromiso vencido, 1 cumplido que puedes pasar "
        "a terminados (Done), 1 sin KPI y 1 con fecha por confirmar."
    )
    assert "**B11**" in message  # first empty row of the Done table
    assert result.paste_block in message
    assert "«fin de mes»" in message  # unreadable: asked, never guessed
    assert "Ctrl+Z" in message and "No uses «Restaurar esta versión»" in message
    assert "No moví nada en tu hoja." in message
    assert "No elimines la fila completa." in message
    assert message.endswith(
        "¿Pasas «Contratar gerente» a Done? ¿Qué hacemos con «Cobrar cartera»: "
        "nueva fecha o ya no va? ¿Me dices los KPI y las fechas que faltan?"
    )
    assert _files_snapshot(tmp_path) == before


def test_prepare_reads_swappable_dates_in_the_order_the_tab_shows(
    tmp_path: Path,
) -> None:
    """S82.7: 03/04/2026 follows the tab's own dd/mm dates, and says so."""
    pasted = _PASTED_WITH_DONE.replace("fin de mes", "03/04/2026")
    _confirm_pasted(str(tmp_path), pasted)

    result = _prepare(str(tmp_path), connector_text=None, pasted_text=pasted)

    assert result.prep is not None
    assert [i.text for i in result.prep.overdue] == ["Cobrar cartera", "Lanzar curso"]
    assert result.prep.unclear_due == []
    assert (
        "Leí «03/04/2026» como día/mes, igual que las demás fechas de tu hoja."
        in result.message
    )


def test_prepare_keeps_swappable_dates_unclear_when_the_tab_mixes_orders(
    tmp_path: Path,
) -> None:
    pasted = _PASTED_WITH_DONE.replace("fin de mes", "03/04/2026").replace(
        "15/10/2026", "10/15/2026"
    )
    _confirm_pasted(str(tmp_path), pasted)

    result = _prepare(str(tmp_path), connector_text=None, pasted_text=pasted)

    assert result.prep is not None
    assert result.prep.date_order is None
    assert [i.text for i in result.prep.unclear_due] == ["Lanzar curso"]
    assert "«03/04/2026»" in result.message
    assert "Leí «" not in result.message


def test_prepare_on_an_empty_sheet_offers_to_propose_rows(tmp_path: Path) -> None:
    empty = "Participant Name\t\tAna Demo\nMonthly Commitments\n"
    _confirm_pasted(str(tmp_path), empty)

    result = _prepare(str(tmp_path), connector_text=None, pasted_text=empty)

    assert result.errors == []
    assert "todavía no tiene compromisos del mes" in result.message
    assert result.message.endswith("?")


def test_prepare_on_a_different_file_asks_for_the_tab_again(tmp_path: Path) -> None:
    _confirm_ana(str(tmp_path))

    result = _prepare(str(tmp_path), file_title="Otro archivo", file_id="f-2")

    assert result.errors == ["link_mismatch"]
    assert result.prep is None


def test_prepare_user_messages_have_no_internal_jargon(tmp_path: Path) -> None:
    _confirm_pasted(str(tmp_path), _PASTED_WITH_DONE)

    message = _prepare(
        str(tmp_path), connector_text=None, pasted_text=_PASTED_WITH_DONE
    ).message

    for word in ["tracker", "TSV", "MCP", "escala-", "skill", "yaml", "grid"]:
        assert word.lower() not in message.lower(), word


def test_privacy_prepare_keeps_other_tabs_out_and_writes_nothing(
    tmp_path: Path,
) -> None:
    _confirm_ana(str(tmp_path))
    before = _files_snapshot(tmp_path)

    result = _prepare(str(tmp_path))

    dump = _dump(result)
    for marker in _foreign("Ana"):
        assert marker not in dump, marker
    assert _files_snapshot(tmp_path) == before  # ESCALA only suggests


def test_prep_message_plural_and_up_to_date() -> None:
    from datetime import date

    from coaching.tracker.maintenance import review_before_meeting
    from coaching.tracker.messages import PREP_UP_TO_DATE, prep_message
    from coaching.tracker.models import TrackerItem, TrackerSheet

    today = date(2026, 11, 2)
    finished = TrackerSheet(
        commitments=[
            TrackerItem(text=f"T{i}", kpi="1", due="30/11/2026", status="done")
            for i in range(2)
        ]
    )
    on_track = TrackerSheet(
        commitments=[TrackerItem(text="Abrir", kpi="1", due="30/11/2026")]
    )

    many = prep_message(review_before_meeting(finished, today), None, "Ana", "x")
    fine = prep_message(review_before_meeting(on_track, today), None, "Ana", "")

    assert many.startswith(
        "Antes de tu reunión: 2 cumplidos que puedes pasar a terminados (Done)"
    )
    assert "Si decides pasarlos a Done:" in many
    assert many.endswith("¿Pasas los terminados a Done?")
    assert fine == PREP_UP_TO_DATE


def test_seams_confirm_then_propose_then_paste_then_prepare(tmp_path: Path) -> None:
    """Epic checkpoint: S82.3 -> S82.4 -> S82.5 on one synthetic tab."""
    base = str(tmp_path)
    header = (
        "Participant Name\t\tAna Demo\n"
        "Monthly Commitments\n"
        "\tFocus Area\tPriorities\tKPIs\tDue Dates\n"
    )
    done = "\nDone - record anything you want to keep track\n\tFocus Area\tGoals\n"
    confirmed = run(
        {
            "action": "confirm",
            "base_path": base,
            "user_confirmed": True,
            "name": "Ana",
            "pasted_text": header + done,
        }
    )
    assert confirmed.errors == []

    proposed = run(
        {
            "action": "propose",
            "base_path": base,
            "pasted_text": header + done,
            "plan": _PLAN,
            "month": "2026-10",
        }
    )
    assert proposed.errors == [] and "**B4**" in proposed.message

    # The owner pastes the block at B4, then marks the first row as done.
    pasted_rows = [f"\t{line}" for line in proposed.paste_block.splitlines()]
    pasted_rows[0] += "\tHecho"
    after_paste = header + "\n".join(pasted_rows) + "\n" + done
    before = _files_snapshot(tmp_path)

    prepared = run(
        {
            "action": "prepare",
            "base_path": base,
            "pasted_text": after_paste,
            "today": "2026-11-02",
        }
    )

    assert prepared.errors == []
    assert prepared.prep is not None
    assert [i.text for i in prepared.prep.finished] == ["Contratar vendedor"]
    assert [i.text for i in prepared.prep.overdue] == ["Definir cliente ideal"]
    assert prepared.paste_block == "People\tContratar vendedor"
    assert "**B9**" in prepared.message  # first empty row of Done (row 9)
    assert _files_snapshot(tmp_path) == before


# --- S82.7: Rocks rows through the same propose action ------------------------


def _rocks_tab(heading: str, *rocks: str) -> str:
    return (
        "Participant Name\t\tAna Demo\n"
        "Monthly Commitments\n"
        "\tFocus Area\tPriorities\tKPIs\tDue Dates\n"
        "\n"
        f"{heading}\n"
        "\tFocus Area\tGoals/Rock for this quarter\n"
        + "".join(f"\t{rock}\n" for rock in rocks)
        + "\nDone - record anything you want to keep track\n"
        "\tFocus Area\tGoals/Rock/Action\n"
    )


def _propose_pasted(base: str, pasted: str, **extra: object) -> FlowResult:
    _confirm_pasted(base, pasted)
    return _propose(
        base, connector_text=None, pasted_text=pasted, table="rocks", **extra
    )


def test_propose_rocks_says_where_to_paste_and_how_to_undo(tmp_path: Path) -> None:
    _confirm_ana(str(tmp_path))

    result = _propose(str(tmp_path), table="rocks")

    assert result.errors == []
    assert result.proposal is None
    assert result.rock_proposal is not None
    assert result.rock_proposal.quarter == "Q4-2026"
    assert result.paste_block.splitlines() == [
        "People\tContratar vendedor",
        "\tDefinir cliente ideal",
    ]
    message = result.message
    assert message.startswith(
        "Te propongo estas 2 filas para tus metas del trimestre (Rocks) del **Q4-2026**:"
    )
    assert "| Focus Area | Goals/Rock for this quarter |" in message
    assert "**B13**" in message  # first empty row under the Rocks table
    assert "Quarterly Goals" in message
    assert result.paste_block in message
    assert "no tiene columna de KPI" in message  # the plan's KPI is not pasted
    assert "Ctrl+Z" in message and "No uses «Restaurar esta versión»" in message


def test_propose_rocks_without_a_quarter_asks_and_gives_no_block(
    tmp_path: Path,
) -> None:
    pasted = _rocks_tab("Quarterly Goals (Rocks)")

    asked = _propose_pasted(str(tmp_path), pasted)

    assert asked.errors == ["needs_quarter"]
    assert asked.paste_block == "" and asked.rock_proposal is None
    assert asked.quarter_check is not None
    assert "no dice de qué trimestre" in asked.message
    assert asked.message.endswith("¿Son del **Q4-2026**?")

    answered = _propose(
        str(tmp_path),
        connector_text=None,
        pasted_text=pasted,
        table="rocks",
        quarter="Q4-2026",
    )

    assert answered.errors == []
    assert answered.rock_proposal is not None
    assert answered.rock_proposal.quarter == "Q4-2026"
    assert "**B7**" in answered.message


def test_propose_rocks_with_an_unclear_quarter_asks_which_one(tmp_path: Path) -> None:
    pasted = _rocks_tab("Quarterly Goals (Rocks) - este trimestre")

    result = _propose_pasted(str(tmp_path), pasted, plan={"priorities": ["Vender"]})

    assert result.errors == ["needs_quarter"]
    assert "«este trimestre»" in result.message
    assert result.message.endswith("¿De qué trimestre son? (por ejemplo, Q4-2026)")


def test_propose_rocks_for_another_quarter_asks_first(tmp_path: Path) -> None:
    pasted = _rocks_tab("Quarterly Goals (Rocks) - Q3-2026", "Cash\tRock viejo")

    result = _propose_pasted(str(tmp_path), pasted)

    assert result.errors == ["quarter_mismatch"]
    assert result.paste_block == ""
    assert "**Q3-2026**" in result.message and "**Q4-2026**" in result.message
    assert result.message.endswith("?")


def test_propose_rocks_skips_rocks_already_written(tmp_path: Path) -> None:
    pasted = _rocks_tab(
        "Quarterly Goals (Rocks) - Q4-2026",
        "People\tContratar vendedor",
        "Strategy\tdefinir cliente IDEAL",
    )

    result = _propose_pasted(str(tmp_path), pasted)

    assert result.rock_proposal is not None and result.rock_proposal.rows == []
    assert result.paste_block == ""
    assert "nada nuevo" in result.message


def test_propose_rocks_without_a_rocks_table_says_so(tmp_path: Path) -> None:
    pasted = "Participant Name\t\tAna Demo\nMonthly Commitments\n"

    result = _propose_pasted(str(tmp_path), pasted)

    assert result.errors == ["no_rocks_table"]
    assert "Quarterly Goals" in result.message


def test_propose_with_an_unknown_table_asks_which_one(tmp_path: Path) -> None:
    _confirm_ana(str(tmp_path))

    result = _propose(str(tmp_path), table="ventas")

    assert result.errors == ["bad_table"]
    assert "Rocks" in result.message


def test_propose_rocks_user_messages_have_no_internal_jargon(tmp_path: Path) -> None:
    _confirm_ana(str(tmp_path))
    pasted = _rocks_tab("Quarterly Goals (Rocks)")
    messages_seen = [
        _propose(str(tmp_path), table="rocks").message,
        _propose_pasted(str(tmp_path / "b"), pasted).message,
    ]

    for message in messages_seen:
        for word in ["tracker", "TSV", "MCP", "escala-", "skill", "yaml", "grid"]:
            assert word.lower() not in message.lower(), word


def test_privacy_propose_rocks_keeps_other_tabs_out_and_writes_nothing(
    tmp_path: Path,
) -> None:
    _confirm_ana(str(tmp_path))
    before = _files_snapshot(tmp_path)

    result = _propose(str(tmp_path), table="rocks")

    dump = _dump(result)
    for marker in _foreign("Ana"):
        assert marker not in dump, marker
    assert _files_snapshot(tmp_path) == before  # ESCALA only proposes


# --- S82.7: prepare also reviews the Rocks, in their own block ----------------


def _workbook_with_rock_dates() -> str:
    """Every tab's Rocks table has a due column and an overdue Rock."""
    return (
        _workbook()
        .replace(
            "| | Focus Area | Goals/Rock for this quarter | |",
            "| | Focus Area | Goals/Rock for this quarter | Due Dates |",
        )
        .replace("Vamos en 40%", "15/10/2026")
    )


_PASTED_ROCKS = (
    "Participant Name\t\tAna Demo\n"
    "Monthly Commitments\n"
    "\tFocus Area\tPriorities\tKPIs\tDue Dates\n"
    "\tCash\tCobrar cartera\t90%\t30/11/2026\n"
    "\n"
    "Quarterly Goals (Rocks) - Q4-2026\n"
    "\tFocus Area\tGoals/Rock for this quarter\tKPIs\tDue Dates\n"
    "\tCash\tAbrir sucursal\t1\t15/10/2026\n"
    "\tPeople\tContratar gerente\t\t2026-12-15\n"
    "\tExecution\tLanzar curso\t3\tfin de año\n"
    "\tStrategy\tRock terminado\t1\t01/10/2026\tTerminado\n"
    "\n"
    "Done - record anything you want to keep track\n"
    "\tFocus Area\tGoals/Rock/Action\n"
)


def test_prepare_reviews_rocks_in_their_own_block(tmp_path: Path) -> None:
    _confirm_pasted(str(tmp_path), _PASTED_ROCKS)
    before = _files_snapshot(tmp_path)

    result = _prepare(str(tmp_path), connector_text=None, pasted_text=_PASTED_ROCKS)

    assert result.errors == []
    assert result.prep is not None
    rocks = result.prep.rocks
    assert [i.text for i in rocks.overdue] == ["Abrir sucursal"]
    assert [i.text for i in rocks.missing_kpi] == ["Contratar gerente"]
    assert [i.text for i in rocks.unclear_due] == ["Lanzar curso"]
    message = result.message
    assert message.startswith(
        "Antes de tu reunión: tus compromisos del mes están al día."
    )
    assert (
        "**Tus metas del trimestre (Rocks) del Q4-2026:** 1 vencido, 1 sin KPI y 1 con fecha por "
        "confirmar." in message
    )
    assert "- Vencido: Abrir sucursal (era para el 15/10/2026)" in message
    assert "- Fecha por confirmar: Lanzar curso («fin de año»)" in message
    assert "Rock terminado" not in message  # finished Rocks are left alone
    assert "No moví nada en tu hoja." in message
    assert result.paste_block == ""
    assert message.endswith(
        "¿Qué hacemos con el Rock «Abrir sucursal»: nueva fecha o ya no va este "
        "trimestre? ¿Me dices los KPI y las fechas que faltan en tus Rocks?"
    )
    assert _files_snapshot(tmp_path) == before


def test_prepare_keeps_commitments_and_rocks_visibly_apart(tmp_path: Path) -> None:
    pasted = _PASTED_ROCKS.replace("30/11/2026", "30/10/2026")
    _confirm_pasted(str(tmp_path), pasted)

    message = _prepare(str(tmp_path), connector_text=None, pasted_text=pasted).message

    commitments, rest = message.split(
        "**Tus metas del trimestre (Rocks) del Q4-2026:**"
    )
    rocks, decisions = rest.split("No moví nada en tu hoja.")
    assert "Cobrar cartera" in commitments and "Cobrar cartera" not in rocks
    assert "Abrir sucursal" in rocks and "Abrir sucursal" not in commitments
    assert message.startswith("Antes de tu reunión: 1 compromiso vencido.")
    assert "¿Qué hacemos con «Cobrar cartera»" in decisions  # decisions close it
    assert message.endswith("¿Me dices los KPI y las fechas que faltan en tus Rocks?")


def test_prepare_with_only_rocks_says_there_are_no_commitments_yet(
    tmp_path: Path,
) -> None:
    pasted = _PASTED_ROCKS.replace("\tCash\tCobrar cartera\t90%\t30/11/2026\n", "")
    _confirm_pasted(str(tmp_path), pasted)

    message = _prepare(str(tmp_path), connector_text=None, pasted_text=pasted).message

    assert message.startswith(
        "Antes de tu reunión: todavía no tienes compromisos del mes."
    )
    assert "**Tus metas del trimestre (Rocks) del Q4-2026:**" in message


def test_prepare_template_rocks_are_not_asked_for_columns_they_lack(
    tmp_path: Path,
) -> None:
    """The observed template has no KPI or date column for Rocks."""
    _confirm_ana(str(tmp_path))

    result = _prepare(str(tmp_path))

    assert result.prep is not None
    assert result.prep.rocks.reviewed == 1
    assert not result.prep.rocks.has_findings
    assert "**Tus Rocks" not in result.message  # only the commitments block


def test_prepare_all_up_to_date_mentions_the_rocks(tmp_path: Path) -> None:
    pasted = (
        _PASTED_ROCKS.replace("15/10/2026", "15/12/2026")
        .replace("\t\t2026-12-15", "\t2\t2026-12-15")
        .replace("fin de año", "2026-12-20")
    )
    _confirm_pasted(str(tmp_path), pasted)

    message = _prepare(str(tmp_path), connector_text=None, pasted_text=pasted).message

    assert (
        "compromisos del mes y tus metas del trimestre (Rocks) están al día" in message
    )
    assert message.endswith("?")


def test_prepare_rocks_user_messages_have_no_internal_jargon(tmp_path: Path) -> None:
    _confirm_pasted(str(tmp_path), _PASTED_ROCKS)

    message = _prepare(
        str(tmp_path), connector_text=None, pasted_text=_PASTED_ROCKS
    ).message

    for word in ["tracker", "TSV", "MCP", "escala-", "skill", "yaml", "grid", "None"]:
        assert word.lower() not in message.lower(), word


def test_privacy_prepare_with_rocks_keeps_other_tabs_out(tmp_path: Path) -> None:
    workbook = _workbook_with_rock_dates()
    run(
        {
            "action": "confirm",
            "base_path": str(tmp_path),
            "user_confirmed": True,
            "tab_name": "Ana",
            "connector_text": workbook,
            "file_title": "Tracker del grupo",
            "file_id": "f-1",
        }
    )
    before = _files_snapshot(tmp_path)

    result = _prepare(str(tmp_path), connector_text=workbook)

    assert result.prep is not None
    assert [i.text for i in result.prep.rocks.overdue] == [f"Rock {MARKERS['Ana']}"]
    assert f"Rock {MARKERS['Ana']}" in result.message
    dump = _dump(result)
    for marker in _foreign("Ana"):
        assert marker not in dump, marker
    assert _files_snapshot(tmp_path) == before
