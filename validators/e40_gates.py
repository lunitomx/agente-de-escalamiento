"""Executable acceptance gates for E40's eight executive requirements."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import ClassVar

from validators.gate_contract import GateContext, GateResult


REQUIREMENT_STORIES: dict[str, str] = {
    "REQ-E40-001": "S40.1",
    "REQ-E40-002": "S40.1",
    "REQ-E40-003": "S40.2",
    "REQ-E40-004": "S40.3",
    "REQ-E40-005": "S40.3",
    "REQ-E40-006": "S40.4",
    "REQ-E40-007": "S40.2",
    "REQ-E40-008": "S40.4",
}

_EVIDENCE_PATH = Path(
    "work/epics/e40-executive-cockpit-and-coaching/evidence/master-acceptance-e40.json"
)
_FOCUSED_TESTS = "tests/test_e40_executive_cockpit.py"


class E40RequirementGate:
    """Fail closed unless E40 qualification evidence and focused tests pass."""

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
                message="E40 qualification evidence missing",
            )
        try:
            payload = json.loads(evidence_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return GateResult(
                passed=False,
                gate_id=self.gate_id,
                message="E40 qualification evidence invalid",
            )
        if not _proves(payload, self.requirement_id):
            return GateResult(
                passed=False,
                gate_id=self.gate_id,
                message="E40 qualification does not prove requirement",
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
                message="E40 focused tests could not run",
            )
        if completed.returncode != 0:
            return GateResult(
                passed=False,
                gate_id=self.gate_id,
                message="E40 focused tests failed",
            )
        return GateResult(
            passed=True,
            gate_id=self.gate_id,
            message="E40 qualification and focused tests pass",
            details=(REQUIREMENT_STORIES[self.requirement_id], "focused tests pass"),
        )


def _proves(payload: object, requirement_id: str) -> bool:
    if not isinstance(payload, dict) or payload.get("status") != "pass":
        return False
    requirements = payload.get("requirements_proved")
    return isinstance(requirements, list) and requirement_id in requirements


class E40RequirementGate001(E40RequirementGate):
    requirement_id = "REQ-E40-001"
    gate_id = "gate-req-e40-001"
    description = "E40-001 guided company profile"


class E40RequirementGate002(E40RequirementGate):
    requirement_id = "REQ-E40-002"
    gate_id = "gate-req-e40-002"
    description = "E40-002 evidence-backed four-decision diagnostic"


class E40RequirementGate003(E40RequirementGate):
    requirement_id = "REQ-E40-003"
    gate_id = "gate-req-e40-003"
    description = "E40-003 pain drill-down"


class E40RequirementGate004(E40RequirementGate):
    requirement_id = "REQ-E40-004"
    gate_id = "gate-req-e40-004"
    description = "E40-004 strategy and OPSP coaching"


class E40RequirementGate005(E40RequirementGate):
    requirement_id = "REQ-E40-005"
    gate_id = "gate-req-e40-005"
    description = "E40-005 four-decision routing"


class E40RequirementGate006(E40RequirementGate):
    requirement_id = "REQ-E40-006"
    gate_id = "gate-req-e40-006"
    description = "E40-006 persistent execution continuity"


class E40RequirementGate007(E40RequirementGate):
    requirement_id = "REQ-E40-007"
    gate_id = "gate-req-e40-007"
    description = "E40-007 local visual cockpit"


class E40RequirementGate008(E40RequirementGate):
    requirement_id = "REQ-E40-008"
    gate_id = "gate-req-e40-008"
    description = "E40-008 honest guidance"


GATE_CLASSES: dict[str, type[E40RequirementGate]] = {
    gate.requirement_id: gate
    for gate in (
        E40RequirementGate001,
        E40RequirementGate002,
        E40RequirementGate003,
        E40RequirementGate004,
        E40RequirementGate005,
        E40RequirementGate006,
        E40RequirementGate007,
        E40RequirementGate008,
    )
}
