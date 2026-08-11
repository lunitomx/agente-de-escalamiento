"""Executable acceptance gates for E39's seven meeting requirements."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import ClassVar

from validators.gate_contract import GateContext, GateResult


REQUIREMENT_STORIES: dict[str, str] = {
    "REQ-E39-001": "S39.1",
    "REQ-E39-002": "S39.1",
    "REQ-E39-003": "S39.2",
    "REQ-E39-004": "S39.2",
    "REQ-E39-005": "S39.3",
    "REQ-E39-006": "S39.3",
    "REQ-E39-007": "S39.4",
}

_EVIDENCE_PATH = Path(
    "work/epics/e39-meeting-and-team-intelligence/evidence/master-acceptance-e39.json"
)
_FOCUSED_TESTS = "tests/test_e39_meeting_intelligence.py"


class E39RequirementGate:
    """Fail closed unless E39 qualification evidence and focused tests pass."""

    requirement_id: ClassVar[str]
    gate_id: ClassVar[str]
    description: ClassVar[str]
    workflow_point: ClassVar[str] = "before:epic:close"

    def evaluate(self, context: GateContext) -> GateResult:
        evidence_path = context.working_dir / _EVIDENCE_PATH
        if evidence_path.is_symlink() or not evidence_path.is_file():
            return GateResult(
                passed=False,
                gate_id=self.gate_id,
                message="E39 qualification evidence missing",
            )
        try:
            payload = json.loads(evidence_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return GateResult(
                passed=False,
                gate_id=self.gate_id,
                message="E39 qualification evidence invalid",
            )
        if not _proves(payload, self.requirement_id):
            return GateResult(
                passed=False,
                gate_id=self.gate_id,
                message="E39 qualification does not prove requirement",
            )
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", _FOCUSED_TESTS, "-q"],
                cwd=context.working_dir,
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (OSError, subprocess.SubprocessError):
            return GateResult(
                passed=False,
                gate_id=self.gate_id,
                message="E39 focused tests could not run",
            )
        if completed.returncode != 0:
            return GateResult(
                passed=False,
                gate_id=self.gate_id,
                message="E39 focused tests failed",
            )
        return GateResult(
            passed=True,
            gate_id=self.gate_id,
            message="E39 qualification and focused tests pass",
            details=(REQUIREMENT_STORIES[self.requirement_id], "focused tests pass"),
        )


def _proves(payload: object, requirement_id: str) -> bool:
    if not isinstance(payload, dict) or payload.get("status") != "pass":
        return False
    requirements = payload.get("requirements_proved")
    return isinstance(requirements, list) and requirement_id in requirements


class E39RequirementGate001(E39RequirementGate):
    requirement_id = "REQ-E39-001"
    gate_id = "gate-req-e39-001"
    description = "E39-001 idempotent transcript intake"


class E39RequirementGate002(E39RequirementGate):
    requirement_id = "REQ-E39-002"
    gate_id = "gate-req-e39-002"
    description = "E39-002 meeting context and provenance"


class E39RequirementGate003(E39RequirementGate):
    requirement_id = "REQ-E39-003"
    gate_id = "gate-req-e39-003"
    description = "E39-003 evidence fact extraction"


class E39RequirementGate004(E39RequirementGate):
    requirement_id = "REQ-E39-004"
    gate_id = "gate-req-e39-004"
    description = "E39-004 non-punitive rhythm assessment"


class E39RequirementGate005(E39RequirementGate):
    requirement_id = "REQ-E39-005"
    gate_id = "gate-req-e39-005"
    description = "E39-005 temporal team signals"


class E39RequirementGate006(E39RequirementGate):
    requirement_id = "REQ-E39-006"
    gate_id = "gate-req-e39-006"
    description = "E39-006 daily executive review"


class E39RequirementGate007(E39RequirementGate):
    requirement_id = "REQ-E39-007"
    gate_id = "gate-req-e39-007"
    description = "E39-007 local schedule and report exchange"


GATE_CLASSES: dict[str, type[E39RequirementGate]] = {
    gate.requirement_id: gate
    for gate in (
        E39RequirementGate001,
        E39RequirementGate002,
        E39RequirementGate003,
        E39RequirementGate004,
        E39RequirementGate005,
        E39RequirementGate006,
        E39RequirementGate007,
    )
}
