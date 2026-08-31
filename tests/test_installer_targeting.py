# Regression coverage for S10.11's explicit, PEP-668-safe installer.

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install.sh"


def _executable(
    directory: Path, name: str, source: str = "#!/bin/sh\\nexit 0\\n"
) -> Path:
    path = directory / name
    path.write_text(source, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def _platform_bin(directory: Path, *platforms: str) -> None:
    for platform in platforms:
        _executable(directory, platform)


def _run(
    command: list[str], home: Path, bin_dir: Path, cwd: Path = ROOT
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env={"HOME": str(home), "PATH": str(bin_dir) + ":" + os.environ["PATH"]},
        capture_output=True,
        text=True,
        check=False,
    )


def _minimal_checkout(root: Path) -> Path:
    checkout = root / "checkout"
    (checkout / ".git").mkdir(parents=True)
    skill = checkout / "escala-skills" / "escala"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: escala\ndescription: test\n---\n", encoding="utf-8"
    )
    capability_catalog = checkout / "capabilities" / "mvp" / "catalog.json"
    capability_catalog.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "capabilities" / "mvp" / "catalog.json", capability_catalog)
    adapter = checkout / "adapters" / "claude"
    adapter.mkdir(parents=True)
    shutil.copy2(ROOT / "adapters" / "claude" / "CLAUDE.template.md", adapter)
    (checkout / "install.sh").write_text(
        INSTALLER.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (checkout / "install.sh").chmod(0o755)
    return checkout


def _fake_uv(*, succeeds: bool) -> str:
    outcome = "exit 0" if succeeds else "exit 73"
    return f"""#!/usr/bin/env bash
set -euo pipefail
if [[ \"$1\" == \"venv\" ]]; then
  mkdir -p \"$2/bin\"
  printf '%s\\n' '#!/bin/sh' 'exit 0' > \"$2/bin/python\"
  chmod +x \"$2/bin/python\"
  exit 0
fi
if [[ \"$1\" == \"pip\" && \"$2\" == \"install\" ]]; then
  {outcome}
fi
exit 91
"""


def test_installer_requires_an_explicit_platform_before_side_effects(
    tmp_path: Path,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _platform_bin(bin_dir, "claude")

    completed = _run(
        ["bash", str(INSTALLER), "--skills-only"], tmp_path / "home", bin_dir
    )

    assert completed.returncode == 2
    assert "Elige una plataforma" in completed.stderr
    assert not (tmp_path / "home").exists()


def test_targeted_claude_install_preserves_other_platforms_and_mcp(
    tmp_path: Path,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _platform_bin(bin_dir, "claude", "codex", "hermes")
    home = tmp_path / "home"

    codex_config = ROOT / ".codex" / "config.toml"
    config_before = codex_config.read_bytes() if codex_config.exists() else None
    completed = _run(
        ["bash", str(INSTALLER), "--skills-only", "--platform", "claude"], home, bin_dir
    )

    assert completed.returncode == 0, completed.stderr
    assert (home / ".claude" / "skills" / "escala").is_symlink()
    assert not (home / ".codex").exists()
    assert not (home / ".hermes").exists()
    config_after = codex_config.read_bytes() if codex_config.exists() else None
    assert config_after == config_before


def test_all_platforms_is_an_explicit_opt_in(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _platform_bin(bin_dir, "claude", "codex", "hermes")
    home = tmp_path / "home"

    completed = _run(
        ["bash", str(INSTALLER), "--skills-only", "--all-platforms"], home, bin_dir
    )

    assert completed.returncode == 0, completed.stderr
    for directory in (".claude", ".codex", ".hermes"):
        assert (home / directory / "skills" / "escala").is_symlink()


def test_complete_install_uses_local_uv_venv_not_system_pip(tmp_path: Path) -> None:
    checkout = _minimal_checkout(tmp_path)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _platform_bin(bin_dir, "claude")
    pip_marker = tmp_path / "system-pip-called"
    _executable(bin_dir, "pip", f"#!/bin/sh\\ntouch {pip_marker}\\nexit 99\\n")
    _executable(bin_dir, "uv", _fake_uv(succeeds=True))

    completed = _run(
        ["bash", str(checkout / "install.sh"), "--platform", "claude"],
        tmp_path / "home",
        bin_dir,
        checkout,
    )

    assert completed.returncode == 0, completed.stderr
    assert (checkout / ".venv" / "bin" / "python").is_file()
    assert not pip_marker.exists()
    assert "Paquete Python instalado" in completed.stdout
    assert (tmp_path / "home" / ".claude" / "skills" / "escala").is_symlink()


def test_failed_local_runtime_never_reports_success_or_creates_skill_link(
    tmp_path: Path,
) -> None:
    checkout = _minimal_checkout(tmp_path)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _platform_bin(bin_dir, "claude")
    _executable(bin_dir, "uv", _fake_uv(succeeds=False))
    home = tmp_path / "home"

    completed = _run(
        ["bash", str(checkout / "install.sh"), "--platform", "claude"],
        home,
        bin_dir,
        checkout,
    )

    assert completed.returncode == 1
    assert "No se pudo instalar escala-coaching" in completed.stderr
    assert "Instalación completada exitosamente" not in completed.stdout
    assert "Paquete Python instalado" not in completed.stdout
    assert not (home / ".claude" / "skills" / "escala").exists()
