"""Evidence-bounded quarterly review drafts for the E65 MVP.

This module evaluates only what a caller reports with supporting evidence.  It
never infers causality, writes company state, marks commitments complete, or
schedules a future review.  Those actions require later trusted adapters.
"""

from __future__ import annotations

import math
import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from validators.procedure_compiler import compile_mvp_procedures


_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_PERIOD = re.compile(r"^\d{4}-q[1-4]$")
_TEXT_MAX = 300


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _identifier(value: str, label: str) -> str:
    if _ID.fullmatch(value) is None:
        raise ValueError(f"unsafe {label}")
    return value


def _text(value: str, label: str) -> str:
    if (
        not value.strip()
        or value != value.strip()
        or len(value) > _TEXT_MAX
        or "\n" in value
        or "://" in value
        or "/" in value
        or "\\" in value
    ):
        raise ValueError(f"unsafe {label}")
    return value


def _evidence(values: list[str]) -> list[str]:
    if not values:
        raise ValueError("supporting evidence is required")
    identifiers = [_identifier(value, "evidence ID") for value in values]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate evidence ID")
    return identifiers


class Measurement(_StrictModel):
    name: str
    unit: str
    baseline: float
    current: float
    baseline_evidence_ids: list[str] = Field(min_length=1)
    current_evidence_ids: list[str] = Field(min_length=1)
    delta: float = 0
    direction: Literal["increased", "decreased", "unchanged"] = "unchanged"

    @field_validator("name", "unit")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return _text(value, "measurement text")

    @field_validator("baseline", "current")
    @classmethod
    def validate_finite_value(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("measurement value must be finite")
        return value

    @field_validator("baseline_evidence_ids", "current_evidence_ids")
    @classmethod
    def validate_evidence(cls, value: list[str]) -> list[str]:
        return _evidence(value)

    @model_validator(mode="after")
    def derive_comparison(self) -> "Measurement":
        delta = self.current - self.baseline
        direction: Literal["increased", "decreased", "unchanged"]
        if delta > 0:
            direction = "increased"
        elif delta < 0:
            direction = "decreased"
        else:
            direction = "unchanged"
        if self.delta != delta or self.direction != direction:
            return self.model_copy(update={"delta": delta, "direction": direction})
        return self


ClaimKind = Literal["fact", "hypothesis", "assumption", "commitment", "no-result-yet"]


class ReviewClaim(_StrictModel):
    kind: ClaimKind
    statement: str
    evidence_ids: list[str] = Field(min_length=1)
    causal_claim: Literal[False] = False

    @field_validator("statement")
    @classmethod
    def validate_statement(cls, value: str) -> str:
        return _text(value, "claim statement")

    @field_validator("evidence_ids")
    @classmethod
    def validate_evidence(cls, value: list[str]) -> list[str]:
        return _evidence(value)


class PlannedCommitment(_StrictModel):
    id: str
    owner_id: str
    action: str
    due_on: date

    @field_validator("id", "owner_id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _identifier(value, "commitment ID")

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        return _text(value, "commitment action")


class ReportedCommitment(_StrictModel):
    id: str
    status: Literal["reported-complete", "reported-open", "no-result-yet"]
    evidence_ids: list[str] = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _identifier(value, "commitment ID")

    @field_validator("evidence_ids")
    @classmethod
    def validate_evidence(cls, value: list[str]) -> list[str]:
        return _evidence(value)


class PlannedCadence(_StrictModel):
    cadence: Literal["daily", "weekly", "monthly", "quarterly"]
    purpose: str

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, value: str) -> str:
        return _text(value, "cadence purpose")


class ReportedCadence(_StrictModel):
    cadence: Literal["daily", "weekly", "monthly", "quarterly"]
    status: Literal["reported-held", "reported-not-held", "no-result-yet"]
    evidence_ids: list[str] = Field(min_length=1)

    @field_validator("evidence_ids")
    @classmethod
    def validate_evidence(cls, value: list[str]) -> list[str]:
        return _evidence(value)


class CommitmentComparison(_StrictModel):
    id: str
    planned_action: str
    reported_status: Literal["reported-complete", "reported-open", "no-result-yet"]
    evidence_ids: list[str]


class CadenceComparison(_StrictModel):
    cadence: Literal["daily", "weekly", "monthly", "quarterly"]
    planned_purpose: str
    reported_status: Literal["reported-held", "reported-not-held", "no-result-yet"]
    evidence_ids: list[str]


class ProposedReviewPersistence(_StrictModel):
    status: Literal["proposed"] = "proposed"
    writes_state: Literal[False] = False
    closes_commitments: Literal[False] = False
    schedules_review: Literal[False] = False


class NextReview(_StrictModel):
    status: Literal["proposed"] = "proposed"
    prompt: str = "Confirm when to hold the next quarterly review."
    scheduled_on: Literal[None] = None


class QuarterlyReviewInput(_StrictModel):
    period: str
    measurement: Measurement | None
    claims: list[ReviewClaim] = Field(min_length=1, max_length=64)
    planned_commitments: list[PlannedCommitment] | None = None
    reported_commitments: list[ReportedCommitment] | None = None
    planned_cadences: list[PlannedCadence] | None = None
    reported_cadences: list[ReportedCadence] | None = None
    proposed_learning: str
    proposed_decision: str

    @field_validator("period")
    @classmethod
    def validate_period(cls, value: str) -> str:
        if _PERIOD.fullmatch(value) is None:
            raise ValueError("unsafe period")
        return value

    @field_validator("proposed_learning", "proposed_decision")
    @classmethod
    def validate_proposal(cls, value: str) -> str:
        return _text(value, "proposed review text")

    @model_validator(mode="after")
    def require_consistent_comparison_pairs(self) -> "QuarterlyReviewInput":
        pairs = (
            (self.planned_commitments, self.reported_commitments, "commitment"),
            (self.planned_cadences, self.reported_cadences, "cadence"),
        )
        for planned, reported, name in pairs:
            if (planned is None) != (reported is None):
                raise ValueError(
                    f"both planned and reported {name} inputs are required"
                )
        if self.measurement is None and not any(
            claim.kind == "no-result-yet" for claim in self.claims
        ):
            raise ValueError(
                "missing measurement requires an explicit no-result-yet claim"
            )
        return self


class QuarterlyReview(_StrictModel):
    procedure_id: Literal["procedure.scaleup-quarterly-review"]
    period: str
    measurement: Measurement | None
    claims: list[ReviewClaim]
    www_comparison: list[CommitmentComparison] | None
    cadence_comparison: list[CadenceComparison] | None
    learning: str
    decision: str
    open_questions: list[str]
    next_review: NextReview
    persistence: ProposedReviewPersistence


def _ensure_review_contract() -> None:
    identifiers = {contract.id for contract in compile_mvp_procedures().contracts}
    if "procedure.scaleup-quarterly-review" not in identifiers:
        raise ValueError("quarterly review procedure is not in the MVP release")


def _compare_commitments(
    planned: list[PlannedCommitment] | None,
    reported: list[ReportedCommitment] | None,
) -> list[CommitmentComparison] | None:
    if planned is None or reported is None:
        return None
    planned_by_id = {item.id: item for item in planned}
    reported_by_id = {item.id: item for item in reported}
    if len(planned_by_id) != len(planned) or len(reported_by_id) != len(reported):
        raise ValueError("duplicate commitment comparison ID")
    if set(planned_by_id) != set(reported_by_id):
        raise ValueError("planned and reported commitments must match exactly")
    return [
        CommitmentComparison(
            id=item.id,
            planned_action=item.action,
            reported_status=reported_by_id[item.id].status,
            evidence_ids=reported_by_id[item.id].evidence_ids,
        )
        for item in planned
    ]


def _compare_cadences(
    planned: list[PlannedCadence] | None,
    reported: list[ReportedCadence] | None,
) -> list[CadenceComparison] | None:
    if planned is None or reported is None:
        return None
    planned_by_name = {item.cadence: item for item in planned}
    reported_by_name = {item.cadence: item for item in reported}
    if len(planned_by_name) != len(planned) or len(reported_by_name) != len(reported):
        raise ValueError("duplicate cadence comparison")
    if set(planned_by_name) != set(reported_by_name):
        raise ValueError("planned and reported cadences must match exactly")
    return [
        CadenceComparison(
            cadence=item.cadence,
            planned_purpose=item.purpose,
            reported_status=reported_by_name[item.cadence].status,
            evidence_ids=reported_by_name[item.cadence].evidence_ids,
        )
        for item in planned
    ]


def build_quarterly_review(
    payload: QuarterlyReviewInput | dict[str, object],
) -> QuarterlyReview:
    """Build a non-persistent review proposal from bounded reported inputs."""
    _ensure_review_contract()
    review_input = QuarterlyReviewInput.model_validate(payload)
    www_comparison = _compare_commitments(
        review_input.planned_commitments, review_input.reported_commitments
    )
    cadence_comparison = _compare_cadences(
        review_input.planned_cadences, review_input.reported_cadences
    )
    open_questions: list[str] = []
    if review_input.measurement is None:
        open_questions.append("measurement")
    if www_comparison is None:
        open_questions.append("who-what-when")
    if cadence_comparison is None:
        open_questions.append("cadence")
    return QuarterlyReview(
        procedure_id="procedure.scaleup-quarterly-review",
        period=review_input.period,
        measurement=review_input.measurement,
        claims=review_input.claims,
        www_comparison=www_comparison,
        cadence_comparison=cadence_comparison,
        learning=review_input.proposed_learning,
        decision=review_input.proposed_decision,
        open_questions=open_questions,
        next_review=NextReview(),
        persistence=ProposedReviewPersistence(),
    )
