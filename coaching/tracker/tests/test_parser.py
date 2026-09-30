"""Tests for reading an accountability tracker participant sheet (S82.2).

Fixtures are synthetic but keep the shape of the real 2025-26 template:
labels in column A, tables starting in column B, unlabeled status columns,
side tables and trailing custom blocks.
"""

from __future__ import annotations

from coaching.tracker import parse_connector_text, parse_sheet

Row = list[str | None]


def _row(*cells: str | None) -> Row:
    return list(cells)


def _header_block() -> list[Row]:
    return [
        _row("Participant Name", None, "Ana Demo"),
        _row("Business Name", None, "Demo SA"),
        _row("Critical Number", None, "5 mdp 2026"),
        _row(),
    ]


def test_reads_identity_and_critical_number() -> None:
    sheet = parse_sheet(_header_block())

    assert sheet.participant == "Ana Demo"
    assert sheet.business == "Demo SA"
    assert sheet.critical_number == "5 mdp 2026"


def test_blank_template_sheet_is_empty_not_an_error() -> None:
    rows = [
        _row("Participant Name", None, None),
        _row("Business Name", None, None),
        _row("Monthly Commitments"),
        _row(None, "Focus Area", "Priorities", "KPIs", "Due Dates"),
        _row("Quarterly Goals (Rocks) - Q2"),
        _row(None, "Focus Area", "Goals/Rock for this quarter"),
        _row("Done - record anything you want to keep track"),
        _row(None, "Focus Area", "Goals/Rock/Action"),
    ]

    sheet = parse_sheet(rows)

    assert sheet.participant is None
    assert sheet.commitments == []
    assert sheet.rocks == []
    assert sheet.done == []


def test_commitments_accept_action_area_header_and_map_decision() -> None:
    rows = _header_block() + [
        _row("Monthly Commitments"),
        _row(None, "Action Area", "Priorities", "KPIs", "Due Dates"),
        _row(None, "Cash", "Cobrar cartera", "90% cobrado", "30/11/2025"),
    ]

    item = parse_sheet(rows).commitments[0]

    assert item.focus_area == "Cash"
    assert item.decision == "cash"
    assert item.text == "Cobrar cartera"
    assert item.kpi == "90% cobrado"
    assert item.due == "30/11/2025"


def test_unlabeled_columns_after_the_table_are_status_and_note() -> None:
    rows = _header_block() + [
        _row("Monthly Commitments"),
        _row(None, "Focus Area", "Priorities", "KPIs", "Due Dates"),
        _row(
            None,
            "Execution",
            "Lanzar curso",
            "Temario",
            "30/11/2025",
            "En proceso",
            "movida",
        ),
    ]

    item = parse_sheet(rows).commitments[0]

    assert item.status == "En proceso"
    assert item.notes == ["movida"]


def test_side_table_on_the_header_row_is_not_part_of_commitments() -> None:
    rows = _header_block() + [
        _row("Monthly Commitments"),
        _row(
            None,
            "Focus Area",
            "Priorities",
            "KPIs",
            "Due Dates",
            None,
            "Monthly Revenue Tracking",
            "Real",
        ),
        _row(
            None,
            "Ventas",
            "Dos grupos",
            "25 personas",
            "15/11/2025",
            None,
            "Octubre",
            "100",
        ),
    ]

    item = parse_sheet(rows).commitments[0]

    assert item.status is None
    assert item.notes == []
    assert "Octubre" not in item.model_dump_json()


def test_trailing_custom_block_ends_done_and_is_reported() -> None:
    rows = _header_block() + [
        _row("Done - record anything you want to keep track"),
        _row(None, "Focus Area", "Goals/Rock/Action"),
        _row(None, "People", "Contraté gerente"),
        _row(),
        _row("Monthly Revenue", "Venta", "EBITDA"),
        _row("July", "303000", "14780"),
    ]

    sheet = parse_sheet(rows)

    assert [item.text for item in sheet.done] == ["Contraté gerente"]
    assert sheet.unparsed_blocks == ["Monthly Revenue"]


