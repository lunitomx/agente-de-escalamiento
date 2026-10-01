"""S86.9: one copy-paste line installs ESCALA for Claude Code.

``instalar.sh`` runs against a fake HOME and a PATH made only of stubs and a
few real shell utilities: no network, no real git/uv/claude, nothing outside
``tmp_path``. Every stub appends ``name args`` to ``$CALLS``.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "instalar.sh"
PILOT_GUIDE = ROOT / "PILOTO-EMPRESARIOS.md"
REPO_URL = "https://github.com/lunitomx/agente-de-escalamiento.git"
FINAL_LINE = (
    "Listo. Pega esta línea, presiona Enter y cuéntale a ESCALA "
    "lo que más te preocupa de tu negocio:  cd ~/ESCALA && claude"
)

# Real utilities the bootstrap (and the stubs) may use. Anything else —
# git, uv, curl, claude, xcode-select, uname — is a stub or absent.
SYSTEM_TOOLS = ("sh", "bash", "env", "cat", "cp", "mkdir", "date", "dirname")

FAKE_INSTALL = """#!/usr/bin/env bash
echo "install.sh $* (cwd=$PWD)" >> "$CALLS"
exit "${FAKE_INSTALL_EXIT:-0}"
"""

GIT_STUB = """#!/bin/sh
echo "git $*" >> "$CALLS"
if [ "$1" = "-C" ]; then
    shift 2
fi
case "$1" in
    clone)
        [ "${FAKE_CLONE_EXIT:-0}" = 0 ] || exit "$FAKE_CLONE_EXIT"
        for dest in "$@"; do :; done
        mkdir -p "$dest/.git" "$dest/escala-skills"
        cp "$STUBS/fake-install.sh" "$dest/install.sh"
        ;;
    remote) echo "${FAKE_ORIGIN-https://github.com/lunitomx/agente-de-escalamiento.git}" ;;
    pull) exit "${FAKE_PULL_EXIT:-0}" ;;
esac
exit 0
"""

UV_STUB = """#!/bin/sh
echo "uv $*" >> "$CALLS"
exit "${FAKE_UV_EXIT:-0}"
"""

CLAUDE_STUB = """#!/bin/sh
echo "claude $*" >> "$CALLS"
exit 0
"""

# The official installers drop their binary in ~/.local/bin; the fake curl
# prints an installer that does the same with a stub.
CURL_STUB = """#!/bin/sh
echo "curl $*" >> "$CALLS"
[ "${FAKE_CURL_EXIT:-0}" = 0 ] || exit "$FAKE_CURL_EXIT"
case "$*" in
    *astral.sh*) tool=uv ;;
    *claude.ai*) tool=claude ;;
    *) exit 22 ;;
