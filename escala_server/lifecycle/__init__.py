"""Installer-local lifecycle public API."""

from .installer import prepare_local_install
from .models import (
    BackupRecord,
    InstallCheck,
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
    "build_native_schedule",
    "create_backup",
    "prepare_local_install",
    "make_update_artifact",
    "migrate_local_state",
    "render_native_schedule",
    "verify_update_artifact",
    "write_native_schedule",
]
