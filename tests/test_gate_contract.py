from __future__ import annotations

from importlib.metadata import entry_points
from pathlib import Path

from validators.gate_contract import GateContext, GateResult


def test_local_gate_contract_has_safe_compatible_defaults(tmp_path: Path) -> None:
    context = GateContext(gate_id="gate-example", working_dir=tmp_path)
    result = GateResult(passed=True, gate_id=context.gate_id)

    assert context.extra_args == ()
    assert context.working_dir == tmp_path
    assert result.details == ()
    assert result.advisory is False
    assert result.skipped is False


def test_qualification_gate_entry_points_load_without_raise_cli() -> None:
    expected = {
        "e37-req-001",
        "e38-req-001",
        "e39-req-001",
        "e40-req-001",
        "e41-req-001",
    }
    discovered = {
        entry_point.name: entry_point.load()
        for entry_point in entry_points(group="rai.gates")
        if entry_point.name in expected
    }

    assert set(discovered) == expected
    assert all(isinstance(gate, type) for gate in discovered.values())
