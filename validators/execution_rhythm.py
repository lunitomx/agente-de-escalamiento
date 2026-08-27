"""Evidence-bound, non-canonical receipt for Execution meeting rhythms."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RhythmReceiptItem(_StrictModel):
    id: str = Field(min_length=3, max_length=96)
    candidate_ids: list[str] = Field(min_length=1, max_length=8)
    evidence_units: list[str] = Field(min_length=1, max_length=32)
    assertions: list[str] = Field(min_length=1, max_length=16)
    duration_status: Literal[
        "requires independent source check before canonical promotion"
    ]


class ExecutionRhythmReceipt(_StrictModel):
    schema_version: Literal[1]
    domain: Literal["execution"]
    status: Literal["pending-independent-review", "approved"]
    purpose: str = Field(min_length=24, max_length=512)
    routines: list[RhythmReceiptItem] = Field(min_length=1, max_length=16)
    external_reference_boundary: str = Field(min_length=24, max_length=1024)

    @model_validator(mode="after")
    def validate_unique_routines(self) -> "ExecutionRhythmReceipt":
        ids = [item.id for item in self.routines]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate rhythm receipt item")
        return self


def validate_execution_rhythm_receipt(
    receipt: ExecutionRhythmReceipt, candidate_evidence: dict[str, set[str]]
) -> None:
    """Keep assertions attached to source candidates pending independent review."""
    for routine in receipt.routines:
        if not set(routine.candidate_ids).issubset(candidate_evidence):
            raise ValueError("rhythm receipt references unknown candidate")
        expected = set().union(
            *(
                candidate_evidence[candidate_id]
                for candidate_id in routine.candidate_ids
            )
        )
        if set(routine.evidence_units) != expected:
            raise ValueError("rhythm receipt evidence differs from candidates")
