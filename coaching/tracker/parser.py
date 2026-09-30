"""Read a tracker participant sheet from a cell grid or Drive connector text.

The template varies per participant (S82.2 story): tables may start in
column A or B, status lives in unlabeled columns, side tables share the
header row and custom blocks follow the Done section. The parser keeps what
the participant wrote and never reinterprets a cell.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

from coaching.tracker.models import Decision, TrackerItem, TrackerSheet

Cell = str | None
Grid = list[list[Cell]]
Section = Literal["commitments", "rocks", "done"]
Column = Literal["focus", "text", "kpi", "due", "status", "note"]

_IDENTITY = {
    "participant name": "participant",
    "business name": "business",
    "critical number": "critical_number",
}
_SECTIONS: tuple[tuple[str, Section], ...] = (
    ("monthly commitments", "commitments"),
    ("quarterly goals", "rocks"),
    ("done", "done"),
)
_FOCUS_HEADERS = {"focus area", "action area"}
_MAX_UNLABELED = 2
_DECISIONS: dict[str, Decision] = {
    "cash": "cash",
    "efectivo": "cash",
    "flujo": "cash",
    "flujo de efectivo": "cash",
    "strategy": "strategy",
    "estrategia": "strategy",
    "execution": "execution",
    "ejecucion": "execution",
    "people": "people",
    "personas": "people",
    "equipo": "people",
    "gente": "people",
}


def _clean(cell: object) -> str | None:
    if cell is None:
        return None
    text = str(cell).strip()
    return text or None


def _key(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return " ".join(folded.lower().split())


def _cell(row: list[Cell], index: int) -> str | None:
    return _clean(row[index]) if index < len(row) else None


def _decision(focus: str | None) -> Decision | None:
    return _DECISIONS.get(_key(focus)) if focus else None


def _section_of(label: str) -> Section | None:
    key = _key(label)
    for prefix, section in _SECTIONS:
        if key.startswith(prefix):
            return section
    return None


def _field_of(header: str) -> Column:
    key = _key(header)
    if key in _FOCUS_HEADERS:
        return "focus"
    if key.startswith(("priorit", "goal")):
        return "text"
    if key.startswith("kpi"):
        return "kpi"
    if key.startswith("due"):
        return "due"
    if key in {"status", "estado"}:
        return "status"
    return "note"


def _columns(header: list[Cell], start: int) -> list[tuple[int, Column]]:
    """Map the header run starting at the focus cell, plus unlabeled columns."""
    columns: list[tuple[int, Column]] = []
    index = start
    while _cell(header, index) is not None:
        columns.append((index, _field_of(_cell(header, index) or "")))
        index += 1
    has_status = any(field == "status" for _, field in columns)
    for offset in range(_MAX_UNLABELED):
        if _cell(header, index + offset) is not None:
            break  # a side table shares the header row
        field: Column = "status" if offset == 0 and not has_status else "note"
        columns.append((index + offset, field))
    return columns


def _item(row: list[Cell], columns: list[tuple[int, Column]]) -> TrackerItem | None:
    values: dict[str, str] = {}
    notes: list[str] = []
    for index, field in columns:
        value = _cell(row, index)
        if value is None:
            continue
        if field == "note":
            notes.append(value)
        else:
            values.setdefault(field, value)
    focus = values.get("focus")
    if focus is None and "text" not in values:
        return None
    return TrackerItem(
        focus_area=focus,
        decision=_decision(focus),
        text=values.get("text"),
        kpi=values.get("kpi"),
        due=values.get("due"),
        status=values.get("status"),
        notes=notes,
    )


def _focus_start(row: list[Cell]) -> int | None:
    for index, cell in enumerate(row):
        value = _clean(cell)
        if value and _key(value) in _FOCUS_HEADERS:
            return index
    return None


def parse_sheet(rows: Grid) -> TrackerSheet:
    """Parse one participant sheet given as rows of cells (column A first)."""
    sheet = TrackerSheet()
    section: Section | None = None
    columns: list[tuple[int, Column]] | None = None
    for row in rows:
        first = _cell(row, 0)
        if first and _key(first) in _IDENTITY:
            value = next((v for v in map(_clean, row[1:]) if v), None)
            setattr(sheet, _IDENTITY[_key(first)], value)
            continue
        heading = _section_of(first) if first else None
        if first and heading is not None:
            section, columns = heading, None
            if heading == "rocks" and " - " in first:
                sheet.rocks_quarter = first.split(" - ", 1)[1].strip() or None
            continue
        if section is None:
            continue
        if columns is None:
            start = _focus_start(row)
            if start is not None:
                columns = _columns(row, start)
            continue
        table_in_column_a = columns[0][0] == 0
        if first and not table_in_column_a:
            sheet.unparsed_blocks.append(first)
            section, columns = None, None
            continue
        item = _item(row, columns)
        if item is not None:
            getattr(sheet, section).append(item)
    return sheet


_RANGE = re.compile(r"^([A-Z]+)(\d+):([A-Z]+)(\d+)$")
_SEPARATOR = re.compile(r"^\|(\s*:?-+:?\s*\|)+\s*$")


def _column_index(letters: str) -> int:
    index = 0
    for letter in letters:
        index = index * 26 + (ord(letter) - ord("A") + 1)
    return index - 1


def _split_markdown_row(line: str) -> list[Cell]:
    cells = re.split(r"(?<!\\)\|", line.strip())[1:-1]
    return [_clean(re.sub(r"\\(.)", r"\1", cell)) for cell in cells]


def _place(grid: Grid, top: int, left: int, table: Grid) -> None:
    for r, cells in enumerate(table):
        while len(grid) <= top + r:
            grid.append([])
        target = grid[top + r]
        for c, value in enumerate(cells):
            while len(target) <= left + c:
                target.append(None)
            if value is not None:
                target[left + c] = value


def parse_connector_text(text: str) -> dict[str, Grid]:
    """Turn the Drive connector's text rendering into one grid per sheet.

    Each table is placed at its declared ``Table Range``. The connector adds
    an empty header row before the data; it is dropped when the row count
    shows it is extra.
    """
    grids: dict[str, Grid] = {}
    sheet: str | None = None
    bounds: tuple[int, int, int] | None = None
    table: Grid = []

    def flush() -> None:
        if sheet is not None and bounds is not None and table:
            top, left, height = bounds
            rows = (
                table[1:] if len(table) == height + 1 and not any(table[0]) else table
            )
            _place(grids[sheet], top, left, rows)

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("### Sheet Name:"):
            flush()
            sheet, bounds, table = line.split(":", 1)[1].strip(), None, []
            grids.setdefault(sheet, [])
        elif line.startswith("### Table Range:"):
            flush()
            table = []
            match = _RANGE.match(line.split(":", 1)[1].strip())
            if match:
                col_a, row_a, _, row_b = match.groups()
                bounds = (
                    int(row_a) - 1,
                    _column_index(col_a),
                    int(row_b) - int(row_a) + 1,
                )
            else:
                bounds = None
        elif line.startswith("|") and bounds is not None:
            if not _SEPARATOR.match(line):
                table.append(_split_markdown_row(line))
        elif table:
            flush()
            table = []
    flush()
    return grids
