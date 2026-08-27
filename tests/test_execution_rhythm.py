from __future__ import annotations

import pytest

from validators.execution_rhythm import (
    ExecutionRhythmReceipt,
    validate_execution_rhythm_receipt,
)


def _receipt() -> ExecutionRhythmReceipt:
    return ExecutionRhythmReceipt.model_validate(
        {
            "schema_version": 1,
            "domain": "execution",
            "status": "pending-independent-review",
            "purpose": "Source-bounded receipt for a meeting rhythm pending review.",
            "external_reference_boundary": "External methods remain bounded until separately sourced and reviewed.",
            "routines": [
                {
                    "id": "daily-huddle",
                    "candidate_ids": ["candidate.execution.daily"],
                    "evidence_units": ["source.example.u0001"],
                    "assertions": ["A short operational check-in."],
                    "duration_status": "requires independent source check before canonical promotion",
                }
            ],
        }
    )


def test_rhythm_receipt_requires_exact_candidate_evidence() -> None:
    validate_execution_rhythm_receipt(
        _receipt(), {"candidate.execution.daily": {"source.example.u0001"}}
    )


def test_rhythm_receipt_rejects_unknown_candidate() -> None:
    item = (
        _receipt()
        .routines[0]
        .model_copy(update={"candidate_ids": ["candidate.execution.unknown"]})
    )
    with pytest.raises(ValueError, match="unknown candidate"):
        validate_execution_rhythm_receipt(
            _receipt().model_copy(update={"routines": [item]}),
            {"candidate.execution.daily": {"source.example.u0001"}},
        )


def test_rhythm_receipt_rejects_evidence_drift() -> None:
    item = (
        _receipt()
        .routines[0]
        .model_copy(update={"evidence_units": ["source.example.u0002"]})
    )
    with pytest.raises(ValueError, match="evidence differs"):
        validate_execution_rhythm_receipt(
            _receipt().model_copy(update={"routines": [item]}),
            {"candidate.execution.daily": {"source.example.u0001"}},
        )
