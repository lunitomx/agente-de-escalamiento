from __future__ import annotations

from scripts.qualify_e44_e45 import run_qualification


def test_technical_qualification_is_redacted_and_explicit_about_its_limits() -> None:
    receipt = run_qualification()

    assert receipt["status"] == "pass"
    assert receipt["e44"]["completed_decision_areas"] == [
        "people",
        "strategy",
        "execution",
        "cash",
    ]
    assert receipt["e44"]["confirmed_reusable_learnings"] == 4
    assert receipt["e45"]["simple_case"]["roles"] == ["cash-analyst"]
    assert receipt["e45"]["missing_cash_context"]["blocked"] is True
    assert receipt["e45"]["cross_decision_disagreement"]["disagreements"] == 1
    assert "entrepreneur_pilot" in receipt["not_proved"]
    assert "cycle:" not in str(receipt)
    assert "action:" not in str(receipt)
