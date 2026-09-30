"""Structured, evidence-bounded quarterly review drafts for the E65 MVP.

Claims deliberately have no free narrative field.  They are bounded records and
are rendered by code, so a caller cannot turn a quarterly observation or a
hypothesis into an unverified causal story.
"""

from __future__ import annotations

import math
import re
from datetime import date
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from validators.procedure_compiler import compile_mvp_procedures


_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_PERIOD = re.compile(r"^(?P<year>\d{4})-q(?P<quarter>[1-4])$")
_SAFE_METRIC_IDS = frozenset(
    {
        "metric.collection-days",
        "metric.cash-balance",
        "metric.receivables-days",
        "metric.revenue",
    }
)
_SAFE_UNIT_IDS = frozenset({"unit.days", "unit.currency", "unit.percent"})
_SAFE_FACTOR_IDS = frozenset(
    {
        "factor.invoice-timing",
        "factor.customer-mix",
        "factor.meeting-rhythm",
    }
)
_SAFE_ASSUMPTION_IDS = frozenset({"assumption.customer-mix-comparable"})
_SAFE_COMMITMENT_IDS = frozenset(
    {
        "commitment.reconcile-disputes",
        "commitment.invoice-review",
    }
)
_SAFE_ACTION_IDS = frozenset({"action.review-receivables"})
_SAFE_PURPOSE_IDS = frozenset({"purpose.review-collections"})
_SAFE_SUBJECT_IDS = _SAFE_METRIC_IDS | frozenset(
    {
        "constraint.cash",
        "constraint.people",
        "constraint.strategy",
        "constraint.execution",
    }
)
_TAXONOMY_FORBIDDEN_TERMS = re.compile(
    r"(?:^|[._-])(causes|improves|growth|raises|drives|boosts|rose|"
    r"aumenta|mejora|crecimiento|eleva|impulsa)(?:$|[._-])",
    re.IGNORECASE,
)


def _validate_safe_taxonomy() -> None:
    for identifier in (
        _SAFE_METRIC_IDS
        | _SAFE_UNIT_IDS
        | _SAFE_FACTOR_IDS
        | _SAFE_ASSUMPTION_IDS
        | _SAFE_COMMITMENT_IDS
        | _SAFE_ACTION_IDS
        | _SAFE_PURPOSE_IDS
        | _SAFE_SUBJECT_IDS
    ):
        if _ID.fullmatch(identifier) is None or _TAXONOMY_FORBIDDEN_TERMS.search(
            identifier
        ):
            raise RuntimeError("safe taxonomy contains an unsafe rendered identifier")


_validate_safe_taxonomy()


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _identifier(value: str, label: str) -> str:
    if _ID.fullmatch(value) is None:
        raise ValueError(f"unsafe {label}")
    return value


def _allow(value: str, allowed: frozenset[str], label: str) -> str:
    if value not in allowed:
        raise ValueError(f"{label} is not in the safe taxonomy")
    return value


def _period_bounds(period: str) -> tuple[date, date]:
    match = _PERIOD.fullmatch(period)
    if match is None:
        raise ValueError("unsafe period")
    year = int(match.group("year"))
    quarter = int(match.group("quarter"))
    start_month = (quarter - 1) * 3 + 1
    start = date(year, start_month, 1)
    if quarter == 4:
        return start, date(year, 12, 31)
    next_quarter = date(year, start_month + 3, 1)
    return start, date.fromordinal(next_quarter.toordinal() - 1)


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


class _PeriodEvidence(_StrictModel):
    period: str
    reported_on: date
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
    def validate_evidence_time(self) -> "_PeriodEvidence":
        _in_period(self.reported_on, self.period, "report date")
        for item in self.evidence:
            _in_period(item.observed_on, self.period, "evidence date")
            if item.observed_on > self.reported_on:
                raise ValueError("evidence date cannot follow report date")
        return self


class Observation(_PeriodEvidence):
    """A single observed measurement, not an explanation or relationship."""

    kind: Literal["fact"]
    metric_id: str
    value: float
    unit_id: str

    @field_validator("metric_id")
    @classmethod
    def validate_metric(cls, value: str) -> str:
        return _allow(value, _SAFE_METRIC_IDS, "observation metric")

    @field_validator("unit_id")
    @classmethod
    def validate_unit(cls, value: str) -> str:
        return _allow(value, _SAFE_UNIT_IDS, "observation unit")

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("observation value must be finite")
        return value


