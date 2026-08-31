"""S67.3 contract tests for the minimal Claude Code adapter."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "adapters" / "claude"
INSTALLER = ROOT / "install.sh"


def test_claude_adapter_has_one_declared_public_door_and_portable_core() -> None:
    """Claude may package ESCALA, but cannot become a second product core."""
    manifest = json.loads((ADAPTER / "adapter.json").read_text(encoding="utf-8"))

    assert manifest == {
        "schema_version": 1,
        "platform": "claude-code",
        "public_entrypoint": "escala",
        "core_skill": "../../escala-skills/escala/SKILL.md",
        "local_state": "consent-required",
        "remote_extensions": {"enabled_by_default": False},
    }
    assert (ADAPTER / manifest["core_skill"]).resolve() == (
        ROOT / "escala-skills" / "escala" / "SKILL.md"
    )


def test_claude_adapter_contains_no_methodology_or_remote_configuration() -> None:
    """Platform files must not list routes, credentials, or a second skill."""
    allowed = {"README.md", "CLAUDE.template.md", "adapter.json"}
    assert {path.name for path in ADAPTER.iterdir() if path.is_file()} == allowed

    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in sorted(ADAPTER.iterdir())
        if path.is_file()
    )
    forbidden = (
        "procedure.",
        "capability.",
        "route_capability",
        "mcp",
        "credential",
        "secret",
        "token",
        "connector",
        "cash",
        "people",
        "strategy",
        "execution",
    )
    assert not [term for term in forbidden if term in combined]
    assert "single public entrypoint" in combined
    assert "portable core" in combined
    assert "consent" in combined


def test_clean_claude_install_exposes_only_escala(tmp_path: Path) -> None:
    """The existing targeted installer remains the integration boundary."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    claude = bin_dir / "claude"
    claude.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    claude.chmod(0o755)
    home = tmp_path / "home"
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / ".git").mkdir()
    shutil.copy2(INSTALLER, checkout / "install.sh")
    shutil.copytree(ROOT / "escala-skills", checkout / "escala-skills")

    completed = subprocess.run(
        ["bash", str(checkout / "install.sh"), "--skills-only", "--platform", "claude"],
        cwd=checkout,
        env={"HOME": str(home), "PATH": f"{bin_dir}:{os.environ['PATH']}"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    installed = home / ".claude" / "skills"
    assert [path.name for path in installed.iterdir()] == ["escala"]
    assert (installed / "escala").resolve() == checkout / "escala-skills" / "escala"