esac
echo 'mkdir -p "$HOME/.local/bin"'
echo "cp \\"\\$STUBS/$tool\\" \\"\\$HOME/.local/bin/$tool\\""
"""


def _write_executable(path: Path, source: str) -> None:
    path.write_text(source, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


@dataclass
class Machine:
    """A fake computer: HOME, a PATH of stubs and the call log."""

    tmp: Path
    home: Path
    bin: Path
    stubs: Path
    calls: Path
    os_name: str = "Darwin"
    apple_tools: bool = True

    def add(self, *tools: str) -> None:
        for tool in tools:
            shutil.copy2(self.stubs / tool, self.bin / tool)

    def remove(self, tool: str) -> None:
        (self.bin / tool).unlink()

    def env(self, **extra: str) -> dict[str, str]:
        env = {
            "HOME": str(self.home),
            "PATH": str(self.bin),
            "CALLS": str(self.calls),
            "STUBS": str(self.stubs),
            "FAKE_OS": self.os_name,
            "FAKE_APPLE_TOOLS": "1" if self.apple_tools else "0",
            "ESCALA_REPO_URL": REPO_URL,
        }
        env.update(extra)
        return env

    def log(self) -> list[str]:
        if not self.calls.exists():
            return []
        return self.calls.read_text(encoding="utf-8").splitlines()


def _machine(tmp_path: Path) -> Machine:
    home = tmp_path / "home"
    home.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stubs = tmp_path / "stubs"
    stubs.mkdir()
    for tool in SYSTEM_TOOLS:
        real = shutil.which(tool)
        assert real, f"{tool} is required to run this test"
        (bin_dir / tool).symlink_to(real)
    _write_executable(stubs / "git", GIT_STUB)
    _write_executable(stubs / "uv", UV_STUB)
    _write_executable(stubs / "claude", CLAUDE_STUB)
    _write_executable(stubs / "curl", CURL_STUB)
    _write_executable(stubs / "fake-install.sh", FAKE_INSTALL)
    _write_executable(bin_dir / "uname", '#!/bin/sh\necho "$FAKE_OS"\n')
    _write_executable(
        bin_dir / "xcode-select",
        '#!/bin/sh\necho "xcode-select $*" >> "$CALLS"\n'
        '[ "$1" = "-p" ] && [ "$FAKE_APPLE_TOOLS" = 0 ] && exit 2\nexit 0\n',
    )
    machine = Machine(tmp_path, home, bin_dir, stubs, tmp_path / "calls.log")
    machine.add("git", "curl")
    return machine


def _pipe(machine: Machine, **extra: str) -> subprocess.CompletedProcess[str]:
    """``curl -fsSL …/instalar.sh | sh``: the script arrives on stdin."""
    return subprocess.run(
        ["sh"],
        input=BOOTSTRAP.read_text(encoding="utf-8"),
        cwd=machine.home,
        env=machine.env(**extra),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def _owner_text(completed: subprocess.CompletedProcess[str]) -> str:
    return completed.stdout + completed.stderr


def _assert_plain_failure(completed: subprocess.CompletedProcess[str]) -> str:
    text = _owner_text(completed)
    assert completed.returncode == 1, text
    assert "Traceback" not in text
    assert "vuelve a pegar el mismo comando" in text
    return text


# --- fresh machine and re-run ------------------------------------------------


def test_clean_machine_installs_everything_and_ends_with_one_next_step(
    tmp_path: Path,
) -> None:
    machine = _machine(tmp_path)

    completed = _pipe(machine)

    assert completed.returncode == 0, _owner_text(completed)
    log = machine.log()
    assert any(
        line.startswith("curl") and "astral.sh/uv/install.sh" in line for line in log
    )
    assert "uv python install 3.12" in log
    assert any(
        line.startswith("curl") and "claude.ai/install.sh" in line for line in log
    )
    escala = machine.home / "ESCALA"
    assert f"git clone --quiet {REPO_URL} {escala}" in log
    assert f"install.sh --platform claude --with-specialists (cwd={escala})" in log
    assert completed.stdout.strip().splitlines()[-1] == FINAL_LINE
    assert "--platform" not in _owner_text(completed)


def test_rerun_updates_without_cloning_or_reinstalling_tools(tmp_path: Path) -> None:
    machine = _machine(tmp_path)
    assert _pipe(machine).returncode == 0
    machine.calls.unlink()

    completed = _pipe(machine)

    assert completed.returncode == 0, _owner_text(completed)
    log = machine.log()
    escala = machine.home / "ESCALA"
    assert f"git -C {escala} pull --ff-only --quiet" in log
    assert not [line for line in log if line.startswith(("git clone", "curl"))]
    assert f"install.sh --platform claude --with-specialists (cwd={escala})" in log
    assert completed.stdout.strip().splitlines()[-1] == FINAL_LINE


def test_tools_already_installed_are_not_downloaded_again(tmp_path: Path) -> None:
    machine = _machine(tmp_path)
    machine.add("uv", "claude")

    completed = _pipe(machine)

    assert completed.returncode == 0, _owner_text(completed)
    assert not [line for line in machine.log() if line.startswith("curl")]


def test_update_without_internet_keeps_the_installed_version(tmp_path: Path) -> None:
    machine = _machine(tmp_path)
    assert _pipe(machine).returncode == 0
    machine.calls.unlink()

    completed = _pipe(machine, FAKE_PULL_EXIT="1")

    assert completed.returncode == 0, _owner_text(completed)
    assert "Sigo con la que ya tienes; tu información no se tocó." in completed.stdout
    assert any(line.startswith("install.sh") for line in machine.log())
    assert completed.stdout.strip().splitlines()[-1] == FINAL_LINE


def test_git_never_runs_a_destructive_command(tmp_path: Path) -> None:
    machine = _machine(tmp_path)
    _pipe(machine)
    _pipe(machine, FAKE_PULL_EXIT="1")

    git_calls = [line for line in machine.log() if line.startswith("git")]
    assert git_calls
    for word in ("clean", "reset", "checkout", "stash", "rm"):
        assert not [line for line in git_calls if f" {word}" in line], word
    script = BOOTSTRAP.read_text(encoding="utf-8")
    assert not re.search(r"(^|[;&|(]\s*)rm\s", script, flags=re.MULTILINE)


# --- run from a copy of the product -----------------------------------------


def test_run_from_a_copy_uses_that_copy(tmp_path: Path) -> None:
    machine = _machine(tmp_path)
    machine.add("uv", "claude")
    copy = tmp_path / "mi copia"
    (copy / ".git").mkdir(parents=True)
    (copy / "escala-skills").mkdir()
    shutil.copy2(machine.stubs / "fake-install.sh", copy / "install.sh")
    shutil.copy2(BOOTSTRAP, copy / "instalar.sh")

    completed = subprocess.run(
        ["sh", str(copy / "instalar.sh")],
        cwd=machine.home,
        env=machine.env(),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    assert completed.returncode == 0, _owner_text(completed)
    log = machine.log()
    assert not [line for line in log if line.startswith("git clone")]
    assert f"git -C {copy} pull --ff-only --quiet" in log
    assert f"install.sh --platform claude --with-specialists (cwd={copy})" in log
    assert not (machine.home / "ESCALA").exists()
    assert completed.stdout.strip().splitlines()[-1].endswith(f'cd "{copy}" && claude')


# --- failures in plain Spanish ------------------------------------------------


def test_folder_that_is_not_escala_is_left_untouched(tmp_path: Path) -> None:
    machine = _machine(tmp_path)
    foreign = machine.home / "ESCALA"
    foreign.mkdir()
    (foreign / "mis-notas.txt").write_text("sintético\n", encoding="utf-8")

    completed = _pipe(machine, FAKE_ORIGIN="")

    text = _assert_plain_failure(completed)
    assert "No la toqué" in text
    assert [p.name for p in foreign.iterdir()] == ["mis-notas.txt"]
    assert not [line for line in machine.log() if "clone" in line or "pull" in line]
    assert not [line for line in machine.log() if line.startswith("install.sh")]


def test_mac_without_apple_tools_opens_their_installer(tmp_path: Path) -> None:
    machine = _machine(tmp_path)
    machine.apple_tools = False
    machine.remove("git")

    completed = _pipe(machine)

    text = _assert_plain_failure(completed)
    assert "xcode-select --install" in machine.log()
    assert "Se abrió una ventana de Apple" in text
    assert not [line for line in machine.log() if line.startswith("git")]


def test_linux_without_git_says_what_to_do(tmp_path: Path) -> None:
    machine = _machine(tmp_path)
    machine.os_name = "Linux"
    machine.remove("git")

    text = _assert_plain_failure(_pipe(machine))

    assert "Falta Git" in text


def test_windows_points_to_wsl(tmp_path: Path) -> None:
    machine = _machine(tmp_path)
    machine.os_name = "MINGW64_NT-10.0"

    completed = _pipe(machine)

    text = _owner_text(completed)
    assert completed.returncode == 1
    assert "WSL2" in text
    assert machine.log() == []


def test_no_internet_for_tools_explains_the_way_out(tmp_path: Path) -> None:
    machine = _machine(tmp_path)

    text = _assert_plain_failure(_pipe(machine, FAKE_CURL_EXIT="6"))

    assert "Revisa tu internet" in text


def test_download_failure_explains_the_way_out(tmp_path: Path) -> None:
    machine = _machine(tmp_path)
    machine.add("uv", "claude")

    text = _assert_plain_failure(_pipe(machine, FAKE_CLONE_EXIT="128"))

    assert "No pude descargar ESCALA" in text
    assert not [line for line in machine.log() if line.startswith("install.sh")]


def test_installer_failure_says_nothing_was_lost(tmp_path: Path) -> None:
    machine = _machine(tmp_path)
    machine.add("uv", "claude")

    completed = _pipe(machine, FAKE_INSTALL_EXIT="1")

    text = _assert_plain_failure(completed)
    assert "No se borró nada" in text
    assert "instalacion.log" in text
    log_file = machine.home / ".config" / "agente-de-escalamiento" / "instalacion.log"
    assert log_file.is_file()


# --- the owner's data and the guide ------------------------------------------


def test_owner_data_in_the_copy_is_ignored_by_git() -> None:
    """The agent opens in the copy, so ``.escala/`` data shares the folder."""
    completed = subprocess.run(
        [
            "git",
            "check-ignore",
            ".escala/my-company/tracker.yaml",
            ".escala/agent/memory/company-profile.yaml",
            "work/mi-plan.md",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert len(completed.stdout.splitlines()) == 3


def test_bootstrap_is_posix_sh() -> None:
    assert BOOTSTRAP.read_text(encoding="utf-8").startswith("#!/bin/sh\n")
    for parser in ("sh", "bash"):
        if shutil.which(parser):
            completed = subprocess.run(
                [parser, "-n", str(BOOTSTRAP)],
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                check=False,
                env={"PATH": os.environ.get("PATH", "")},
            )
            assert completed.returncode == 0, completed.stderr
