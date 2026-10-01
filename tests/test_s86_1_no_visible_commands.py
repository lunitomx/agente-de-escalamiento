"""S86.1: the owner only talks to ESCALA — no slash commands, no stale shortcuts."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "escala-skills"
FRONT_DOOR = "escala"


def _internal_procedures() -> list[Path]:
    return sorted(
        path for path in SKILLS.glob("*/SKILL.md") if path.parent.name != FRONT_DOOR
    )


def test_internal_procedures_never_show_slash_commands() -> None:
    offenders = [
        f"{path.relative_to(ROOT)}:{number}"
        for path in _internal_procedures()
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if "/escala-" in line
    ]

    assert offenders == []


def test_internal_references_still_name_existing_procedures() -> None:
    """A rewritten internal reference must keep a real procedure id."""

    known = {path.parent.name for path in SKILLS.glob("escala*/SKILL.md")}
    pattern = re.compile(r"procedimiento interno `(escala[a-z0-9-]*)`")
    referenced = {
        match
        for path in _internal_procedures()
        for match in pattern.findall(path.read_text(encoding="utf-8"))
    }

    assert referenced, "expected internal references to procedures"
    assert referenced - known == set()


# --- Q4: stale shortcuts from earlier installs -------------------------------

INSTALLER = ROOT / "install.sh"
UPDATER = ROOT / "update.sh"


def _fake_bin(tmp_path: Path, *commands: str) -> Path:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir(exist_ok=True)
    for command in commands:
        executable = fake_bin / command
        executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        executable.chmod(0o755)
    return fake_bin


def _install_skills_only(
    home: Path, fake_bin: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(INSTALLER), "--skills-only", "--platform", "claude"],
        cwd=ROOT,
        env={"HOME": str(home), "PATH": f"{fake_bin}:{os.environ['PATH']}"},
        capture_output=True,
        text=True,
        check=False,
    )


def test_installer_removes_only_stale_escala_symlinks(tmp_path: Path) -> None:
    home = tmp_path / "home"
    skills = home / ".claude" / "skills"
    skills.mkdir(parents=True)
    old_repo = tmp_path / "agente-de-escalamiento" / "escala-skills"
    (old_repo / "escala-cash").mkdir(parents=True)
    (skills / "escala").symlink_to(old_repo / "escala")
    (skills / "escala-cash").symlink_to(old_repo / "escala-cash")
    (skills / "escala-people").symlink_to(ROOT / "escala-skills" / "escala-people")
    (skills / "escala-gone").symlink_to(tmp_path / "missing" / "escala-gone")
    (skills / "escala.bak").symlink_to(old_repo / "escala-cash")
    (skills / "escala-real-dir").mkdir()
    (skills / "escala-notes.md").write_text("mine", encoding="utf-8")
    (skills / "scaleup-cash").symlink_to(old_repo / "escala-cash")
    (skills / "kokoro").symlink_to(old_repo / "escala-cash")

    result = _install_skills_only(home, _fake_bin(tmp_path, "claude"))

    assert result.returncode == 0, result.stderr
    front_door = skills / "escala"
    assert front_door.is_symlink()
    assert front_door.resolve() == ROOT / "escala-skills" / "escala"
    for stale in ("escala-cash", "escala-people", "escala-gone", "escala.bak"):
        assert not (skills / stale).is_symlink(), stale
    assert (skills / "escala-real-dir").is_dir()
    assert (skills / "escala-notes.md").read_text(encoding="utf-8") == "mine"
    assert (skills / "scaleup-cash").is_symlink()
    assert (skills / "kokoro").is_symlink()
    assert (old_repo / "escala-cash").is_dir()
    assert "Quité 4 atajos viejos; ahora sólo hablas con ESCALA." in result.stdout


def test_installer_stays_quiet_when_nothing_is_stale(tmp_path: Path) -> None:
    home = tmp_path / "home"
    fake_bin = _fake_bin(tmp_path, "claude")
    (home / ".claude" / "skills").mkdir(parents=True)
    (home / ".claude" / "skills" / "escala-cash").symlink_to(
        ROOT / "escala-skills" / "escala-cash"
    )

    first = _install_skills_only(home, fake_bin)
    second = _install_skills_only(home, fake_bin)

    assert first.returncode == 0, first.stderr
    assert "Quité 1 atajo viejo; ahora sólo hablas con ESCALA." in first.stdout
    assert second.returncode == 0, second.stderr
    assert "atajo" not in second.stdout


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
            "GIT_CONFIG_GLOBAL": "/dev/null",
        },
    )


def _synthetic_repo(tmp_path: Path) -> tuple[Path, Path]:
    """A tiny repo whose install.sh only records the arguments it received."""

    origin = tmp_path / "origin.git"
    repo = tmp_path / "repo"
    record = tmp_path / "install-args.txt"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    _git(tmp_path, "init", "-q", "-b", "main", str(repo))
    (repo / "install.sh").write_text(
        f'#!/usr/bin/env bash\nprintf "%s\\n" "$*" > "{record}"\n',
        encoding="utf-8",
    )
    _git(repo, "add", "install.sh")
    _git(repo, "commit", "-q", "-m", "init")
    _git(repo, "remote", "add", "origin", str(origin))
    _git(repo, "push", "-q", "origin", "main")
    return repo, record


def _run_updater(home: Path, repo: Path) -> subprocess.CompletedProcess[str]:
    config = home / ".config" / "agente-de-escalamiento"
    config.mkdir(parents=True, exist_ok=True)
    (config / "repo-path").write_text(f"{repo}\n", encoding="utf-8")
    return subprocess.run(
        ["bash", str(UPDATER)],
        cwd=home,
        env={
            "HOME": str(home),
            "PATH": os.environ["PATH"],
            "GIT_CONFIG_GLOBAL": "/dev/null",
        },
        capture_output=True,
        text=True,
        check=False,
    )


def test_updater_reinstalls_where_escala_was_installed(tmp_path: Path) -> None:
    repo, record = _synthetic_repo(tmp_path)
    home = tmp_path / "home"
    (home / ".claude" / "skills").mkdir(parents=True)
    (home / ".claude" / "skills" / "escala-cash").symlink_to(tmp_path / "old")
    (home / ".codex" / "skills").mkdir(parents=True)
    (home / ".codex" / "skills" / "escala").symlink_to(tmp_path / "old")
    (home / ".hermes" / "skills").mkdir(parents=True)
    (home / ".hermes" / "skills" / "scaleup-cash").symlink_to(tmp_path / "old")

    result = _run_updater(home, repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert record.read_text(encoding="utf-8").split() == [
        "--platform",
        "claude",
        "--platform",
        "codex",
    ]
    assert "/escala-" not in result.stdout


def test_updater_without_previous_install_explains_next_step(tmp_path: Path) -> None:
    repo, record = _synthetic_repo(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    result = _run_updater(home, repo)

    assert result.returncode == 1
    assert not record.exists()
    assert "./install.sh --platform" in result.stdout + result.stderr
