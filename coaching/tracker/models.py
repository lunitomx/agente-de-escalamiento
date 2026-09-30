"""Typed view of one participant sheet of the accountability tracker."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Decision = Literal["people", "strategy", "execution", "cash"]


class TrackerItem(BaseModel):
    """One commitment, rock or done row, kept as the participant wrote it."""

    focus_area: str | None = None
    decision: Decision | None = None
    text: str | None = None
    kpi: str | None = None
    due: str | None = None
    status: str | None = None
    notes: list[str] = Field(default_factory=list)


class TrackerSheet(BaseModel):
    """A participant sheet: identity, critical number and the three tables."""

    participant: str | None = None
    business: str | None = None
    critical_number: str | None = None
    commitments: list[TrackerItem] = Field(default_factory=list)
    rocks_quarter: str | None = None
    rocks: list[TrackerItem] = Field(default_factory=list)
    done: list[TrackerItem] = Field(default_factory=list)
    unparsed_blocks: list[str] = Field(default_factory=list)
