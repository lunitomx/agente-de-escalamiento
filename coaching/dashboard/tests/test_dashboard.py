"""
Tests for coaching.dashboard — Progress Dashboard.

Covers T1 (skeleton), T2 (current scores), T3 (pulse history + wins + attention).
"""

import yaml
from pathlib import Path


# ---------------------------------------------------------------------------
# T1: Skeleton tests
# ---------------------------------------------------------------------------


def test_run_returns_dict():
    from coaching.dashboard import run

    result = run({})
    assert isinstance(result, dict)
    assert result.get("success") is True


def test_output_is_string():
    from coaching.dashboard import run

    result = run({})
    assert isinstance(result["output"], str)
    assert len(result["output"]) > 0


def test_output_has_current_scores_section():
    from coaching.dashboard import run

    result = run({})
    assert "## Current Scores" in result["output"]


def test_output_has_pulse_history_section():
    from coaching.dashboard import run

    result = run({})
    assert "## Pulse History" in result["output"]


def test_output_has_wins_section():
    from coaching.dashboard import run

    result = run({})
    assert "## Wins" in result["output"]


def test_output_has_attention_section():
    from coaching.dashboard import run

    result = run({})
    assert "## Attention Areas" in result["output"]


def test_result_has_artifacts_key():
    from coaching.dashboard import run

    result = run({})
    assert "artifacts" in result


def test_result_has_errors_key():
    from coaching.dashboard import run

    result = run({})
    assert "errors" in result
    assert isinstance(result["errors"], list)


# ---------------------------------------------------------------------------
# T2: Current Scores section tests
# ---------------------------------------------------------------------------


def test_scores_table_has_header(tmp_path):
    """When scores > 0 exist, table has | Decision header."""
    profile_dir = tmp_path / ".escala" / "agent" / "memory"
    profile_dir.mkdir(parents=True)
    profile = {
        "company": {"name": "TestCo"},
        "scores": {"people": 3, "strategy": 2, "execution": 2, "cash": 3},
    }
    (profile_dir / "company-profile.yaml").write_text(yaml.dump(profile))

    from coaching.dashboard import run

    result = run({"base_path": str(tmp_path)})
    assert "| Decision" in result["output"]
    assert "| Score" in result["output"]


def test_scores_table_level_mapping(tmp_path):
    """Score 3 maps to Emergente, score 4 maps to Establecido."""
    profile_dir = tmp_path / ".escala" / "agent" / "memory"
    profile_dir.mkdir(parents=True)
    profile = {
        "scores": {"people": 3, "strategy": 4, "execution": 2, "cash": 1},
    }
    (profile_dir / "company-profile.yaml").write_text(yaml.dump(profile))

    from coaching.dashboard import run

    result = run({"base_path": str(tmp_path)})
    assert "Emergente" in result["output"]
    assert "Establecido" in result["output"]
    assert "Ad hoc" in result["output"]
    assert "No iniciado" in result["output"]


def test_scores_graceful_missing_file():
    """Missing profile file → placeholder message in output."""
    from coaching.dashboard import run

    result = run({"base_path": "/nonexistent/path/xyz"})
    assert result["success"] is True
    assert "## Current Scores" in result["output"]
    assert "No diagnosis yet" in result["output"]


def test_scores_all_zeros_treated_as_no_diagnosis(tmp_path):
    """All-zero scores (not yet diagnosed) → show placeholder, not empty table."""
    profile_dir = tmp_path / ".escala" / "agent" / "memory"
    profile_dir.mkdir(parents=True)
    profile = {
        "scores": {"people": 0, "strategy": 0, "execution": 0, "cash": 0},
    }
    (profile_dir / "company-profile.yaml").write_text(yaml.dump(profile))

    from coaching.dashboard import run

    result = run({"base_path": str(tmp_path)})
    assert "No diagnosis yet" in result["output"]


def test_scores_in_artifacts(tmp_path):
    """Scores are returned in artifacts."""
    profile_dir = tmp_path / ".escala" / "agent" / "memory"
    profile_dir.mkdir(parents=True)
    profile = {
        "scores": {"people": 3, "strategy": 2, "execution": 2, "cash": 3},
    }
    (profile_dir / "company-profile.yaml").write_text(yaml.dump(profile))

    from coaching.dashboard import run

    result = run({"base_path": str(tmp_path)})
    assert "scores" in result["artifacts"]
    assert result["artifacts"]["scores"]["people"] == 3


# ---------------------------------------------------------------------------
# T3: Pulse History + Wins + Attention Areas tests
# ---------------------------------------------------------------------------


def _make_pulse_dir(tmp_path: Path) -> Path:
    """Create .escala/my-company/ dir structure under tmp_path."""
    pulse_dir = tmp_path / ".escala" / "my-company"
    pulse_dir.mkdir(parents=True)
    return pulse_dir


