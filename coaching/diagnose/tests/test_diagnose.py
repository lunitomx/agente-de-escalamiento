"""Tests for diagnose module."""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent.parent))
from coaching.diagnose import DIAGNOSE_QUESTIONS, SCORE_LABELS, calculate_score, detect_priority


class TestCalculateScore:
    def test_all_max(self):
        assert calculate_score([5, 5, 5, 5, 5]) == 5

    def test_all_min(self):
        assert calculate_score([1, 1, 1, 1, 1]) == 1

    def test_mixed(self):
        assert calculate_score([3, 4, 2, 5, 1]) == 3

    def test_empty(self):
        assert calculate_score([]) == 0

    def test_rounding(self):
        assert calculate_score([3, 3]) == 3
        assert calculate_score([2, 3]) == 2  # round(2.5) = 2 in Python
        assert calculate_score([1, 2]) == 2  # round(1.5) = 2 in Python


class TestDetectPriority:
    def test_lowest_score_wins(self):
        scores = {"people": 3, "strategy": 2, "execution": 4, "cash": 3}
        assert detect_priority(scores) == "strategy"

    def test_tiebreak_by_order(self):
        scores = {"people": 2, "strategy": 2, "execution": 4, "cash": 5}
        assert detect_priority(scores) == "people"

    def test_all_zero(self):
        assert detect_priority({"people": 0, "strategy": 0, "execution": 0, "cash": 0}) == "people"

    def test_partial_scores(self):
        # Filter: exclude scores < 1 (strategy=0 excluded, valid: people=3, execution=4, cash=2 → min=2 → cash)
        scores = {"people": 3, "strategy": 0, "execution": 4, "cash": 2}
        assert detect_priority(scores) == "cash"

    def test_missing_keys(self):
        assert detect_priority({}) == "people"


class TestDiagnoseQuestions:
    def test_four_decisions(self):
        assert set(DIAGNOSE_QUESTIONS.keys()) == {"people", "strategy", "execution", "cash"}

    def test_five_questions_per_decision(self):
        for decision, data in DIAGNOSE_QUESTIONS.items():
            assert len(data["questions"]) == 5, f"{decision} has {len(data['questions'])} questions"

    def test_all_questions_have_ids(self):
        for decision, data in DIAGNOSE_QUESTIONS.items():
            for q in data["questions"]:
                assert q["id"].startswith(decision), f"Question {q['id']} doesn't start with {decision}"
                assert 1 <= len(q["text"]) <= 200
                assert q["concept"].startswith("concept-") or q["concept"].startswith("tool-") or q["concept"].startswith("metric-")


class TestScoreLabels:
    def test_all_levels_present(self):
        for score in range(1, 6):
            assert score in SCORE_LABELS, f"Missing label for score {score}"

    def test_labels_meaningful(self):
        assert "No iniciado" in SCORE_LABELS[1]
        assert "Optimizado" in SCORE_LABELS[5]
