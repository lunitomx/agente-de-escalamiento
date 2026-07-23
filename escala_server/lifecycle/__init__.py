"""Installer-local lifecycle public API."""

from .installer import build_install_bundle, install_package
from .models import (
    BackupRecord,
    InstallCheck,
    InstallFile,
    InstallManifest,
    InstallReceipt,
    InstallRequest,
    LifecycleError,
    MigrationReceipt,
    RuntimeStatus,
    ScheduleReceipt,
    ScheduleRequest,
    ScheduleSpec,
    UpdateArtifact,
    UpdateReceipt,
)
from .runtime import LifecycleRuntime
from .scheduler import (
    build_native_schedule,
    render_native_schedule,
    write_native_schedule,
)
from .updates import (
    UpdateManager,
    create_backup,
    make_update_artifact,
    migrate_local_state,
    verify_update_artifact,
)

__all__ = [
    "BackupRecord",
    "InstallCheck",
    "InstallFile",
    "InstallManifest",
    "InstallReceipt",
    "InstallRequest",
    "LifecycleError",
    "LifecycleRuntime",
    "MigrationReceipt",
    "RuntimeStatus",
    "ScheduleReceipt",
    "ScheduleRequest",
    "ScheduleSpec",
    "UpdateArtifact",
    "UpdateManager",
    "UpdateReceipt",
    "build_install_bundle",
    "build_native_schedule",
    "create_backup",
    "install_package",
    "make_update_artifact",
    "migrate_local_state",
    "render_native_schedule",
    "verify_update_artifact",
    "write_native_schedule",
]
