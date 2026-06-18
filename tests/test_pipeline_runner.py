from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / ".raise/pipelines/scaleup.yaml"
SPEC = importlib.util.spec_from_file_location(
    "pipeline_runner",
    ROOT / "validators/pipeline_runner.py",
)
assert SPEC is not None
assert SPEC.loader is not None
PIPELINE_RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PIPELINE_RUNNER)

load_registry = PIPELINE_RUNNER.load_registry
get_pipeline = PIPELINE_RUNNER.get_pipeline
list_pipeline_summaries = PIPELINE_RUNNER.list_pipeline_summaries
render_pipeline_detail = PIPELINE_RUNNER.render_pipeline_detail
run_guided_pipeline = PIPELINE_RUNNER.run_guided_pipeline
load_run_evidence = PIPELINE_RUNNER.load_run_evidence
inspect_pipeline_run = PIPELINE_RUNNER.inspect_pipeline_run
resume_pipeline_run = PIPELINE_RUNNER.resume_pipeline_run
UnknownPipelineError = PIPELINE_RUNNER.UnknownPipelineError
main = PIPELINE_RUNNER.main


def test_list_pipeline_summaries() -> None:
    registry = load_registry(REGISTRY)

    summaries = list_pipeline_summaries(registry)

    assert any(
        summary["id"] == "scaleup-session-start"
        and summary["phase_count"] == 4
        and summary["entrypoint"] == "scaleup-start"
        for summary in summaries
    )


def test_inspect_pipeline_includes_details() -> None:
    registry = load_registry(REGISTRY)
    pipeline = get_pipeline(registry, "scaleup-cash-acceleration-system")

    detail = render_pipeline_detail(pipeline)

    assert "scaleup-cash-acceleration-system" in detail
    assert "phase: ccc" in detail
    assert "gate: ccc_inputs_complete" in detail
    assert "Missing baseline cash data." in detail


def test_unknown_pipeline_does_not_write_evidence(tmp_path: Path) -> None:
    registry = load_registry(REGISTRY)
    evidence_path = tmp_path / "missing.yaml"

    with pytest.raises(UnknownPipelineError):
        run_guided_pipeline(
            registry,
            "missing-pipeline",
            evidence_path=evidence_path,
        )

    assert not evidence_path.exists()


def test_guided_run_writes_stopped_evidence(tmp_path: Path) -> None:
    registry = load_registry(REGISTRY)
    evidence_path = tmp_path / "stopped.yaml"

    evidence = run_guided_pipeline(
        registry,
        "scaleup-execution-system",
        evidence_path=evidence_path,
        stopped_reason="User cannot assign accountability.",
    )

    assert evidence.state == "stopped"
    written = yaml.safe_load(evidence_path.read_text(encoding="utf-8"))
    assert written["pipeline_id"] == "scaleup-execution-system"
    assert written["state"] == "stopped"
    assert written["stopped_reason"] == "User cannot assign accountability."
    assert written["phases_reviewed"] == [
        "rockefeller",
        "rhythms",
        "priorities",
        "create-tasks",
    ]
    assert written["gate_decisions"] == [
        {
            "name": "priorities_have_single_critical_number",
            "type": "manual",
            "after_phase": "priorities",
            "decision": "not_checked",
        }
    ]


def test_guided_run_writes_completed_evidence(tmp_path: Path) -> None:
    registry = load_registry(REGISTRY)
    evidence_path = tmp_path / "completed.yaml"

    evidence = run_guided_pipeline(
        registry,
        "scaleup-session-start",
        evidence_path=evidence_path,
    )

    assert evidence.state == "completed"
    written = yaml.safe_load(evidence_path.read_text(encoding="utf-8"))
    assert written["pipeline_id"] == "scaleup-session-start"
    assert written["state"] == "completed"
    assert written["stopped_reason"] is None
    assert written["phases_reviewed"] == [
        "load-profile",
        "load-sessions",
        "load-tasks",
        "present-context",
    ]


