"""S68.1 evaluates routing activation with synthetic, non-identifying cases."""

from __future__ import annotations

from pathlib import Path

import pytest

from validators.activation_evals import (
    ActivationEvalError,
    ActivationObservation,
    evaluate_activation_suite,
    load_activation_suite,
    validate_activation_suite,
)
from validators.procedure_compiler import MVP_PROCEDURE_IDS


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "tests" / "fixtures" / "e68" / "activation_cases.json"


def _perfect_observations() -> tuple[ActivationObservation, ...]:
    suite = load_activation_suite(SUITE)
    return tuple(
        ActivationObservation(
            case_id=case.case_id,
            action=case.expected_action,
            resolved_intent=case.expected_intent,
        )
        for case in suite.cases
    )


def test_activation_dataset_covers_all_mvp_procedures_and_case_types() -> None:
    suite = load_activation_suite(SUITE)

    assert validate_activation_suite(suite) == ()
    assert {case.case_type for case in suite.cases} == {
        "should_trigger",
        "should_not_trigger",
        "ambiguous",
        "sequence",
    }
    assert {
        case.expected_procedure_id
        for case in suite.cases
        if case.expected_procedure_id is not None
    } == set(MVP_PROCEDURE_IDS)
    assert all("@" not in case.user_message for case in suite.cases)


def test_perfect_observations_score_one_without_claiming_model_quality() -> None:
    result = evaluate_activation_suite(
        load_activation_suite(SUITE), _perfect_observations()
    )

    assert result.precision == 1.0
    assert result.recall == 1.0
    assert result.true_negatives == 2
    assert all(case.passed for case in result.cases)


def test_wrong_routing_counts_as_both_false_positive_and_false_negative() -> None:
    observations = list(_perfect_observations())
    observations[2] = ActivationObservation(
        case_id=observations[2].case_id,
        action="route",
        resolved_intent="build-leader-oppp",
    )

    result = evaluate_activation_suite(load_activation_suite(SUITE), observations)

    assert result.true_positives == 6
    assert result.false_positives == 1
    assert result.false_negatives == 1
    assert result.precision < 0.9
    assert result.recall < 0.9


def test_missing_or_extra_observations_fail_closed() -> None:
    observations = _perfect_observations()
    with pytest.raises(ActivationEvalError, match="observations_missing"):
        evaluate_activation_suite(load_activation_suite(SUITE), observations[:-1])

    with pytest.raises(ActivationEvalError, match="observations_unknown"):
        evaluate_activation_suite(
            load_activation_suite(SUITE),
            (*observations, ActivationObservation(case_id="ACT-999", action="clarify")),
        )
