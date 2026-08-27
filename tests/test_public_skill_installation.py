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


def _portable_artifact(destination: Path) -> Path:
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    build_public_export(
        repository=ROOT,
        destination=destination,
        source_commit=source_commit,
        policy=load_public_export_policy(ROOT / "governance/public-export.yaml"),
        inventory=load_third_party_inventory(ROOT / "governance/third-party.yaml"),
    )
    assert not (destination / ".git").exists()
    return destination


def _portable_install(artifact: Path, home: Path) -> subprocess.CompletedProcess[str]:
    fake_bin = home.parent / "bin"
    fake_bin.mkdir(exist_ok=True)
    for command in ("claude", "hermes", "codex"):
        executable = fake_bin / command
        executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        executable.chmod(0o755)
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
    active = _portable_artifact(tmp_path / "active-escala")
    home = tmp_path / "portable-home"
    installed = tuple(
        home / f"{directory}/skills/escala"
        for directory in (".claude", ".hermes", ".codex")
    )

    first = _portable_install(active, home)
    assert first.returncode == 0, first.stderr
    assert all(path.is_symlink() for path in installed)
    assert all(path.resolve() == active / "escala-skills/escala" for path in installed)

    candidate = _portable_artifact(tmp_path / "tampered-candidate")
    catalog = candidate / "escala-skills/catalog.yaml"
    catalog.write_text(
        catalog.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8"
    )
    rejected = _portable_install(candidate, home)

    assert rejected.returncode == 1
    assert "no pasó su verificación" in rejected.stderr
    assert all(path.resolve() == active / "escala-skills/escala" for path in installed)

    replacement = _portable_artifact(tmp_path / "replacement-escala")
    update = _portable_install(replacement, home)
    idempotent = _portable_install(replacement, home)

    assert update.returncode == 0, update.stderr
    assert idempotent.returncode == 0, idempotent.stderr
    assert all(
        path.resolve() == replacement / "escala-skills/escala" for path in installed
    )
    assert not any(
        "tests" in path.relative_to(replacement).parts
        for path in replacement.rglob("*")
        if path.is_file()
    )
    imports = subprocess.run(
        [
            str(replacement / "scripts/escala-python"),
            "-c",
            (
                "import importlib; "
                'modules = ("coaching.dashboard", "coaching.decision", '
                '"coaching.diagnose", "coaching.evidence", '
                '"coaching.execution_habits", "coaching.export", '
                '"coaching.level", "coaching.people_facchart", '
                '"coaching.progress", "coaching.pulse", '
                '"coaching.qualifier", "coaching.responder", '
                '"coaching.reviewer", "coaching.router", '
                '"coaching.selector", "coaching.strategy_opsp", '
                '"coaching.summary", "coaching.welcome", '
                '"coaching.worksheet"); '
                "[importlib.import_module(name) for name in modules]"
            ),
        ],
        cwd=tmp_path,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert imports.returncode == 0, imports.stderr
    verification = subprocess.run(
        [sys.executable, str(replacement / "scripts/verify_portable_bundle.py")],
        cwd=replacement,
        capture_output=True,
        text=True,
        check=False,
    )
    assert verification.returncode == 0, verification.stderr
