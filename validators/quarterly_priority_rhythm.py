"""Fail-closed draft validation for a quarterly priority and meeting rhythm.

This module represents an internal planning proposal only.  It does not write
company state, schedule meetings, create calendar events, or enable an
automation.  A caller must obtain explicit acceptance outside this boundary
before any proposal can become an operational commitment.
"""

from __future__ import annotations

from datetime import date, timedelta
import math
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _id(value: str, label: str) -> str:
    if _ID.fullmatch(value) is None:
        raise ValueError(f"unsafe {label}")
    return value


def _text(value: str, label: str) -> str:
    if (
        not value.strip()
        or value != value.strip()
        or len(value) > 160
        or len(value.split()) > 24
        or "\n" in value
        or ";" in value
        or "•" in value
        or "://" in value
        or "/" in value
        or "\\" in value
    ):
        raise ValueError(f"unsafe {label}")
    return value


class ConfirmedDiagnosis(_StrictModel):
    """A diagnosis may be proposed, but it must never be silently treated as fact."""

    status: Literal["confirmed", "proposed"]
    primary_constraint: str
    confirmation_receipt: str | None = None

    @field_validator("primary_constraint")
    @classmethod
    def validate_constraint(cls, value: str) -> str:
        return _text(value, "primary constraint")

    @field_validator("confirmation_receipt")
    @classmethod
    def validate_receipt(cls, value: str | None) -> str | None:
        return None if value is None else _id(value, "diagnosis receipt")

    @model_validator(mode="after")
    def require_receipt_only_for_confirmed_diagnosis(self) -> "ConfirmedDiagnosis":
        if self.status == "confirmed" and self.confirmation_receipt is None:
            raise ValueError("confirmed diagnosis requires a confirmation receipt")
        if self.status == "proposed" and self.confirmation_receipt is not None:
            raise ValueError("proposed diagnosis must not carry a confirmation receipt")
        return self


class CriticalNumber(_StrictModel):
    name: str
    unit: str
    baseline: float
    owner_id: str

    @field_validator("name", "unit")
    @classmethod
    def validate_metric_text(cls, value: str) -> str:
        return _text(value, "critical number")

    @field_validator("owner_id")
    @classmethod
    def validate_owner(cls, value: str) -> str:
        return _id(value, "critical number owner")

    @field_validator("baseline")
    @classmethod
    def validate_finite_baseline(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("critical number baseline must be finite")
        return value


class WhoWhatWhen(_StrictModel):
    owner_id: str
    action: str
    due_on: date

    @field_validator("owner_id")
    @classmethod
    def validate_owner(cls, value: str) -> str:
        return _id(value, "commitment owner")

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        return _text(value, "commitment action")


class MeetingCadence(_StrictModel):
    cadence: Literal["daily", "weekly", "monthly", "quarterly"]
    purpose: str
    owner_id: str
    status: Literal["proposed"]
    accepted: Literal[False]

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, value: str) -> str:
        return _text(value, "meeting purpose")

    @field_validator("owner_id")
    @classmethod
    def validate_owner(cls, value: str) -> str:
        return _id(value, "meeting owner")


class AutomationProposal(_StrictModel):
    """A suggestion only; E52 has not supplied a trusted acceptance authority."""

    id: str
    purpose: str
    status: Literal["proposed"]
    accepted: Literal[False] = False
    acceptance_receipt: Literal[None] = None

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _id(value, "automation proposal ID")

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, value: str) -> str:
        return _text(value, "automation proposal purpose")


class QuarterlyPriorityRhythmPlan(_StrictModel):
    """A complete, proposed 90-day plan; it is intentionally non-executing."""

    status: Literal["proposed"]
    diagnosis: ConfirmedDiagnosis
    priority: str
    priority_candidates: list[str] = Field(min_length=1, max_length=16)
    priority_justification: str | None = None
    window_start: date
    window_end: date
    critical_number: CriticalNumber
    commitments: list[WhoWhatWhen] = Field(min_length=1, max_length=16)
    meeting_cadences: list[MeetingCadence] = Field(min_length=4, max_length=4)
    automation_proposals: list[AutomationProposal] = Field(
        default_factory=list, max_length=16
    )
    requires_explicit_acceptance: Literal[True]

    @field_validator("priority", "priority_justification")
    @classmethod
    def validate_priority_text(cls, value: str | None) -> str | None:
        return None if value is None else _text(value, "priority")

    @field_validator("priority_candidates")
    @classmethod
    def validate_priority_candidates(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate priority candidate")
        return [_text(value, "priority candidate") for value in values]

    @model_validator(mode="after")
    def validate_complete_single_priority_draft(self) -> "QuarterlyPriorityRhythmPlan":
        owners = [item.owner_id for item in self.commitments]
        if len(
            {(item.owner_id, item.action, item.due_on) for item in self.commitments}
        ) != len(self.commitments):
            raise ValueError("duplicate Who What When commitment")
        cadences = {item.cadence for item in self.meeting_cadences}
        if cadences != {"daily", "weekly", "monthly", "quarterly"}:
            raise ValueError(
                "plan requires daily weekly monthly and quarterly proposals"
            )
        if len(cadences) != len(self.meeting_cadences):
            raise ValueError("duplicate meeting cadence")
        if self.diagnosis.status == "proposed" and self.priority_justification is None:
            raise ValueError("proposed diagnosis requires priority justification")
        if self.priority not in self.priority_candidates:
            raise ValueError("selected priority must be among priority candidates")
        if len(self.priority_candidates) > 1 and self.priority_justification is None:
            raise ValueError(
                "multiple priority candidates require explicit justification"
            )
        if self.window_end != self.window_start + timedelta(days=90):
            raise ValueError("window end must equal start plus 90 days")
        if any(
            item.due_on < self.window_start or item.due_on > self.window_end
            for item in self.commitments
        ):
            raise ValueError("every commitment due date must be within plan window")
        if self.critical_number.owner_id not in set(owners):
            raise ValueError(
                "critical number owner requires a Who What When commitment"
            )
        automation_ids = [item.id for item in self.automation_proposals]
        if len(automation_ids) != len(set(automation_ids)):
            raise ValueError("duplicate automation proposal")
        return self


def validate_quarterly_priority_rhythm_plan(
    payload: object,
) -> QuarterlyPriorityRhythmPlan:
    """Parse a complete proposal without scheduling or persisting anything."""
    return QuarterlyPriorityRhythmPlan.model_validate(payload)
