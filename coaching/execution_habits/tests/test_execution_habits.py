"""Tests for the Execution Habits engine (S50.4.3)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from coaching.execution_habits import run  # noqa: E402
from coaching.execution_habits.engine import (  # noqa: E402
    HABITS,
    HabitScore,
    ExecutionAssessment,
    score,
    validate,
)
from coaching.execution_habits.formatter import render_markdown  # noqa: E402


def test_load_on_fresh_company_has_empty_assessment(tmp_path):
    result = run({"action": "load", "base_path": str(tmp_path)})
    assert result["errors"] == []
    assert len(result["artifacts"]["state"]["scores"]) == len(HABITS)
    assert result["artifacts"]["resuming"] is False
    assert result["artifacts"]["score"]["completeness"] == 0


def test_save_and_load_roundtrip(tmp_path):
    base = str(tmp_path)
    data = {
        "scores": [{"habit_id": h["id"], "score": 3, "notes": "ok"} for h in HABITS]
    }
    save_result = run({"action": "save", "base_path": base, "data": data})
    assert save_result["errors"] == []
    assert save_result["artifacts"]["score"]["total"] == 3 * len(HABITS)

    load_result = run({"action": "load", "base_path": base})
    assert load_result["artifacts"]["resuming"] is True
    assert load_result["artifacts"]["score"]["average"] == 3.0


def test_validation_flags_missing_scores():
    assessment = ExecutionAssessment()
    errors = validate(assessment)
    assert len(errors) == len(HABITS)


def test_validation_rejects_out_of_range_score():
    scores = [HabitScore(habit_id=h["id"], score=7) for h in HABITS]
    assessment = ExecutionAssessment(scores=scores)
    errors = validate(assessment)
    assert any("entre" in e for e in errors)


def test_score_zero_for_empty_assessment():
    result = score(ExecutionAssessment())
    assert result["total"] == 0
    assert result["completeness"] == 0
    assert result["top_weaknesses"] == []


def test_score_identifies_top_weaknesses():
    scores = [
        HabitScore(habit_id=HABITS[0]["id"], score=5),
        HabitScore(habit_id=HABITS[1]["id"], score=1),
        HabitScore(habit_id=HABITS[2]["id"], score=2),
        *[HabitScore(habit_id=h["id"], score=4) for h in HABITS[3:]],
    ]
    assessment = ExecutionAssessment(scores=scores)
    result = score(assessment)
    assert result["total"] == 5 + 1 + 2 + 4 * 7
    assert result["top_weaknesses"][0]["habit_id"] == HABITS[1]["id"]
    assert result["top_weaknesses"][1]["habit_id"] == HABITS[2]["id"]


def test_export_writes_markdown_to_disk(tmp_path):
    base = str(tmp_path)
    data = {
        "scores": [{"habit_id": h["id"], "score": 4, "notes": "bien"} for h in HABITS]
    }
    run({"action": "save", "base_path": base, "data": data})
    result = run(
        {
            "action": "export",
            "base_path": base,
            "company_name": "Acme",
            "action_plan": ["Mejorar daily huddles"],
        }
    )
    md_path = Path(result["artifacts"]["export_path"])
    assert md_path.exists()
    text = md_path.read_text(encoding="utf-8")
    assert "Acme" in text
    assert "Mejorar daily huddles" in text


def test_render_markdown_shows_pending_marker():
    assessment = ExecutionAssessment()
    markdown = render_markdown(assessment)
    assert "[PENDIENTE]" in markdown


def test_unknown_action_is_rejected(tmp_path):
    result = run({"action": "teleport", "base_path": str(tmp_path)})
    assert result["errors"] != []


def test_partial_scores_compute_completeness():
    scores = [
        HabitScore(habit_id=HABITS[0]["id"], score=5),
        HabitScore(habit_id=HABITS[1]["id"], score=4),
    ]
    assessment = ExecutionAssessment(scores=scores)
    result = score(assessment)
    assert result["completeness"] == 20  # 2 of 10 habits scored
