"""Offline local runtime and health lifecycle."""

from __future__ import annotations

import json
import os
from pathlib import Path

from escala_server.workspace.authority import (
    WorkspaceAuthorityError,
    WorkspaceConfig,
    validate_workspace,
)

from .models import InstallRequest, RuntimeStatus


class LifecycleRuntime:
    """Manage a local marker-based runtime without a hosted worker."""

    def __init__(self, request: InstallRequest) -> None:
        self.request = request
        self._marker = request.data_root / ".escala-runtime.json"

    def start(self) -> RuntimeStatus:
        self._assert_authority()
        self.request.data_root.mkdir(parents=True, exist_ok=True)
        version = self._version()
        _atomic_json(
            self._marker,
            {
                "schema_version": 1,
                "status": "healthy",
                "version": version,
                "hosted_service": False,
                "network_required": False,
            },
        )
        return RuntimeStatus(status="healthy", version=version)

    def stop(self) -> RuntimeStatus:
        self._assert_authority()
        self._marker.unlink(missing_ok=True)
        return RuntimeStatus(status="stopped", version=self._version())

    def status(self) -> RuntimeStatus:
        version = self._version()
        if not self._marker.exists():
            return RuntimeStatus(status="stopped", version=version)
        try:
            payload = json.loads(self._marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return RuntimeStatus(
                status="degraded", version=version, findings=("runtime_state_corrupt",)
            )
        if (
            payload.get("status") != "healthy"
            or payload.get("hosted_service") is not False
        ):
            return RuntimeStatus(
                status="degraded", version=version, findings=("runtime_state_invalid",)
            )
        return RuntimeStatus(
            status="healthy", version=str(payload.get("version", version))
        )

    def _version(self) -> str:
        metadata = self.request.install_root / "install.json"
        if metadata.exists():
            try:
                value = json.loads(metadata.read_text(encoding="utf-8")).get("version")
                if isinstance(value, str) and value:
                    return value
            except (OSError, json.JSONDecodeError):
                pass
        return self.request.version

    def _assert_authority(self) -> None:
        workspace = WorkspaceConfig(
            platform=self.request.platform,
            data_root=self.request.data_root,
            database_path=self.request.database_path,
            exchange_root=self.request.effective_exchange_root(),
        )
        receipt = validate_workspace(workspace)
        if receipt.status != "pass":
            code = receipt.findings[0].code if receipt.findings else "workspace_invalid"
            raise WorkspaceAuthorityError(code)


def _atomic_json(path: Path, data: object) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)
