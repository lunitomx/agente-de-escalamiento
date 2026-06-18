"""Guided runtime helpers for declarative ScaleUp pipeline registries."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Literal, Any

from pydantic import BaseModel, ConfigDict, Field

try:
    import yaml
except ImportError as exc:  # pragma: no cover - project dependency
    raise ImportError("PyYAML required: pip install pyyaml") from exc


RunState = Literal["completed", "stopped"]
GateDecisionState = Literal["not_checked"]
RunEventType = Literal["stop", "resume"]


class UnknownPipelineError(ValueError):
    """Raised when a requested pipeline id is not present in the registry."""


class PipelinePhase(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    skill: str
    mode: str
    context: str
    output: str
    evidence: str
    inference_budget: str
    model_hint: str


class PipelineGate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    type: str
    on_fail: str
    after_phase: str | None = None
    validator: str | None = None


class PipelineDefinition(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    entrypoint: str
    intent: str
    inputs: list[str]
    phases: list[PipelinePhase]
    gates: list[PipelineGate]
    stop_conditions: list[str]
    outputs: list[str]
    evidence: list[str]


class PipelineRegistry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    version: int
    description: str
    principles: list[str]
    pipelines: list[PipelineDefinition]


class GateDecision(BaseModel):
    name: str
    type: str
    after_phase: str | None
    decision: GateDecisionState = "not_checked"


class RunEvent(BaseModel):
    event: RunEventType
    phase: str | None
    note: str


class PipelineRunEvidence(BaseModel):
    pipeline_id: str
    entrypoint: str
    state: RunState
    stopped_reason: str | None
    phases_reviewed: list[str]
    gate_decisions: list[GateDecision]
    stop_conditions: list[str]
    outputs_expected: list[str]
    evidence_expected: list[str]
    events: list[RunEvent] = Field(default_factory=list)


RunEvent.model_rebuild()
GateDecision.model_rebuild()
PipelineRunEvidence.model_rebuild()
PipelineRegistry.model_rebuild()


def load_registry(registry_path: Path) -> PipelineRegistry:
    """Load a pipeline registry from YAML into typed runtime models."""
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    return PipelineRegistry.model_validate(data)


def list_pipeline_summaries(
    registry: PipelineRegistry,
) -> list[dict[str, str | int]]:
    """Return compact pipeline summaries suitable for CLI list output."""
    return [
        {
            "id": pipeline.id,
            "intent": pipeline.intent,
            "phase_count": len(pipeline.phases),
            "entrypoint": pipeline.entrypoint,
        }
        for pipeline in registry.pipelines
    ]


def get_pipeline(registry: PipelineRegistry, pipeline_id: str) -> PipelineDefinition:
    """Return one pipeline by id or raise UnknownPipelineError."""
    for pipeline in registry.pipelines:
        if pipeline.id == pipeline_id:
            return pipeline
    raise UnknownPipelineError(f"Unknown pipeline: {pipeline_id}")


def render_pipeline_detail(pipeline: PipelineDefinition) -> str:
    """Render deterministic human-readable pipeline detail."""
    lines = [
        f"pipeline: {pipeline.id}",
        f"entrypoint: {pipeline.entrypoint}",
        f"intent: {pipeline.intent}",
        "phases:",
    ]
    for phase in pipeline.phases:
        lines.extend(
            [
                f"- phase: {phase.id}",
                f"  skill: {phase.skill}",
                f"  mode: {phase.mode}",
                f"  output: {phase.output}",
                f"  evidence: {phase.evidence}",
            ]
        )

    lines.append("gates:")
    for gate in pipeline.gates:
        after_phase = gate.after_phase or "end"
        lines.extend(
            [
                f"- gate: {gate.name}",
                f"  type: {gate.type}",
                f"  after_phase: {after_phase}",
                f"  on_fail: {gate.on_fail}",
            ]
        )

    lines.append("stop_conditions:")
    lines.extend(f"- {condition}" for condition in pipeline.stop_conditions)
    lines.append("outputs:")
    lines.extend(f"- {output}" for output in pipeline.outputs)
    lines.append("evidence:")
    lines.extend(f"- {item}" for item in pipeline.evidence)
    return "\n".join(lines)


def load_run_evidence(evidence_path: Path) -> PipelineRunEvidence:
    """Load and validate a guided pipeline run evidence file."""
    data = yaml.safe_load(evidence_path.read_text(encoding="utf-8"))
    return PipelineRunEvidence.model_validate(data)


def next_incomplete_phase(
    registry: PipelineRegistry,
    evidence: PipelineRunEvidence,
) -> str | None:
    """Return the first pipeline phase not yet reviewed in the evidence."""
    pipeline = get_pipeline(registry, evidence.pipeline_id)
    reviewed = set(evidence.phases_reviewed)
    for phase in pipeline.phases:
        if phase.id not in reviewed:
            return phase.id
    return None


def inspect_pipeline_run(
    registry: PipelineRegistry,
    evidence_path: Path,
) -> dict[str, str | int | None]:
    """Return compact, deterministic metadata for an existing run."""
    evidence = load_run_evidence(evidence_path)
    return {
        "pipeline_id": evidence.pipeline_id,
        "state": evidence.state,
        "next_phase": next_incomplete_phase(registry, evidence),
        "event_count": len(evidence.events),
        "evidence_path": str(evidence_path),
    }


def resume_pipeline_run(
    registry: PipelineRegistry,
    evidence_path: Path,
    note: str = "Resume requested.",
    expected_pipeline_id: str | None = None,
) -> dict[str, str | int | None]:
    """Append a resume event to validated evidence and report next phase."""
    evidence = load_run_evidence(evidence_path)
    if (
        expected_pipeline_id is not None
        and evidence.pipeline_id != expected_pipeline_id
    ):
        raise UnknownPipelineError(
            f"Evidence is for {evidence.pipeline_id}, not {expected_pipeline_id}"
        )
    next_phase = next_incomplete_phase(registry, evidence)
    updated = evidence.model_copy(
        update={
            "events": [
                *evidence.events,
                RunEvent(event="resume", phase=next_phase, note=note),
            ]
        }
    )
    evidence_path.write_text(
        yaml.safe_dump(updated.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    return {
        "pipeline_id": evidence.pipeline_id,
        "state": evidence.state,
        "next_phase": next_phase,
        "event_count": len(updated.events),
        "evidence_path": str(evidence_path),
    }


def run_guided_pipeline(
    registry: PipelineRegistry,
    pipeline_id: str,
    evidence_path: Path,
    stopped_reason: str | None = None,
) -> PipelineRunEvidence:
    """Record guided run evidence without automatically executing skills."""
    pipeline = get_pipeline(registry, pipeline_id)
    state: RunState = "stopped" if stopped_reason else "completed"
    evidence = PipelineRunEvidence(
        pipeline_id=pipeline.id,
        entrypoint=pipeline.entrypoint,
        state=state,
        stopped_reason=stopped_reason,
        phases_reviewed=[phase.id for phase in pipeline.phases],
        gate_decisions=[
            GateDecision(
                name=gate.name,
                type=gate.type,
                after_phase=gate.after_phase,
            )
            for gate in pipeline.gates
        ],
        stop_conditions=pipeline.stop_conditions,
        outputs_expected=pipeline.outputs,
        evidence_expected=pipeline.evidence,
    )
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        yaml.safe_dump(evidence.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    return evidence


def _print_run_summary(summary: dict[str, Any]) -> None:
    print(f"pipeline: {summary['pipeline_id']}")
    print(f"state: {summary['state']}")
    print(f"next_phase: {summary['next_phase'] or 'complete'}")
    print(f"events: {summary['event_count']}")
    print(f"evidence_path: {summary['evidence_path']}")


def _cmd_list(args: argparse.Namespace) -> int:
    registry = load_registry(Path(args.registry))
    for summary in list_pipeline_summaries(registry):
        print(
            f"{summary['id']} | phases={summary['phase_count']} | "
            f"entrypoint={summary['entrypoint']} | {summary['intent']}"
        )
    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    registry = load_registry(Path(args.registry))
    print(render_pipeline_detail(get_pipeline(registry, args.pipeline_id)))
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    registry = load_registry(Path(args.registry))
    evidence = run_guided_pipeline(
        registry,
        args.pipeline_id,
        evidence_path=Path(args.evidence_out),
        stopped_reason=args.stop,
    )
    print(f"{evidence.pipeline_id}: {evidence.state}")
    return 0


def _cmd_evidence_inspect(args: argparse.Namespace) -> int:
    registry = load_registry(Path(args.registry))
    summary = inspect_pipeline_run(registry, Path(args.evidence_path))
    _print_run_summary(summary)
    return 0


def _cmd_resume(args: argparse.Namespace) -> int:
    registry = load_registry(Path(args.registry))
    summary = resume_pipeline_run(
        registry,
        Path(args.evidence),
        note=args.note,
        expected_pipeline_id=args.pipeline_id,
    )
    print(f"{args.pipeline_id}: resumed at {summary['next_phase'] or 'complete'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipeline-runner",
        description="Guided runner for ScaleUp pipeline registries.",
    )
    _add_registry_argument(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List registered pipelines.")
    _add_registry_argument(list_parser)
    list_parser.set_defaults(func=_cmd_list)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect one pipeline.")
    inspect_parser.add_argument("pipeline_id")
    _add_registry_argument(inspect_parser)
    inspect_parser.set_defaults(func=_cmd_inspect)

    run_parser = subparsers.add_parser("run", help="Record guided run evidence.")
    run_parser.add_argument("pipeline_id")
    run_parser.add_argument("--evidence-out", required=True)
    run_parser.add_argument("--stop")
    _add_registry_argument(run_parser)
    run_parser.set_defaults(func=_cmd_run)

    evidence_parser = subparsers.add_parser(
        "evidence",
        help="Inspect guided run evidence.",
    )
    evidence_subparsers = evidence_parser.add_subparsers(
        dest="evidence_command",
        required=True,
    )
    evidence_inspect_parser = evidence_subparsers.add_parser(
        "inspect",
        help="Inspect one evidence file.",
    )
    evidence_inspect_parser.add_argument("evidence_path")
    _add_registry_argument(evidence_inspect_parser)
    evidence_inspect_parser.set_defaults(func=_cmd_evidence_inspect)

    resume_parser = subparsers.add_parser(
        "resume",
        help="Append a resume event to existing run evidence.",
    )
    resume_parser.add_argument("pipeline_id")
    resume_parser.add_argument("--evidence", required=True)
    resume_parser.add_argument("--note", default="Resume requested.")
    _add_registry_argument(resume_parser)
    resume_parser.set_defaults(func=_cmd_resume)
    return parser


def _add_registry_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--registry",
        default=".raise/pipelines/scaleup.yaml",
        help="Path to the ScaleUp pipeline registry YAML.",
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except UnknownPipelineError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
