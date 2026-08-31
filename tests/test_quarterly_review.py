from __future__ import annotations

from copy import deepcopy

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
            "metric_id": "metric.collection-days",
            "unit_id": "unit.days",
            "baseline": 76,
            "current": 68,
            "baseline_evidence": [_evidence("baseline", "2026-07-01")],
            "current_evidence": [_evidence("current", "2026-09-30")],
        },
        "claims": [
            {
                "kind": "fact",
                "period": _PERIOD,
                "reported_on": "2026-09-30",
                "metric_id": "metric.collection-days",
                "value": 68,
                "unit_id": "unit.days",
                "evidence": [_evidence("current", "2026-09-30")],
            },
            {
                "kind": "hypothesis",
                "period": _PERIOD,
                "reported_on": "2026-09-07",
                "model_origin": "model-hypothesis",
                "factor_id": "factor.invoice-timing",
                "metric_id": "metric.collection-days",
                "evidence": [_evidence("invoice-review")],
            },
            {
                "kind": "assumption",
                "period": _PERIOD,
                "reported_on": "2026-09-07",
                "assumption_id": "assumption.customer-mix-comparable",
                "evidence": [_evidence("customer-mix")],
            },
            {
                "kind": "commitment",
                "period": _PERIOD,
                "reported_on": "2026-09-07",
                "commitment_id": "commitment.reconcile-disputes",
                "evidence": [_evidence("commitment")],
            },
        ],
        "planned_commitments": [
            {
                "period": _PERIOD,
                "id": "commitment.invoice-review",
                "owner_id": "person.finance.owner",
                "action_id": "action.review-receivables",
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
                "purpose_id": "purpose.review-collections",
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
        "proposal": {
            "learning_kind": "continue-measurement",
            "decision_kind": "continue-review",
            "subject_id": "metric.collection-days",
        },
    }


def test_review_renders_user_readable_bounded_claims_without_free_narrative() -> None:
    review = build_quarterly_review(_review())

    assert review.measurement is not None
    assert review.measurement.delta == -8
    assert review.rendered_claims == [
        "Observation: metric.collection-days measured 68 unit.days.",
        "Hypothesis to investigate: factor.invoice-timing and metric.collection-days.",
        "Assumption awaiting confirmation: assumption.customer-mix-comparable.",
        "Commitment under review: commitment.reconcile-disputes.",
    ]
    assert (
        review.learning
        == "Learning proposal: continue measuring metric.collection-days."
    )
    assert (
        review.decision
        == "Decision proposal: continue review of metric.collection-days."
    )
    assert review.persistence.writes_state is False
    assert review.persistence.closes_commitments is False
    assert review.persistence.schedules_review is False


@pytest.mark.parametrize(
    ("kind", "injected"),
    [
        ("fact", {"statement": "Sales boosted collections."}),
        ("hypothesis", {"statement": "Invoices explain collections."}),
        ("fact", {"metric_id": "metric.boosted-sales"}),
        ("hypothesis", {"factor_id": "factor.aumentó-cash"}),
    ],
)
def test_claims_reject_free_or_causal_narrative_surfaces(
    kind: str, injected: dict[str, str]
) -> None:
    payload = _review()
    claim = next(item for item in payload["claims"] if item["kind"] == kind)  # type: ignore[index]
    claim.update(injected)
    with pytest.raises(
        ValidationError,
        match="Extra inputs|safe taxonomy",
    ):
        build_quarterly_review(payload)


def test_observation_and_hypothesis_only_accept_structured_shapes() -> None:
    payload = _review()
    payload["claims"][0].pop("value")  # type: ignore[index]
    with pytest.raises(ValidationError, match="value"):
        build_quarterly_review(payload)

    payload = _review()
    payload["claims"][1]["model_origin"] = "company-local"  # type: ignore[index]
    with pytest.raises(ValidationError, match="model-hypothesis"):
        build_quarterly_review(payload)


def test_no_result_yet_is_explicit_and_exclusive_without_measurement() -> None:
    payload = _review()
    payload["measurement"] = None
    payload["claims"] = [
        {
            "kind": "no-result-yet",
            "period": _PERIOD,
            "reported_on": "2026-09-07",
            "reason_id": "period-open",
            "evidence": [_evidence("period-open")],
        }
    ]
    payload["planned_commitments"] = None
    payload["reported_commitments"] = None
    payload["planned_cadences"] = None
    payload["reported_cadences"] = None
    review = build_quarterly_review(payload)
    assert review.rendered_claims == ["No result yet: period-open."]
    assert review.open_questions == ["measurement", "who-what-when", "cadence"]

    payload["claims"].append(deepcopy(_review()["claims"][0]))  # type: ignore[index]
    with pytest.raises(ValidationError, match="all claims"):
        build_quarterly_review(payload)


@pytest.mark.parametrize(
    ("path", "value", "match"),
    [
        (("period",), "", "period"),
        (("measurement", "metric_id"), "metric.boosted", "safe taxonomy"),
        (("measurement", "baseline"), None, "baseline"),
        (("measurement", "current_evidence"), [], "evidence"),
        (("proposal", "subject_id"), "cash explains sales", "proposal subject"),
    ],
)
def test_review_fails_closed_for_missing_or_unsafe_required_fields(
    path: tuple[str, ...], value: object, match: str
) -> None:
    payload = _review()
    target: object = payload
    for part in path[:-1]:
        target = target[part]  # type: ignore[index]
    target[path[-1]] = value  # type: ignore[index]
    with pytest.raises(ValidationError, match=match):
        build_quarterly_review(payload)


def test_comparisons_preserve_evidence_on_both_sides() -> None:
    review = build_quarterly_review(_review())
    assert review.www_comparison is not None
    assert review.www_comparison[0].planned_evidence[0].id == "evidence.commitment-plan"
    assert review.www_comparison[0].reported_evidence[0].id == "evidence.invoice-review"
    assert review.cadence_comparison is not None
    assert review.cadence_comparison[0].planned_evidence[0].id == "evidence.weekly-plan"


@pytest.mark.parametrize(
    ("path", "value", "match"),
    [
        (
            ("measurement", "current_evidence", 0, "observed_on"),
            "2026-10-01",
            "measurement",
        ),
        (("claims", 0, "reported_on"), "2026-09-29", "report"),
        (
            ("planned_commitments", 0, "evidence", 0, "observed_on"),
            "2026-10-01",
            "commitment",
        ),
        (
            ("reported_commitments", 0, "evidence", 0, "observed_on"),
            "2026-10-01",
            "report",
        ),
        (
            ("planned_cadences", 0, "evidence", 0, "observed_on"),
            "2026-10-01",
            "cadence",
        ),
        (
            ("reported_cadences", 0, "evidence", 0, "observed_on"),
            "2026-10-01",
            "report",
        ),
    ],
)
def test_review_rejects_evidence_after_its_event(
    path: tuple[object, ...], value: object, match: str
) -> None:
    payload = _review()
    target: object = payload
    for part in path[:-1]:
        target = target[part]  # type: ignore[index]
    target[path[-1]] = value  # type: ignore[index]
    with pytest.raises(ValidationError, match=match):
        build_quarterly_review(payload)


def test_baseline_must_precede_current_and_due_date_stays_inclusive() -> None:
    payload = _review()
    payload["measurement"]["current_evidence"][0]["observed_on"] = "2026-09-29"  # type: ignore[index]
    payload["measurement"]["baseline_evidence"][0]["observed_on"] = "2026-09-30"  # type: ignore[index]
    with pytest.raises(ValidationError, match="baseline evidence"):
        build_quarterly_review(payload)

    payload = _review()
    payload["planned_commitments"][0]["due_on"] = "2026-07-01"  # type: ignore[index]
    assert build_quarterly_review(payload).www_comparison is not None
    payload["planned_commitments"][0]["due_on"] = "2026-10-01"  # type: ignore[index]
    with pytest.raises(ValidationError, match="due date"):
        build_quarterly_review(payload)


def test_arbitrary_multiline_and_backslash_fields_are_not_in_the_schema() -> None:
    payload = _review()
    payload["proposal"]["statement"] = "boosted\\nrevenue"  # type: ignore[index]
    with pytest.raises(ValidationError, match="Extra inputs"):
        build_quarterly_review(payload)


@pytest.mark.parametrize(
    "identifier",
    [
        "metric.causes-cash",
        "metric.improves-cash",
        "metric.growth",
        "metric.raises-cash",
        "metric.drives-cash",
        "metric.boosts-cash",
        "metric.aumenta-cash",
        "metric.mejora-cash",
        "metric.safe-looking-unknown",
    ],
)
def test_rendered_identifiers_must_be_allowlisted_not_merely_lexical(
    identifier: str,
) -> None:
    payload = _review()
    payload["claims"][0]["metric_id"] = identifier  # type: ignore[index]
    with pytest.raises(ValidationError, match="safe taxonomy"):
        build_quarterly_review(payload)


def test_allowed_neutral_taxonomy_identifiers_render() -> None:
    review = build_quarterly_review(_review())
    assert (
        review.rendered_claims[0]
        == "Observation: metric.collection-days measured 68 unit.days."
    )
    assert review.rendered_claims[1] == (
        "Hypothesis to investigate: factor.invoice-timing and metric.collection-days."
    )
