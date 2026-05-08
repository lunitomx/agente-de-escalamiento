"""Tests for coaching.diagnose engine, formatter, and I/O."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest
import yaml

from coaching.diagnose.engine import build_diagnosis, calculate_focus, validate_scores
from coaching.diagnose.formatter import format_diagnosis


class TestValidateScores:
    def test_valid(self):
        assert validate_scores({"people": 3, "strategy": 2, "execution": 4, "cash": 1}) == []

    def test_missing_decision(self):
        errors = validate_scores({"people": 3, "strategy": 2})
        assert any("execution" in e for e in errors)
        assert any("cash" in e for e in errors)

    def test_out_of_range(self):
        errors = validate_scores({"people": 0, "strategy": 6, "execution": 3, "cash": 3})
        assert len(errors) == 2

    def test_non_integer(self):
        errors = validate_scores({"people": "high", "strategy": 2, "execution": 3, "cash": 4})
        assert any("integer" in e for e in errors)


class TestCalculateFocus:
    def test_lowest_wins(self):
        assert calculate_focus({"people": 3, "strategy": 2, "execution": 4, "cash": 5}) == "strategy"

    def test_tie_first_in_order(self):
        focus = calculate_focus({"people": 1, "strategy": 1, "execution": 3, "cash": 3})
        assert focus in ("people", "strategy")

    def test_empty_defaults_people(self):
        assert calculate_focus({}) == "people"


class TestBuildDiagnosis:
    def test_complete(self):
        d = build_diagnosis({"people": 3, "strategy": 2, "execution": 4, "cash": 1, "date": "2026-05-07"})
        assert d["scores"]["cash"] == 1
        assert d["focus"]["decision"] == "cash"
        assert d["summary"]["average"] == 2.5
        assert d["labels"]["strategy"] == "Ad hoc"

    def test_focus_date(self):
        d = build_diagnosis({"people": 3, "strategy": 2, "execution": 4, "cash": 1, "date": "2026-05-07"})
        assert d["focus"]["last_diagnosis"] == "2026-05-07"


class TestFormatDiagnosis:
    def test_contains_scores(self):
        d = build_diagnosis({"people": 3, "strategy": 2, "execution": 4, "cash": 1})
        md = format_diagnosis(d)
        assert "Cash" in md
        assert "1/5" in md
        assert "Recommended Focus" in md

    def test_score_bar(self):
        d = build_diagnosis({"people": 3, "strategy": 2, "execution": 4, "cash": 5})
        md = format_diagnosis(d)
        assert "[#####]" in md
        assert "[##...]" in md


class TestRunIntegration:
    def test_run_updates_profile(self, tmp_path):
        from coaching.diagnose import run

        profile = {"company": {"name": "Test"}, "scores": {}, "focus": None}
        profile_path = tmp_path / "profile.yaml"
        profile_path.write_text(yaml.dump(profile), encoding="utf-8")

        result = run({
            "people": 3, "strategy": 2, "execution": 4, "cash": 1,
            "date": "2026-05-07",
            "profile_path": str(profile_path),
        })
        assert result["errors"] == []
        assert result["artifacts"]["focus"] == "cash"

        updated = yaml.safe_load(profile_path.read_text())
        assert updated["scores"]["cash"] == 1
        assert updated["focus"]["decision"] == "cash"

    def test_run_without_profile(self):
        from coaching.diagnose import run

        result = run({"people": 3, "strategy": 4, "execution": 2, "cash": 5})
        assert result["errors"] == []
        assert result["artifacts"]["focus"] == "execution"
        assert not result["artifacts"]["profile_updated"]

    def test_run_validation_error(self):
        from coaching.diagnose import run

        result = run({"people": 3})
        assert len(result["errors"]) > 0


class TestCLI:
    def test_cli(self):
        ctx = json.dumps({"people": 3, "strategy": 2, "execution": 4, "cash": 1, "date": "2026-05-07"})
        result = subprocess.run(
            [sys.executable, "-m", "coaching.diagnose", "--context", ctx],
            capture_output=True, text=True,
            cwd=str(pathlib.Path(__file__).parents[3]),
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["artifacts"]["focus"] == "cash"
