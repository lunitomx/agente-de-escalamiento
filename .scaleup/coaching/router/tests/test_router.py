"""Tests for coaching.router engine and I/O."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import yaml

from coaching.router.engine import route


class TestRoute:
    def test_lowest_score(self):
        r = route({"people": 3, "strategy": 2, "execution": 4, "cash": 1})
        assert r["decision"] == "cash"
        assert r["skill"] == "scaleup-cash"
        assert r["reason"] == "lowest_score"

    def test_explicit_override(self):
        r = route({"people": 3, "strategy": 2, "execution": 4, "cash": 1}, explicit="people")
        assert r["decision"] == "people"
        assert r["reason"] == "explicit_request"

    def test_no_scores(self):
        r = route({})
        assert r["decision"] == "people"
        assert r["reason"] == "no_scores_default"

    def test_tie(self):
        r = route({"people": 2, "strategy": 2, "execution": 4, "cash": 3})
        assert r["decision"] in ("people", "strategy")


class TestRunIntegration:
    def test_run_with_scores(self):
        from coaching.router import run
        result = run({"people": 3, "strategy": 2, "execution": 4, "cash": 1})
        assert result["errors"] == []
        assert result["artifacts"]["decision"] == "cash"
        assert result["artifacts"]["skill"] == "scaleup-cash"

    def test_run_with_profile(self, tmp_path):
        from coaching.router import run
        profile = {"scores": {"people": 4, "strategy": 1, "execution": 3, "cash": 3}}
        path = tmp_path / "profile.yaml"
        path.write_text(yaml.dump(profile), encoding="utf-8")
        result = run({"profile_path": str(path)})
        assert result["artifacts"]["decision"] == "strategy"

    def test_run_explicit(self):
        from coaching.router import run
        result = run({"people": 3, "strategy": 2, "execution": 4, "cash": 1, "explicit": "execution"})
        assert result["artifacts"]["decision"] == "execution"


class TestCLI:
    def test_cli(self):
        ctx = json.dumps({"people": 3, "strategy": 2, "execution": 4, "cash": 1})
        result = subprocess.run(
            [sys.executable, "-m", "coaching.router", "--context", ctx],
            capture_output=True, text=True,
            cwd=str(pathlib.Path(__file__).parents[3]),
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["artifacts"]["decision"] == "cash"
