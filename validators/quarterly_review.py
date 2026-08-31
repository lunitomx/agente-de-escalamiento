"""Evidence-bounded quarterly review drafts for the E65 MVP.

This module evaluates only reported, period-bound evidence. It never infers
causality, writes company state, marks commitments complete, or schedules a
future review. Those actions require later trusted adapters.
"""

from __future__ import annotations

import math
import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from validators.procedure_compiler import compile_mvp_procedures


_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_PERIOD = re.compile(r"^(?P<year>\d{4})-q(?P<quarter>[1-4])$")
_TEXT_MAX = 300
_CAUSAL_LANGUAGE = re.compile(
    r"\b(because|caused|causes|causing|resulted in|led to|due to|therefore|"
    r"as a result|attributed to|driven by|porque|caus[óo]|provoc[óo]|"
    r"result[óo] en|debido a|por lo tanto|atribui(?:do|da)|gener[óo]|"
    r"improved|increased|reduced|decreased|grew|declined|aument[óo]|reduj[óo]|"
    r"increment[óo]|disminuy[óo])\b",
    re.IGNORECASE,
)


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
    if _CAUSAL_LANGUAGE.search(value):
        raise ValueError(f"causal or outcome language is not allowed in {label}")
    return value


def _period_bounds(period: str) -> tuple[date, date]:
    match = _PERIOD.fullmatch(period)
    if match is None:
        raise ValueError("unsafe period")
    year = int(match.group("year"))
    quarter = int(match.group("quarter"))
    month = ((quarter - 1) * 3) + 1
    start = date(year, month, 1)
    if quarter == 4:
        end = date(year, 12, 31)
    else:
        end = date(year, month + 3, 1).fromordinal(
            date(year, month + 3, 1).toordinal() - 1
        )
    return start, end


def _in_period(value: date, period: str, label: str) -> date:
    start, end = _period_bounds(period)
    if not start <= value <= end:
        raise ValueError(f"{label} must be within review period")
    return value


class EvidenceReference(_StrictModel):
    id: str
    observed_on: date

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _identifier(value, "evidence ID")


def _evidence(values: list[EvidenceReference]) -> list[EvidenceReference]:
    if not values:
        raise ValueError("supporting evidence is required")
    if len({item.id for item in values}) != len(values):
        raise ValueError("duplicate evidence ID")
    return values


class Measurement(_StrictModel):
    period: str
    measured_on: date
    name: str
    unit: str
    baseline: float
    current: float
    baseline_evidence: list[EvidenceReference] = Field(min_length=1)
    current_evidence: list[EvidenceReference] = Field(min_length=1)
    delta: float = 0
    direction: Literal["increased", "decreased", "unchanged"] = "unchanged"

    @field_validator("period")
    @classmethod
    def validate_period(cls, value: str) -> str:
        _period_bounds(value)
        return value

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

    @field_validator("baseline_evidence", "current_evidence")
    @classmethod
    def validate_evidence(
        cls, value: list[EvidenceReference]
    ) -> list[EvidenceReference]:
        return _evidence(value)

    @model_validator(mode="after")
    def validate_period_and_derive_comparison(self) -> "Measurement":
        _in_period(self.measured_on, self.period, "measurement date")
        for evidence in (*self.baseline_evidence, *self.current_evidence):
            _in_period(evidence.observed_on, self.period, "evidence date")
            if evidence.observed_on > self.measured_on:
                raise ValueError("evidence date cannot follow measurement date")
        if max(item.observed_on for item in self.baseline_evidence) > min(
            item.observed_on for item in self.current_evidence
        ):
            raise ValueError(
                "baseline evidence must be before or equal to current evidence"
            )
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
    period: str
    kind: ClaimKind
    reported_on: date
    statement: str
    evidence: list[EvidenceReference] = Field(min_length=1)
    causal_claim: Literal[False] = False

    @field_validator("period")
    @classmethod
    def validate_period(cls, value: str) -> str:
        _period_bounds(value)
        return value

    @field_validator("statement")
    @classmethod
    def validate_statement(cls, value: str) -> str:
        return _text(value, "claim statement")

    @field_validator("evidence")
    @classmethod
    def validate_evidence(
        cls, value: list[EvidenceReference]
    ) -> list[EvidenceReference]:
        return _evidence(value)

    @model_validator(mode="after")
    def validate_evidence_period(self) -> "ReviewClaim":
        _in_period(self.reported_on, self.period, "claim report date")
        for evidence in self.evidence:
            _in_period(evidence.observed_on, self.period, "evidence date")
            if evidence.observed_on > self.reported_on:
                raise ValueError("evidence date cannot follow claim report date")
        required_prefix = {
            "fact": "Observation:",
            "hypothesis": "Hypothesis:",
        }.get(self.kind)
        if required_prefix is not None and not self.statement.startswith(
            required_prefix
        ):
            raise ValueError(
                f"{self.kind} statement must use {required_prefix} grammar"
            )
        return self


