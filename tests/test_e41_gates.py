from __future__ import annotations

import json
from pathlib import Path
import subprocess

from raise_cli.gates.models import GateContext

from validators import e41_gates


def test_e41_gate_fails_closed_without_qualification(tmp_path: Path) -> None:
    gate = e41_gates.GATE_CLASSES["REQ-E41-001"]()
    result = gate.evaluate(GateContext(gate_id=gate.gate_id, working_dir=tmp_path))
    assert result.passed is False
    assert result.message == "E41 qualification evidence missing"


def test_e41_gates_require_focused_tests(tmp_path: Path, monkeypatch) -> None:
    evidence = tmp_path / e41_gates._EVIDENCE_PATH
    evidence.parent.mkdir(parents=True)
    evidence.write_text(
        json.dumps({"status": "pass", "requirements_proved": ["REQ-E41-001"]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        e41_gates.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0),
    )
    result = e41_gates.GATE_CLASSES["REQ-E41-001"]().evaluate(
        GateContext(gate_id="gate-req-e41-001", working_dir=tmp_path)
    )
    assert result.passed is True
