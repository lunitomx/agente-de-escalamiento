from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_e76_gate_preserves_codex_only_contract() -> None:
    script = (ROOT / "scripts/check_e76_workspace_contract.py").read_text()
    assert "workspace-hermes_config_missing" in script
    assert "workspace-runtime_python_missing" in script
    assert "workspace-runtime_command_outside_workspace" in script
    assert ".venv-mcp" in script
    assert ".hermes" in script