def test_pulse_history_table_structure(tmp_path):
    """Pulse history table has | Date header."""
    pulse_dir = _make_pulse_dir(tmp_path)
    history = {
        "pulses": [
            {
                "date": "2026-05-06",
                "answers": {
                    "people": 1,
                    "strategy": 0,
                    "execution": -1,
                    "cash": 0,
                    "overall": 0,
                },
                "trends": {
                    "people": "improving",
                    "strategy": "stalling",
                    "execution": "regressing",
                    "cash": "stalling",
                    "overall": "stalling",
                },
                "course_corrections": ["Execution regressing → run /escala-execution"],
            }
        ]
    }
    (pulse_dir / "pulse-history.yaml").write_text(yaml.dump(history))

    from coaching.dashboard import run

    result = run({"base_path": str(tmp_path)})
    assert "| Date" in result["output"]
    assert "2026-05-06" in result["output"]


def test_pulse_history_reverse_chronological(tmp_path):
    """Most-recent pulse appears before older ones in table."""
    pulse_dir = _make_pulse_dir(tmp_path)
    history = {
        "pulses": [
            {
                "date": "2026-01-01",
                "answers": {
                    "people": 0,
                    "strategy": 0,
                    "execution": 0,
                    "cash": 0,
                    "overall": 0,
                },
                "trends": {
                    "people": "stalling",
                    "strategy": "stalling",
                    "execution": "stalling",
                    "cash": "stalling",
                    "overall": "stalling",
                },
                "course_corrections": [],
            },
            {
                "date": "2026-05-06",
                "answers": {
                    "people": 1,
                    "strategy": 0,
                    "execution": -1,
                    "cash": 0,
                    "overall": 0,
                },
                "trends": {
                    "people": "improving",
                    "strategy": "stalling",
                    "execution": "regressing",
                    "cash": "stalling",
                    "overall": "stalling",
                },
                "course_corrections": [],
            },
        ]
    }
    (pulse_dir / "pulse-history.yaml").write_text(yaml.dump(history))

    from coaching.dashboard import run

    result = run({"base_path": str(tmp_path)})
    output = result["output"]
    # 2026-05-06 should appear before 2026-01-01 in the output
    assert output.index("2026-05-06") < output.index("2026-01-01")


def test_wins_detecting_improving(tmp_path):
    """Decision with improving trend in last pulse appears in Wins section."""
    pulse_dir = _make_pulse_dir(tmp_path)
    history = {
        "pulses": [
            {
                "date": "2026-05-06",
                "answers": {
                    "people": 1,
                    "strategy": 0,
                    "execution": -1,
                    "cash": 0,
                    "overall": 0,
                },
                "trends": {
                    "people": "improving",
                    "strategy": "stalling",
                    "execution": "regressing",
                    "cash": "stalling",
                    "overall": "stalling",
                },
                "course_corrections": [],
            }
        ]
    }
    (pulse_dir / "pulse-history.yaml").write_text(yaml.dump(history))

    from coaching.dashboard import run

    result = run({"base_path": str(tmp_path)})

    # Find wins section
    output = result["output"]
    wins_start = output.index("## Wins")
    attention_start = output.index("## Attention Areas")
    wins_section = output[wins_start:attention_start]
    assert "People" in wins_section


def test_attention_regressing(tmp_path):
    """Decision with regressing trend in last pulse appears in Attention Areas."""
    pulse_dir = _make_pulse_dir(tmp_path)
    history = {
        "pulses": [
            {
                "date": "2026-05-06",
                "answers": {
                    "people": 1,
                    "strategy": 0,
                    "execution": -1,
                    "cash": 0,
                    "overall": 0,
                },
                "trends": {
                    "people": "improving",
                    "strategy": "stalling",
                    "execution": "regressing",
                    "cash": "stalling",
                    "overall": "stalling",
                },
                "course_corrections": [],
            }
        ]
    }
    (pulse_dir / "pulse-history.yaml").write_text(yaml.dump(history))

    from coaching.dashboard import run

    result = run({"base_path": str(tmp_path)})

    output = result["output"]
    attention_start = output.index("## Attention Areas")
    attention_section = output[attention_start:]
    assert "Execution" in attention_section
    assert "regressing" in attention_section


