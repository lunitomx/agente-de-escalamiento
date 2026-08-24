"""Acceptance and unit tests for the canonical coaching.summary module."""

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
FULL_CONTEXT = {
    "date": "2026-08-24",
    "duration_minutes": 45,
    "decision_focus": "strategy",
    "worksheets_completed": ["7 Strata"],
    "tasks_created": ["Define brand promise"],
    "tasks_completed": ["Review OPSP"],
    "notes": ["Clarified the differentiators"],
    "scores_before": None,
}


def _session_log(tmp_path: Path) -> Path:
    log_path = tmp_path / "2026-08-24.md"
    log_path.write_text(
        "---\ndate: 2026-08-24\nduration_minutes: 45\n"
        "decision_focus: strategy\n---\n## Session Notes\n- Test note\n",
        encoding="utf-8",
    )
    return log_path


def test_build_summary_preserves_structured_session_data():
    from coaching.summary.engine import build_summary

    summary = build_summary(FULL_CONTEXT)

    assert summary["decision_focus"] == "strategy"
    assert summary["worksheets_completed"] == ["7 Strata"]
    assert summary["tasks_completed"] == ["Review OPSP"]


def test_formatter_renders_only_populated_optional_sections():
    from coaching.summary.formatter import format_summary

    rendered = format_summary(
        {
            **FULL_CONTEXT,
            "worksheets_completed": [],
            "tasks_created": [],
            "tasks_completed": [],
            "notes": [],
        }
    )

    assert "## Session Summary" in rendered
    assert "### What We Worked On" not in rendered
    assert "### Tasks" not in rendered
    assert "### Key Points" not in rendered


def test_run_appends_one_valid_summary_when_retried(tmp_path):
    from coaching.summary import run

    log_path = _session_log(tmp_path)
    context = {**FULL_CONTEXT, "log_file_path": str(log_path)}

    first = run(context)
    second = run(context)

    assert first["errors"] == []
    assert second["errors"] == []
    content = log_path.read_text(encoding="utf-8")
    assert content.count("## Session Summary") == 1

    validator = REPO_ROOT / ".scaleup" / "agent" / "validators" / "summary_validator.py"
    completed = subprocess.run(
        [sys.executable, str(validator), str(log_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_module_cli_runs_from_outside_the_repository(tmp_path):
    log_path = _session_log(tmp_path)
    context = {**FULL_CONTEXT, "log_file_path": str(log_path)}
    process_env = os.environ.copy()
    process_env["PYTHONPATH"] = str(REPO_ROOT)

    completed = subprocess.run(
        [sys.executable, "-m", "coaching.summary"],
        cwd=tmp_path,
        input=json.dumps(context),
        env=process_env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["errors"] == []
