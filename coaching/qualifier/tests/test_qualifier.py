"""Tests for the coaching.qualifier module."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent.parent))

import pytest

from coaching.qualifier import qualify
from coaching.qualifier.cases import ALL_CASES
from coaching.qualifier.runner import run_case


@pytest.mark.parametrize("case", ALL_CASES, ids=lambda c: c.case_id)
def test_case_outcome(case):
    """Each qualification case must reach its expected responder action."""
    outcome = run_case(case.decision, case.package)
    actual = outcome.get("responder", {}).get("artifacts", {}).get("action")
    assert actual == case.expected_action, (
        f"{case.case_id}: expected {case.expected_action}, got {actual}"
    )


def test_qualify_reports_all_cases():
    result = qualify({})
    assert result["artifacts"]["passed"] + result["artifacts"]["failed"] == len(
        ALL_CASES
    )
    assert result["artifacts"]["failed"] == 0
    assert "Calificación del ciclo de coaching confiable" in result["output"]
