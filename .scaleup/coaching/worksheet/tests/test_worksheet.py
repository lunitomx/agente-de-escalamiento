"""Tests for coaching.worksheet engine, formatter, and I/O."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest
import yaml

from coaching.worksheet.engine import (
    build_worksheet_session,
    check_prerequisites,
    find_worksheet,
    list_worksheets,
)
from coaching.worksheet.formatter import format_worksheet_list, format_worksheet_guide

SAMPLE_REGISTRY = [
    {"id": "ws-a", "name": "Worksheet A", "decision": "people", "prerequisites": [], "difficulty": "beginner", "time_estimate": "1h", "outputs": ["output-a"]},
    {"id": "ws-b", "name": "Worksheet B", "decision": "people", "prerequisites": ["ws-a"], "difficulty": "intermediate", "time_estimate": "2h", "outputs": ["output-b"]},
    {"id": "ws-c", "name": "Worksheet C", "decision": "strategy", "prerequisites": [], "difficulty": "advanced", "time_estimate": "4h", "outputs": ["output-c"]},
]


class TestFindWorksheet:
    def test_found(self):
        assert find_worksheet(SAMPLE_REGISTRY, "ws-b")["name"] == "Worksheet B"

    def test_not_found(self):
        assert find_worksheet(SAMPLE_REGISTRY, "ws-z") is None


class TestListWorksheets:
    def test_all(self):
        assert len(list_worksheets(SAMPLE_REGISTRY)) == 3

    def test_by_decision(self):
        result = list_worksheets(SAMPLE_REGISTRY, "people")
        assert len(result) == 2
        assert all(w["decision"] == "people" for w in result)


class TestCheckPrerequisites:
    def test_met(self):
        assert check_prerequisites(SAMPLE_REGISTRY, "ws-b", {"ws-a"}) == []

    def test_not_met(self):
        missing = check_prerequisites(SAMPLE_REGISTRY, "ws-b", set())
        assert "ws-a" in missing

    def test_no_prerequisites(self):
        assert check_prerequisites(SAMPLE_REGISTRY, "ws-a", set()) == []

    def test_not_found(self):
        errors = check_prerequisites(SAMPLE_REGISTRY, "ws-z", set())
        assert any("not found" in e for e in errors)


class TestBuildWorksheetSession:
    def test_basic(self):
        meta = SAMPLE_REGISTRY[0]
        content = {"fields": [{"name": "f1", "description": "desc"}]}
        session = build_worksheet_session(meta, content)
        assert session["id"] == "ws-a"
        assert session["total_fields"] == 1
        assert session["outputs"] == ["output-a"]


class TestFormatWorksheetList:
    def test_all(self):
        md = format_worksheet_list(SAMPLE_REGISTRY)
        assert "People" in md
        assert "Strategy" in md
        assert "ws-a" in md

    def test_filtered(self):
        people = list_worksheets(SAMPLE_REGISTRY, "people")
        md = format_worksheet_list(people, "people")
        assert "people" in md.lower()


class TestFormatWorksheetGuide:
    def test_basic(self):
        session = build_worksheet_session(SAMPLE_REGISTRY[0], {"fields": [{"name": "f1", "description": "d1"}]})
        md = format_worksheet_guide(session)
        assert "Worksheet A" in md
        assert "f1" in md


class TestRunIntegration:
    def test_list_action(self):
        from coaching.worksheet import run
        result = run({"action": "list"})
        assert result["errors"] == []
        assert result["artifacts"]["count"] == 15

    def test_load_action(self):
        from coaching.worksheet import run
        result = run({"action": "load", "worksheet_id": "worksheet-face"})
        assert result["errors"] == []
        assert result["artifacts"]["worksheet_id"] == "worksheet-face"
        assert result["artifacts"]["decision"] == "people"

    def test_load_not_found(self):
        from coaching.worksheet import run
        result = run({"action": "load", "worksheet_id": "worksheet-nonexistent"})
        assert any("not found" in e for e in result["errors"])

    def test_save_action(self, tmp_path):
        from coaching.worksheet import run
        result = run({
            "action": "save",
            "data": {
                "worksheet_id": "ws-test",
                "worksheet_name": "Test",
                "decision": "people",
                "status": "completed",
                "fields": {"f1": "value1"},
            },
            "worksheets_dir": str(tmp_path),
        })
        assert result["errors"] == []
        assert (tmp_path / "ws-test.yaml").exists()

    def test_unknown_action(self):
        from coaching.worksheet import run
        result = run({"action": "foo"})
        assert any("Unknown" in e for e in result["errors"])


class TestCLI:
    def test_cli_list(self):
        ctx = json.dumps({"action": "list", "decision": "cash"})
        result = subprocess.run(
            [sys.executable, "-m", "coaching.worksheet", "--context", ctx],
            capture_output=True, text=True,
            cwd=str(pathlib.Path(__file__).parents[3]),
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["artifacts"]["count"] == 3
