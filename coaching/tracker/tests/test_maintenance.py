"""Pre-meeting maintenance (S82.5): overdue, finished, missing; suggestions only."""

from __future__ import annotations

from datetime import date

import pytest

from coaching.tracker.maintenance import (
    infer_date_order,
    is_finished,
    parse_due,
    review_before_meeting,
    to_done_block,
)
from coaching.tracker.models import TrackerItem, TrackerSheet


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
    "status",
    [
        "Done",
        "hecho",
        "Hecha",
        "Terminado",
        "terminada",
        "COMPLETADO",
        "completada",
        "✅",
        "100%",
        " done. ",
    ],
)
def test_closed_vocabulary_counts_as_finished(status: str) -> None:
    assert is_finished(status)


@pytest.mark.parametrize(
    "status", [None, "", "En proceso", "90%", "casi hecho", "movida", "pendiente"]
)
def test_anything_else_is_not_finished(status: str | None) -> None:
    assert not is_finished(status)


# --- review_before_meeting ------------------------------------------------------

TODAY = date(2026, 11, 2)


def _item(
    text: str | None,
    *,
    kpi: str | None = "1",
    due: str | None = "30/11/2026",
    status: str | None = None,
    focus: str | None = "Cash",
) -> TrackerItem:
    return TrackerItem(focus_area=focus, text=text, kpi=kpi, due=due, status=status)


def _texts(items: list[object]) -> list[str]:
    return [getattr(item, "text") for item in items]


def test_overdue_is_past_due_and_not_finished() -> None:
    sheet = TrackerSheet(
        commitments=[
            _item("Cobrar cartera", due="30/10/2026"),
            _item("Cerrar mes", due="2026-11-01", status="En proceso"),
            _item("Pagar nómina", due="30/10/2026", status="Hecho"),
            _item("Lanzar curso", due="2026-11-02"),  # due today is not overdue
            _item("Abrir tienda", due="30/11/2026"),
        ]
    )

    prep = review_before_meeting(sheet, TODAY)

    assert _texts(list(prep.overdue)) == ["Cobrar cartera", "Cerrar mes"]
    assert prep.overdue[0].due_date == date(2026, 10, 30)
    assert prep.overdue[0].due == "30/10/2026"  # kept as the owner wrote it


def test_finished_commitments_are_suggested_for_done() -> None:
    sheet = TrackerSheet(
        commitments=[
            _item("Pagar nómina", status="✅", kpi=None, due=None),
            _item("Contratar gerente", status="Terminado"),
            _item("Cobrar cartera", status="90%"),
        ]
    )

    prep = review_before_meeting(sheet, TODAY)

    assert _texts(list(prep.finished)) == ["Pagar nómina", "Contratar gerente"]
    # a finished row is not asked for its missing KPI or date
    assert prep.missing_kpi == [] and prep.missing_due == []


def test_finished_rows_already_in_done_are_not_repeated() -> None:
    sheet = TrackerSheet(
        commitments=[_item("Contratar gerente", status="done")],
        done=[_item("contratar  GERENTE.")],
    )

    prep = review_before_meeting(sheet, TODAY)

    assert prep.finished == []
    assert _texts(list(prep.already_in_done)) == ["Contratar gerente"]


def test_missing_kpi_missing_due_and_unclear_due() -> None:
    sheet = TrackerSheet(
        commitments=[
            _item("Sin KPI", kpi=None, due="2026-11-30"),
            _item("Sin fecha", due=None),
            _item("Fecha rara", due="fin de mes"),
            _item("Fecha ambigua", due="03/04/2026"),
        ]
    )

    prep = review_before_meeting(sheet, TODAY)

    assert _texts(list(prep.missing_kpi)) == ["Sin KPI"]
    assert _texts(list(prep.missing_due)) == ["Sin fecha"]
    assert _texts(list(prep.unclear_due)) == ["Fecha rara", "Fecha ambigua"]
    assert prep.overdue == []  # an unread date is never counted as overdue


def test_rows_without_text_and_the_done_table_are_not_reviewed() -> None:
    sheet = TrackerSheet(
        commitments=[_item(None, kpi=None, due=None)],  # template row: area only
        rocks=[_item(None, kpi=None, due=None)],
        done=[_item("Hecho antes", due="01/01/2026")],
    )

    prep = review_before_meeting(sheet, TODAY)

    assert not prep.has_findings
    assert prep.reviewed == 0
    assert prep.rocks.reviewed == 0


def test_rocks_are_reviewed_apart_from_commitments() -> None:
    sheet = TrackerSheet(
        commitments=[_item("Cobrar cartera", due="30/10/2026")],
        rocks_quarter="Q4-2026",
        rocks=[
            _item("Rock vencido", due="15/10/2026", status="Vamos en 40%"),
            _item("Rock terminado", due="15/10/2026", status="Terminado"),
            _item("Rock a tiempo", due="2026-12-31"),
            _item("Rock fecha rara", due="fin de año"),
        ],
    )

    prep = review_before_meeting(sheet, TODAY)

    assert _texts(list(prep.overdue)) == ["Cobrar cartera"]
    assert prep.rocks.quarter == "Q4-2026"
    assert prep.rocks.reviewed == 4
    assert _texts(list(prep.rocks.overdue)) == ["Rock vencido"]
    assert _texts(list(prep.rocks.unclear_due)) == ["Rock fecha rara"]
    assert prep.rocks.has_findings and prep.has_findings
    # a finished Rock is left alone: moving Rocks to Done is not suggested
    assert prep.finished == []


