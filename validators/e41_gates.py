"""Executable acceptance gates for E41's seven lifecycle requirements."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import ClassVar

from raise_cli.gates.models import GateContext, GateResult


REQUIREMENT_STORIES: dict[str, str] = {
    "REQ-E41-001": "S41.1",
    "REQ-E41-002": "S41.1",
    "REQ-E41-003": "S41.2",
    "REQ-E41-004": "S41.3",
    "REQ-E41-005": "S41.3",
    "REQ-E41-006": "S41.2",
    "REQ-E41-007": "S41.4",
}

_EVIDENCE_PATH = Path(
    "work/epics/e41-local-installation-and-lifecycle/evidence/master-acceptance-e41.json"
)
_FOCUSED_TESTS = "tests/test_e41_lifecycle.py"


class E41RequirementGate:
    """Fail closed unless E41 qualification and focused tests pass."""

    requirement_id: ClassVar[str]
    gate_id: ClassVar[str]
    description: ClassVar[str]
    workflow_point: ClassVar[str] = "before:epic:close"

    def evaluate(self, context: GateContext) -> GateResult:
        evidence_path = context.working_dir / _EVIDENCE_PATH
        if evidence_path.is_symlink() or not evidence_path.is_file():
            return GateResult(False, self.gate_id, "E41 qualification evidence missing")
        try:
            payload = json.loads(evidence_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return GateResult(False, self.gate_id, "E41 qualification evidence invalid")
        if not _proves(payload, self.requirement_id):
            return GateResult(
                False, self.gate_id, "E41 qualification does not prove requirement"
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
            return GateResult(False, self.gate_id, "E41 focused tests could not run")
        if completed.returncode != 0:
            return GateResult(False, self.gate_id, "E41 focused tests failed")
        return GateResult(
            True,
            self.gate_id,
            "E41 qualification and focused tests pass",
            details=(REQUIREMENT_STORIES[self.requirement_id], "focused tests pass"),
        )


def _proves(payload: object, requirement_id: str) -> bool:
    if not isinstance(payload, dict) or payload.get("status") != "pass":
        return False
    requirements = payload.get("requirements_proved")
    return isinstance(requirements, list) and requirement_id in requirements


class E41RequirementGate001(E41RequirementGate):
    requirement_id = "REQ-E41-001"
    gate_id = "gate-req-e41-001"
    description = "E41-001 macOS installation"


class E41RequirementGate002(E41RequirementGate):
    requirement_id = "REQ-E41-002"
    gate_id = "gate-req-e41-002"
    description = "E41-002 Windows installation"


class E41RequirementGate003(E41RequirementGate):
    requirement_id = "REQ-E41-003"
    gate_id = "gate-req-e41-003"
    description = "E41-003 local runtime health"


class E41RequirementGate004(E41RequirementGate):
    requirement_id = "REQ-E41-004"
    gate_id = "gate-req-e41-004"
    description = "E41-004 migration backup and rollback"


class E41RequirementGate005(E41RequirementGate):
    requirement_id = "REQ-E41-005"
    gate_id = "gate-req-e41-005"
    description = "E41-005 verified update provenance"


class E41RequirementGate006(E41RequirementGate):
    requirement_id = "REQ-E41-006"
    gate_id = "gate-req-e41-006"
    description = "E41-006 optional synchronized exchange"


class E41RequirementGate007(E41RequirementGate):
    requirement_id = "REQ-E41-007"
    gate_id = "gate-req-e41-007"
    description = "E41-007 release qualification matrix"


GATE_CLASSES: dict[str, type[E41RequirementGate]] = {
    gate.requirement_id: gate
    for gate in (
        E41RequirementGate001,
        E41RequirementGate002,
        E41RequirementGate003,
        E41RequirementGate004,
        E41RequirementGate005,
        E41RequirementGate006,
        E41RequirementGate007,
    )
}
