"""Executable acceptance gates for E38's seven financial requirements."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import ClassVar

from validators.gate_contract import GateContext, GateResult


REQUIREMENT_STORIES: dict[str, str] = {
    "REQ-E38-001": "S38.1",
    "REQ-E38-002": "S38.1",
    "REQ-E38-003": "S38.2",
    "REQ-E38-004": "S38.2",
    "REQ-E38-005": "S38.3",
    "REQ-E38-006": "S38.3",
    "REQ-E38-007": "S38.4",
}

_EVIDENCE_PATH = Path(
    "work/epics/e38-cash-and-financial-intelligence/evidence/master-acceptance-e38.json"
)
_FOCUSED_TESTS = "tests/test_e38_financial_intelligence.py"


class E38RequirementGate:
    """Fail closed unless E38 evidence and focused qualification pass."""

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
                message="E38 qualification evidence missing",
            )
        try:
            payload = json.loads(evidence_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return GateResult(
                passed=False,
                gate_id=self.gate_id,
                message="E38 qualification evidence invalid",
            )
        if not _proves(payload, self.requirement_id):
            return GateResult(
                passed=False,
                gate_id=self.gate_id,
                message="E38 qualification does not prove requirement",
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
                message="E38 focused tests could not run",
            )
        if completed.returncode != 0:
            return GateResult(
                passed=False,
                gate_id=self.gate_id,
                message="E38 focused tests failed",
            )
        return GateResult(
            passed=True,
            gate_id=self.gate_id,
            message="E38 qualification and focused tests pass",
            details=(REQUIREMENT_STORIES[self.requirement_id], "focused tests pass"),
        )


def _proves(payload: object, requirement_id: str) -> bool:
    if not isinstance(payload, dict) or payload.get("status") != "pass":
        return False
    requirements = payload.get("requirements_proved")
    return isinstance(requirements, list) and requirement_id in requirements


class E38RequirementGate001(E38RequirementGate):
    requirement_id = "REQ-E38-001"
    gate_id = "gate-req-e38-001"
    description = "E38-001 flexible workbook profiling"


class E38RequirementGate002(E38RequirementGate):
    requirement_id = "REQ-E38-002"
    gate_id = "gate-req-e38-002"
    description = "E38-002 ambiguity questions before mapping"


class E38RequirementGate003(E38RequirementGate):
    requirement_id = "REQ-E38-003"
    gate_id = "gate-req-e38-003"
    description = "E38-003 traceable statement reconstruction"


class E38RequirementGate004(E38RequirementGate):
    requirement_id = "REQ-E38-004"
    gate_id = "gate-req-e38-004"
    description = "E38-004 figure provenance"


class E38RequirementGate005(E38RequirementGate):
    requirement_id = "REQ-E38-005"
    gate_id = "gate-req-e38-005"
    description = "E38-005 CCC and Power-of-One scenarios"


class E38RequirementGate006(E38RequirementGate):
    requirement_id = "REQ-E38-006"
    gate_id = "gate-req-e38-006"
    description = "E38-006 confidence and freshness fail-closed"


class E38RequirementGate007(E38RequirementGate):
    requirement_id = "REQ-E38-007"
    gate_id = "gate-req-e38-007"
    description = "E38-007 local visual evidence report"


GATE_CLASSES: dict[str, type[E38RequirementGate]] = {
    gate.requirement_id: gate
    for gate in (
        E38RequirementGate001,
        E38RequirementGate002,
        E38RequirementGate003,
        E38RequirementGate004,
        E38RequirementGate005,
        E38RequirementGate006,
        E38RequirementGate007,
    )
}