def test_rocks_missing_kpi_or_date_only_when_their_table_has_the_column() -> None:
    sheet = TrackerSheet(
        rocks=[_item("Sin KPI", kpi=None), _item("Sin fecha", due=None)],
    )

    template = review_before_meeting(sheet, TODAY, rock_fields=["focus", "text"])
    full = review_before_meeting(
        sheet, TODAY, rock_fields=["focus", "text", "kpi", "due"]
    )

    assert not template.rocks.has_findings  # the template has no KPI/date column
    assert _texts(list(full.rocks.missing_kpi)) == ["Sin KPI"]
    assert _texts(list(full.rocks.missing_due)) == ["Sin fecha"]
    assert not full.has_commitment_findings


def test_rock_dates_follow_the_order_of_the_tab() -> None:
    sheet = TrackerSheet(
        commitments=[_item("Cobrar", due="30/12/2026")],
        rocks=[_item("Rock ambiguo", due="03/04/2026")],
    )

    prep = review_before_meeting(sheet, TODAY)

    assert _texts(list(prep.rocks.overdue)) == ["Rock ambiguo"]
    assert prep.ordered_dates == ["03/04/2026"]


def test_review_never_changes_the_sheet() -> None:
    sheet = TrackerSheet(commitments=[_item("Pagar", status="done", due="1/1/2026")])
    before = sheet.model_dump()

    review_before_meeting(sheet, TODAY)

    assert sheet.model_dump() == before


def test_done_block_follows_the_done_columns() -> None:
    sheet = TrackerSheet(
        commitments=[
            _item("Pagar =nómina", status="done", focus="Efectivo"),
            _item("Contratar\tgerente", status="hecho", focus=None),
        ]
    )
    finished = review_before_meeting(sheet, TODAY).finished

    assert to_done_block(finished, ["focus", "text"]).splitlines() == [
        "Efectivo\tPagar =nómina",
        "\tContratar gerente",
    ]
    assert to_done_block(finished, None).splitlines()[0] == "Efectivo\tPagar =nómina"
    assert to_done_block([], None) == ""


def test_done_block_never_starts_a_cell_with_a_formula() -> None:
    sheet = TrackerSheet(commitments=[_item("=SUM(A1)", status="done")])

    block = to_done_block(review_before_meeting(sheet, TODAY).finished, None)

    assert block == "Cash\tSUM(A1)"


# --- S82.7: ambiguous dates follow the order the owner's own sheet shows --------


@pytest.mark.parametrize(
    ("texts", "expected"),
    [
        (["30/11/2026", "15/10/2026", "03/04/2026", "2026-10-01"], "dd/mm"),
        (["11/30/2026", "10-15-2026", "03/04/2026"], "mm/dd"),
        (["30/11/2026", "11/30/2026"], None),  # conflict
        (["03/04/2026", "05/05/2026", "2026-10-01", "fin de mes", None], None),
        ([], None),
        (["31/02/2026"], None),  # not a real date: no evidence
        (["30/11/26"], None),  # two-digit year: no evidence
    ],
)
def test_infer_date_order_needs_unanimous_unambiguous_dates(
    texts: list[str | None], expected: str | None
) -> None:
    assert infer_date_order(texts) == expected


def test_parse_due_reads_ambiguous_dates_in_the_given_order() -> None:
    assert parse_due("03/04/2026", "dd/mm") == date(2026, 4, 3)
    assert parse_due("03/04/2026", "mm/dd") == date(2026, 3, 4)
    assert parse_due("03/04/2026") is None


def test_parse_due_reads_month_first_only_when_the_sheet_says_so() -> None:
    assert parse_due("11/30/2025", "mm/dd") == date(2025, 11, 30)
    assert parse_due("11/30/2025", "dd/mm") is None
    assert parse_due("11/30/2025") is None
    assert parse_due("30/11/2025", "dd/mm") == date(2025, 11, 30)


def test_review_reads_ambiguous_dates_when_the_sheet_agrees() -> None:
    sheet = TrackerSheet(
        commitments=[
            _item("Cobrar", due="30/10/2026"),
            _item("Ambigua", due="03/04/2026"),
        ],
    )

    prep = review_before_meeting(sheet, TODAY)

    assert prep.date_order == "dd/mm"
    assert prep.ordered_dates == ["03/04/2026"]
    assert _texts(list(prep.overdue)) == ["Cobrar", "Ambigua"]
    assert prep.overdue[1].due_date == date(2026, 4, 3)
    assert prep.unclear_due == []


def test_review_uses_evidence_from_rocks_and_done_of_the_same_tab() -> None:
    sheet = TrackerSheet(
        commitments=[_item("Ambigua", due="12/01/2026")],
        rocks=[_item("Rock", due="12/31/2026")],
        done=[_item("Hecho", due="10/15/2026")],
    )

    prep = review_before_meeting(sheet, TODAY)

    assert prep.date_order == "mm/dd"
    assert prep.overdue == []  # December 1st, 2026 is not overdue yet
    assert prep.unclear_due == []


def test_review_keeps_ambiguous_dates_unclear_on_conflict() -> None:
    sheet = TrackerSheet(
        commitments=[
            _item("Día primero", due="30/10/2026"),
            _item("Mes primero", due="10/30/2026"),
            _item("Ambigua", due="03/04/2026"),
        ],
    )

    prep = review_before_meeting(sheet, TODAY)

    assert prep.date_order is None
    assert prep.ordered_dates == []
    assert _texts(list(prep.unclear_due)) == ["Mes primero", "Ambigua"]


def test_review_keeps_ambiguous_dates_unclear_without_evidence() -> None:
    sheet = TrackerSheet(
        commitments=[
            _item("Ambigua", due="03/04/2026"),
            _item("ISO", due="2026-10-01"),
        ],
    )

    prep = review_before_meeting(sheet, TODAY)

    assert prep.date_order is None
    assert _texts(list(prep.unclear_due)) == ["Ambigua"]
