"""S67.5 verifies packaged private specialists without widening ESCALA's door."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import stat
import subprocess

from adapters.codex.build_adapter import build_codex_adapter
from validators.specialist_agents import (
    CLAUDE_AGENT_DIRECTORY,
    CODEX_AGENT_DIRECTORY,
    SPECIALIST_AREAS,
    SPECIALIST_CONTRACT_PATH,
    build_specialist_contract,
    validate_specialist_artifacts,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "capabilities" / "mvp" / "catalog.json"
INSTALLER = ROOT / "install.sh"


def _executable(directory: Path, name: str) -> None:
    path = directory / name
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _checkout_with_adapter_inputs(root: Path) -> Path:
    checkout = root / "checkout"
    checkout.mkdir()
    (checkout / ".git").mkdir()
    shutil.copy2(INSTALLER, checkout / "install.sh")
    (checkout / "install.sh").chmod(0o755)
    shutil.copytree(ROOT / "escala-skills", checkout / "escala-skills")
    shutil.copytree(ROOT / "capabilities", checkout / "capabilities")
    shutil.copytree(ROOT / "adapters", checkout / "adapters")
    return checkout


def _run_install(
    checkout: Path, home: Path, bin_dir: Path, *arguments: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(checkout / "install.sh"), *arguments],
        cwd=checkout,
        env={"HOME": str(home), "PATH": f"{bin_dir}:{os.environ['PATH']}"},
        capture_output=True,
        text=True,
        check=False,
    )


def test_specialist_contract_is_exactly_the_four_e45_profiles() -> None:
    contract = json.loads(SPECIALIST_CONTRACT_PATH.read_text(encoding="utf-8"))

    assert contract == build_specialist_contract()
    assert contract["public_entrypoint"] == "escala"
    assert [item["decision_area"] for item in contract["specialists"]] == list(
        SPECIALIST_AREAS
    )
    assert all(
        set(item)
        == {
            "agent_name",
            "capability_ids",
            "contract_ref",
            "decision_area",
            "id",
            "limits",
            "minimum_context",
            "non_trigger",
            "output",
            "permissions",
            "role",
            "trigger",
        }
        for item in contract["specialists"]
    )


def test_generated_platform_agents_are_complete_private_and_drift_free() -> None:
    assert validate_specialist_artifacts() == ()

    expected = {f"escala-{area}" for area in SPECIALIST_AREAS}
    assert {path.stem for path in CODEX_AGENT_DIRECTORY.glob("*.toml")} == expected
    assert {path.stem for path in CLAUDE_AGENT_DIRECTORY.glob("*.md")} == expected

    for area in SPECIALIST_AREAS:
        codex = (CODEX_AGENT_DIRECTORY / f"escala-{area}.toml").read_text(
            encoding="utf-8"
        )
        claude = (CLAUDE_AGENT_DIRECTORY / f"escala-{area}.md").read_text(
            encoding="utf-8"
        )
        assert f'name = "escala-{area}"' in codex
        assert f"name: escala-{area}" in claude
        assert "private specialist" in codex.lower()
        assert "private specialist" in claude.lower()
        assert "public command" in codex.lower()
        assert "public command" in claude.lower()
        assert "mcp" not in codex.lower()
        assert "credential" not in codex.lower()
        assert "mcp" not in claude.lower()
        assert "credential" not in claude.lower()


def test_codex_adapter_packages_private_agents_but_one_public_skill(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "install" / "codex"
    destination.parent.mkdir()

    build_codex_adapter(
        catalog_path=CATALOG,
        output=destination,
        allowed_root=destination.parent,
    )

    manifest = json.loads(
        (destination / "codex-adapter.json").read_text(encoding="utf-8")
    )
    assert manifest["public_skills"] == ["escala"]
    assert manifest["private_agents"] == [f"escala-{area}" for area in SPECIALIST_AREAS]
    assert {path.stem for path in (destination / "agents").glob("*.toml")} == {
        f"escala-{area}" for area in SPECIALIST_AREAS
    }
    assert [
        path.parent.name for path in (destination / "skills").glob("*/SKILL.md")
    ] == ["escala"]


def test_explicit_specialist_install_preserves_foreign_agents(tmp_path: Path) -> None:
    checkout = _checkout_with_adapter_inputs(tmp_path)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _executable(bin_dir, "claude")
    _executable(bin_dir, "codex")
    home = tmp_path / "home"
    foreign_claude = home / ".claude" / "agents" / "other-team.md"
    foreign_codex = home / ".codex" / "agents" / "other-team.toml"
    foreign_claude.parent.mkdir(parents=True)
    foreign_codex.parent.mkdir(parents=True)
    foreign_claude.write_text("preserve claude", encoding="utf-8")
    foreign_codex.write_text("preserve codex", encoding="utf-8")

    completed = _run_install(
        checkout,
        home,
        bin_dir,
        "--skills-only",
        "--with-specialists",
        "--platform",
        "claude",
        "--platform",
        "codex",
    )

    assert completed.returncode == 0, completed.stderr
    assert foreign_claude.read_text(encoding="utf-8") == "preserve claude"
    assert foreign_codex.read_text(encoding="utf-8") == "preserve codex"
    assert {
        path.stem for path in (home / ".claude" / "agents").glob("escala-*.md")
    } == {f"escala-{area}" for area in SPECIALIST_AREAS}
    assert {
        path.stem for path in (home / ".codex" / "agents").glob("escala-*.toml")
    } == {f"escala-{area}" for area in SPECIALIST_AREAS}
    assert sorted(path.name for path in (home / ".claude" / "skills").iterdir()) == [
        "escala"
    ]
    assert sorted(path.name for path in (home / ".codex" / "skills").iterdir()) == [
        "escala"
    ]


def test_regular_skills_only_keeps_specialists_opt_in(tmp_path: Path) -> None:
    checkout = _checkout_with_adapter_inputs(tmp_path)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _executable(bin_dir, "codex")
    home = tmp_path / "home"

    completed = _run_install(
        checkout, home, bin_dir, "--skills-only", "--platform", "codex"
    )

    assert completed.returncode == 0, completed.stderr
    assert not (home / ".codex" / "agents").exists()
    assert (home / ".codex" / "skills" / "escala").is_symlink()
