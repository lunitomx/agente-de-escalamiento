"""
Tests for coaching.pulse module.

TDD — RED phase (T1): trend mapping and basic return contract.
"""
import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# T1 — Basic return contract + trend mapping
# ---------------------------------------------------------------------------

def test_run_returns_dict():
    from coaching.pulse import run
    result = run({"answers": {"people": 1, "strategy": 0, "execution": -1, "cash": 0, "overall": 0}})
    assert isinstance(result, dict)
    assert result.get("success") is True


def test_run_includes_output_artifacts_errors():
    from coaching.pulse import run
    result = run({"answers": {"people": 1, "strategy": 0, "execution": -1, "cash": 0, "overall": 0}})
    assert "output" in result
    assert "artifacts" in result
    assert "errors" in result


def test_run_includes_trends():
    from coaching.pulse import run
    result = run({"answers": {"people": 1, "strategy": 0, "execution": -1, "cash": 0, "overall": 0}})
    assert "trends" in result.get("artifacts", {})


def test_trend_improving():
    from coaching.pulse import run
    result = run({"answers": {"people": 1, "strategy": 1, "execution": 1, "cash": 1, "overall": 1}})
    trends = result["artifacts"]["trends"]
    assert all(v == "improving" for v in trends.values())


def test_trend_stalling():
    from coaching.pulse import run
    result = run({"answers": {"people": 0, "strategy": 0, "execution": 0, "cash": 0, "overall": 0}})
    trends = result["artifacts"]["trends"]
    assert all(v == "stalling" for v in trends.values())


def test_trend_regressing():
    from coaching.pulse import run
    result = run({"answers": {"people": -1, "strategy": -1, "execution": -1, "cash": -1, "overall": -1}})
    trends = result["artifacts"]["trends"]
    assert all(v == "regressing" for v in trends.values())


def test_trend_all_decisions_present():
    from coaching.pulse import run
    result = run({"answers": {"people": 1, "strategy": 0, "execution": -1, "cash": 0, "overall": 0}})
    trends = result["artifacts"]["trends"]
    assert set(trends.keys()) == {"people", "strategy", "execution", "cash", "overall"}


# ---------------------------------------------------------------------------
# T2 — History persistence
# ---------------------------------------------------------------------------

def test_history_created_on_first_run(tmp_path):
    import yaml
    base = tmp_path
    history = base / ".scaleup" / "my-company" / "pulse-history.yaml"
    result = run_with_base({"answers": {"people": 1, "strategy": 0, "execution": -1, "cash": 0, "overall": 0}}, base)
    assert history.exists()
    data = yaml.safe_load(history.read_text())
    assert "pulses" in data
    assert len(data["pulses"]) == 1


def test_history_appended_on_second_run(tmp_path):
    import yaml
    base = tmp_path
    answers = {"people": 0, "strategy": 0, "execution": 0, "cash": 0, "overall": 0}
    run_with_base({"answers": answers}, base)
    run_with_base({"answers": answers}, base)
    history = base / ".scaleup" / "my-company" / "pulse-history.yaml"
    data = yaml.safe_load(history.read_text())
    assert len(data["pulses"]) == 2


def test_history_entry_has_required_keys(tmp_path):
    import yaml
    base = tmp_path
    run_with_base({"answers": {"people": 1, "strategy": 0, "execution": -1, "cash": 0, "overall": 0}}, base)
    history = base / ".scaleup" / "my-company" / "pulse-history.yaml"
    data = yaml.safe_load(history.read_text())
    entry = data["pulses"][0]
    for key in ["date", "answers", "trends", "course_corrections"]:
        assert key in entry, f"Missing key: {key}"


def test_prior_pulse_date_null_on_first_run(tmp_path):
    base = tmp_path
    result = run_with_base({"answers": {"people": 0, "strategy": 0, "execution": 0, "cash": 0, "overall": 0}}, base)
    assert result["artifacts"]["prior_pulse_date"] is None


def test_prior_pulse_date_populated_on_second_run(tmp_path):
    import yaml
    base = tmp_path
    answers = {"people": 0, "strategy": 0, "execution": 0, "cash": 0, "overall": 0}
    first = run_with_base({"answers": answers}, base)
    second = run_with_base({"answers": answers}, base)
    first_date = first["artifacts"]["pulse_date"]
    assert second["artifacts"]["prior_pulse_date"] == first_date


def test_first_run_no_history_file(tmp_path):
    base = tmp_path
    result = run_with_base({"answers": {"people": 0, "strategy": 0, "execution": 0, "cash": 0, "overall": 0}}, base)
    assert result["success"] is True
    assert result["errors"] == []


def test_invalid_answer_value_returns_error(tmp_path):
    base = tmp_path
    result = run_with_base({"answers": {"people": 2, "strategy": 0, "execution": 0, "cash": 0, "overall": 0}}, base)
    assert len(result["errors"]) > 0


# ---------------------------------------------------------------------------
# T3 — Course corrections + output formatting
# ---------------------------------------------------------------------------

def test_course_corrections_for_regressing(tmp_path):
    base = tmp_path
    result = run_with_base({"answers": {"people": 1, "strategy": 0, "execution": -1, "cash": 0, "overall": 0}}, base)
    corrections = result["artifacts"]["course_corrections"]
    assert any("execution" in c.lower() or "Execution" in c for c in corrections)


def test_no_course_corrections_when_none_regressing(tmp_path):
    base = tmp_path
    result = run_with_base({"answers": {"people": 1, "strategy": 1, "execution": 1, "cash": 1, "overall": 1}}, base)
    assert result["artifacts"]["course_corrections"] == []


def test_output_contains_pulse_header(tmp_path):
    base = tmp_path
    result = run_with_base({"answers": {"people": 1, "strategy": 0, "execution": -1, "cash": 0, "overall": 0}}, base)
    assert "## Pulse —" in result["output"]


def test_output_contains_decision_table(tmp_path):
    base = tmp_path
    result = run_with_base({"answers": {"people": 1, "strategy": 0, "execution": -1, "cash": 0, "overall": 0}}, base)
    output = result["output"]
    for label in ["People", "Strategy", "Execution", "Cash", "Overall"]:
        assert label in output


def test_output_contains_course_corrections_section(tmp_path):
    base = tmp_path
    result = run_with_base({"answers": {"people": 1, "strategy": 0, "execution": -1, "cash": 0, "overall": 0}}, base)
    assert "Course corrections" in result["output"] or "course corrections" in result["output"].lower()


def test_artifacts_history_path_present(tmp_path):
    base = tmp_path
    result = run_with_base({"answers": {"people": 0, "strategy": 0, "execution": 0, "cash": 0, "overall": 0}}, base)
    assert "history_path" in result["artifacts"]


def test_artifacts_pulse_date_present(tmp_path):
    base = tmp_path
    result = run_with_base({"answers": {"people": 0, "strategy": 0, "execution": 0, "cash": 0, "overall": 0}}, base)
    assert "pulse_date" in result["artifacts"]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def run_with_base(context: dict, base: Path) -> dict:
    """Run pulse with base_path override for isolation."""
    from coaching.pulse import run
    ctx = {**context, "base_path": str(base)}
    return run(ctx)
