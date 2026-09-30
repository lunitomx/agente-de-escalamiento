"""Deterministic activation evaluation for the six ESCALA MVP capabilities."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from validators.capability_map import (
    AuthorizedEvidence,
    CapabilityMapError,
    route_capability,
)
from validators.procedure_compiler import MVP_PROCEDURE_IDS


class ActivationEvalError(ValueError):
    """A stable failure while loading or scoring activation evidence."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ActivationCase(_StrictModel):
    case_id: str = Field(pattern=r"^ACT-[0-9]{3}$")
    case_type: Literal["should_trigger", "should_not_trigger", "ambiguous", "sequence"]
    user_message: str = Field(min_length=1, max_length=1_000)
    prior_turns: tuple[str, ...] = Field(default=(), max_length=8)
    evidence_kinds: tuple[str, ...] = Field(default=(), max_length=8)
    expected_action: Literal["route", "clarify"]
    expected_intent: str | None = None
    expected_procedure_id: str | None = None

    @model_validator(mode="after")
    def validate_expectation(self) -> "ActivationCase":
        if self.expected_action == "route":
            if (
                self.expected_intent is None
                or self.expected_procedure_id is None
                or not self.evidence_kinds
            ):
                raise ValueError("route case requires intent, procedure, and evidence")
        elif self.expected_intent is not None or self.expected_procedure_id is not None:
            raise ValueError("clarify case cannot declare a route")
        if self.case_type == "sequence" and not self.prior_turns:
            raise ValueError("sequence case requires prior turns")
        return self


class ActivationSuite(_StrictModel):
    schema_version: Literal[1]
    suite_id: Literal["escala.mvp.activation.v1"]
    cases: tuple[ActivationCase, ...] = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_case_ids(self) -> "ActivationSuite":
        ids = [case.case_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("case ids must be unique")
        return self


class ActivationObservation(_StrictModel):
    case_id: str = Field(pattern=r"^ACT-[0-9]{3}$")
    action: Literal["route", "clarify"]
    resolved_intent: str | None = None

    @model_validator(mode="after")
    def validate_observed_action(self) -> "ActivationObservation":
        if self.action == "route" and self.resolved_intent is None:
            raise ValueError("route observation requires resolved intent")
        if self.action == "clarify" and self.resolved_intent is not None:
            raise ValueError("clarify observation cannot carry an intent")
        return self


@dataclass(frozen=True)
class ActivationCaseResult:
    case_id: str
    expected_action: str
    observed_action: str
    expected_procedure_id: str | None
    observed_procedure_id: str | None
    passed: bool
    routing_error: str | None


@dataclass(frozen=True)
class ActivationEvaluation:
    cases: tuple[ActivationCaseResult, ...]
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int
    precision: float
    recall: float


def load_activation_suite(path: Path) -> ActivationSuite:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return ActivationSuite.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise ActivationEvalError("activation_suite_invalid") from exc


def validate_activation_suite(suite: ActivationSuite) -> tuple[str, ...]:
    """Validate MVP coverage and expected routes against the authority."""

    errors: list[str] = []
    if {case.case_type for case in suite.cases} != {
        "should_trigger",
        "should_not_trigger",
        "ambiguous",
        "sequence",
    }:
        errors.append("case_type_coverage_incomplete")
    expected_procedures = {
        case.expected_procedure_id
        for case in suite.cases
        if case.expected_procedure_id is not None
    }
    if expected_procedures != set(MVP_PROCEDURE_IDS):
        errors.append("mvp_procedure_coverage_incomplete")
    for case in suite.cases:
        if case.expected_action != "route":
            continue
        try:
            route = route_capability(
                case.expected_intent or "",
                _evidence_for(case),
            )
        except CapabilityMapError:
            errors.append(f"expected_route_invalid:{case.case_id}")
            continue
        if route.procedure_id != case.expected_procedure_id:
            errors.append(f"expected_procedure_mismatch:{case.case_id}")
    return tuple(sorted(errors))


def evaluate_activation_suite(
    suite: ActivationSuite,
    observations: Sequence[ActivationObservation],
) -> ActivationEvaluation:
    """Score a complete set of observed routing actions against the suite."""

    validation_errors = validate_activation_suite(suite)
    if validation_errors:
        raise ActivationEvalError(
            "activation_suite_invalid:" + ",".join(validation_errors)
        )
    observations_by_id = _index_observations(observations)
    expected_ids = {case.case_id for case in suite.cases}
    observed_ids = set(observations_by_id)
    missing = expected_ids - observed_ids
    unknown = observed_ids - expected_ids
    if missing:
        raise ActivationEvalError("observations_missing")
    if unknown:
        raise ActivationEvalError("observations_unknown")

    results: list[ActivationCaseResult] = []
    true_positives = false_positives = false_negatives = true_negatives = 0
    for case in suite.cases:
        observation = observations_by_id[case.case_id]
        observed_procedure_id, routing_error = _observed_procedure(case, observation)
        if case.expected_action == "clarify":
            passed = observation.action == "clarify"
            if passed:
                true_negatives += 1
            else:
                false_positives += 1
        elif observation.action != "route" or observed_procedure_id is None:
            passed = False
            false_negatives += 1
            if observation.action == "route":
                false_positives += 1
        elif observed_procedure_id == case.expected_procedure_id:
            passed = True
            true_positives += 1
        else:
            passed = False
            false_positives += 1
            false_negatives += 1
        results.append(
            ActivationCaseResult(
                case_id=case.case_id,
                expected_action=case.expected_action,
                observed_action=observation.action,
                expected_procedure_id=case.expected_procedure_id,
                observed_procedure_id=observed_procedure_id,
                passed=passed,
                routing_error=routing_error,
            )
        )
    precision_denominator = true_positives + false_positives
    recall_denominator = true_positives + false_negatives
    return ActivationEvaluation(
        cases=tuple(results),
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        true_negatives=true_negatives,
        precision=true_positives / precision_denominator
        if precision_denominator
        else 0.0,
        recall=true_positives / recall_denominator if recall_denominator else 0.0,
    )


def _index_observations(
    observations: Sequence[ActivationObservation],
) -> dict[str, ActivationObservation]:
    index = {observation.case_id: observation for observation in observations}
    if len(index) != len(observations):
        raise ActivationEvalError("observations_duplicate")
    return index


def _evidence_for(case: ActivationCase) -> tuple[AuthorizedEvidence, ...]:
    return tuple(
        AuthorizedEvidence(
            kind=kind,
            receipt="receipt.sha256."
            + hashlib.sha256(f"{case.case_id}:{kind}".encode()).hexdigest(),
            status="confirmed",
        )
        for kind in case.evidence_kinds
    )


def _observed_procedure(
    case: ActivationCase,
    observation: ActivationObservation,
) -> tuple[str | None, str | None]:
    if observation.action == "clarify":
        return None, None
    try:
        route = route_capability(observation.resolved_intent or "", _evidence_for(case))
        return route.procedure_id, None
    except CapabilityMapError as exc:
        return None, str(exc)
