# pyright: strict
"""Before the group meeting (S82.5): suggestions only, nothing is moved.

Dates are read conservatively (design U4): ISO, ``dd/mm/aaaa`` and written
month names in Spanish or English. There is no ``mm/dd`` branch: when day and
month could swap, or the text is anything else, the date stays "por
confirmar". Finished is a closed vocabulary; everything else is unfinished.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date

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


def parse_due(text: str | None) -> date | None:
    """The due date when it can be read without guessing, else ``None``."""
    if text is None:
        return None
    key = _fold(text)
    if match := _ISO.match(key):
        year, month, day = (int(part) for part in match.groups())
        return _date(year, month, day)
    if match := _NUMERIC.match(key):
        day, month, year = int(match[1]), int(match[3]), int(match[4])
        if month > 12 or (day <= 12 and day != month):
            return None  # month/day order or a swappable date: por confirmar
        return _date(year, month, day)
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

    @property
    def has_findings(self) -> bool:
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


def _reviewed(item: TrackerItem, text: str) -> ReviewedItem:
    return ReviewedItem(
        focus_area=item.focus_area,
        text=text,
        kpi=item.kpi,
        due=item.due,
        due_date=parse_due(item.due),
        status=item.status,
    )


def review_before_meeting(sheet: TrackerSheet, today: date) -> MeetingPrep:
    """Overdue, finished (to move to Done) and incomplete monthly commitments.

    Only rows with a written commitment are reviewed; Rocks and Done are left
    alone. A date that cannot be read is "por confirmar", never overdue.
    """
    in_done = {_same_text(item.text) for item in sheet.done if item.text}
    prep = MeetingPrep(today=today)
    for item in sheet.commitments:
        if item.text is None:
            continue  # a template row with only the area filled in
        row = _reviewed(item, item.text)
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