def test_spanish_or_custom_areas_keep_text_and_only_map_when_unambiguous() -> None:
    rows = _header_block() + [
        _row("Monthly Commitments"),
        _row(None, "Focus Area", "Priorities", "KPIs", "Due Dates"),
        _row(None, "Estrategia", "Definir oferta", None, None),
        _row(None, "Ejecución", "Junta quincenal", None, None),
        _row(None, "Ventas", "Pipeline de 7", None, None),
        _row(None, "Strategy/People", "Comunicación interna", None, None),
    ]

    items = parse_sheet(rows).commitments

    assert [(i.focus_area, i.decision) for i in items] == [
        ("Estrategia", "strategy"),
        ("Ejecución", "execution"),
        ("Ventas", None),
        ("Strategy/People", None),
    ]


def test_rows_without_area_are_kept_as_written() -> None:
    rows = _header_block() + [
        _row("Monthly Commitments"),
        _row(None, "Focus Area", "Priorities", "KPIs", "Due Dates"),
        _row(None, None, "Leer un libro", "done", None),
        _row(),
        _row(None, None, None, None, None, None),
    ]

    items = parse_sheet(rows).commitments

    assert len(items) == 1
    assert items[0].focus_area is None
    assert items[0].decision is None
    assert items[0].kpi == "done"
    assert items[0].status is None


def test_rocks_keep_quarter_label_and_progress() -> None:
    rows = _header_block() + [
        _row("Quarterly Goals (Rocks) - Q4-2025"),
        _row(None, "Focus Area", "Goals/Rock for this quarter"),
        _row(None, "Marketing", "Pasar de 12 a 30 pacientes", "Vamos en 18"),
    ]

    sheet = parse_sheet(rows)

    assert sheet.rocks_quarter == "Q4-2025"
    assert sheet.rocks[0].text == "Pasar de 12 a 30 pacientes"
    assert sheet.rocks[0].status == "Vamos en 18"


CONNECTOR_TEXT = """Context Type: corpus_document
## Table Context
### File Name: Tracker
### Sheet Name: START HERE
### Table Range: A1:D3
### Table Sample Data:
|               |          |       |               |
| :-----------: | :------: | :---: | :-----------: |
| Group Info    |          |       |               |
| Name          | Phone \\# | Email | Business Name |
| Ana Demo      |          |       | Demo SA       |

### Table Columns:
-
  - range: A1:A3

### Sheet Name: Ana
### Table Range: A1:E6
### Table Sample Data:
|                     |            |      |           |        |
| :-----------------: | :--------: | :--: | :-------: | :----: |
| Participant Name    | Ana Demo   |      |           |        |
| Business Name       | Demo SA    |      |           |        |
| Monthly Commitments |            |      |           |        |
| Focus Area          | Priorities | KPIs | Due Dates | Status |
| Cash                | Cobrar     | 90%  | 30/11     | listo  |
| Done                |            |      |           |        |

### Table Range: B8:C9
### Table Sample Data:
|            |                   |
| :--------: | :---------------: |
| Focus Area | Goals/Rock/Action |
| People     | Contraté gerente  |
"""


def test_connector_text_becomes_grids_per_sheet_respecting_ranges() -> None:
    grids = parse_connector_text(CONNECTOR_TEXT)

    assert list(grids) == ["START HERE", "Ana"]
    assert grids["START HERE"][1][1] == "Phone #"
    ana = grids["Ana"]
    assert ana[0][:2] == ["Participant Name", "Ana Demo"]
    assert ana[7][1:3] == ["Focus Area", "Goals/Rock/Action"]
    assert ana[8][1:3] == ["People", "Contraté gerente"]


def test_connector_sheet_with_table_in_column_a_still_parses() -> None:
    sheet = parse_sheet(parse_connector_text(CONNECTOR_TEXT)["Ana"])

    assert sheet.participant == "Ana Demo"
    assert sheet.commitments[0].text == "Cobrar"
    assert sheet.commitments[0].status == "listo"
    assert [item.text for item in sheet.done] == ["Contraté gerente"]
