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
        "core_capability_catalog": "../../capabilities/mvp/catalog.json",
        "local_state": "consent-required",
        "managed_instruction_file": "CLAUDE.md",
        "remote_extensions": {"enabled_by_default": False},
    }
    assert (ADAPTER / manifest["core_skill"]).resolve() == (
        ROOT / "escala-skills" / "escala" / "SKILL.md"
    )
    assert (ADAPTER / manifest["core_capability_catalog"]).resolve() == (
        ROOT / "capabilities" / "mvp" / "catalog.json"
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
    claude_home = home / ".claude"
    claude_home.mkdir(parents=True)
    (claude_home / "CLAUDE.md").write_text("# Mis instrucciones\n", encoding="utf-8")
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / ".git").mkdir()
    shutil.copy2(INSTALLER, checkout / "install.sh")
    shutil.copytree(ROOT / "escala-skills", checkout / "escala-skills")
    (checkout / "capabilities").mkdir()
    shutil.copytree(ROOT / "capabilities" / "mvp", checkout / "capabilities" / "mvp")
    (checkout / "adapters").mkdir()
    shutil.copytree(ADAPTER, checkout / "adapters" / "claude")

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
    instructions = home / ".claude" / "CLAUDE.md"
    initial = instructions.read_text(encoding="utf-8")
    assert "# Mis instrucciones" in initial
    assert "<!-- ESCALA:BEGIN -->" in initial
    assert str(checkout / "escala-skills" / "escala" / "SKILL.md") in initial
    assert str(checkout / "capabilities" / "mvp" / "catalog.json") in initial

    repeated = subprocess.run(
        ["bash", str(checkout / "install.sh"), "--skills-only", "--platform", "claude"],
        cwd=checkout,
        env={"HOME": str(home), "PATH": f"{bin_dir}:{os.environ['PATH']}"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert repeated.returncode == 0, repeated.stderr
    assert instructions.read_text(encoding="utf-8") == initial


def test_malformed_managed_claude_block_fails_before_skill_install(
    tmp_path: Path,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    claude = bin_dir / "claude"
    claude.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    claude.chmod(0o755)
    home = tmp_path / "home"
    instructions = home / ".claude" / "CLAUDE.md"
    instructions.parent.mkdir(parents=True)
    original = "# Mis reglas\n<!-- ESCALA:BEGIN -->\ncontenido interrumpido\n"
    instructions.write_text(original, encoding="utf-8")

    completed = subprocess.run(
        ["bash", str(INSTALLER), "--skills-only", "--platform", "claude"],
        cwd=ROOT,
        env={"HOME": str(home), "PATH": f"{bin_dir}:{os.environ['PATH']}"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "está incompleto" in completed.stderr
    assert instructions.read_text(encoding="utf-8") == original
    assert not (home / ".claude" / "skills" / "escala").exists()


def test_checkout_claude_surface_exposes_only_escala() -> None:
    skills = ROOT / ".claude" / "skills"
    assert sorted(path.name for path in skills.iterdir()) == ["escala"]
    assert (skills / "escala").is_symlink()
    assert (skills / "escala").resolve() == ROOT / "escala-skills" / "escala"
