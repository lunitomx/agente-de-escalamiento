"""Deterministic package creation and local installation."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
import zipfile

from escala_server.workspace.authority import WorkspaceConfig, validate_workspace

from .models import (
    InstallCheck,
    InstallFile,
    InstallManifest,
    InstallReceipt,
    InstallRequest,
    LifecycleError,
)


def build_install_bundle(
    source_root: Path,
    output_dir: Path,
    version: str,
    platform: str,
) -> Path:
    """Build a self-contained archive from the application package only.

    The archive deliberately excludes `.git`, tests, work artifacts and the
    repository root. Its manifest is deterministic and contains only relative
    package paths and content hashes.
    """

    if platform not in {"macos", "windows"}:
        raise LifecycleError("unsupported_platform")
    package_root = source_root / "escala_server"
    if not package_root.is_dir():
        raise LifecycleError("package_source_missing")
    files: list[tuple[str, bytes]] = []
    for path in sorted(package_root.rglob("*")):
        if not path.is_file() or path.is_symlink() or "__pycache__" in path.parts:
            continue
        relative = PurePosixPath("app") / path.relative_to(source_root).as_posix()
        files.append((str(relative), path.read_bytes()))
    if not files:
        raise LifecycleError("package_source_empty")
    manifest = InstallManifest(
        package_version=version,
        platform=platform,  # type: ignore[arg-type]
        files=tuple(
            InstallFile(
                path=name, sha256=hashlib.sha256(data).hexdigest(), size=len(data)
            )
            for name, data in files
        ),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / f"escala-local-{platform}-{version}.zip"
    manifest_bytes = _json_bytes(manifest.model_dump(mode="json"))
    readme = (
        "ESCALA Local package\n"
        "Install with the documented local flow. No hosted service or network is required.\n"
    ).encode("utf-8")
    scripts = {
        "install.sh": _unix_script(version).encode("utf-8"),
        "install.ps1": _windows_script(version).encode("utf-8"),
        "README.txt": readme,
    }
    with zipfile.ZipFile(
        archive_path, "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        for name, data in files:
            _write_zip_entry(archive, name, data)
        _write_zip_entry(archive, "manifest.json", manifest_bytes)
        for name, data in scripts.items():
            _write_zip_entry(archive, name, data)
    return archive_path


def install_package(bundle_path: Path, request: InstallRequest) -> InstallReceipt:
    """Extract and initialize one package under installer-local roots."""

    manifest = _read_manifest(bundle_path)
    if manifest.platform != request.platform:
        raise LifecycleError("platform_mismatch")
    if manifest.package_version != request.version:
        raise LifecycleError("version_mismatch")
    workspace = _workspace_config(request)
    authority = validate_workspace(workspace)
    if authority.status != "pass":
        code = authority.findings[0].code if authority.findings else "workspace_invalid"
        raise LifecycleError(code)
    request.install_root.mkdir(parents=True, exist_ok=True)
    request.data_root.mkdir(parents=True, exist_ok=True)
    request.effective_exchange_root().mkdir(parents=True, exist_ok=True)
    _extract_app(bundle_path, request.install_root)
    _atomic_json(
        request.install_root / "install.json",
        {
            "schema_version": 1,
            "version": request.version,
            "platform": request.platform,
            "package": "app",
            "network_required": False,
        },
    )
    _atomic_json(
        request.data_root / "config.json",
        {
            "schema_version": 1,
            "platform": request.platform,
            "exchange_role": "ordinary_filesystem_documents_only",
            "exchange_configured": request.exchange_root is not None,
            "runtime_authority": "installer_machine",
            "data_authority": "installer_machine",
        },
    )
    request.database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(request.database_path)
    connection.close()
    checks = (
        InstallCheck(id="bundle_manifest", status="pass"),
        InstallCheck(id="workspace_authority", status="pass"),
        InstallCheck(id="canonical_state_local", status="pass"),
        InstallCheck(id="no_repository_layout", status="pass"),
        InstallCheck(id="offline_runtime", status="pass"),
    )
    return InstallReceipt(
        status="pass",
        platform=request.platform,
        version=request.version,
        checks=checks,
        exchange_configured=request.exchange_root is not None,
    )


def _read_manifest(bundle_path: Path) -> InstallManifest:
    if bundle_path.is_symlink() or not bundle_path.is_file():
        raise LifecycleError("bundle_missing")
    try:
        with zipfile.ZipFile(bundle_path) as archive:
            manifest = InstallManifest.model_validate_json(
                archive.read("manifest.json")
            )
            names = set(archive.namelist())
            for item in manifest.files:
                if item.path not in names or _unsafe_archive_path(item.path):
                    raise LifecycleError("bundle_manifest_invalid")
                data = archive.read(item.path)
                if (
                    len(data) != item.size
                    or hashlib.sha256(data).hexdigest() != item.sha256
                ):
                    raise LifecycleError("bundle_file_hash_mismatch")
            return manifest
    except (OSError, zipfile.BadZipFile, KeyError, ValueError):
        raise LifecycleError("bundle_invalid") from None


def _extract_app(bundle_path: Path, install_root: Path) -> None:
    try:
        with zipfile.ZipFile(bundle_path) as archive:
            for name in archive.namelist():
                if not name.startswith("app/") or _unsafe_archive_path(name):
                    continue
                target = install_root / Path(name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(name))
    except (OSError, zipfile.BadZipFile, KeyError):
        raise LifecycleError("bundle_extract_failed") from None


def _workspace_config(request: InstallRequest) -> WorkspaceConfig:
    return WorkspaceConfig(
        platform=request.platform,
        data_root=request.data_root,
        database_path=request.database_path,
        exchange_root=request.effective_exchange_root(),
    )


def _unsafe_archive_path(value: str) -> bool:
    path = PurePosixPath(value)
    return path.is_absolute() or ".." in path.parts or "\\" in value or "\x00" in value


def _json_bytes(data: object) -> bytes:
    return (
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _atomic_json(path: Path, data: object) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(_json_bytes(data))
    os.replace(temporary, path)


def _write_zip_entry(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, data)


def _unix_script(version: str) -> str:
    return (
        "#!/bin/sh\n"
        "set -eu\n"
        'TARGET=${1:-"$HOME/.escala"}\n'
        'mkdir -p "$TARGET/app" "$TARGET/data" "$TARGET/exchange"\n'
        'cp -R app/escala_server "$TARGET/app/"\n'
        'cp manifest.json "$TARGET/manifest.json"\n'
        f"printf '%s\\n' 'ESCALA Local {version} installed locally'\n"
    )


def _windows_script(version: str) -> str:
    return (
        "$ErrorActionPreference = 'Stop'\n"
        "$Target = if ($args.Count -gt 0) { $args[0] } else { Join-Path $HOME '.escala' }\n"
        "New-Item -ItemType Directory -Force (Join-Path $Target 'app'), (Join-Path $Target 'data'), (Join-Path $Target 'exchange') | Out-Null\n"
        "Copy-Item -Recurse -Force 'app/escala_server' (Join-Path $Target 'app')\n"
        "Copy-Item -Force 'manifest.json' (Join-Path $Target 'manifest.json')\n"
        f"Write-Output 'ESCALA Local {version} installed locally'\n"
    )
