"""Where the new commitment rows can be pasted (S82.4).

Synthetic grids with the template's shape: labels in column A, the commitments
table from column B, the Rocks heading right below. The layout never points at
a cell that already holds something.
"""

from __future__ import annotations

from coaching.tracker.parser import cell_ref, commitments_layout, done_layout

Row = list[str | None]


def _row(*cells: str | None) -> Row:
    return list(cells)


def _sheet(*commitments: Row, blank_rows: int = 3, rocks: bool = True) -> list[Row]:
    rows: list[Row] = [
        _row("Participant Name", None, "Ana Demo"),
        _row("Critical Number", None, "10 clientes"),
        _row(),
        _row("Monthly Commitments"),
        _row(None, "Focus Area", "Priorities", "KPIs", "Due Dates"),
        *commitments,
    ]
    rows += [_row() for _ in range(blank_rows)]
    if rocks:
        rows += [
            _row("Quarterly Goals (Rocks) - Q4"),
            _row(None, "Focus Area", "Goals/Rock for this quarter"),
        ]
    return rows


def test_first_free_row_is_right_below_the_last_commitment() -> None:
    grid = _sheet(_row(None, "Cash", "Cobrar", "90%", "30/10/2026"))

    layout = commitments_layout(grid)

    assert layout is not None
    assert layout.header_row == 4
    assert layout.focus_col == 1
    assert layout.headers == ["Focus Area", "Priorities", "KPIs", "Due Dates"]
    assert layout.fields == ["focus", "text", "kpi", "due"]
    assert layout.first_free_row == 6
    assert layout.free_rows == 3
    assert cell_ref(layout.first_free_row, layout.focus_col) == "B7"


def test_empty_table_starts_right_under_the_header() -> None:
    layout = commitments_layout(_sheet(blank_rows=2))

    assert layout is not None
    assert layout.first_free_row == 5
    assert layout.free_rows == 2


def test_a_gap_before_a_later_row_is_not_free() -> None:
    grid = _sheet(
        _row(None, "Cash", "Cobrar"),
        _row(),
        _row(None, None, None, None, None, "a medias"),
    )

    layout = commitments_layout(grid)

    assert layout is not None
    assert layout.first_free_row == 8  # the status-only row is occupied


def test_no_rows_left_before_the_rocks_section() -> None:
    layout = commitments_layout(_sheet(_row(None, "Cash", "Cobrar"), blank_rows=0))

    assert layout is not None
    assert layout.free_rows == 0


def test_last_section_has_unlimited_room() -> None:
    layout = commitments_layout(_sheet(_row(None, "Cash", "Cobrar"), rocks=False))

    assert layout is not None
    assert layout.free_rows is None


def test_side_table_on_the_header_row_is_not_part_of_the_paste_span() -> None:
    grid: list[Row] = [
        _row("Monthly Commitments"),
        _row(
            None,
            "Focus Area",
            "Priorities",
            "KPIs",
            "Due Dates",
            None,
            "Monthly Revenue Tracking",
        ),
        _row(None, None, None, None, None, None, "Oct", "100"),
    ]

    layout = commitments_layout(grid)

    assert layout is not None
    assert layout.headers == ["Focus Area", "Priorities", "KPIs", "Due Dates"]
    assert layout.first_free_row == 2


def test_table_in_column_a_ends_at_the_next_heading() -> None:
    grid: list[Row] = [
        _row("Monthly Commitments"),
        _row("Action Area", "Priorities", "KPIs", "Due Dates"),
        _row("Ventas", "Llamar", "20", "31/10/2026"),
        _row(),
        _row("Done - record anything"),
    ]

    layout = commitments_layout(grid)

    assert layout is not None
    assert layout.focus_col == 0
    assert layout.first_free_row == 3
    assert layout.free_rows == 1


def test_sheet_without_commitments_table_has_no_layout() -> None:
    assert commitments_layout([_row("Participant Name", None, "Ana")]) is None


def test_cell_ref_handles_double_letters() -> None:
    assert cell_ref(0, 0) == "A1"
    assert cell_ref(9, 26) == "AA10"


# --- S82.5: where finished rows can be pasted in Done -------------------------


def test_done_layout_points_below_the_last_done_row() -> None:
    grid = _sheet(_row(None, "Cash", "Cobrar", "90%", "30/10/2026")) + [
        _row("Done - record anything you want to keep track"),
        _row(None, "Focus Area", "Goals/Rock/Action"),
        _row(None, "People", "Contraté gerente"),
        _row(),
        _row(),
        _row("Notas del coach"),
    ]

    layout = done_layout(grid)

    assert layout is not None
    assert layout.fields == ["focus", "text"]
    assert layout.headers == ["Focus Area", "Goals/Rock/Action"]
    assert cell_ref(layout.first_free_row, layout.focus_col) == "B15"
    assert layout.free_rows == 2  # the custom block below ends the table


def test_done_layout_is_none_without_a_done_table() -> None:
    assert done_layout(_sheet()) is None
