from __future__ import annotations

import pytest
from pydantic import ValidationError

from validators.quarterly_review import build_quarterly_review


_PERIOD = "2026-q3"


def _evidence(identifier: str, observed_on: str = "2026-09-07") -> dict[str, str]:
    return {"id": f"evidence.{identifier}", "observed_on": observed_on}


def _review() -> dict[str, object]:
    return {
        "period": _PERIOD,
        "measurement": {
            "period": _PERIOD,
            "measured_on": "2026-09-30",
            "name": "collection days",
            "unit": "days",
            "baseline": 76,
            "current": 68,
            "baseline_evidence": [_evidence("baseline", "2026-07-01")],
            "current_evidence": [_evidence("current", "2026-09-30")],
        },
        "claims": [
            {
                "period": _PERIOD,
                "kind": "fact",
                "statement": "Collections were measured at 68 days.",
                "evidence": [_evidence("current", "2026-09-30")],
            },
            {
                "period": _PERIOD,
                "kind": "hypothesis",
                "statement": "Earlier invoice review may have helped collections.",
                "evidence": [_evidence("invoice-review")],
            },
            {
                "period": _PERIOD,
                "kind": "assumption",
                "statement": "Customer mix remained comparable.",
                "evidence": [_evidence("customer-mix")],
            },
            {
                "period": _PERIOD,
                "kind": "commitment",
                "statement": "Finance will reconcile disputed invoices.",
                "evidence": [_evidence("commitment")],
            },
        ],
        "planned_commitments": [
            {
                "period": _PERIOD,
                "id": "commitment.invoice-review",
                "owner_id": "person.finance.owner",
                "action": "Review receivables",
                "due_on": "2026-09-30",
                "evidence": [_evidence("commitment-plan", "2026-07-01")],
            }
        ],
        "reported_commitments": [
            {
                "period": _PERIOD,
                "id": "commitment.invoice-review",
                "reported_on": "2026-09-30",
                "status": "reported-complete",
                "evidence": [_evidence("invoice-review", "2026-09-30")],
            }
        ],
        "planned_cadences": [
            {
                "period": _PERIOD,
                "cadence": "weekly",
                "purpose": "Review collections",
                "planned_on": "2026-07-01",
                "evidence": [_evidence("weekly-plan", "2026-07-01")],
            }
        ],
        "reported_cadences": [
            {
                "period": _PERIOD,
                "cadence": "weekly",
                "reported_on": "2026-09-30",
                "status": "reported-held",
                "evidence": [_evidence("weekly", "2026-09-30")],
            }
        ],
        "proposed_learning": "Continue measuring collection days before changing priorities.",
        "proposed_decision": "Review the next quarter after reconciled evidence is available.",
    }


def test_review_preserves_claim_types_and_evidence_without_causality() -> None:
    review = build_quarterly_review(_review())

    assert review.measurement is not None
    assert review.measurement.delta == -8
    assert review.measurement.direction == "decreased"
    assert review.claims[1].kind == "hypothesis"
    assert review.claims[1].statement.endswith("helped collections.")
    assert review.claims[1].causal_claim is False
    assert review.www_comparison is not None
    assert review.www_comparison[0].planned_evidence[0].id == "evidence.commitment-plan"
    assert review.www_comparison[0].reported_evidence[0].id == "evidence.invoice-review"
    assert review.cadence_comparison is not None
    assert review.cadence_comparison[0].planned_evidence[0].id == "evidence.weekly-plan"
    assert review.persistence.writes_state is False
    assert review.persistence.closes_commitments is False
    assert review.next_review.status == "proposed"


