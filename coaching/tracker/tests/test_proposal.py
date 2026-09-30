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
    month_name,
    propose_rows,
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
