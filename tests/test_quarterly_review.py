from __future__ import annotations

import pytest
from pydantic import ValidationError

from validators.quarterly_review import build_quarterly_review


def _evidence(identifier: str) -> str:
    return f"evidence.{identifier}"


def _review() -> dict[str, object]:
    return {
        "period": "2026-q3",
        "measurement": {
            "name": "collection days",
            "unit": "days",
            "baseline": 76,
            "current": 68,
            "baseline_evidence_ids": [_evidence("baseline")],
            "current_evidence_ids": [_evidence("current")],
        },
        "claims": [
            {
                "kind": "fact",
                "statement": "Collections were measured at 68 days.",
                "evidence_ids": [_evidence("current")],
            },
            {
                "kind": "hypothesis",
                "statement": "Earlier invoice review may have helped collections.",
                "evidence_ids": [_evidence("invoice-review")],
            },
            {
                "kind": "assumption",
                "statement": "Customer mix remained comparable.",
                "evidence_ids": [_evidence("customer-mix")],
            },
            {
                "kind": "commitment",
                "statement": "Finance will reconcile disputed invoices.",
                "evidence_ids": [_evidence("commitment")],
            },
        ],
        "planned_commitments": [
            {
                "id": "commitment.invoice-review",
                "owner_id": "person.finance.owner",
                "action": "Review receivables",
                "due_on": "2026-09-07",
            }
        ],
        "reported_commitments": [
            {
                "id": "commitment.invoice-review",
                "status": "reported-complete",
                "evidence_ids": [_evidence("invoice-review")],
            }
        ],
        "planned_cadences": [{"cadence": "weekly", "purpose": "Review collections"}],
        "reported_cadences": [
            {
                "cadence": "weekly",
                "status": "reported-held",
                "evidence_ids": [_evidence("weekly")],
            }
        ],
        "proposed_learning": "Continue measuring collection days before changing priorities.",
        "proposed_decision": "Review the next quarter after reconciled evidence is available.",
    }


def test_review_preserves_claim_types_and_never_turns_hypothesis_into_causality() -> (
    None
):
    review = build_quarterly_review(_review())

    assert review.measurement is not None
    assert review.measurement.delta == -8
    assert review.measurement.direction == "decreased"
    assert review.claims[1].kind == "hypothesis"
    assert review.claims[1].causal_claim is False
    assert review.www_comparison is not None
    assert review.cadence_comparison is not None
    assert review.persistence.writes_state is False
    assert review.persistence.closes_commitments is False
    assert review.next_review.status == "proposed"


def test_no_result_yet_is_explicit_and_has_no_measurement_or_causal_learning() -> None:
    payload = _review()
    payload["measurement"] = None
    payload["claims"] = [
        {
            "kind": "no-result-yet",
            "statement": "The quarter has not closed and no result is available.",
            "evidence_ids": [_evidence("period-open")],
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
    assert all(claim.causal_claim is False for claim in review.claims)


@pytest.mark.parametrize(
    ("path", "value", "match"),
    [
        (("period",), "", "period"),
        (("measurement", "unit"), "", "unit"),
        (("measurement", "baseline"), None, "baseline"),
        (("measurement", "current"), None, "current"),
        (("measurement", "current_evidence_ids"), [], "evidence"),
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


def test_review_rejects_inconsistent_comparison_pairs_and_unsupported_commitments() -> (
    None
):
    payload = _review()
    payload["reported_cadences"] = None
    with pytest.raises(ValidationError, match="both planned and reported cadence"):
        build_quarterly_review(payload)

    payload = _review()
    reported = payload["reported_commitments"]  # type: ignore[index]
    reported[0]["evidence_ids"] = []  # type: ignore[index]
    with pytest.raises(ValidationError, match="evidence"):
        build_quarterly_review(payload)


def test_review_rejects_an_unmarked_causal_claim() -> None:
    payload = _review()
    claims = payload["claims"]  # type: ignore[index]
    claims[1]["causal_claim"] = True  # type: ignore[index]

    with pytest.raises(ValidationError, match="causal"):
        build_quarterly_review(payload)
