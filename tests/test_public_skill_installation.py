"""E56 installer contract: publish one public skill without touching user state."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from validators.public_export import (
    build_public_export,
    load_public_export_policy,
    load_third_party_inventory,
)

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install.sh"


def test_skills_only_install_publishes_one_front_door(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir(exist_ok=True)
    fake_codex = fake_bin / "codex"
    fake_codex.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_codex.chmod(0o755)
    skills_dir = tmp_path / "home" / ".codex" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "escala-cash").symlink_to(ROOT / "escala-skills/escala-cash")

    result = subprocess.run(
        ["bash", str(INSTALLER), "--skills-only"],
        cwd=ROOT,
        env={
            "HOME": str(tmp_path / "home"),
            "PATH": str(fake_bin) + ":" + os.environ["PATH"],
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    installed = skills_dir / "escala"
    assert installed.is_symlink()
    assert installed.resolve() == ROOT / "escala-skills/escala"
    assert not (skills_dir / "escala-cash").exists()
    assert (
        installed / "../catalog.yaml"
    ).resolve() == ROOT / "escala-skills/catalog.yaml"
    assert "1 skills instalados" in result.stdout
    assert "lenguaje natural" in result.stdout


def test_installer_rejects_unknown_arguments_without_side_effects(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        ["bash", str(INSTALLER), "--not-a-real-option"],
        cwd=ROOT,
        env={"HOME": str(tmp_path / "home"), "PATH": os.environ["PATH"]},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Uso:" in result.stderr
    assert not (tmp_path / "home").exists()


def _portable_artifact(tmp_path: Path) -> Path:
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    artifact = tmp_path / "portable-escala"
    build_public_export(
        repository=ROOT,
        destination=artifact,
        source_commit=source_commit,
        policy=load_public_export_policy(ROOT / "governance/public-export.yaml"),
        inventory=load_third_party_inventory(ROOT / "governance/third-party.yaml"),
    )
    assert not (artifact / ".git").exists()
    return artifact


def _portable_install(artifact: Path, home: Path) -> subprocess.CompletedProcess[str]:
    fake_bin = home.parent / "bin"
    fake_bin.mkdir(exist_ok=True)
    fake_codex = fake_bin / "codex"
    fake_codex.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_codex.chmod(0o755)
    return subprocess.run(
        ["bash", str(artifact / "install.sh"), "--skills-only"],
        cwd=artifact,
        env={
            "HOME": str(home),
            "PATH": str(fake_bin) + ":" + os.environ["PATH"],
        },
        capture_output=True,
        text=True,
        check=False,
    )


def test_portable_export_installs_without_source_checkout_and_rejects_tampering(
    tmp_path: Path,
) -> None:
    artifact = _portable_artifact(tmp_path)

    first = _portable_install(artifact, tmp_path / "portable-home")
    second = _portable_install(artifact, tmp_path / "portable-home")
    installed = tmp_path / "portable-home/.codex/skills/escala"

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert installed.is_symlink()
    assert installed.resolve() == artifact / "escala-skills/escala"
    verification = subprocess.run(
        [sys.executable, str(artifact / "scripts/verify_portable_bundle.py")],
        cwd=artifact,
        capture_output=True,
        text=True,
        check=False,
    )
    assert verification.returncode == 0, verification.stderr

    catalog = artifact / "escala-skills/catalog.yaml"
    catalog.write_text(
        catalog.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8"
    )
    rejected_home = tmp_path / "rejected-home"
    rejected = _portable_install(artifact, rejected_home)

    assert rejected.returncode == 1
    assert "no pasó su verificación" in rejected.stderr
    assert not (rejected_home / ".codex/skills/escala").exists()
