"""TDD tests for coaching/summary — RED → GREEN → REFACTOR.

Run from repo root:
    python3 -m pytest .scaleup/coaching/summary/tests/ -v
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

import pytest

# ── path resolution ──────────────────────────────────────────────────────────
# When run directly (not through conftest.py), ensure .scaleup/ is on path
_scaleup = pathlib.Path(__file__).parent.parent.parent.parent  # .scaleup/
if str(_scaleup) not in sys.path:
    sys.path.insert(0, str(_scaleup))


# ── helpers ──────────────────────────────────────────────────────────────────

FULL_CONTEXT = {
    "base_path": ".",
    "log_file_path": None,  # overridden per test
    "date": "2026-05-06",
    "duration_minutes": 45,
    "decision_focus": "strategy",
    "worksheets_completed": ["7 Strata of Strategy", "BHAG draft"],
    "tasks_created": ["Define brand promise by May 15", "Schedule strategy offsite"],
    "tasks_completed": ["Review One-Page Strategic Plan"],
    "notes": ["Clarified our 10-year BHAG", "Identified 3 core differentiators"],
    "scores_before": None,
}

MINIMAL_CONTEXT = {
    "base_path": ".",
    "log_file_path": None,
    "date": "2026-05-06",
    "duration_minutes": 30,
    "decision_focus": "cash",
    "worksheets_completed": [],
    "tasks_created": [],
    "tasks_completed": [],
    "notes": [],
    "scores_before": None,
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# T1 — engine.py
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestBuildSummary:
    """Tests for coaching.summary.engine.build_summary()."""

    def _get_engine(self):
        from coaching.summary.engine import build_summary
        return build_summary

    def test_returns_dict(self):
        build_summary = self._get_engine()
        result = build_summary(FULL_CONTEXT)
        assert isinstance(result, dict)

    def test_required_keys_present(self):
        build_summary = self._get_engine()
        result = build_summary(FULL_CONTEXT)
        required = {
            "date",
            "duration_minutes",
            "decision_focus",
            "worksheets_completed",
            "tasks_created",
            "tasks_completed",
            "notes",
        }
        missing = required - result.keys()
        assert not missing, f"Missing keys: {missing}"

    def test_values_passed_through(self):
        build_summary = self._get_engine()
        result = build_summary(FULL_CONTEXT)
        assert result["date"] == "2026-05-06"
        assert result["duration_minutes"] == 45
        assert result["decision_focus"] == "strategy"
        assert result["worksheets_completed"] == ["7 Strata of Strategy", "BHAG draft"]

    def test_scores_before_null_handled_gracefully(self):
        """scores_before: null should not raise — just absent from result or None."""
        build_summary = self._get_engine()
        ctx = {**FULL_CONTEXT, "scores_before": None}
        result = build_summary(ctx)
        # No exception, no score-change key required when null
        assert isinstance(result, dict)
        assert result.get("scores_before") is None or "scores_before" not in result

    def test_minimal_context_no_exception(self):
        build_summary = self._get_engine()
        result = build_summary(MINIMAL_CONTEXT)
        assert isinstance(result, dict)
        assert result["worksheets_completed"] == []
        assert result["tasks_created"] == []

    def test_no_io_in_engine(self):
        """engine.build_summary is a pure function — no file I/O allowed."""
        import inspect
        from coaching.summary import engine
        src = inspect.getsource(engine)
        forbidden = ["open(", "read_text", "write_text", "pathlib.Path", "os.path"]
        for token in forbidden:
            assert token not in src, f"engine.py must not contain I/O: found '{token}'"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# T1 — formatter.py
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestFormatSummary:
    """Tests for coaching.summary.formatter.format_summary()."""

    def _engine(self):
        from coaching.summary.engine import build_summary
        return build_summary

    def _formatter(self):
        from coaching.summary.formatter import format_summary
        return format_summary

    def _build(self, ctx):
        return self._engine()(ctx)

    def test_returns_string(self):
        result = self._formatter()(self._build(FULL_CONTEXT))
        assert isinstance(result, str)

    def test_contains_session_summary_header(self):
        result = self._formatter()(self._build(FULL_CONTEXT))
        assert "## Session Summary" in result

    def test_contains_what_we_worked_on_when_worksheets_present(self):
        result = self._formatter()(self._build(FULL_CONTEXT))
        assert "### What We Worked On" in result

    def test_omits_what_we_worked_on_when_no_worksheets(self):
        result = self._formatter()(self._build(MINIMAL_CONTEXT))
        assert "### What We Worked On" not in result

    def test_contains_tasks_section_when_tasks_present(self):
        result = self._formatter()(self._build(FULL_CONTEXT))
        assert "### Tasks" in result

    def test_tasks_section_shows_created_count(self):
        result = self._formatter()(self._build(FULL_CONTEXT))
        assert "Created (2)" in result

    def test_tasks_section_shows_completed_count(self):
        result = self._formatter()(self._build(FULL_CONTEXT))
        assert "Completed (1)" in result

    def test_contains_key_points_when_notes_present(self):
        result = self._formatter()(self._build(FULL_CONTEXT))
        assert "### Key Points" in result

    def test_omits_key_points_when_no_notes(self):
        result = self._formatter()(self._build(MINIMAL_CONTEXT))
        assert "### Key Points" not in result

    def test_omits_score_change_section_when_scores_before_null(self):
        result = self._formatter()(self._build(FULL_CONTEXT))
        # No score-delta heading when scores_before is None
        assert "Score" not in result or "score" not in result.lower() or \
               "Score Changes" not in result

    def test_contains_date(self):
        result = self._formatter()(self._build(FULL_CONTEXT))
        assert "2026-05-06" in result

    def test_contains_duration(self):
        result = self._formatter()(self._build(FULL_CONTEXT))
        assert "45" in result

    def test_contains_decision_focus(self):
        result = self._formatter()(self._build(FULL_CONTEXT))
        assert "Strategy" in result or "strategy" in result

    def test_worksheet_names_included(self):
        result = self._formatter()(self._build(FULL_CONTEXT))
        assert "7 Strata of Strategy" in result

    def test_task_names_included(self):
        result = self._formatter()(self._build(FULL_CONTEXT))
        assert "Define brand promise by May 15" in result

    def test_autogenerated_footer(self):
        result = self._formatter()(self._build(FULL_CONTEXT))
        assert "auto-generated" in result.lower()

    def test_no_io_in_formatter(self):
        """formatter.format_summary is a pure function — no file I/O allowed."""
        import inspect
        from coaching.summary import formatter
        src = inspect.getsource(formatter)
        forbidden = ["open(", "read_text", "write_text", "pathlib.Path", "os.path"]
        for token in forbidden:
            assert token not in src, f"formatter.py must not contain I/O: found '{token}'"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# T1 — __init__.py run() API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestRunAPI:
    """Tests for coaching.summary.run() public API."""

    def _run(self):
        from coaching.summary import run
        return run

    def test_run_returns_dict_with_required_keys(self, tmp_path):
        log_file = tmp_path / "2026-05-06.md"
        log_file.write_text(
            "---\ndate: 2026-05-06\nduration_minutes: 45\ndecision_focus: strategy\n---\n"
            "## Session Notes\n- Test note\n",
            encoding="utf-8",
        )
        ctx = {**FULL_CONTEXT, "log_file_path": str(log_file)}
        result = self._run()(ctx)
        assert isinstance(result, dict)
        assert "output" in result
        assert "artifacts" in result
        assert "errors" in result

    def test_run_returns_empty_errors_on_success(self, tmp_path):
        log_file = tmp_path / "2026-05-06.md"
        log_file.write_text(
            "---\ndate: 2026-05-06\nduration_minutes: 45\ndecision_focus: strategy\n---\n"
            "## Session Notes\n- Test note\n",
            encoding="utf-8",
        )
        ctx = {**FULL_CONTEXT, "log_file_path": str(log_file)}
        result = self._run()(ctx)
        assert result["errors"] == []

    def test_run_appends_summary_to_file(self, tmp_path):
        log_file = tmp_path / "2026-05-06.md"
        log_file.write_text(
            "---\ndate: 2026-05-06\nduration_minutes: 45\ndecision_focus: strategy\n---\n"
            "## Session Notes\n- Test note\n",
            encoding="utf-8",
        )
        ctx = {**FULL_CONTEXT, "log_file_path": str(log_file)}
        self._run()(ctx)
        content = log_file.read_text(encoding="utf-8")
        assert "## Session Summary" in content

    def test_run_artifacts_summary_appended_true(self, tmp_path):
        log_file = tmp_path / "2026-05-06.md"
        log_file.write_text(
            "---\ndate: 2026-05-06\nduration_minutes: 45\ndecision_focus: strategy\n---\n"
            "## Session Notes\n- Test note\n",
            encoding="utf-8",
        )
        ctx = {**FULL_CONTEXT, "log_file_path": str(log_file)}
        result = self._run()(ctx)
        assert result["artifacts"].get("summary_appended") is True

    def test_run_returns_errors_when_log_file_path_missing(self):
        ctx = {**FULL_CONTEXT, "log_file_path": None}
        result = self._run()(ctx)
        assert len(result["errors"]) > 0

    def test_run_returns_errors_when_log_file_not_found(self, tmp_path):
        ctx = {**FULL_CONTEXT, "log_file_path": str(tmp_path / "nonexistent.md")}
        result = self._run()(ctx)
        assert len(result["errors"]) > 0

    def test_import_run_succeeds(self):
        from coaching.summary import run  # noqa: F401


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# T1 — __main__ entry point (stdin and --context)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestMainEntry:
    """Integration test: invoke module via subprocess."""

    _SCALEUP = str(pathlib.Path(__file__).parent.parent.parent.parent)  # .scaleup/

    def _make_log(self, tmp_path: pathlib.Path) -> pathlib.Path:
        log_file = tmp_path / "2026-05-06.md"
        log_file.write_text(
            "---\ndate: 2026-05-06\nduration_minutes: 45\ndecision_focus: strategy\n---\n"
            "## Session Notes\n- Test note\n",
            encoding="utf-8",
        )
        return log_file

    def _ctx(self, log_file: pathlib.Path) -> dict:
        return {**FULL_CONTEXT, "log_file_path": str(log_file)}

    def test_stdin_invocation(self, tmp_path):
        log_file = self._make_log(tmp_path)
        ctx = self._ctx(log_file)
        proc = subprocess.run(
            [sys.executable, "-m", "coaching.summary"],
            input=json.dumps(ctx),
            capture_output=True,
            text=True,
            cwd=self._SCALEUP,
        )
        assert proc.returncode == 0, f"stderr: {proc.stderr}"
        result = json.loads(proc.stdout)
        assert result["errors"] == []
        assert result["artifacts"]["summary_appended"] is True

    def test_context_arg_invocation(self, tmp_path):
        log_file = self._make_log(tmp_path)
        ctx = self._ctx(log_file)
        proc = subprocess.run(
            [sys.executable, "-m", "coaching.summary", "--context", json.dumps(ctx)],
            capture_output=True,
            text=True,
            cwd=self._SCALEUP,
        )
        assert proc.returncode == 0, f"stderr: {proc.stderr}"
        result = json.loads(proc.stdout)
        assert result["errors"] == []

    def test_missing_log_file_exits_nonzero(self, tmp_path):
        ctx = {**FULL_CONTEXT, "log_file_path": str(tmp_path / "missing.md")}
        proc = subprocess.run(
            [sys.executable, "-m", "coaching.summary"],
            input=json.dumps(ctx),
            capture_output=True,
            text=True,
            cwd=self._SCALEUP,
        )
        assert proc.returncode == 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# T2 — summary_validator.py
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestValidateSummary:
    """Tests for .scaleup/agent/validators/summary_validator.validate_summary()."""

    _SCALEUP = pathlib.Path(__file__).parent.parent.parent.parent  # .scaleup/

    def _validator(self):
        # Import from .scaleup/agent/validators/summary_validator
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "summary_validator",
            self._SCALEUP / "agent" / "validators" / "summary_validator.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.validate_summary

    def test_returns_empty_list_when_summary_present(self, tmp_path):
        log_file = tmp_path / "valid.md"
        log_file.write_text(
            "---\ndate: 2026-05-06\n---\n## Session Notes\n- note\n\n## Session Summary\n\n**Date:** 2026-05-06\n",
            encoding="utf-8",
        )
        validate_summary = self._validator()
        errors = validate_summary(str(log_file))
        assert errors == []

    def test_returns_errors_when_summary_missing(self, tmp_path):
        log_file = tmp_path / "no_summary.md"
        log_file.write_text(
            "---\ndate: 2026-05-06\n---\n## Session Notes\n- note\n",
            encoding="utf-8",
        )
        validate_summary = self._validator()
        errors = validate_summary(str(log_file))
        assert len(errors) > 0
        assert any("Session Summary" in e for e in errors)

    def test_returns_errors_when_file_not_found(self, tmp_path):
        validate_summary = self._validator()
        errors = validate_summary(str(tmp_path / "nonexistent.md"))
        assert len(errors) > 0
        assert any("not found" in e.lower() or "File not found" in e for e in errors)

    def test_subprocess_exits_zero_on_valid_file(self, tmp_path):
        log_file = tmp_path / "valid.md"
        log_file.write_text(
            "---\ndate: 2026-05-06\n---\n## Session Notes\n- note\n\n## Session Summary\n\n**Date:** 2026-05-06\n",
            encoding="utf-8",
        )
        validator_path = self._SCALEUP / "agent" / "validators" / "summary_validator.py"
        proc = subprocess.run(
            [sys.executable, str(validator_path), str(log_file)],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, f"stderr: {proc.stderr}"

    def test_subprocess_exits_one_on_invalid_file(self, tmp_path):
        log_file = tmp_path / "no_summary.md"
        log_file.write_text(
            "---\ndate: 2026-05-06\n---\n## Session Notes\n- note\n",
            encoding="utf-8",
        )
        validator_path = self._SCALEUP / "agent" / "validators" / "summary_validator.py"
        proc = subprocess.run(
            [sys.executable, str(validator_path), str(log_file)],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 1
