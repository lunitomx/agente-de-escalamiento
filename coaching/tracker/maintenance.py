# pyright: strict
"""Before the group meeting (S82.5): suggestions only, nothing is moved.

Dates are read conservatively (design U4): ISO, ``dd/mm/aaaa`` and written
month names in Spanish or English. When day and month could swap, the order
the confirmed tab's own unambiguous dates agree on is used (S82.7); with no
such dates, or mixed ones, the date stays "por confirmar", and so does any
other text. Month-first is read only when the tab shows it. Finished is a
closed vocabulary; everything else is unfinished.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from coaching.tracker.models import TrackerItem, TrackerSheet
from coaching.tracker.parser import Column
from coaching.tracker.proposal import paste_cell

_MONTHS: dict[str, int] = {
    **{
        name: number
        for number, names in enumerate(
            [
                ("enero", "ene", "january", "jan"),
                ("febrero", "feb", "february"),
                ("marzo", "mar", "march"),
                ("abril", "abr", "april", "apr"),
                ("mayo", "may"),
                ("junio", "jun", "june"),
                ("julio", "jul", "july"),
                ("agosto", "ago", "august", "aug"),
                ("septiembre", "setiembre", "sep", "sept", "set", "september"),
                ("octubre", "oct", "october"),
                ("noviembre", "nov", "november"),
                ("diciembre", "dic", "december", "dec"),
            ],
            start=1,
        )
        for name in names
    }
}
_ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")
_NUMERIC = re.compile(r"^(\d{1,2})([/.-])(\d{1,2})\2(\d{4})$")
_DAY_FIRST = re.compile(r"^(\d{1,2}) (?:de )?([a-z]+)\.?,? (?:de |del )?(\d{4})$")
_MONTH_FIRST = re.compile(r"^([a-z]+)\.? (\d{1,2}),? (\d{4})$")
# Design § S82.5: closed vocabulary, compared without accents or case.
FINISHED = frozenset(
    {
        "done",
        "hecho",
        "hecha",
        "terminado",
        "terminada",
        "completado",
        "completada",
        "✅",
        "100%",
    }
)


def _fold(text: str) -> str:
    """Lowercase, no accents, single spaces; symbols such as ✅ survive."""
    decomposed = unicodedata.normalize("NFKD", text)
    plain = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(plain.lower().split())


def _date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


DateOrder = Literal["dd/mm", "mm/dd"]


def _numeric(text: str) -> tuple[int, int, int] | None:
    """``(first, second, year)`` of a ``nn/nn/aaaa`` date (also ``-`` or ``.``)."""
    match = _NUMERIC.match(_fold(text))
    return (int(match[1]), int(match[3]), int(match[4])) if match else None


def _order_shown(text: str | None) -> DateOrder | None:
    """The order a numeric date proves by itself (one part > 12), else ``None``."""
    parts = _numeric(text) if text else None
    if parts is None:
        return None
    first, second, year = parts
    if first > 12 and _date(year, second, first):
        return "dd/mm"
    if second > 12 and _date(year, first, second):
        return "mm/dd"
    return None


def infer_date_order(texts: Iterable[str | None]) -> DateOrder | None:
    """The order every unambiguous numeric date agrees on; ``None`` if none or mixed."""
    shown: set[DateOrder] = {
        order for order in map(_order_shown, texts) if order is not None
    }
    return shown.pop() if len(shown) == 1 else None


def is_ambiguous(text: str | None) -> bool:
    """A numeric date whose day and month could swap (``03/04/2026``)."""
    parts = _numeric(text) if text else None
    return (
        parts is not None and parts[0] <= 12 and parts[1] <= 12 and parts[0] != parts[1]
    )


def parse_due(text: str | None, order: DateOrder | None = None) -> date | None:
    """The due date when it can be read without guessing, else ``None``.

    ``order`` is the order the owner's own sheet shows (``infer_date_order``);
    without it a swappable date stays unread and month-first is not read.
    """
    if text is None:
        return None
    key = _fold(text)
    if match := _ISO.match(key):
        year, month, day = (int(part) for part in match.groups())
        return _date(year, month, day)
    if (parts := _numeric(key)) is not None:
        first, second, year = parts
        if order == "mm/dd":
            first, second = second, first  # read as day, month
        elif order is None and (second > 12 or (first <= 12 and first != second)):
            return None  # month/day order or a swappable date: por confirmar
        if second > 12:
            return None
        return _date(year, second, first)
    if match := _DAY_FIRST.match(key):
        month = _MONTHS.get(match[2])
        return _date(int(match[3]), month, int(match[1])) if month else None
    if match := _MONTH_FIRST.match(key):
        month = _MONTHS.get(match[1])
        return _date(int(match[3]), month, int(match[2])) if month else None
    return None


def is_finished(status: str | None) -> bool:
    """True only for the closed "finished" vocabulary of the design."""
    return status is not None and _fold(status).strip(" .;:,!") in FINISHED


class ReviewedItem(BaseModel):
    """One commitment as the owner wrote it, plus the date ESCALA could read."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    focus_area: str | None
    text: str
    kpi: str | None
    due: str | None
    due_date: date | None
    status: str | None