class PlannedCommitment(_StrictModel):
    period: str
    id: str
    owner_id: str
    action: str
    due_on: date
    evidence: list[EvidenceReference] = Field(min_length=1)

    @field_validator("period")
    @classmethod
    def validate_period(cls, value: str) -> str:
        _period_bounds(value)
        return value

    @field_validator("id", "owner_id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _identifier(value, "commitment ID")

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        return _text(value, "commitment action")

    @field_validator("evidence")
    @classmethod
    def validate_evidence(
        cls, value: list[EvidenceReference]
    ) -> list[EvidenceReference]:
        return _evidence(value)

    @model_validator(mode="after")
    def validate_dates(self) -> "PlannedCommitment":
        _in_period(self.due_on, self.period, "commitment due date")
        for evidence in self.evidence:
            _in_period(evidence.observed_on, self.period, "evidence date")
            if evidence.observed_on > self.due_on:
                raise ValueError("evidence date cannot follow commitment due date")
        return self


class ReportedCommitment(_StrictModel):
    period: str
    id: str
    reported_on: date
    status: Literal["reported-complete", "reported-open", "no-result-yet"]
    evidence: list[EvidenceReference] = Field(min_length=1)

    @field_validator("period")
    @classmethod
    def validate_period(cls, value: str) -> str:
        _period_bounds(value)
        return value

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _identifier(value, "commitment ID")

    @field_validator("evidence")
    @classmethod
    def validate_evidence(
        cls, value: list[EvidenceReference]
    ) -> list[EvidenceReference]:
        return _evidence(value)

    @model_validator(mode="after")
    def validate_dates(self) -> "ReportedCommitment":
        _in_period(self.reported_on, self.period, "commitment report date")
        for evidence in self.evidence:
            _in_period(evidence.observed_on, self.period, "evidence date")
            if evidence.observed_on > self.reported_on:
                raise ValueError("evidence date cannot follow commitment report date")
        return self


class PlannedCadence(_StrictModel):
    period: str
    cadence: Literal["daily", "weekly", "monthly", "quarterly"]
    purpose: str
    planned_on: date
    evidence: list[EvidenceReference] = Field(min_length=1)

    @field_validator("period")
    @classmethod
    def validate_period(cls, value: str) -> str:
        _period_bounds(value)
        return value

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, value: str) -> str:
        return _text(value, "cadence purpose")

    @field_validator("evidence")
    @classmethod
    def validate_evidence(
        cls, value: list[EvidenceReference]
    ) -> list[EvidenceReference]:
        return _evidence(value)

    @model_validator(mode="after")
    def validate_dates(self) -> "PlannedCadence":
        _in_period(self.planned_on, self.period, "cadence planned date")
        for evidence in self.evidence:
            _in_period(evidence.observed_on, self.period, "evidence date")
            if evidence.observed_on > self.planned_on:
                raise ValueError("evidence date cannot follow cadence planned date")
        return self


class ReportedCadence(_StrictModel):
    period: str
    cadence: Literal["daily", "weekly", "monthly", "quarterly"]
    reported_on: date
    status: Literal["reported-held", "reported-not-held", "no-result-yet"]
    evidence: list[EvidenceReference] = Field(min_length=1)

    @field_validator("period")
    @classmethod
    def validate_period(cls, value: str) -> str:
        _period_bounds(value)
        return value

    @field_validator("evidence")
    @classmethod
    def validate_evidence(
        cls, value: list[EvidenceReference]
    ) -> list[EvidenceReference]:
        return _evidence(value)

    @model_validator(mode="after")
    def validate_dates(self) -> "ReportedCadence":
        _in_period(self.reported_on, self.period, "cadence report date")
        for evidence in self.evidence:
            _in_period(evidence.observed_on, self.period, "evidence date")
            if evidence.observed_on > self.reported_on:
                raise ValueError("evidence date cannot follow cadence report date")
        return self


class CommitmentComparison(_StrictModel):
    id: str
    planned_action: str
    planned_evidence: list[EvidenceReference]
    reported_status: Literal["reported-complete", "reported-open", "no-result-yet"]
    reported_evidence: list[EvidenceReference]


class CadenceComparison(_StrictModel):
    cadence: Literal["daily", "weekly", "monthly", "quarterly"]
    planned_purpose: str
    planned_evidence: list[EvidenceReference]
    reported_status: Literal["reported-held", "reported-not-held", "no-result-yet"]
    reported_evidence: list[EvidenceReference]


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
        _period_bounds(value)
        return value

    @field_validator("proposed_learning", "proposed_decision")
    @classmethod
    def validate_proposal(cls, value: str) -> str:
        return _text(value, "proposed review text")

    @model_validator(mode="after")
    def validate_review_boundary(self) -> "QuarterlyReviewInput":
        pairs = (
            (self.planned_commitments, self.reported_commitments, "commitment"),
            (self.planned_cadences, self.reported_cadences, "cadence"),
        )
        for planned, reported, name in pairs:
            if (planned is None) != (reported is None):
                raise ValueError(
                    f"both planned and reported {name} inputs are required"
                )
        if self.measurement is None and any(
            claim.kind != "no-result-yet" for claim in self.claims
        ):
            raise ValueError(
                "missing measurement requires all claims to be no-result-yet"
            )
        if self.measurement is not None and self.measurement.period != self.period:
            raise ValueError("measurement period must match review period")
        for claim in self.claims:
            if claim.period != self.period:
                raise ValueError("claim period must match review period")
        for items, label in (
            (self.planned_commitments, "planned commitment"),
            (self.reported_commitments, "reported commitment"),
            (self.planned_cadences, "planned cadence"),
            (self.reported_cadences, "reported cadence"),
        ):
            if items is not None and any(item.period != self.period for item in items):
                raise ValueError(f"{label} period must match review period")
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
            planned_evidence=item.evidence,
            reported_status=reported_by_id[item.id].status,
            reported_evidence=reported_by_id[item.id].evidence,
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
            planned_evidence=item.evidence,
            reported_status=reported_by_name[item.cadence].status,
            reported_evidence=reported_by_name[item.cadence].evidence,
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
