from __future__ import annotations

import pytest

from validators.e44_e45_business_pilot import (
    E44E45BusinessPilotReceipt,
    validate_business_pilot,
)


def _receipt() -> E44E45BusinessPilotReceipt:
    return E44E45BusinessPilotReceipt.model_validate(
        {
            "schema_version": 1,
            "status": "pass",
            "participant_ref": "owner-001",
            "company_ref": "company-001",
            "reviewed_on": "2026-08-27",
            "data_storage": "private-local-only",
            "owner_acceptance": True,
            "retrospective_completed": True,
            "cycles": [
                {
                    "area": "people",
                    "outcome_status": "observed",
                    "owner_review": "confirmed",
                    "people_consent": True,
                },
                {
                    "area": "strategy",
                    "outcome_status": "observed",
                    "owner_review": "corrected",
                },
                {
                    "area": "execution",
                    "outcome_status": "no_result_yet",
                    "owner_review": "rejected",
                },
                {
                    "area": "cash",
                    "outcome_status": "observed",
                    "owner_review": "confirmed",
                },
            ],
            "team_scenarios": [
                {
                    "scenario_id": "cash-execution",
                    "areas": ["cash", "execution"],
                    "single_coach_completed": True,
                    "team_completed": True,
                    "one_executive_response": True,
                    "additional_risk_found": True,
                    "owner_value": "higher",
                    "conclusion": "retain-team",
                    "rounds_used": 1,
                    "elapsed_minutes": 15,
                    "data_minimized": True,
                },
                {
                    "scenario_id": "growth-cross-decision",
                    "areas": ["people", "strategy", "execution"],
                    "single_coach_completed": True,
                    "team_completed": True,
                    "one_executive_response": True,
                    "additional_risk_found": False,
                    "owner_value": "inconclusive",
                    "conclusion": "needs-more-evidence",
                    "rounds_used": 0,
                    "elapsed_minutes": 12,
                    "data_minimized": True,
                },
            ],
        }
    )


def test_business_pilot_receipt_requires_all_human_acceptance_evidence() -> None:
    receipt = _receipt()
    validate_business_pilot(receipt)


def test_business_pilot_rejects_people_cycle_without_consent() -> None:
    payload = _receipt().model_dump(mode="json")
    payload["cycles"][0]["people_consent"] = False
    with pytest.raises(ValueError, match="consent"):
        E44E45BusinessPilotReceipt.model_validate(payload)


def test_business_pilot_rejects_wrong_cross_decision_scenario() -> None:
    payload = _receipt().model_dump(mode="json")
    payload["team_scenarios"][1]["areas"] = ["strategy", "cash"]
    with pytest.raises(ValueError, match="required decisions"):
        E44E45BusinessPilotReceipt.model_validate(payload)


def test_business_pilot_rejects_personal_participant_name() -> None:
    payload = _receipt().model_dump(mode="json")
    payload["participant_ref"] = "Ana García"
    with pytest.raises(ValueError, match="opaque"):
        E44E45BusinessPilotReceipt.model_validate(payload)
