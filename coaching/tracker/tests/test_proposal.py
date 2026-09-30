"""Proposed commitment rows from the quarter's priorities (S82.4).

ESCALA only proposes: rows reuse the area labels the sheet already uses, skip
what is already written, and never overwrite a different Critical Number.
All fixtures are synthetic.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from coaching.tracker.models import TrackerItem, TrackerSheet
from coaching.tracker.proposal import (
    ProposedRow,
    QuarterlyPlanInput,
    check_quarter,
    month_name,
    propose_rocks,
    propose_rows,
    quarter_key,
    render_table,
    to_paste_block,
)


def _plan(**extra: object) -> QuarterlyPlanInput:
    data: dict[str, object] = {
        "quarter": "Q4-2026",
        "critical_number": "10 clientes nuevos",
        "priorities": [
            {
                "priority": "Cobrar cartera vencida",
                "owner": "Ana",
                "kpi": "90%",
                "decision": "cash",
            },
            {
                "priority": "Definir cliente ideal",
                "kpi": "1 documento",
                "decision": "strategy",
                "due": "15/10/2026",
            },
            {"priority": "Contratar vendedor", "kpi": "1 contratado"},
        ],
    }
    data.update(extra)
    return QuarterlyPlanInput.model_validate(data)


def test_plan_reads_the_opsp_quarterly_plan_section() -> None:
    state: dict[str, object] = {
        "purpose": "otra sección",
        "quarterly_plan": {
            "quarter": "Q4",
            "critical_number": "10",
            "priorities": [
                {"priority": "A", "owner": "Ana", "kpi": "1", "status": "en curso"},
                "B como texto",
                {"priority": "  "},
            ],
            "theme": {"name": "Cash is King"},
        },
    }

    plan = QuarterlyPlanInput.from_opsp_state(state)

    assert plan is not None
    assert [p.priority for p in plan.priorities] == ["A", "B como texto"]
    assert plan.priorities[0].owner == "Ana"


def test_plan_accepts_deadline_and_spanish_area_names() -> None:
    plan = QuarterlyPlanInput.model_validate(
        {"priorities": [{"priority": "A", "deadline": "31/12", "decision": "Personas"}]}
    )

    assert plan.priorities[0].due == "31/12"
    assert plan.priorities[0].decision == "people"


def test_missing_quarterly_plan_is_none() -> None:
    assert QuarterlyPlanInput.from_opsp_state({}) is None
    assert QuarterlyPlanInput.from_opsp_state({"quarterly_plan": {}}) is None


def test_rows_map_priorities_with_default_area_labels_and_month_end() -> None:
    proposal = propose_rows(TrackerSheet(), _plan(), "2026-10")

    assert proposal.rows == [
        ProposedRow(
            focus_area="Cash",
            priority="Cobrar cartera vencida",
            kpi="90%",
            due="2026-10-31",
        ),
        ProposedRow(
            focus_area="Strategy",
            priority="Definir cliente ideal",
            kpi="1 documento",
            due="15/10/2026",
        ),
        ProposedRow(
            focus_area=None,
            priority="Contratar vendedor",
            kpi="1 contratado",
            due="2026-10-31",
        ),
    ]
    assert proposal.month_name == "octubre"
    assert proposal.missing_area == ["Contratar vendedor"]


def test_rows_reuse_the_area_labels_the_sheet_already_uses() -> None:
    sheet = TrackerSheet(
        rocks=[TrackerItem(focus_area="Flujo de efectivo", decision="cash")],
        commitments=[
            TrackerItem(focus_area="Estrategia", decision="strategy", text="Otra cosa")
        ],
    )

    proposal = propose_rows(sheet, _plan(), "2026-10")

    assert [row.focus_area for row in proposal.rows][:2] == [
        "Flujo de efectivo",
        "Estrategia",
    ]


def test_rows_already_written_are_skipped_after_normalizing() -> None:
    sheet = TrackerSheet(
        commitments=[TrackerItem(text="  cobrar CARTERA vencida. ")],
        done=[TrackerItem(text="Definir cliente IDEAL")],
    )

    proposal = propose_rows(sheet, _plan(), "2026-11")

    assert [row.priority for row in proposal.rows] == ["Contratar vendedor"]
    assert proposal.skipped == ["Cobrar cartera vencida", "Definir cliente ideal"]
    assert proposal.rows[0].due == "2026-11-30"


@pytest.mark.parametrize(
    ("sheet_value", "status"),
    [
        (None, "add"),
        ("10 Clientes nuevos", "same"),
        ("5 mdp de ventas", "different"),
    ],
)
def test_critical_number_is_proposed_kept_or_questioned(
    sheet_value: str | None, status: str
) -> None:
    proposal = propose_rows(
        TrackerSheet(critical_number=sheet_value), _plan(), "2026-10"
    )

    assert proposal.critical_number == status
    assert proposal.plan_critical_number == "10 clientes nuevos"
    assert proposal.sheet_critical_number == sheet_value


def test_plan_without_critical_number_leaves_the_sheet_alone() -> None:
    proposal = propose_rows(
        TrackerSheet(critical_number="5 mdp"), _plan(critical_number=None), "2026-10"
    )

    assert proposal.critical_number == "not_in_plan"


def test_bad_month_is_rejected() -> None:
    with pytest.raises(ValueError):
        propose_rows(TrackerSheet(), _plan(), "octubre")


def test_month_name_is_spanish() -> None:
    assert month_name("2026-01") == "enero"
    assert month_name("2026-12") == "diciembre"


def test_paste_block_follows_the_sheet_column_order() -> None:
    rows = [
        ProposedRow(focus_area="Cash", priority="Cobrar", kpi=None, due="2026-10-31")
    ]

    block = to_paste_block(rows, ["focus", "note", "text", "due", "kpi"])

    assert block == "Cash\t\tCobrar\t2026-10-31\t"


def test_paste_block_cells_never_break_the_grid_or_become_formulas() -> None:
    rows = [
        ProposedRow(
            focus_area="Cash",
            priority="Cobrar\tcartera\nvencida",
            kpi="=SUM(A1)",
            due="2026-10-31",
        ),
        ProposedRow(focus_area=None, priority="Vender", kpi="3", due="2026-10-31"),
    ]

    block = to_paste_block(rows)

    assert block.splitlines() == [
        "Cash\tCobrar cartera vencida\tSUM(A1)\t2026-10-31",
        "\tVender\t3\t2026-10-31",
    ]


def test_readable_table_uses_the_sheet_headers() -> None:
    rows = [
        ProposedRow(
            focus_area="Cash", priority="Cobrar | todo", kpi="90%", due="2026-10-31"
        )
    ]

    table = render_table(rows, ["Action Area", "Priorities", "KPIs", "Due Dates"])

    assert table.splitlines() == [
        "| Action Area | Priorities | KPIs | Due Dates |",
        "|---|---|---|---|",
        "| Cash | Cobrar \\| todo | 90% | 2026-10-31 |",
    ]


def test_unknown_plan_fields_are_ignored_but_priority_is_required() -> None:
    with pytest.raises(ValidationError):
        QuarterlyPlanInput.model_validate({"priorities": [{"kpi": "1"}]})


# --- S82.7: Rocks rows for the quarter the sheet declares -----------------------


@pytest.mark.parametrize(
    ("text", "key"),
    [
        ("Q4-2026", "Q4-2026"),
        ("q4 2026", "Q4-2026"),
        ("Q4", "Q4"),
        ("2026-Q1", "Q1-2026"),
        ("T3 2026", "Q3-2026"),
        (" Q2/2027 ", "Q2-2027"),
        ("Q5", None),
        ("Cuarto trimestre", None),
        ("", None),
        (None, None),
    ],
)
def test_quarter_key_reads_only_clear_quarter_labels(
    text: str | None, key: str | None
) -> None:
    assert quarter_key(text) == key


@pytest.mark.parametrize(
    ("sheet_quarter", "plan_quarter", "answered", "status", "quarter"),
    [
        ("Q4-2026", "Q4-2026", None, "ok", "Q4-2026"),
        ("Q4-2026", "Q4", None, "ok", "Q4-2026"),
        ("Q4", "Q4-2026", None, "ok", "Q4"),
        ("Q4-2026", None, None, "ok", "Q4-2026"),
        ("Q4-2026", "Cuarto", None, "ok", "Q4-2026"),  # unreadable plan: no check
        ("Q4-2025", "Q4-2026", None, "mismatch", "Q4-2025"),
        ("Q3", "Q4-2026", None, "mismatch", "Q3"),
        (None, "Q4-2026", None, "ask", None),
        ("este trimestre", "Q4-2026", None, "ask", None),
        (None, "Q4-2026", "Q4-2026", "ok", "Q4-2026"),
        (None, None, "no sé", "ask", None),
        ("Q4-2026", "Q4-2026", "Q1-2027", "ok", "Q4-2026"),  # the sheet rules
    ],
)
def test_rocks_quarter_comes_from_the_sheet_or_is_asked(
    sheet_quarter: str | None,
    plan_quarter: str | None,
    answered: str | None,
    status: str,
    quarter: str | None,
) -> None:
    check = check_quarter(
        TrackerSheet(rocks_quarter=sheet_quarter),
        _plan(quarter=plan_quarter),
        answered,
    )

    assert check.status == status
    assert check.quarter == quarter
    assert check.sheet_quarter == sheet_quarter
    assert check.plan_quarter == plan_quarter


def test_rocks_rows_skip_existing_rocks_and_done_and_keep_areas() -> None:
    sheet = TrackerSheet(
        rocks_quarter="Q4-2026",
        rocks=[
            TrackerItem(
                focus_area="Flujo", decision="cash", text="Cobrar CARTERA vencida."
            )
        ],
        done=[TrackerItem(text="definir cliente ideal")],
        commitments=[TrackerItem(text="Contratar vendedor")],  # not a Rock yet
    )

    proposal = propose_rocks(sheet, _plan(), "Q4-2026")

    assert proposal.quarter == "Q4-2026"
    assert proposal.skipped == ["Cobrar cartera vencida", "Definir cliente ideal"]
    assert proposal.rows == [
        ProposedRow(
            focus_area=None, priority="Contratar vendedor", kpi="1 contratado", due=None
        )
    ]
    assert proposal.missing_area == ["Contratar vendedor"]


def test_rocks_rows_reuse_sheet_areas_and_never_invent_a_date() -> None:
    sheet = TrackerSheet(
        rocks_quarter="Q4-2026",
        rocks=[TrackerItem(focus_area="Flujo de efectivo", decision="cash", text="X")],
    )

    rows = propose_rocks(sheet, _plan(), "Q4-2026").rows

    assert [(r.focus_area, r.due) for r in rows] == [
        ("Flujo de efectivo", None),
        ("Strategy", "15/10/2026"),
        (None, None),
    ]


def test_rocks_paste_block_only_fills_the_columns_the_rocks_table_has() -> None:
    rows = propose_rocks(TrackerSheet(), _plan(), "Q4").rows

    assert to_paste_block(rows, ["focus", "text"]).splitlines() == [
        "Cash\tCobrar cartera vencida",
        "Strategy\tDefinir cliente ideal",
        "\tContratar vendedor",
    ]
    assert to_paste_block(rows[1:2], ["focus", "text", "kpi", "due"]) == (
        "Strategy\tDefinir cliente ideal\t1 documento\t15/10/2026"
    )


def test_readable_table_follows_the_given_fields() -> None:
    rows = propose_rocks(TrackerSheet(), _plan(), "Q4").rows[:1]

    table = render_table(
        rows, ["Focus Area", "Goals/Rock for this quarter"], ["focus", "text"]
    )

    assert table.splitlines() == [
        "| Focus Area | Goals/Rock for this quarter |",
        "|---|---|",
        "| Cash | Cobrar cartera vencida |",
    ]
