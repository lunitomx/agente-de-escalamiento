"""Tests for level module."""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent.parent))
from coaching.level import LEVEL_THRESHOLDS, LEVEL_INSTRUCTIONS, detect_level
from coaching.core import GROWTH_STAGES


class TestDetectLevel:
    def test_shu_low_scores(self):
        assert detect_level({"people": 1, "strategy": 1, "execution": 2, "cash": 1}) == "shu"

    def test_ha_mid_scores(self):
        assert detect_level({"people": 3, "strategy": 3, "execution": 2, "cash": 3}) == "ha"

    def test_ri_high_scores(self):
        assert detect_level({"people": 4, "strategy": 4, "execution": 5, "cash": 5}) == "ri"

    def test_empty_scores_defaults_shu(self):
        assert detect_level({}) == "shu"

    def test_boundary_shu_ha(self):
        """Score 2.4 is still Shu, 2.5 is Ha."""
        assert detect_level({"people": 2, "strategy": 2, "execution": 3, "cash": 2}) == "shu"
        assert detect_level({"people": 2, "strategy": 3, "execution": 3, "cash": 2}) == "ha"

    def test_boundary_ha_ri(self):
        """Score 3.5 is still Ha, 3.6 is Ri."""
        assert detect_level({"people": 3, "strategy": 4, "execution": 3, "cash": 4}) == "ha"
        assert detect_level({"people": 4, "strategy": 4, "execution": 3, "cash": 4}) == "ri"


class TestLevelThresholds:
    def test_all_levels_present(self):
        assert set(LEVEL_THRESHOLDS.keys()) == {"shu", "ha", "ri"}

    def test_monotonic_thresholds(self):
        assert LEVEL_THRESHOLDS["shu"]["max"] < LEVEL_THRESHOLDS["ha"]["max"] < LEVEL_THRESHOLDS["ri"]["max"]

    def test_each_level_has_required_keys(self):
        for level, info in LEVEL_THRESHOLDS.items():
            assert "max" in info
            assert "label" in info
            assert "description" in info

    def test_each_level_has_instructions(self):
        for level in LEVEL_THRESHOLDS:
            assert level in LEVEL_INSTRUCTIONS
            assert "tone" in LEVEL_INSTRUCTIONS[level]
            assert "depth" in LEVEL_INSTRUCTIONS[level]
