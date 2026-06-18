"""Guided runtime helpers for declarative ScaleUp pipeline registries."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

try:
    import yaml
except ImportError as exc:  # pragma: no cover - project dependency
    raise ImportError("PyYAML required: pip install pyyaml") from exc


RunState = Literal["completed", "stopped"]
GateDecisionState = Literal["not_checked"]


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
