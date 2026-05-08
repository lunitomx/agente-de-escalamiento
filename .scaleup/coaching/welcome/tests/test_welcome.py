"""Tests for coaching.welcome engine, formatter, and I/O."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

import pytest
import yaml

from coaching.welcome.engine import build_profile, detect_growth_stage, validate_intake
from coaching.welcome.formatter import format_profile, format_summary


class TestDetectGrowthStage:
    def test_startup(self):
        assert detect_growth_stage(5) == "startup"

    def test_growth(self):
        assert detect_growth_stage(25) == "growth"

    def test_scaleup(self):
        assert detect_growth_stage(100) == "scaleup"

    def test_enterprise(self):
        assert detect_growth_stage(500) == "enterprise"

    def test_boundary_startup_growth(self):
        assert detect_growth_stage(9) == "startup"
        assert detect_growth_stage(10) == "growth"

    def test_boundary_growth_scaleup(self):
        assert detect_growth_stage(50) == "growth"
        assert detect_growth_stage(51) == "scaleup"


class TestValidateIntake:
    def test_valid(self):
        assert validate_intake({"name": "Acme", "industry": "SaaS", "employees": 10}) == []

    def test_missing_name(self):
        errors = validate_intake({"industry": "SaaS", "employees": 10})
        assert any("name" in e for e in errors)

    def test_invalid_employees(self):
        errors = validate_intake({"name": "X", "industry": "Y", "employees": -1})
        assert any("positive integer" in e for e in errors)

    def test_zero_employees(self):
        errors = validate_intake({"name": "X", "industry": "Y", "employees": 0})
        assert any("positive integer" in e for e in errors)


class TestBuildProfile:
    def test_complete(self):
        profile = build_profile({"name": "Acme", "industry": "SaaS", "employees": 25})
        assert profile["company"]["name"] == "Acme"
        assert profile["company"]["growth_stage"] == "growth"
        assert profile["scores"]["people"] is None

    def test_explicit_stage_overrides(self):
        profile = build_profile({"name": "X", "industry": "Y", "employees": 5, "growth_stage": "scaleup"})
        assert profile["company"]["growth_stage"] == "scaleup"

    def test_existing_scores_preserved(self):
        scores = {"people": 3, "strategy": 2, "execution": 4, "cash": 1}
        profile = build_profile({"name": "X", "industry": "Y", "employees": 10, "scores": scores})
        assert profile["scores"] == scores


class TestFormatProfile:
    def test_roundtrip(self):
        profile = build_profile({"name": "Acme", "industry": "SaaS", "employees": 25})
        yaml_str = format_profile(profile)
        loaded = yaml.safe_load(yaml_str)
        assert loaded["company"]["name"] == "Acme"


class TestFormatSummary:
    def test_contains_company_name(self):
        profile = build_profile({"name": "Acme", "industry": "SaaS", "employees": 25})
        md = format_summary(profile)
        assert "Acme" in md
        assert "Growth" in md or "growth" in md

    def test_no_scores_message(self):
        profile = build_profile({"name": "X", "industry": "Y", "employees": 10})
        md = format_summary(profile)
        assert "diagnose" in md.lower()


class TestRunIntegration:
    def test_run_writes_profile(self, tmp_path):
        from coaching.welcome import run

        profile_path = tmp_path / "profile.yaml"
        result = run({
            "name": "TestCo",
            "industry": "Tech",
            "employees": 30,
            "profile_path": str(profile_path),
        })
        assert result["errors"] == []
        assert profile_path.exists()
        loaded = yaml.safe_load(profile_path.read_text())
        assert loaded["company"]["name"] == "TestCo"
        assert result["artifacts"]["growth_stage"] == "growth"

    def test_run_validation_error(self):
        from coaching.welcome import run

        result = run({"industry": "Tech"})
        assert len(result["errors"]) > 0
        assert result["output"] == ""


class TestCLI:
    def test_cli_with_context_arg(self, tmp_path):
        profile_path = tmp_path / "profile.yaml"
        ctx = json.dumps({
            "name": "CLI Co",
            "industry": "Retail",
            "employees": 15,
            "profile_path": str(profile_path),
        })
        result = subprocess.run(
            [sys.executable, "-m", "coaching.welcome", "--context", ctx],
            capture_output=True, text=True,
            cwd=str(pathlib.Path(__file__).parents[3]),
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["errors"] == []
        assert profile_path.exists()