class Hypothesis(_PeriodEvidence):
    """A bounded research question; it does not encode a causal conclusion."""

    kind: Literal["hypothesis"]
    model_origin: Literal["model-hypothesis"]
    factor_id: str
    metric_id: str

    @field_validator("factor_id")
    @classmethod
    def validate_factor(cls, value: str) -> str:
        return _allow(value, _SAFE_FACTOR_IDS, "hypothesis factor")

    @field_validator("metric_id")
    @classmethod
    def validate_metric(cls, value: str) -> str:
        return _allow(value, _SAFE_METRIC_IDS, "hypothesis metric")


class Assumption(_PeriodEvidence):
    kind: Literal["assumption"]
    assumption_id: str

    @field_validator("assumption_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return _allow(value, _SAFE_ASSUMPTION_IDS, "assumption ID")


class CommitmentClaim(_PeriodEvidence):
    kind: Literal["commitment"]
    commitment_id: str

    @field_validator("commitment_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return _allow(value, _SAFE_COMMITMENT_IDS, "commitment ID")


class NoResultYet(_PeriodEvidence):
    kind: Literal["no-result-yet"]
    reason_id: Literal["period-open", "evidence-pending", "measurement-pending"]


ReviewClaim = Annotated[
    Union[Observation, Hypothesis, Assumption, CommitmentClaim, NoResultYet],
    Field(discriminator="kind"),
]


class Measurement(_StrictModel):
    period: str
    measured_on: date
    metric_id: str
    unit_id: str
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

    @field_validator("metric_id")
    @classmethod
    def validate_metric(cls, value: str) -> str:
        return _allow(value, _SAFE_METRIC_IDS, "measurement metric")

    @field_validator("unit_id")
    @classmethod
    def validate_unit(cls, value: str) -> str:
        return _allow(value, _SAFE_UNIT_IDS, "measurement unit")

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
    def validate_time_and_derive(self) -> "Measurement":
        _in_period(self.measured_on, self.period, "measurement date")
        for item in (*self.baseline_evidence, *self.current_evidence):
            _in_period(item.observed_on, self.period, "evidence date")
            if item.observed_on > self.measured_on:
                raise ValueError("evidence date cannot follow measurement date")
        if max(item.observed_on for item in self.baseline_evidence) > min(
            item.observed_on for item in self.current_evidence
        ):
            raise ValueError(
                "baseline evidence must be before or equal to current evidence"
            )
        delta = self.current - self.baseline
        direction: Literal["increased", "decreased", "unchanged"]
        direction = (
            "increased" if delta > 0 else "decreased" if delta < 0 else "unchanged"
        )
        if self.delta != delta or self.direction != direction:
            return self.model_copy(update={"delta": delta, "direction": direction})
        return self


class PlannedCommitment(_StrictModel):
    period: str
    id: str
    owner_id: str
    action_id: str
    due_on: date
    evidence: list[EvidenceReference] = Field(min_length=1)

    @field_validator("period")
    @classmethod
    def validate_period(cls, value: str) -> str:
        _period_bounds(value)
        return value

    @field_validator("id")
    @classmethod
    def validate_commitment(cls, value: str) -> str:
        return _allow(value, _SAFE_COMMITMENT_IDS, "planned commitment")

    @field_validator("owner_id")
    @classmethod
    def validate_owner(cls, value: str) -> str:
        return _identifier(value, "commitment owner")

    @field_validator("action_id")
    @classmethod
    def validate_action(cls, value: str) -> str:
        return _allow(value, _SAFE_ACTION_IDS, "commitment action")

    @field_validator("evidence")
    @classmethod
    def validate_evidence(
        cls, value: list[EvidenceReference]
    ) -> list[EvidenceReference]:
        return _evidence(value)

    @model_validator(mode="after")
    def validate_time(self) -> "PlannedCommitment":
        _in_period(self.due_on, self.period, "commitment due date")
        for item in self.evidence:
            _in_period(item.observed_on, self.period, "evidence date")
            if item.observed_on > self.due_on:
                raise ValueError("evidence date cannot follow commitment due date")
        return self


class ReportedCommitment(_PeriodEvidence):
    id: str
    status: Literal["reported-complete", "reported-open", "no-result-yet"]

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _allow(value, _SAFE_COMMITMENT_IDS, "commitment ID")


class PlannedCadence(_StrictModel):
    period: str
    cadence: Literal["daily", "weekly", "monthly", "quarterly"]
    purpose_id: str
    planned_on: date
    evidence: list[EvidenceReference] = Field(min_length=1)

    @field_validator("period")
    @classmethod
    def validate_period(cls, value: str) -> str:
        _period_bounds(value)
        return value

    @field_validator("purpose_id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        return _allow(value, _SAFE_PURPOSE_IDS, "cadence purpose ID")

    @field_validator("evidence")
    @classmethod
    def validate_evidence(
        cls, value: list[EvidenceReference]
    ) -> list[EvidenceReference]:
        return _evidence(value)

    @model_validator(mode="after")
    def validate_time(self) -> "PlannedCadence":
        _in_period(self.planned_on, self.period, "cadence planned date")
        for item in self.evidence:
            _in_period(item.observed_on, self.period, "evidence date")
            if item.observed_on > self.planned_on:
                raise ValueError("evidence date cannot follow cadence planned date")
        return self


class ReportedCadence(_PeriodEvidence):
    cadence: Literal["daily", "weekly", "monthly", "quarterly"]
    status: Literal["reported-held", "reported-not-held", "no-result-yet"]


class CommitmentComparison(_StrictModel):
    id: str
    planned_action_id: str
    planned_evidence: list[EvidenceReference]
    reported_status: Literal["reported-complete", "reported-open", "no-result-yet"]
    reported_evidence: list[EvidenceReference]
    summary: str


class CadenceComparison(_StrictModel):
    cadence: Literal["daily", "weekly", "monthly", "quarterly"]
    planned_purpose_id: str
    planned_evidence: list[EvidenceReference]
    reported_status: Literal["reported-held", "reported-not-held", "no-result-yet"]
    reported_evidence: list[EvidenceReference]
    summary: str


LearningKind = Literal[
    "continue-measurement", "request-evidence", "reassess-constraint"
]
DecisionKind = Literal["continue-review", "request-evidence", "reassess-constraint"]


class ReviewProposal(_StrictModel):
    learning_kind: LearningKind
    decision_kind: DecisionKind
    subject_id: str

    @field_validator("subject_id")
    @classmethod
    def validate_subject(cls, value: str) -> str:
        return _allow(value, _SAFE_SUBJECT_IDS, "proposal subject ID")


class ProposedReviewPersistence(_StrictModel):
    status: Literal["proposed"] = "proposed"
    writes_state: Literal[False] = False
    closes_commitments: Literal[False] = False
    schedules_review: Literal[False] = False


class NextReview(_StrictModel):
    status: Literal["proposed"] = "proposed"
    prompt: Literal["Confirm when to hold the next quarterly review."] = (
        "Confirm when to hold the next quarterly review."
    )
    scheduled_on: Literal[None] = None


class QuarterlyReviewInput(_StrictModel):
    period: str
    measurement: Measurement | None
    claims: list[ReviewClaim] = Field(min_length=1, max_length=64)
    planned_commitments: list[PlannedCommitment] | None = None
    reported_commitments: list[ReportedCommitment] | None = None
    planned_cadences: list[PlannedCadence] | None = None
    reported_cadences: list[ReportedCadence] | None = None
    proposal: ReviewProposal

    @field_validator("period")
    @classmethod
    def validate_period(cls, value: str) -> str:
        _period_bounds(value)
        return value

    @model_validator(mode="after")
    def validate_boundary(self) -> "QuarterlyReviewInput":
        for planned, reported, name in (
            (self.planned_commitments, self.reported_commitments, "commitment"),
            (self.planned_cadences, self.reported_cadences, "cadence"),
        ):
            if (planned is None) != (reported is None):
                raise ValueError(
                    f"both planned and reported {name} inputs are required"
                )
        if self.measurement is None and any(
            item.kind != "no-result-yet" for item in self.claims
        ):
            raise ValueError(
                "missing measurement requires all claims to be no-result-yet"
            )
        if self.measurement is not None and self.measurement.period != self.period:
            raise ValueError("measurement period must match review period")
        for items, label in (
            (self.claims, "claim"),
            (self.planned_commitments, "planned commitment"),
            (self.reported_commitments, "reported commitment"),
            (self.planned_cadences, "planned cadence"),
            (self.reported_cadences, "reported cadence"),
        ):
            if items is not None and any(item.period != self.period for item in items):
                raise ValueError(f"{label} period must match review period")
        return self


class QuarterlyReview(_StrictModel):
    procedure_id: Literal["procedure.quarterly-review"]
    period: str
    measurement: Measurement | None
    claims: list[ReviewClaim]
    rendered_claims: list[str]
    www_comparison: list[CommitmentComparison] | None
    cadence_comparison: list[CadenceComparison] | None
    learning: str
    decision: str
    open_questions: list[str]
    next_review: NextReview
    persistence: ProposedReviewPersistence


def _render_claim(item: ReviewClaim) -> str:
    if isinstance(item, Observation):
        return f"Observation: {item.metric_id} measured {item.value:g} {item.unit_id}."
    if isinstance(item, Hypothesis):
        return f"Hypothesis to investigate: {item.factor_id} and {item.metric_id}."
    if isinstance(item, Assumption):
        return f"Assumption awaiting confirmation: {item.assumption_id}."
    if isinstance(item, CommitmentClaim):
        return f"Commitment under review: {item.commitment_id}."
    return f"No result yet: {item.reason_id}."


def _render_learning(kind: LearningKind, subject: str) -> str:
    return {
        "continue-measurement": f"Learning proposal: continue measuring {subject}.",
        "request-evidence": f"Learning proposal: request evidence for {subject}.",
        "reassess-constraint": f"Learning proposal: reassess constraint {subject}.",
    }[kind]


def _render_decision(kind: DecisionKind, subject: str) -> str:
    return {
        "continue-review": f"Decision proposal: continue review of {subject}.",
        "request-evidence": f"Decision proposal: request evidence for {subject}.",
        "reassess-constraint": f"Decision proposal: reassess constraint {subject}.",
    }[kind]


def _ensure_review_contract() -> None:
    if "procedure.quarterly-review" not in {
        contract.id for contract in compile_mvp_procedures().contracts
    }:
        raise ValueError("quarterly review procedure is not in the MVP release")


def _compare_commitments(
    planned: list[PlannedCommitment] | None, reported: list[ReportedCommitment] | None
) -> list[CommitmentComparison] | None:
    if planned is None or reported is None:
        return None
    planned_by_id, reported_by_id = (
        {item.id: item for item in planned},
        {item.id: item for item in reported},
    )
    if len(planned_by_id) != len(planned) or len(reported_by_id) != len(reported):
        raise ValueError("duplicate commitment comparison ID")
    if set(planned_by_id) != set(reported_by_id):
        raise ValueError("planned and reported commitments must match exactly")
    return [
        CommitmentComparison(
            id=item.id,
            planned_action_id=item.action_id,
            planned_evidence=item.evidence,
            reported_status=reported_by_id[item.id].status,
            reported_evidence=reported_by_id[item.id].evidence,
            summary=f"Commitment {item.id}: {reported_by_id[item.id].status}.",
        )
        for item in planned
    ]


def _compare_cadences(
    planned: list[PlannedCadence] | None, reported: list[ReportedCadence] | None
) -> list[CadenceComparison] | None:
    if planned is None or reported is None:
        return None
    planned_by_name, reported_by_name = (
        {item.cadence: item for item in planned},
        {item.cadence: item for item in reported},
    )
    if len(planned_by_name) != len(planned) or len(reported_by_name) != len(reported):
        raise ValueError("duplicate cadence comparison")
    if set(planned_by_name) != set(reported_by_name):
        raise ValueError("planned and reported cadences must match exactly")
    return [
        CadenceComparison(
            cadence=item.cadence,
            planned_purpose_id=item.purpose_id,
            planned_evidence=item.evidence,
            reported_status=reported_by_name[item.cadence].status,
            reported_evidence=reported_by_name[item.cadence].evidence,
            summary=f"Cadence {item.cadence}: {reported_by_name[item.cadence].status}.",
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
    questions = [] if review_input.measurement is not None else ["measurement"]
    if www_comparison is None:
        questions.append("who-what-when")
    if cadence_comparison is None:
        questions.append("cadence")
    return QuarterlyReview(
        procedure_id="procedure.quarterly-review",
        period=review_input.period,
        measurement=review_input.measurement,
        claims=review_input.claims,
        rendered_claims=[_render_claim(item) for item in review_input.claims],
        www_comparison=www_comparison,
        cadence_comparison=cadence_comparison,
        learning=_render_learning(
            review_input.proposal.learning_kind, review_input.proposal.subject_id
        ),
        decision=_render_decision(
            review_input.proposal.decision_kind, review_input.proposal.subject_id
        ),
        open_questions=questions,
        next_review=NextReview(),
        persistence=ProposedReviewPersistence(),
    )
