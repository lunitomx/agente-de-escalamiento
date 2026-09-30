"""Privacy-preserving receipts and comparison for isolated E68 experiments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

from validators.activation_evals import ActivationObservation


class IsolatedABError(ValueError):
    """A stable failure while validating an isolated experiment."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SessionReceipt(_StrictModel):
    """A session receipt deliberately containing hashes, never transcript text."""

    schema_version: Literal[1]
    receipt_id: str = Field(pattern=r"^E68-REC-[A-Z0-9-]+$")
    platform: Literal["codex", "claude"]
    client_version: str = Field(min_length=1, max_length=64)
    capability_condition: Literal["available", "unavailable"]
    isolated_session: Literal[True]
    suite_id: Literal["escala.mvp.activation.v1"]
    case_ids: tuple[str, ...] = Field(min_length=1, max_length=128)
    prompt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    observations: tuple[ActivationObservation, ...] = Field(
        min_length=1, max_length=128
    )

    @model_validator(mode="after")
    def validate_coverage(self) -> "SessionReceipt":
        observation_ids = tuple(
            observation.case_id for observation in self.observations
        )
        if len(self.case_ids) != len(set(self.case_ids)):
            raise ValueError("receipt_case_ids_duplicate")
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("receipt_observations_duplicate")
        if set(self.case_ids) != set(observation_ids):
            raise ValueError("receipt_case_coverage_mismatch")
        return self


@dataclass(frozen=True)
class ABComparison:
    """Observed changes only; this object deliberately makes no causal claim."""

    platform: str
    available_receipt_id: str
    unavailable_receipt_id: str
    compared_case_ids: tuple[str, ...]
    changed_case_ids: tuple[str, ...]


def compare_isolated_ab(receipts: Sequence[SessionReceipt]) -> tuple[ABComparison, ...]:
    """Pair declared available/unavailable executions from the same platform."""

    grouped: dict[str, dict[str, SessionReceipt]] = {}
    for receipt in receipts:
        by_condition = grouped.setdefault(receipt.platform, {})
        if receipt.capability_condition in by_condition:
            raise IsolatedABError("receipt_condition_duplicate:" + receipt.platform)
        by_condition[receipt.capability_condition] = receipt

    comparisons: list[ABComparison] = []
    for platform in sorted(grouped):
        by_condition = grouped[platform]
        available = by_condition.get("available")
        unavailable = by_condition.get("unavailable")
        if available is None or unavailable is None:
            raise IsolatedABError("receipt_pair_incomplete:" + platform)
        if set(available.case_ids) != set(unavailable.case_ids):
            raise IsolatedABError("receipt_case_set_mismatch:" + platform)
        available_results = _observation_map(available)
        unavailable_results = _observation_map(unavailable)
        compared_case_ids = tuple(sorted(available_results))
        changed = tuple(
            case_id
            for case_id in compared_case_ids
            if available_results[case_id] != unavailable_results[case_id]
        )
        comparisons.append(
            ABComparison(
                platform=platform,
                available_receipt_id=available.receipt_id,
                unavailable_receipt_id=unavailable.receipt_id,
                compared_case_ids=compared_case_ids,
                changed_case_ids=changed,
            )
        )
    if not comparisons:
        raise IsolatedABError("receipts_empty")
    return tuple(comparisons)


def _observation_map(receipt: SessionReceipt) -> dict[str, tuple[str, str | None]]:
    return {
        observation.case_id: (observation.action, observation.resolved_intent)
        for observation in receipt.observations
    }
