"""Pre-meeting maintenance (S82.5): overdue, finished, missing; suggestions only."""

from __future__ import annotations

from datetime import date

import pytest

from coaching.tracker.maintenance import is_finished, parse_due


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2026-10-31", date(2026, 10, 31)),
        ("30/11/2025", date(2025, 11, 30)),
        ("30-11-2025", date(2025, 11, 30)),
        ("30.11.2025", date(2025, 11, 30)),
        ("5/5/2026", date(2026, 5, 5)),
        ("15 de noviembre de 2025", date(2025, 11, 15)),
        ("15 noviembre 2025", date(2025, 11, 15)),
        ("1 Sept 2026", date(2026, 9, 1)),
        ("November 15, 2025", date(2025, 11, 15)),
        ("15 Nov 2025", date(2025, 11, 15)),
        ("  31 de Octubre, 2026 ", date(2026, 10, 31)),
    ],
)
def test_parse_due_reads_unambiguous_dates(text: str, expected: date) -> None:
    assert parse_due(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        None,
        "",
        "03/04/2026",  # day and month could swap: never guessed
        "11/30/2025",  # month/day order is not supported
        "31/02/2026",  # not a real date
        "30/11/25",  # two-digit year
        "noviembre",  # no day, no year
        "15 de noviembre",  # no year
        "fin de mes",
        "45991",  # a spreadsheet serial number is not read
        "Q4",
    ],
)
def test_parse_due_leaves_unclear_dates_unread(text: str | None) -> None:
    assert parse_due(text) is None


@pytest.mark.parametrize(
    "status", ["Done", "hecho", "Terminado", "COMPLETADO", "✅", "100%", " done. "]
)
def test_closed_vocabulary_counts_as_finished(status: str) -> None:
    assert is_finished(status)


@pytest.mark.parametrize(
    "status", [None, "", "En proceso", "90%", "casi hecho", "movida", "pendiente"]
)
def test_anything_else_is_not_finished(status: str | None) -> None:
    assert not is_finished(status)
