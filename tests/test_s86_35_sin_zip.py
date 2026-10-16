"""S86.35 — el instalador zip viejo no vuelve; la instalación es de una línea.

El dueño instala con `instalar.sh` (clona el repo a ~/ESCALA y corre
install.sh). El paquete `escala-local-<plataforma>-<versión>.zip` de E41 se
quitó. Estas pruebas fallan si alguien vuelve a armar ese zip o si el README
deja de indicar la línea única.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

import escala_server.lifecycle as lifecycle
from escala_server.lifecycle import InstallRequest, prepare_local_install

ROOT = Path(__file__).resolve().parents[1]

# `escala-local-<algo>.zip` o el f-string `escala-local-{platform}-{version}.zip`.
_ZIP_NAME = re.compile(r"escala-local-[\w{}<>.\-]*\.zip")
_SCANNED_DIRS = ("escala_server", "scripts", "validators", "adapters", "docs")
_SCANNED_ROOT_FILES = (
    "instalar.sh",
    "install.sh",
    "update.sh",
    "uninstall.sh",
    "README.md",
    "pyproject.toml",
)
_SCANNED_SUFFIXES = {".py", ".sh", ".ps1", ".md", ".toml", ".yaml", ".yml", ".json"}

ONE_LINE_INSTALL = (
    "curl -fsSL https://raw.githubusercontent.com/lunitomx/agente-de-escalamiento"
    "/main/instalar.sh | sh"
)


def _scanned_files() -> list[Path]:
    files = [ROOT / name for name in _SCANNED_ROOT_FILES if (ROOT / name).is_file()]
    for directory in _SCANNED_DIRS:
        files.extend(
            path
            for path in sorted((ROOT / directory).rglob("*"))
            if path.is_file()
            and path.suffix in _SCANNED_SUFFIXES
            and "__pycache__" not in path.parts
        )
    return files


def test_no_file_names_or_builds_an_escala_local_zip() -> None:
    offenders = [
        str(path.relative_to(ROOT))
        for path in _scanned_files()
        if _ZIP_NAME.search(path.read_text(encoding="utf-8", errors="ignore"))
    ]
    assert offenders == []


def test_the_zip_pattern_catches_the_old_generator() -> None:
    # La prueba de arriba puede fallar: el nombre que armaba E41 cae en el patrón.
    assert _ZIP_NAME.search('archive = out / f"escala-local-{platform}-{version}.zip"')
    assert _ZIP_NAME.search("escala-local-macos-1.0.0.zip")
    # La misión del libro maestro no es un zip y no debe atraparse.
    assert not _ZIP_NAME.search("escala-local-v2-plan-maestro-2607202112")


def test_lifecycle_no_longer_exposes_bundle_builders() -> None:
    for name in ("build_install_bundle", "install_package", "InstallManifest"):
        assert not hasattr(lifecycle, name), name
    assert not (ROOT / "install.ps1").exists()


def test_readme_still_shows_the_one_line_install() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert ONE_LINE_INSTALL in readme
    assert "~/ESCALA" in readme
    assert ".zip" not in readme


def test_installer_script_still_clones_and_runs_install_sh() -> None:
    script = (ROOT / "instalar.sh").read_text(encoding="utf-8")
    assert "lunitomx/agente-de-escalamiento" in script
    assert "git" in script and "clone" in script
    assert "install.sh" in script and "--with-specialists" in script


def test_prepare_local_install_creates_local_roots_without_a_package(
    tmp_path: Path,
) -> None:
    request = InstallRequest(
        platform="macos",
        version="1.2.3",
        install_root=tmp_path / "install",
        data_root=tmp_path / "data",
        database_path=tmp_path / "data" / "escala.sqlite",
    )

    receipt = prepare_local_install(request)

    assert receipt.status == "pass"
    assert "bundle_manifest" not in {check.id for check in receipt.checks}
    marker = json.loads((request.install_root / "install.json").read_text("utf-8"))
    assert marker["version"] == "1.2.3"
    assert (request.data_root / "escala.sqlite").is_file()
    assert not (request.install_root / "app").exists()
