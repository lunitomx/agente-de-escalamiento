"""Executable acceptance gates for E37's local workspace requirements."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import ClassVar

from validators.gate_contract import GateContext, GateResult


REQUIREMENT_STORIES: dict[str, str] = {
    "REQ-E37-001": "S37.1",
    "REQ-E37-002": "S37.1",
    "REQ-E37-003": "S37.2",
    "REQ-E37-004": "S37.2",
    "REQ-E37-005": "S37.2",
    "REQ-E37-006": "S37.3",
    "REQ-E37-007": "S37.3",
}

_FOCUSED_TESTS: dict[str, str] = {
    "S37.1": "tests/test_workspace_authority.py",
    "S37.2": "tests/test_workspace_ingestion.py",
    "S37.3": "tests/test_workspace_inbox.py",
}

_EVIDENCE_ROOT = Path("work/epics/e37-local-workspace-flexible-ingestion/stories")


class E37RequirementGate:
    """Validate one E37 story qualification and its focused tests."""

    requirement_id: ClassVar[str]
    gate_id: ClassVar[str]
    description: ClassVar[str]
    workflow_point: ClassVar[str] = "before:epic:close"

    def evaluate(self, context: GateContext) -> GateResult:
        """Fail closed unless the exact story evidence and tests pass."""

        qualification_path = _qualification_path(
            context.working_dir, self.requirement_id
        )
        if qualification_path.is_symlink() or not qualification_path.is_file():
            return GateResult(
                passed=False,
                gate_id=self.gate_id,
                message="story qualification evidence missing",
            )

        try:
            payload = json.loads(qualification_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return GateResult(
                passed=False,
                gate_id=self.gate_id,
                message="story qualification evidence invalid",
            )
        if not _qualification_proves_requirement(payload, self.requirement_id):
            return GateResult(
                passed=False,
                gate_id=self.gate_id,
                message="story qualification does not prove requirement",
            )

        story = REQUIREMENT_STORIES[self.requirement_id]
        test_path = _FOCUSED_TESTS[story]
        command = [sys.executable, "-m", "pytest", test_path, "-q"]
        try:
            completed = subprocess.run(
                command,
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
                message="focused tests could not run",
            )
        if completed.returncode != 0:
            return GateResult(
                passed=False,
                gate_id=self.gate_id,
                message="focused tests failed",
            )
        return GateResult(
            passed=True,
            gate_id=self.gate_id,
            message="story qualification and focused tests pass",
            details=(story, "focused tests pass"),
        )


def _qualification_path(working_dir: Path, requirement_id: str) -> Path:
    story = REQUIREMENT_STORIES[requirement_id]
    return (
        working_dir
        / _EVIDENCE_ROOT
        / f"s{story[1:].lower()}-evidence"
        / "qualification.json"
    )


def _qualification_proves_requirement(
    payload: object,
    requirement_id: str,
) -> bool:
    if not isinstance(payload, dict) or payload.get("status") != "pass":
        return False
    story = REQUIREMENT_STORIES[requirement_id]
    key = (
        "requirements_ready_for_master_ledger"
        if story == "S37.1"
        else "requirements_ready_for_exact_receipt"
    )
    requirements = payload.get(key)
    return isinstance(requirements, list) and requirement_id in requirements


class E37RequirementGate001(E37RequirementGate):
    requirement_id = "REQ-E37-001"
    gate_id = "gate-req-e37-001"
    description = "E37-001 local runtime and state authority"


class E37RequirementGate002(E37RequirementGate):
    requirement_id = "REQ-E37-002"
    gate_id = "gate-req-e37-002"
    description = "E37-002 reject synchronized SQLite authority"


class E37RequirementGate003(E37RequirementGate):
    requirement_id = "REQ-E37-003"
    gate_id = "gate-req-e37-003"
    description = "E37-003 flexible declared format ingestion"


class E37RequirementGate004(E37RequirementGate):
    requirement_id = "REQ-E37-004"
    gate_id = "gate-req-e37-004"
    description = "E37-004 structural inference and clarification"


class E37RequirementGate005(E37RequirementGate):
    requirement_id = "REQ-E37-005"
    gate_id = "gate-req-e37-005"
    description = "E37-005 redacted rerun-safe source identity"


class E37RequirementGate006(E37RequirementGate):
    requirement_id = "REQ-E37-006"
    gate_id = "gate-req-e37-006"
    description = "E37-006 filesystem-only idempotent inbox"


class E37RequirementGate007(E37RequirementGate):
    requirement_id = "REQ-E37-007"
    gate_id = "gate-req-e37-007"
    description = "E37-007 safe failure isolation and reporting"


GATE_CLASSES: dict[str, type[E37RequirementGate]] = {
    requirement_id: gate_class
    for requirement_id, gate_class in (
        ("REQ-E37-001", E37RequirementGate001),
        ("REQ-E37-002", E37RequirementGate002),
        ("REQ-E37-003", E37RequirementGate003),
        ("REQ-E37-004", E37RequirementGate004),
        ("REQ-E37-005", E37RequirementGate005),
        ("REQ-E37-006", E37RequirementGate006),
        ("REQ-E37-007", E37RequirementGate007),
    )
}
