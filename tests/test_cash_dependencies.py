from __future__ import annotations

import pytest

from validators.cash_dependencies import (
    CashDependencyReceipt,
    validate_cash_dependencies,
)


def _receipt() -> CashDependencyReceipt:
    return CashDependencyReceipt.model_validate(
        {
            "schema_version": 1,
            "domain": "cash",
            "status": "pending-independent-review",
            "required_blocked_candidates": ["candidate.cash.cash-tool"],
            "dependencies": [
                {
                    "candidate_id": "candidate.cash.cash-tool",
                    "evidence_units": ["source.example.u0001"],
                    "dependency_type": "external-formula-source",
                    "compilation_status": "blocked",
                    "rule": "Do not compile formula details without the authorized source.",
                }
            ],
        }
    )


def test_cash_dependency_requires_exact_candidate_evidence() -> None:
    validate_cash_dependencies(
        _receipt(), {"candidate.cash.cash-tool": {"source.example.u0001"}}
    )


def test_cash_dependency_rejects_missing_required_block() -> None:
    unsafe = _receipt().model_copy(
        update={"required_blocked_candidates": ["candidate.cash.missing"]}
    )
    with pytest.raises(ValueError, match="is absent"):
        validate_cash_dependencies(
            unsafe, {"candidate.cash.cash-tool": {"source.example.u0001"}}
        )


def test_cash_dependency_rejects_unblocked_formula() -> None:
    dependency = (
        _receipt()
        .dependencies[0]
        .model_copy(update={"compilation_status": "source-bounded"})
    )
    unsafe = _receipt().model_copy(update={"dependencies": [dependency]})
    with pytest.raises(ValueError, match="not blocked"):
        validate_cash_dependencies(
            unsafe, {"candidate.cash.cash-tool": {"source.example.u0001"}}
        )
