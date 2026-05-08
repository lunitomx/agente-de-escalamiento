"""Tests for coaching.level engine, formatter, and I/O."""
from __future__ import annotations

import yaml
from coaching.level.engine import build_level_assessment, detect_level
from coaching.level.formatter import format_level


class TestDetectLevel:
    def test_shu_default(self):
        assert detect_level(0, 0, 0) == "shu"

    def test_shu_low_scores(self):
        assert detect_level(1.5, 2, 2) == "shu"

    def test_ha(self):
        assert detect_level(2.5, 5, 5) == "ha"

    def test_ri(self):
        assert detect_level(4.0, 10, 12) == "ri"

    def test_ha_not_enough_worksheets(self):
        assert detect_level(3.0, 2, 5) == "shu"

    def test_ri_not_enough_sessions(self):
        assert detect_level(4.0, 10, 5) == "ha"


class TestBuildLevelAssessment:
    def test_basic(self):
        a = build_level_assessment({"average_score": 2.5, "worksheets_completed": 5, "sessions_count": 5})
        assert a["level"] == "ha"
        assert "Ha" in a["label"]

    def test_override(self):
        a = build_level_assessment({"average_score": 1.0, "worksheets_completed": 0, "sessions_count": 0, "override": "ri"})
        assert a["level"] == "ri"
        assert a["override"] == "ri"


class TestFormatLevel:
    def test_basic(self):
        a = build_level_assessment({"average_score": 2.5, "worksheets_completed": 5, "sessions_count": 5})
        md = format_level(a)
        assert "Ha" in md
        assert "Coaching Level" in md

    def test_override_note(self):
        a = build_level_assessment({"average_score": 1.0, "override": "ri"})
        md = format_level(a)
        assert "manually set" in md


class TestRunIntegration:
    def test_run_basic(self):
        from coaching.level import run
        result = run({"average_score": 3.0, "worksheets_completed": 5, "sessions_count": 5})
        assert result["errors"] == []
        assert result["artifacts"]["level"] == "ha"

    def test_run_with_profile(self, tmp_path):
        from coaching.level import run
        profile = {"scores": {"people": 4, "strategy": 3, "execution": 4, "cash": 3}}
        path = tmp_path / "profile.yaml"
        path.write_text(yaml.dump(profile), encoding="utf-8")
        result = run({"profile_path": str(path), "worksheets_completed": 5, "sessions_count": 5})
        assert result["artifacts"]["level"] == "ha"

    def test_run_override_saves(self, tmp_path):
        from coaching.level import run
        profile = {"scores": {"people": 2, "strategy": 2, "execution": 2, "cash": 2}}
        path = tmp_path / "profile.yaml"
        path.write_text(yaml.dump(profile), encoding="utf-8")
        result = run({"profile_path": str(path), "override": "ri"})
        assert result["artifacts"]["level"] == "ri"
        updated = yaml.safe_load(path.read_text())
        assert updated["coaching_level"] == "ri"
