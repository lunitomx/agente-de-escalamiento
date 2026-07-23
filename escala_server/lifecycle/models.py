"""Closed contracts for the installer-local ESCALA lifecycle."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Platform = Literal["macos", "windows"]
Frequency = Literal["daily", "weekly"]
LifecycleResult = Literal["pass", "fail", "safe_stop"]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class InstallRequest(_StrictModel):
    """All roots required to install one local instance."""

    schema_version: Literal[1] = 1
    platform: Platform
    version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$")
    install_root: Path
    data_root: Path
    database_path: Path
    exchange_root: Path | None = None

    @field_validator(
        "install_root", "data_root", "database_path", "exchange_root", mode="before"
    )
    @classmethod
    def validate_paths(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, str) and (not value.strip() or "\x00" in value):
            raise ValueError("lifecycle path is invalid")
        return value

    def effective_exchange_root(self) -> Path:
        """Use a local exchange by default without putting it under data_root."""

        return self.exchange_root or self.install_root / "exchange"


class InstallFile(_StrictModel):
    path: str = Field(min_length=1, max_length=512)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size: int = Field(ge=0)


class InstallManifest(_StrictModel):
    schema_version: Literal[1] = 1
    package_version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$")
    platform: Platform
    entrypoint: str = "escala_server.lifecycle"
    files: tuple[InstallFile, ...] = ()
    network_required: Literal[False] = False
    repository_layout: Literal[False] = False


class InstallCheck(_StrictModel):
    id: str = Field(min_length=1, max_length=80)
    status: Literal["pass", "fail"]


class InstallReceipt(_StrictModel):
    schema_version: Literal[1] = 1
    status: Literal["pass", "fail"]
    platform: Platform
    version: str
    checks: tuple[InstallCheck, ...] = ()
    findings: tuple[str, ...] = ()
    repository_layout: Literal[False] = False
    network_required: Literal[False] = False
    exchange_configured: bool = False
    runtime_authority: Literal["installer_machine"] = "installer_machine"
    data_authority: Literal["installer_machine"] = "installer_machine"
    team_exchange: Literal["ordinary_filesystem_documents_only"] = (
        "ordinary_filesystem_documents_only"
    )
    authoritative_sqlite_sync: Literal["forbidden"] = "forbidden"


class RuntimeStatus(_StrictModel):
    schema_version: Literal[1] = 1
    status: Literal["stopped", "healthy", "degraded"]
    version: str
    data_location: Literal["data_root"] = "data_root"
    process_id: int | None = None
    hosted_service: Literal[False] = False
    network_required: Literal[False] = False
    findings: tuple[str, ...] = ()


class BackupRecord(_StrictModel):
    schema_version: Literal[1] = 1
    backup_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    previous_version: str
    relative_path: str = Field(min_length=1, max_length=512)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size: int = Field(ge=0)


class UpdateArtifact(_StrictModel):
    schema_version: Literal[1] = 1
    version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$")
    path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_commit: str = Field(pattern=r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
    verification: Literal["unverified", "verified"] = "unverified"
    network_required: Literal[False] = False


class UpdateReceipt(_StrictModel):
    schema_version: Literal[1] = 1
    status: LifecycleResult
    previous_version: str
    current_version: str
    backup_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    backup_relative_path: str = Field(min_length=1, max_length=512)
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_commit: str = Field(pattern=r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
    rollback_available: bool
    verification: Literal["verified", "safe_stop"]
    safe_stop_reason: str | None = None
    runtime_authority: Literal["installer_machine"] = "installer_machine"
    data_authority: Literal["installer_machine"] = "installer_machine"


class MigrationReceipt(_StrictModel):
    schema_version: Literal[1] = 1
    status: Literal["pass", "safe_stop"]
    previous_schema: int = Field(ge=1)
    current_schema: int = Field(ge=1)
    backup_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    backup_relative_path: str = Field(min_length=1, max_length=512)
    rollback_available: Literal[True] = True
    safe_stop_reason: str | None = None


class ScheduleRequest(_StrictModel):
    platform: Platform
    install_root: Path
    data_root: Path
    frequency: Frequency
    local_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    weekday: int | None = Field(default=None, ge=0, le=6)


class ScheduleSpec(_StrictModel):
    schema_version: Literal[1] = 1
    platform: Platform
    kind: Literal["launchd", "task_scheduler"]
    frequency: Frequency
    local_time: str
    weekday: int | None = None
    command: tuple[str, ...]
    network_required: Literal[False] = False
    canonical_state_role: Literal["installer_machine"] = "installer_machine"


class ScheduleReceipt(_StrictModel):
    schema_version: Literal[1] = 1
    status: Literal["pass", "fail"]
    platform: Platform
    kind: Literal["launchd", "task_scheduler"]
    frequency: Frequency
    relative_path: str
    network_required: Literal[False] = False


class LifecycleError(ValueError):
    """Safe lifecycle failure with a stable code and no machine paths."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)
