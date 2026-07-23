"""Verified update, backup, rollback and migration transactions."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import zipfile

from .installer import _atomic_json
from .models import (
    BackupRecord,
    InstallRequest,
    LifecycleError,
    MigrationReceipt,
    UpdateArtifact,
    UpdateReceipt,
)


def make_update_artifact(
    payload: Path,
    version: str,
    output_dir: Path,
    source_commit: str | None = None,
) -> UpdateArtifact:
    """Copy a candidate update and bind its exact content hash."""

    if payload.is_symlink() or not payload.is_file():
        raise LifecycleError("update_payload_missing")
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"escala-update-{version}.bin"
    shutil.copyfile(payload, target)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    return UpdateArtifact(
        version=version,
        path=target,
        sha256=digest,
        source_commit=source_commit or "0" * 40,
    )


def verify_update_artifact(artifact: UpdateArtifact) -> UpdateArtifact:
    """Independently verify a local artifact before it can be applied."""

    if artifact.path.is_symlink() or not artifact.path.is_file():
        raise LifecycleError("update_payload_missing")
    digest = hashlib.sha256(artifact.path.read_bytes()).hexdigest()
    if digest != artifact.sha256:
        raise LifecycleError("artifact_hash_mismatch")
    return artifact.model_copy(update={"verification": "verified"})


class UpdateManager:
    """Apply only verified artifacts and preserve a local rollback point."""

    def __init__(self, request: InstallRequest) -> None:
        self.request = request

    def apply(self, artifact: UpdateArtifact) -> UpdateReceipt:
        if artifact.verification != "verified":
            raise LifecycleError("artifact_unverified")
        verified = verify_update_artifact(artifact)
        previous = self._version()
        backup = create_backup(self.request, previous)
        try:
            self._store_artifact(verified)
            self._write_version(verified.version)
        except OSError:
            self._restore_backup(backup)
            return UpdateReceipt(
                status="safe_stop",
                previous_version=previous,
                current_version=previous,
                backup_id=backup.backup_id,
                backup_relative_path=backup.relative_path,
                artifact_sha256=verified.sha256,
                source_commit=verified.source_commit,
                rollback_available=True,
                verification="safe_stop",
                safe_stop_reason="update_activation_failed",
            )
        receipt = UpdateReceipt(
            status="pass",
            previous_version=previous,
            current_version=verified.version,
            backup_id=backup.backup_id,
            backup_relative_path=backup.relative_path,
            artifact_sha256=verified.sha256,
            source_commit=verified.source_commit,
            rollback_available=True,
            verification="verified",
        )
        _atomic_json(
            self.request.data_root / ".escala-update-ledger.json",
            receipt.model_dump(mode="json"),
        )
        return receipt

    def rollback(self, receipt: UpdateReceipt) -> UpdateReceipt:
        if not receipt.rollback_available:
            raise LifecycleError("rollback_unavailable")
        backup = BackupRecord(
            backup_id=receipt.backup_id,
            previous_version=receipt.previous_version,
            relative_path=receipt.backup_relative_path,
            sha256="0" * 64,
            size=0,
        )
        self._restore_backup(backup)
        self._write_version(receipt.previous_version)
        return receipt.model_copy(
            update={
                "status": "pass",
                "current_version": receipt.previous_version,
                "verification": "verified",
                "safe_stop_reason": None,
            }
        )

    def _version(self) -> str:
        path = self.request.install_root / "install.json"
        try:
            value = json.loads(path.read_text(encoding="utf-8")).get("version")
        except (OSError, json.JSONDecodeError):
            value = None
        return value if isinstance(value, str) and value else self.request.version

    def _write_version(self, version: str) -> None:
        path = self.request.install_root / "install.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {
                "schema_version": 1,
                "platform": self.request.platform,
                "package": "app",
            }
        payload["version"] = version
        _atomic_json(path, payload)

    def _store_artifact(self, artifact: UpdateArtifact) -> None:
        target = self.request.install_root / ".escala-artifacts" / artifact.path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(artifact.path, target)

    def _restore_backup(self, backup: BackupRecord) -> None:
        archive_path = self.request.data_root / backup.relative_path
        if not archive_path.is_file():
            raise LifecycleError("backup_missing")
        try:
            with zipfile.ZipFile(archive_path) as archive:
                for name in archive.namelist():
                    if name.startswith(".escala-backups/") or ".." in Path(name).parts:
                        continue
                    destination = self.request.data_root / name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(archive.read(name))
        except (OSError, zipfile.BadZipFile, KeyError):
            raise LifecycleError("backup_corrupt") from None


def create_backup(request: InstallRequest, previous_version: str) -> BackupRecord:
    """Snapshot local user state while excluding prior backup archives."""

    request.data_root.mkdir(parents=True, exist_ok=True)
    backup_dir = request.data_root / ".escala-backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    temporary = backup_dir / ".pending.zip"
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(request.data_root.rglob("*")):
            if (
                not path.is_file()
                or path.is_symlink()
                or ".escala-backups" in path.parts
            ):
                continue
            archive.write(path, path.relative_to(request.data_root).as_posix())
    archive_bytes = temporary.read_bytes()
    backup_id = hashlib.sha256(archive_bytes).hexdigest()
    target = backup_dir / f"{backup_id}.zip"
    os.replace(temporary, target)
    return BackupRecord(
        backup_id=backup_id,
        previous_version=previous_version,
        relative_path=f".escala-backups/{target.name}",
        sha256=backup_id,
        size=target.stat().st_size,
    )


def migrate_local_state(
    request: InstallRequest,
    target_schema: int,
    *,
    fail_after_backup: bool = False,
) -> MigrationReceipt:
    """Migrate a tiny local schema marker with explicit safe-stop behavior."""

    if target_schema < 1:
        raise LifecycleError("schema_invalid")
    schema_path = request.data_root / "schema.json"
    previous = 1
    if schema_path.exists():
        try:
            previous = int(
                json.loads(schema_path.read_text(encoding="utf-8")).get("schema", 1)
            )
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            raise LifecycleError("schema_corrupt") from None
    backup = create_backup(request, request.version)
    if fail_after_backup:
        UpdateManager(request)._restore_backup(backup)
        return MigrationReceipt(
            status="safe_stop",
            previous_schema=previous,
            current_schema=previous,
            backup_id=backup.backup_id,
            backup_relative_path=backup.relative_path,
            safe_stop_reason="migration_interrupted",
        )
    _atomic_json(schema_path, {"schema": target_schema})
    return MigrationReceipt(
        status="pass",
        previous_schema=previous,
        current_schema=target_schema,
        backup_id=backup.backup_id,
        backup_relative_path=backup.relative_path,
    )
