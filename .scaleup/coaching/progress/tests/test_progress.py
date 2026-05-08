"""Tests for coaching.progress engine, formatter, and I/O."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest
import yaml

from coaching.progress.engine import calculate_progress, suggest_next_action
from coaching.progress.formatter import format_progress

SAMPLE_REGISTRY = [
    {"id": "ws-a", "decision": "cash", "name": "WS A", "prerequisites": []},
    {"id": "ws-b", "decision": "cash", "name": "WS B", "prerequisites": ["ws-a"]},
    {"id": "ws-c", "decision": "people", "name": "WS C", "prerequisites": []},
]


class TestCalculateProgress:
    def test_basic(self):
        p = calculate_progress({"people": 3, "strategy": 2, "execution": 4, "cash": 1}, ["ws-a"], 15)
        assert p["average_score"] == 2.5
        assert p["worksheets_completed"] == 1
        assert p["completion_pct"] == 7
        assert p["focus"] == "cash"

    def test_no_scores(self):
        p = calculate_progress({}, [], 15)
        assert p["average_score"] == 0
        assert p["focus"] is None

    def test_all_completed(self):
        p = calculate_progress({"people": 5, "strategy": 5, "execution": 5, "cash": 5}, ["a"] * 15, 15)
        assert p["completion_pct"] == 100


class TestSuggestNextAction:
    def test_no_scores(self):
        s = suggest_next_action({}, set(), SAMPLE_REGISTRY)
        assert s["action"] == "diagnose"

    def test_suggests_worksheet(self):
        s = suggest_next_action({"people": 3, "cash": 1}, set(), SAMPLE_REGISTRY)
        assert s["action"] == "worksheet"
        assert s["worksheet_id"] == "ws-a"
        assert s["decision"] == "cash"

    def test_respects_prerequisites(self):
        s = suggest_next_action({"people": 3, "cash": 1}, {"ws-a"}, SAMPLE_REGISTRY)
        assert s["worksheet_id"] == "ws-b"

    def test_all_done_suggests_coaching(self):
        s = suggest_next_action({"people": 3, "cash": 1}, {"ws-a", "ws-b"}, SAMPLE_REGISTRY)
        assert s["action"] == "coaching"
        assert s["decision"] == "cash"


class TestFormatProgress:
    def test_contains_scores(self):
        p = calculate_progress({"people": 3, "strategy": 2, "execution": 4, "cash": 1}, [], 15)
        md = format_progress(p)
        assert "People" in md
        assert "1/5" in md

    def test_with_suggestion(self):
        p = calculate_progress({"people": 3, "cash": 1}, [], 15)
        s = {"action": "worksheet", "worksheet_id": "ws-a", "worksheet_name": "WS A", "reason": "test"}
        md = format_progress(p, s)
        assert "ws-a" in md


class TestRunIntegration:
    def test_run_with_profile(self, tmp_path):
        from coaching.progress import run

        profile = {"company": {"name": "Test"}, "scores": {"people": 3, "strategy": 2, "execution": 4, "cash": 1}, "focus": None}
        profile_path = tmp_path / "profile.yaml"
        profile_path.write_text(yaml.dump(profile), encoding="utf-8")

        result = run({"profile_path": str(profile_path)})
        assert result["errors"] == []
        assert result["artifacts"]["average_score"] == 2.5
        assert result["artifacts"]["focus"] == "cash"

    def test_run_no_profile(self):
        from coaching.progress import run
        result = run({})
        assert result["errors"] == []
        assert result["artifacts"]["average_score"] == 0
