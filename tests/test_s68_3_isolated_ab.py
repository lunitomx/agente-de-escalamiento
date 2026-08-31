from __future__ import annotations

import hashlib

import pytest

from validators.isolated_ab import (
    IsolatedABError,
    SessionReceipt,
    compare_isolated_ab,
)


def _receipt(*, condition: str, intent: str = "diagnose-primary-constraint") -> SessionReceipt:
    return SessionReceipt.model_validate(
        {
            "schema_version": 1,
            "receipt_id": f"E68-REC-CODEX-{condition.upper()}",
            "platform": "codex",
            "client_version": "test-client",
            "capability_condition": condition,
            "isolated_session": True,
            "suite_id": "escala.mvp.activation.v1",
            "case_ids": ["ACT-001"],
            "prompt_sha256": hashlib.sha256(condition.encode()).hexdigest(),
            "response_sha256": hashlib.sha256(intent.encode()).hexdigest(),
            "observations": [
                {
                    "case_id": "ACT-001",
                    "action": "route",
                    "resolved_intent": intent,
                }
            ],
        }
    )


def test_pairs_receipts_and_reports_only_observed_changes() -> None:
    comparison = compare_isolated_ab(
        (_receipt(condition="available"), _receipt(condition="unavailable"))
    )[0]

    assert comparison.platform == "codex"
    assert comparison.compared_case_ids == ("ACT-001",)
    assert comparison.changed_case_ids == ()


def test_detects_observed_change_without_claiming_cause() -> None:
    comparison = compare_isolated_ab(
        (
            _receipt(condition="available"),
            _receipt(condition="unavailable", intent="build-vision-summary"),
        )
    )[0]

    assert comparison.changed_case_ids == ("ACT-001",)


def test_rejects_incomplete_condition_pair() -> None:
    with pytest.raises(IsolatedABError, match="receipt_pair_incomplete:codex"):
        compare_isolated_ab((_receipt(condition="available"),))


def test_rejects_case_coverage_mismatch() -> None:
    with pytest.raises(ValueError, match="receipt_case_coverage_mismatch"):
        SessionReceipt.model_validate(
            {
                **_receipt(condition="available").model_dump(),
                "case_ids": ["ACT-001", "ACT-002"],
            }
        )
