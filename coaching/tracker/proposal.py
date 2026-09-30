# pyright: strict
"""Propose the month's commitment rows from the quarter's priorities (S82.4).

ESCALA only proposes. The owner reviews the rows and pastes them himself:
S82.6 found no verified way to write into the group's sheet, so there is no
write path here. Rows reuse the area labels the sheet already uses, skip
priorities already written, and a different Critical Number is pointed out,
never replaced.
"""

from __future__ import annotations

import calendar
import re
import unicodedata
from collections.abc import Mapping
from datetime import date
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from coaching.tracker.models import Decision, TrackerSheet
from coaching.tracker.parser import Column, decision_of

DEFAULT_FIELDS: list[Column] = ["focus", "text", "kpi", "due"]
DEFAULT_HEADERS = ["Focus Area", "Priorities", "KPIs", "Due Dates"]
DEFAULT_AREAS: dict[Decision, str] = {
    "cash": "Cash",
    "strategy": "Strategy",
    "execution": "Execution",
    "people": "People",
}
MONTHS = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)
_MONTH = re.compile(r"^(\d{4})-(\d{2})$")

CriticalNumberStatus = Literal["add", "same", "different", "not_in_plan"]


def _key(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return " ".join(folded.lower().split()).strip(" .;:,")


class PlannedPriority(BaseModel):
    """One quarterly priority as the OPSP saves it (plus optional area/due)."""

    model_config = ConfigDict(extra="ignore")

    priority: str
    owner: str | None = None
    kpi: str | None = None
    status: str | None = None
    decision: Decision | None = None
    due: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _aliases(cls, data: object) -> object:
        if isinstance(data, str):
            return {"priority": data}
        if isinstance(data, dict):
            raw = cast(dict[str, object], data)
            fixed = dict(raw)
            if fixed.get("due") is None and fixed.get("deadline") is not None:
                fixed["due"] = fixed["deadline"]
            area = fixed.get("decision")
            fixed["decision"] = decision_of(area) if isinstance(area, str) else None
            return fixed
        return data

    @field_validator("priority")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("priority is empty")
        return value.strip()


class QuarterlyPlanInput(BaseModel):
    """The ``quarterly_plan`` section of the OPSP state, typed."""

    model_config = ConfigDict(extra="ignore")

    quarter: str | None = None
    critical_number: str | None = None
    priorities: list[PlannedPriority] = Field(default_factory=list[PlannedPriority])

    @classmethod
    def from_opsp_state(cls, state: Mapping[str, object]) -> QuarterlyPlanInput | None:
        """Build from the OPSP state; ``None`` when there is no plan yet."""
        raw = state.get("quarterly_plan")
        if not isinstance(raw, dict) or not raw:
            return None
        section = dict(cast(dict[str, object], raw))
        items = section.get("priorities")
        kept: list[object] = []
        if isinstance(items, list):
            for item in cast(list[object], items):
                text: object = item
                if isinstance(item, dict):
                    text = cast(dict[str, object], item).get("priority")
                if isinstance(text, str) and text.strip():
                    kept.append(cast(object, item))
        section["priorities"] = kept
        critical = section.get("critical_number")
        section["critical_number"] = (
            str(critical).strip() or None if critical is not None else None
        )
        return cls.model_validate(section)


class ProposedRow(BaseModel):
    """One row for Monthly Commitments: Focus Area · Priority · KPI · Due Date."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    focus_area: str | None
    priority: str
    kpi: str | None
    due: str


class RowProposal(BaseModel):
    """What ESCALA proposes; nothing here has been written anywhere."""

    month: str
    month_name: str
    rows: list[ProposedRow] = Field(default_factory=list[ProposedRow])
    skipped: list[str] = Field(default_factory=list)
    missing_area: list[str] = Field(default_factory=list)
    critical_number: CriticalNumberStatus
    plan_critical_number: str | None = None
    sheet_critical_number: str | None = None


def _month(month: str) -> tuple[int, int]:
    match = _MONTH.match(month.strip())
    if match is None or not 1 <= int(match.group(2)) <= 12:
        raise ValueError(f"month must be YYYY-MM, got {month!r}")
    return int(match.group(1)), int(match.group(2))


def month_name(month: str) -> str:
    return MONTHS[_month(month)[1] - 1]


def _month_end(month: str) -> str:
    year, number = _month(month)
    return date(year, number, calendar.monthrange(year, number)[1]).isoformat()


def _sheet_areas(sheet: TrackerSheet) -> dict[Decision, str]:
    areas = dict(DEFAULT_AREAS)
    seen: set[Decision] = set()
    for item in [*sheet.commitments, *sheet.rocks, *sheet.done]:
        if item.decision and item.focus_area and item.decision not in seen:
            areas[item.decision] = item.focus_area
            seen.add(item.decision)
    return areas


def _critical(sheet: TrackerSheet, plan: QuarterlyPlanInput) -> CriticalNumberStatus:
    if plan.critical_number is None:
        return "not_in_plan"
    if sheet.critical_number is None or not sheet.critical_number.strip():
        return "add"
    same = _key(sheet.critical_number) == _key(plan.critical_number)
    return "same" if same else "different"


def propose_rows(
    sheet: TrackerSheet, plan: QuarterlyPlanInput, month: str
) -> RowProposal:
    """Rows for ``month`` (``YYYY-MM``) from the plan, consistent with the sheet."""
    due_default = _month_end(month)
    areas = _sheet_areas(sheet)
    written = {
        _key(item.text) for item in [*sheet.commitments, *sheet.done] if item.text
    }
    rows: list[ProposedRow] = []
    skipped: list[str] = []
    missing_area: list[str] = []
    for planned in plan.priorities:
        if _key(planned.priority) in written:
            skipped.append(planned.priority)
            continue
        area = areas[planned.decision] if planned.decision else None
        if area is None:
            missing_area.append(planned.priority)
        rows.append(
            ProposedRow(
                focus_area=area,
                priority=planned.priority,
                kpi=planned.kpi,
                due=(planned.due or "").strip() or due_default,
            )
        )
        written.add(_key(planned.priority))
    return RowProposal(
        month=month,
        month_name=month_name(month),
        rows=rows,
        skipped=skipped,
        missing_area=missing_area,
        critical_number=_critical(sheet, plan),
        plan_critical_number=plan.critical_number,
        sheet_critical_number=sheet.critical_number,
    )


def _paste_cell(value: str | None) -> str:
    """One pasted cell: no tab or line break inside, never a formula."""
    text = " ".join((value or "").split())
    return text.lstrip("=").strip()


def _value(row: ProposedRow, field: Column) -> str | None:
    if field == "focus":
        return row.focus_area
    if field == "text":
        return row.priority
    if field == "kpi":
        return row.kpi
    if field == "due":
        return row.due
    return None


def to_paste_block(rows: list[ProposedRow], fields: list[Column] | None = None) -> str:
    """Tab-separated rows in the sheet's column order, ready to paste in Sheets."""
    order = fields or DEFAULT_FIELDS
    return "\n".join(
        "\t".join(_paste_cell(_value(row, field)) for field in order) for row in rows
    )


def _table_cell(value: str | None) -> str:
    return " ".join((value or "").split()).replace("|", "\\|")


def render_table(rows: list[ProposedRow], headers: list[str] | None = None) -> str:
    """Readable table: area, priority, KPI and date, with the sheet's labels."""
    labels = headers or DEFAULT_HEADERS
    lines = [
        "| " + " | ".join(labels) + " |",
        "|" + "---|" * len(labels),
    ]
    for row in rows:
        cells = [_table_cell(_value(row, field)) for field in DEFAULT_FIELDS]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)
