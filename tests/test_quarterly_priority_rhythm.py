from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from validators.quarterly_priority_rhythm import (
    QuarterlyPriorityRhythmPlan,
    validate_quarterly_priority_rhythm_plan,
)


def _plan() -> dict[str, object]:
    return {
        "status": "proposed",
        "diagnosis": {
            "status": "confirmed",
            "primary_constraint": "collection cycle",
            "confirmation_receipt": "receipt.diagnosis.confirmed",
        },
        "priority": "Reduce collection cycle",
        "priority_justification": None,
        "critical_number": {
            "name": "collection days",
            "unit": "days",
            "baseline": 76,
            "owner_id": "person.finance.owner",
        },
        "commitments": [
            {
                "owner_id": "person.finance.owner",
                "action": "Review receivables",
                "due_on": "2026-09-07",
            }
        ],
        "meeting_cadences": [
            {
                "cadence": cadence,
                "purpose": f"Review {cadence} execution",
                "owner_id": "person.finance.owner",
                "status": "proposed",
                "accepted": False,
            }
            for cadence in ("daily", "weekly", "monthly", "quarterly")
        ],
        "automation_proposals": [
            {
                "id": "automation.review-reminder",
                "purpose": "Offer a review reminder",
                "status": "proposed",
                "accepted": False,
                "acceptance_receipt": None,
            }
        ],
        "requires_explicit_acceptance": True,
    }


def test_complete_plan_is_proposed_only_and_non_executing() -> None:
    plan = validate_quarterly_priority_rhythm_plan(_plan())

    assert plan.status == "proposed"
    assert plan.requires_explicit_acceptance is True
    assert {item.cadence for item in plan.meeting_cadences} == {
        "daily",
        "weekly",
        "monthly",
        "quarterly",
    }
    assert all(
        item.status == "proposed" and not item.accepted
        for item in plan.meeting_cadences
    )


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (lambda payload: payload.pop("critical_number"), "critical_number"),
        (lambda payload: payload["commitments"].clear(), "at least 1"),  # type: ignore[index]
        (
            lambda payload: payload["meeting_cadences"].pop(),  # type: ignore[index]
            "at least 4",
        ),
        (
            lambda payload: payload.__setitem__("requires_explicit_acceptance", False),
            "Input should be True",
        ),
    ],
)
def test_plan_fails_closed_when_required_planning_data_is_missing(
    mutate: object, match: str
) -> None:
    payload = deepcopy(_plan())
    mutate(payload)  # type: ignore[operator]

    with pytest.raises(ValidationError, match=match):
        QuarterlyPriorityRhythmPlan.model_validate(payload)


def test_plan_rejects_more_than_one_primary_priority() -> None:
    payload = _plan()
    payload["priority"] = "Reduce collection cycle; launch new market"

    with pytest.raises(ValidationError, match="unsafe priority"):
        QuarterlyPriorityRhythmPlan.model_validate(payload)


def test_proposed_diagnosis_must_expose_why_priority_is_proposed() -> None:
    payload = _plan()
    payload["diagnosis"] = {
        "status": "proposed",
        "primary_constraint": "collection cycle",
        "confirmation_receipt": None,
    }

    with pytest.raises(ValidationError, match="requires priority justification"):
        QuarterlyPriorityRhythmPlan.model_validate(payload)


def test_plan_rejects_unjustified_meeting_acceptance_or_automation() -> None:
    payload = _plan()
    payload["meeting_cadences"][0]["accepted"] = True  # type: ignore[index]
    with pytest.raises(ValidationError):
        QuarterlyPriorityRhythmPlan.model_validate(payload)

    payload = _plan()
    payload["automation_proposals"][0]["accepted"] = True  # type: ignore[index]
    with pytest.raises(ValidationError, match="accepted automation requires"):
        QuarterlyPriorityRhythmPlan.model_validate(payload)


def test_automation_acceptance_needs_receipt_but_stays_only_a_proposal() -> None:
    payload = _plan()
    automation = payload["automation_proposals"][0]  # type: ignore[index]
    automation["accepted"] = True
    automation["acceptance_receipt"] = "receipt.automation.accepted"

    plan = QuarterlyPriorityRhythmPlan.model_validate(payload)
    assert plan.automation_proposals[0].status == "proposed"
    assert plan.automation_proposals[0].accepted is True


def test_critical_number_owner_must_own_a_commitment() -> None:
    payload = _plan()
    payload["critical_number"]["owner_id"] = "person.other.owner"  # type: ignore[index]

    with pytest.raises(ValidationError, match="requires a Who What When"):
        QuarterlyPriorityRhythmPlan.model_validate(payload)
