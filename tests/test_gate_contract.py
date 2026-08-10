from __future__ import annotations

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
