"""Tests for router module."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent.parent))
from coaching.router import (
    PRIORITY_ORDER,
    SUB_AGENT_COMMANDS,
    SUB_AGENT_LABELS,
    detect_priority,
)


class TestRouterDetectPriority:
    def test_lowest_score_wins(self):
        scores = {"people": 3, "strategy": 2, "execution": 4, "cash": 5}
        assert detect_priority(scores) == "strategy"

    def test_tiebreak_people_first(self):
        scores = {"people": 2, "strategy": 2, "execution": 4, "cash": 5}
        assert detect_priority(scores) == "people"

    def test_tiebreak_order_respected(self):
        scores = {"people": 4, "strategy": 2, "execution": 2, "cash": 5}
        assert detect_priority(scores) == "strategy"

    def test_empty_scores_defaults_people(self):
        assert detect_priority({}) == "people"

    def test_all_same_score_uses_order(self):
        scores = {"people": 3, "strategy": 3, "execution": 3, "cash": 3}
        assert detect_priority(scores) == "people"

    def test_partial_scores(self):
        scores = {"execution": 1, "cash": 5}
        assert detect_priority(scores) == "execution"


class TestRouterConstants:
    def test_priority_order(self):
        assert PRIORITY_ORDER == ["people", "strategy", "execution", "cash"]

    def test_all_decisions_have_commands(self):
        for decision in PRIORITY_ORDER:
            assert decision in SUB_AGENT_COMMANDS
            assert decision in SUB_AGENT_LABELS

    def test_command_format(self):
        for decision, cmd in SUB_AGENT_COMMANDS.items():
            assert cmd.startswith("/scaleup-")
            assert decision in cmd
