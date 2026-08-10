"""TDD contracts for the E37 master-requirement gates."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from validators.gate_contract import GateContext
from validators import e37_gates


def _qualification_payload(requirement_id: str) -> dict[str, object]:
    story = e37_gates.REQUIREMENT_STORIES[requirement_id]
    requirements_key = (
        "requirements_ready_for_master_ledger"
        if story == "S37.1"
        else "requirements_ready_for_exact_receipt"
    )
    return {
        "status": "pass",
        requirements_key: [requirement_id],
        "source_commit": "0" * 40,
    }


@pytest.mark.parametrize("requirement_id", sorted(e37_gates.REQUIREMENT_STORIES))
def test_requirement_gate_passes_qualified_story_and_focused_tests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    requirement_id: str,
) -> None:
    story = e37_gates.REQUIREMENT_STORIES[requirement_id]
    evidence_dir = (
        tmp_path / "work/epics/e37-local-workspace-flexible-ingestion/stories"
    )
    qualification = evidence_dir / f"s{story[1:].lower()}-evidence/qualification.json"
    qualification.parent.mkdir(parents=True)
    qualification.write_text(
        json.dumps(_qualification_payload(requirement_id)), encoding="utf-8"
    )

    monkeypatch.setattr(
        e37_gates.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout="", stderr=""
        ),
    )

    gate = e37_gates.GATE_CLASSES[requirement_id]()
    result = gate.evaluate(GateContext(gate_id=gate.gate_id, working_dir=tmp_path))

    assert result.passed is True
    assert result.gate_id == f"gate-{requirement_id.lower()}"


def test_requirement_gate_fails_closed_when_story_evidence_is_missing(
    tmp_path: Path,
) -> None:
    gate = e37_gates.GATE_CLASSES["REQ-E37-001"]()

    result = gate.evaluate(GateContext(gate_id=gate.gate_id, working_dir=tmp_path))

    assert result.passed is False
    assert result.gate_id == "gate-req-e37-001"
    assert result.message == "story qualification evidence missing"


def test_requirement_gate_fails_when_focused_tests_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requirement_id = "REQ-E37-006"
    story = e37_gates.REQUIREMENT_STORIES[requirement_id]
    qualification = (
        tmp_path
        / "work/epics/e37-local-workspace-flexible-ingestion/stories"
        / f"s{story[1:].lower()}-evidence/qualification.json"
    )
    qualification.parent.mkdir(parents=True)
    qualification.write_text(
        json.dumps(_qualification_payload(requirement_id)), encoding="utf-8"
    )
    monkeypatch.setattr(
        e37_gates.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=1, stdout="", stderr=""
        ),
    )

    result = e37_gates.GATE_CLASSES[requirement_id]().evaluate(
        GateContext(gate_id="gate-req-e37-006", working_dir=tmp_path)
    )

    assert result.passed is False
    assert result.message == "focused tests failed"
