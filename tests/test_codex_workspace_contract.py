from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONFIGURATOR = REPOSITORY_ROOT / "scripts" / "configure_codex_mcp.sh"


def _make_executable(directory: Path, name: str) -> Path:
    executable = directory / name
    executable.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    return executable


def _run_configurator(
    project_root: Path, executable_directory: Path
) -> subprocess.CompletedProcess[str]:
    environment = os.environ | {"PATH": str(executable_directory)}
    return subprocess.run(
        [str(CONFIGURATOR), str(project_root)],
        capture_output=True,
        check=False,
        encoding="utf-8",
        env=environment,
        text=True,
    )


def test_configurator_writes_portable_codex_project_configuration(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "checkout with spaces"
    project_root.mkdir()
    executable_directory = tmp_path / "bin"
    executable_directory.mkdir()
    executable = _make_executable(executable_directory, "rai-mcp-pipeline")

    completed = _run_configurator(project_root, executable_directory)

    config = (project_root / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert completed.returncode == 0, completed.stderr
    assert f'command = "{executable}"' in config
    assert f'args = ["--project", "{project_root}"]' in config
    assert f'RAISE_PROJECT_ROOT = "{project_root}"' in config


def test_configurator_preserves_existing_codex_configuration(tmp_path: Path) -> None:
    project_root = tmp_path / "checkout"
    config_directory = project_root / ".codex"
    config_directory.mkdir(parents=True)
    config = config_directory / "config.toml"
    config.write_text("[existing]\nowned = true\n", encoding="utf-8")
    executable_directory = tmp_path / "bin"
    executable_directory.mkdir()
    _make_executable(executable_directory, "rai-mcp-pipeline")

    completed = _run_configurator(project_root, executable_directory)

    assert completed.returncode == 0, completed.stderr
    assert config.read_text(encoding="utf-8") == "[existing]\nowned = true\n"
    assert "se conserva" in completed.stdout


def test_configurator_warns_without_installing_missing_pipeline(tmp_path: Path) -> None:
    project_root = tmp_path / "checkout"
    project_root.mkdir()
    empty_path = tmp_path / "empty-bin"
    empty_path.mkdir()

    completed = _run_configurator(project_root, empty_path)

    assert completed.returncode == 0
    assert not (project_root / ".codex" / "config.toml").exists()
    assert "rai-mcp-pipeline no está disponible" in completed.stderr


def test_installer_delegates_codex_configuration_without_broadening_permissions() -> (
    None
):
    installer = (REPOSITORY_ROOT / "install.sh").read_text(encoding="utf-8")

    assert '"$configurator" "$SCRIPT_DIR"' in installer
    assert "--with-rai-mcp" in installer
    assert "~/.rai" not in installer


def test_codex_guidance_prefers_mcp_for_readonly_rai_state() -> None:
    guidance = (REPOSITORY_ROOT / "CODEX.md").read_text(encoding="utf-8")

    assert "rai-workspace" in guidance
    assert "solo lectura" in guidance
    assert "~/.rai" in guidance


def test_workspace_mcp_runtime_configuration_is_local_not_tracked() -> None:
    ignored = (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8")
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", ".mcp.json"],
        capture_output=True,
        check=False,
        cwd=REPOSITORY_ROOT,
        encoding="utf-8",
        text=True,
    )

    assert ".mcp.json" in ignored
    assert tracked.returncode != 0