def test_cli_accepts_registry_after_subcommand(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = main(["list", "--registry", str(REGISTRY)])

    assert result == 0
    assert (
        "scaleup-session-start | phases=4 | entrypoint=scaleup-start"
        in capsys.readouterr().out
    )


def test_load_run_evidence_validates_existing_file(tmp_path: Path) -> None:
    evidence_path = tmp_path / "run.yaml"
    evidence_path.write_text(
        yaml.safe_dump(
            {
                "pipeline_id": "scaleup-session-start",
                "entrypoint": "scaleup-start",
                "state": "stopped",
                "stopped_reason": "Need current task board.",
                "phases_reviewed": ["load-profile", "load-sessions"],
                "gate_decisions": [],
                "stop_conditions": ["Missing profile."],
                "outputs_expected": ["Session context."],
                "evidence_expected": ["Loaded profile."],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    evidence = load_run_evidence(evidence_path)

    assert evidence.pipeline_id == "scaleup-session-start"
    assert evidence.events == []


def test_load_run_evidence_rejects_corrupt_file(tmp_path: Path) -> None:
    evidence_path = tmp_path / "corrupt.yaml"
    evidence_path.write_text(
        yaml.safe_dump({"pipeline_id": "scaleup-session-start"}),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_run_evidence(evidence_path)

    assert yaml.safe_load(evidence_path.read_text(encoding="utf-8")) == {
        "pipeline_id": "scaleup-session-start"
    }


def test_inspect_pipeline_run_reports_next_phase(tmp_path: Path) -> None:
    registry = load_registry(REGISTRY)
    evidence_path = tmp_path / "run.yaml"
    evidence_path.write_text(
        yaml.safe_dump(
            {
                "pipeline_id": "scaleup-session-start",
                "entrypoint": "scaleup-start",
                "state": "stopped",
                "stopped_reason": "Need task board.",
                "phases_reviewed": ["load-profile", "load-sessions"],
                "gate_decisions": [],
                "stop_conditions": [],
                "outputs_expected": [],
                "evidence_expected": [],
                "events": [],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    summary = inspect_pipeline_run(registry, evidence_path)

    assert summary["pipeline_id"] == "scaleup-session-start"
    assert summary["state"] == "stopped"
    assert summary["next_phase"] == "load-tasks"
    assert summary["event_count"] == 0
    assert summary["evidence_path"] == str(evidence_path)


def test_resume_pipeline_run_appends_event_without_overwriting(
    tmp_path: Path,
) -> None:
    registry = load_registry(REGISTRY)
    evidence_path = tmp_path / "run.yaml"
    original = {
        "pipeline_id": "scaleup-session-start",
        "entrypoint": "scaleup-start",
        "state": "stopped",
        "stopped_reason": "Need task board.",
        "phases_reviewed": ["load-profile", "load-sessions"],
        "gate_decisions": [
            {
                "name": "context_ready",
                "type": "manual",
                "after_phase": "load-sessions",
                "decision": "not_checked",
            }
        ],
        "stop_conditions": ["Missing task board."],
        "outputs_expected": ["Session context."],
        "evidence_expected": ["Loaded profile."],
        "events": [{"event": "stop", "phase": "load-sessions", "note": "Paused"}],
    }
    evidence_path.write_text(
        yaml.safe_dump(original, sort_keys=False),
        encoding="utf-8",
    )

    summary = resume_pipeline_run(
        registry,
        evidence_path,
        note="Continuing after task board update.",
    )

    written = yaml.safe_load(evidence_path.read_text(encoding="utf-8"))
    assert summary["next_phase"] == "load-tasks"
    assert written["phases_reviewed"] == original["phases_reviewed"]
    assert written["gate_decisions"] == original["gate_decisions"]
    assert written["events"] == [
        {"event": "stop", "phase": "load-sessions", "note": "Paused"},
        {
            "event": "resume",
            "phase": "load-tasks",
            "note": "Continuing after task board update.",
        },
    ]


def test_cli_inspects_and_resumes_evidence(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence_path = tmp_path / "run.yaml"
    evidence_path.write_text(
        yaml.safe_dump(
            {
                "pipeline_id": "scaleup-session-start",
                "entrypoint": "scaleup-start",
                "state": "stopped",
                "stopped_reason": "Need task board.",
                "phases_reviewed": ["load-profile", "load-sessions"],
                "gate_decisions": [],
                "stop_conditions": [],
                "outputs_expected": [],
                "evidence_expected": [],
                "events": [],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    inspect_result = main(
        [
            "evidence",
            "inspect",
            str(evidence_path),
            "--registry",
            str(REGISTRY),
        ]
    )
    inspect_out = capsys.readouterr().out

    resume_result = main(
        [
            "resume",
            "scaleup-session-start",
            "--evidence",
            str(evidence_path),
            "--registry",
            str(REGISTRY),
        ]
    )
    resume_out = capsys.readouterr().out

    assert inspect_result == 0
    assert "next_phase: load-tasks" in inspect_out
    assert resume_result == 0
    assert "scaleup-session-start: resumed at load-tasks" in resume_out