def test_attention_stalling_two_consecutive(tmp_path):
    """Stalling in 2 consecutive pulses → flagged in Attention Areas."""
    pulse_dir = _make_pulse_dir(tmp_path)
    history = {
        "pulses": [
            {
                "date": "2026-04-01",
                "answers": {
                    "people": 0,
                    "strategy": 1,
                    "execution": 0,
                    "cash": 0,
                    "overall": 0,
                },
                "trends": {
                    "people": "stalling",
                    "strategy": "improving",
                    "execution": "stalling",
                    "cash": "stalling",
                    "overall": "stalling",
                },
                "course_corrections": [],
            },
            {
                "date": "2026-05-06",
                "answers": {
                    "people": 0,
                    "strategy": 0,
                    "execution": 0,
                    "cash": 0,
                    "overall": 0,
                },
                "trends": {
                    "people": "stalling",
                    "strategy": "stalling",
                    "execution": "stalling",
                    "cash": "stalling",
                    "overall": "stalling",
                },
                "course_corrections": [],
            },
        ]
    }
    (pulse_dir / "pulse-history.yaml").write_text(yaml.dump(history))

    from coaching.dashboard import run

    result = run({"base_path": str(tmp_path)})

    output = result["output"]
    attention_start = output.index("## Attention Areas")
    attention_section = output[attention_start:]
    # People stalled in both pulses → flagged
    assert "People" in attention_section
    assert "stalling" in attention_section


def test_attention_stalling_one_pulse_no_flag(tmp_path):
    """Single stalling pulse → NOT flagged (need 2 consecutive)."""
    pulse_dir = _make_pulse_dir(tmp_path)
    history = {
        "pulses": [
            {
                "date": "2026-05-06",
                "answers": {
                    "people": 0,
                    "strategy": 0,
                    "execution": 0,
                    "cash": 0,
                    "overall": 0,
                },
                "trends": {
                    "people": "stalling",
                    "strategy": "stalling",
                    "execution": "stalling",
                    "cash": "stalling",
                    "overall": "stalling",
                },
                "course_corrections": [],
            }
        ]
    }
    (pulse_dir / "pulse-history.yaml").write_text(yaml.dump(history))

    from coaching.dashboard import run

    result = run({"base_path": str(tmp_path)})

    output = result["output"]
    attention_start = output.index("## Attention Areas")
    attention_section = output[attention_start:]
    # No regressing, no 2-consecutive stalling → "No attention areas detected"
    assert "No attention areas detected" in attention_section


def test_no_pulse_history_graceful():
    """Missing pulse file → placeholder in all 3 pulse-related sections."""
    from coaching.dashboard import run

    result = run({"base_path": "/nonexistent/path/xyz"})
    assert result["success"] is True
    output = result["output"]
    assert "No pulse data" in output
    # Should appear at least once (shared placeholder in all 3 sections)
    assert output.count("No pulse data") >= 1


def test_scores_null_treated_as_no_diagnosis(tmp_path):
    """scores: null in YAML → no crash, shows placeholder."""
    profile_dir = tmp_path / ".escala" / "agent" / "memory"
    profile_dir.mkdir(parents=True)
    (profile_dir / "company-profile.yaml").write_text("scores: null\n")

    from coaching.dashboard import run

    result = run({"base_path": str(tmp_path)})
    assert result["success"] is True
    assert "No diagnosis yet" in result["output"]


def test_pulses_null_graceful(tmp_path):
    """pulses: null in YAML → no crash, shows placeholder in pulse sections."""
    pulse_dir = tmp_path / ".escala" / "my-company"
    pulse_dir.mkdir(parents=True)
    (pulse_dir / "pulse-history.yaml").write_text("pulses: null\n")

    from coaching.dashboard import run

    result = run({"base_path": str(tmp_path)})
    assert result["success"] is True
    assert "No pulse data" in result["output"]


def test_pulse_count_in_artifacts(tmp_path):
    """artifacts["pulse_count"] equals number of pulse entries."""
    pulse_dir = _make_pulse_dir(tmp_path)
    history = {
        "pulses": [
            {
                "date": "2026-04-01",
                "answers": {
                    "people": 1,
                    "strategy": 0,
                    "execution": 0,
                    "cash": 0,
                    "overall": 0,
                },
                "trends": {
                    "people": "improving",
                    "strategy": "stalling",
                    "execution": "stalling",
                    "cash": "stalling",
                    "overall": "stalling",
                },
                "course_corrections": [],
            },
            {
                "date": "2026-05-06",
                "answers": {
                    "people": 0,
                    "strategy": 1,
                    "execution": -1,
                    "cash": 0,
                    "overall": 0,
                },
                "trends": {
                    "people": "stalling",
                    "strategy": "improving",
                    "execution": "regressing",
                    "cash": "stalling",
                    "overall": "stalling",
                },
                "course_corrections": [],
            },
        ]
    }
    (pulse_dir / "pulse-history.yaml").write_text(yaml.dump(history))

    from coaching.dashboard import run

    result = run({"base_path": str(tmp_path)})
    assert result["artifacts"]["pulse_count"] == 2