def test_no_result_yet_requires_all_claims_to_remain_no_result_yet() -> None:
    payload = _review()
    payload["measurement"] = None
    payload["claims"] = [
        {
            "period": _PERIOD,
            "kind": "no-result-yet",
            "statement": "The quarter has not closed and no result is available.",
            "evidence": [_evidence("period-open")],
        }
    ]
    payload["planned_commitments"] = None
    payload["reported_commitments"] = None
    payload["planned_cadences"] = None
    payload["reported_cadences"] = None
    payload["proposed_learning"] = (
        "Wait for measured results before evaluating the quarter."
    )
    payload["proposed_decision"] = (
        "Request the missing result evidence at the next review."
    )

    review = build_quarterly_review(payload)
    assert review.measurement is None
    assert review.www_comparison is None
    assert review.cadence_comparison is None
    assert "measurement" in review.open_questions

    payload["claims"].append(  # type: ignore[index]
        {
            "period": _PERIOD,
            "kind": "fact",
            "statement": "A result was measured.",
            "evidence": [_evidence("false-result")],
        }
    )
    with pytest.raises(ValidationError, match="all claims"):
        build_quarterly_review(payload)


@pytest.mark.parametrize(
    ("path", "value", "match"),
    [
        (("period",), "", "period"),
        (("measurement", "unit"), "", "measurement text"),
        (("measurement", "baseline"), None, "baseline"),
        (("measurement", "current"), None, "current"),
        (("measurement", "current_evidence"), [], "evidence"),
    ],
)
def test_measured_review_fails_closed_for_missing_or_unproven_measurements(
    path: tuple[str, ...], value: object, match: str
) -> None:
    payload = _review()
    target: dict[str, object] = payload
    for part in path[:-1]:
        target = target[part]  # type: ignore[assignment,index]
    target[path[-1]] = value

    with pytest.raises(ValidationError, match=match):
        build_quarterly_review(payload)


@pytest.mark.parametrize(
    "field",
    [
        ("claims", 0, "statement"),
        ("planned_commitments", 0, "action"),
        ("planned_cadences", 0, "purpose"),
        ("proposed_learning",),
        ("proposed_decision",),
    ],
)
def test_all_narrative_fields_reject_causal_language(field: tuple[object, ...]) -> None:
    payload = _review()
    causal_text = "Collections improved because invoices were reviewed."
    if len(field) == 1:
        payload[field[0]] = causal_text  # type: ignore[index]
    else:
        payload[field[0]][field[1]][field[2]] = causal_text  # type: ignore[index]
    with pytest.raises(ValidationError, match="causal language"):
        build_quarterly_review(payload)


def test_review_rejects_inconsistent_comparison_pairs_and_missing_planned_evidence() -> (
    None
):
    payload = _review()
    payload["reported_cadences"] = None
    with pytest.raises(ValidationError, match="both planned and reported cadence"):
        build_quarterly_review(payload)

    payload = _review()
    payload["planned_commitments"][0]["evidence"] = []  # type: ignore[index]
    with pytest.raises(ValidationError, match="evidence"):
        build_quarterly_review(payload)


def test_review_rejects_an_unmarked_causal_claim_boolean() -> None:
    payload = _review()
    payload["claims"][1]["causal_claim"] = True  # type: ignore[index]
    with pytest.raises(ValidationError, match="causal_claim"):
        build_quarterly_review(payload)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("measurement", "measured_on"), "2026-10-01"),
        (("measurement", "current_evidence", 0, "observed_on"), "2026-06-30"),
        (("claims", 0, "period"), "2026-q2"),
        (("reported_commitments", 0, "reported_on"), "2026-10-01"),
        (("reported_cadences", 0, "reported_on"), "2026-06-30"),
    ],
)
def test_review_rejects_dates_or_periods_outside_review_period(
    path: tuple[object, ...], value: object
) -> None:
    payload = _review()
    target: object = payload
    for part in path[:-1]:
        target = target[part]  # type: ignore[index]
    target[path[-1]] = value  # type: ignore[index]
    with pytest.raises(ValidationError, match="period|date"):
        build_quarterly_review(payload)


def test_commitment_due_on_accepts_quarter_boundaries_and_rejects_outside() -> None:
    payload = _review()
    payload["planned_commitments"][0]["due_on"] = "2026-07-01"  # type: ignore[index]
    assert build_quarterly_review(payload).www_comparison is not None

    payload = _review()
    payload["planned_commitments"][0]["due_on"] = "2026-10-01"  # type: ignore[index]
    with pytest.raises(ValidationError, match="due date"):
        build_quarterly_review(payload)
