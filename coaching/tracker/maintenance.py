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
FINISHED = frozenset({"done", "hecho", "terminado", "completado", "✅", "100%"})


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
