"""Prepare the installer-local roots that the lifecycle runtime reads.

The owner installs ESCALA with the one-line flow (`instalar.sh` clones the
repository and runs `install.sh`). The old `escala-local-*.zip` package from
E41 was removed in S86.35; this module only prepares local state roots.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3

from escala_server.workspace.authority import WorkspaceConfig, validate_workspace

from .models import InstallCheck, InstallReceipt, InstallRequest, LifecycleError


def prepare_local_install(request: InstallRequest) -> InstallReceipt:
    """Create install/data roots, the version marker, config and SQLite file."""

    workspace = _workspace_config(request)
    authority = validate_workspace(workspace)
    if authority.status != "pass":
        code = authority.findings[0].code if authority.findings else "workspace_invalid"
        raise LifecycleError(code)
    request.install_root.mkdir(parents=True, exist_ok=True)
    request.data_root.mkdir(parents=True, exist_ok=True)
    request.effective_exchange_root().mkdir(parents=True, exist_ok=True)
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
        InstallCheck(id="workspace_authority", status="pass"),
        InstallCheck(id="canonical_state_local", status="pass"),
        InstallCheck(id="offline_runtime", status="pass"),
    )
    return InstallReceipt(
        status="pass",
        platform=request.platform,
        version=request.version,
        checks=checks,
        exchange_configured=request.exchange_root is not None,
    )


def _workspace_config(request: InstallRequest) -> WorkspaceConfig:
    return WorkspaceConfig(
        platform=request.platform,
        data_root=request.data_root,
        database_path=request.database_path,
        exchange_root=request.effective_exchange_root(),
    )


def _json_bytes(data: object) -> bytes:
    return (
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _atomic_json(path: Path, data: object) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(_json_bytes(data))
    os.replace(temporary, path)