class RocksPrep(BaseModel):
    """The quarter's Rocks, reviewed apart from the monthly commitments (S82.7).

    Missing KPI or date is only reported when the Rocks table has that column;
    a finished Rock is left alone (moving Rocks to Done is not suggested).
    """

    quarter: str | None = None
    reviewed: int = 0
    overdue: list[ReviewedItem] = Field(default_factory=list[ReviewedItem])
    missing_kpi: list[ReviewedItem] = Field(default_factory=list[ReviewedItem])
    missing_due: list[ReviewedItem] = Field(default_factory=list[ReviewedItem])
    unclear_due: list[ReviewedItem] = Field(default_factory=list[ReviewedItem])

    @property
    def has_findings(self) -> bool:
        return any([self.overdue, self.missing_kpi, self.missing_due, self.unclear_due])


class MeetingPrep(BaseModel):
    """Suggestions for the group meeting; nothing here was moved or written."""

    today: date
    reviewed: int = 0
    overdue: list[ReviewedItem] = Field(default_factory=list[ReviewedItem])
    finished: list[ReviewedItem] = Field(default_factory=list[ReviewedItem])
    already_in_done: list[ReviewedItem] = Field(default_factory=list[ReviewedItem])
    missing_kpi: list[ReviewedItem] = Field(default_factory=list[ReviewedItem])
    missing_due: list[ReviewedItem] = Field(default_factory=list[ReviewedItem])
    unclear_due: list[ReviewedItem] = Field(default_factory=list[ReviewedItem])
    # S82.7: the order the tab's own unambiguous dates agree on, and the
    # swappable dates that were read with it.
    date_order: DateOrder | None = None
    ordered_dates: list[str] = Field(default_factory=list)
    rocks: RocksPrep = Field(default_factory=RocksPrep)

    @property
    def has_findings(self) -> bool:
        return self.has_commitment_findings or self.rocks.has_findings

    @property
    def has_commitment_findings(self) -> bool:
        return any(
            [
                self.overdue,
                self.finished,
                self.already_in_done,
                self.missing_kpi,
                self.missing_due,
                self.unclear_due,
            ]
        )


def _same_text(text: str) -> str:
    return _fold(text).strip(" .;:,")


def _reviewed(item: TrackerItem, text: str, order: DateOrder | None) -> ReviewedItem:
    return ReviewedItem(
        focus_area=item.focus_area,
        text=text,
        kpi=item.kpi,
        due=item.due,
        due_date=parse_due(item.due, order),
        status=item.status,
    )


def sheet_date_order(sheet: TrackerSheet) -> DateOrder | None:
    """The date order of the confirmed tab: commitments, Rocks and Done."""
    items = [*sheet.commitments, *sheet.rocks, *sheet.done]
    return infer_date_order(item.due for item in items)


def _review_rocks(
    sheet: TrackerSheet,
    today: date,
    order: DateOrder | None,
    fields: list[Column] | None,
) -> RocksPrep:
    columns = fields or []
    rocks = RocksPrep(quarter=sheet.rocks_quarter)
    for item in sheet.rocks:
        if item.text is None:
            continue
        row = _reviewed(item, item.text, order)
        rocks.reviewed += 1
        if is_finished(item.status):
            continue
        if row.kpi is None and "kpi" in columns:
            rocks.missing_kpi.append(row)
        if row.due is None:
            if "due" in columns:
                rocks.missing_due.append(row)
        elif row.due_date is None:
            rocks.unclear_due.append(row)
        elif row.due_date < today:
            rocks.overdue.append(row)
    return rocks


def _resolved(items: list[TrackerItem], order: DateOrder | None) -> list[str]:
    if order is None:
        return []
    return [i.due for i in items if i.text and i.due and is_ambiguous(i.due)]


def review_before_meeting(
    sheet: TrackerSheet, today: date, rock_fields: list[Column] | None = None
) -> MeetingPrep:
    """Overdue, finished (to move to Done) and incomplete commitments and Rocks.

    Only rows with written text are reviewed; Done is left alone. Rocks are
    reviewed apart (``prep.rocks``); ``rock_fields`` are the columns of the
    Rocks table, so a Rock is only asked for a KPI or date its table has room
    for. A date that cannot be read is "por confirmar", never overdue.
    """
    in_done = {_same_text(item.text) for item in sheet.done if item.text}
    order = sheet_date_order(sheet)
    prep = MeetingPrep(
        today=today,
        date_order=order,
        ordered_dates=_resolved([*sheet.commitments, *sheet.rocks], order),
        rocks=_review_rocks(sheet, today, order, rock_fields),
    )
    for item in sheet.commitments:
        if item.text is None:
            continue  # a template row with only the area filled in
        row = _reviewed(item, item.text, order)
        prep.reviewed += 1
        if is_finished(item.status):
            done_already = _same_text(row.text) in in_done
            (prep.already_in_done if done_already else prep.finished).append(row)
            continue
        if row.kpi is None:
            prep.missing_kpi.append(row)
        if row.due is None:
            prep.missing_due.append(row)
        elif row.due_date is None:
            prep.unclear_due.append(row)
        elif row.due_date < today:
            prep.overdue.append(row)
    return prep


DONE_FIELDS: list[Column] = ["focus", "text"]


def _value(item: ReviewedItem, field: Column) -> str | None:
    values: dict[Column, str | None] = {
        "focus": item.focus_area,
        "text": item.text,
        "kpi": item.kpi,
        "due": item.due,
        "status": item.status,
    }
    return values.get(field)


def to_done_block(items: list[ReviewedItem], fields: list[Column] | None) -> str:
    """Tab-separated rows in the Done table's column order, ready to paste."""
    order = fields or DONE_FIELDS
    return "\n".join(
        "\t".join(paste_cell(_value(item, field)) for field in order) for item in items
    )
