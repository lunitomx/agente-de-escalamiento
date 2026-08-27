"""Fail-closed external-formula dependency receipt for the Cash corpus."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CashDependency(_StrictModel):
    candidate_id: str = Field(min_length=3, max_length=192)
    evidence_units: list[str] = Field(min_length=1, max_length=64)
    dependency_type: Literal[
        "external-formula-source", "formula-source", "product-data-contract"
    ]
    compilation_status: Literal["blocked", "source-bounded"]
    rule: str = Field(min_length=24, max_length=1024)


class CashDependencyReceipt(_StrictModel):
    schema_version: Literal[1]
    domain: Literal["cash"]
    status: Literal["pending-independent-review", "approved"]
    required_blocked_candidates: list[str] = Field(min_length=1, max_length=32)
    dependencies: list[CashDependency] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_unique_dependencies(self) -> "CashDependencyReceipt":
        ids = [item.candidate_id for item in self.dependencies]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate cash dependency candidate")
        if len(self.required_blocked_candidates) != len(
            set(self.required_blocked_candidates)
        ):
            raise ValueError("duplicate required blocked candidate")
        return self


def validate_cash_dependencies(
    receipt: CashDependencyReceipt, candidate_evidence: dict[str, set[str]]
) -> None:
    """Ensure source-dependent Cash formulas cannot silently be compiled."""
    dependencies = {item.candidate_id: item for item in receipt.dependencies}
    if not set(dependencies).issubset(candidate_evidence):
        raise ValueError("cash dependency references unknown candidate")
    for candidate_id, dependency in dependencies.items():
        if set(dependency.evidence_units) != candidate_evidence[candidate_id]:
            raise ValueError("cash dependency evidence differs from candidate")
    for candidate_id in receipt.required_blocked_candidates:
        dependency = dependencies.get(candidate_id)
        if dependency is None:
            raise ValueError("required blocked cash dependency is absent")
        if dependency.compilation_status != "blocked":
            raise ValueError("required cash dependency is not blocked")
        if dependency.dependency_type not in {
            "external-formula-source",
            "formula-source",
        }:
            raise ValueError("required cash dependency has the wrong type")
