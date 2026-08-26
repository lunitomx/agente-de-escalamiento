"""E56 installer contract: publish one public skill without touching user state."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install.sh"


def test_skills_only_install_publishes_one_front_door(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
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
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
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
