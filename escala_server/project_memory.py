"""Project-scoped, local SQLite runtime for ScaleUp business memory."""

from __future__ import annotations

import os
import shutil
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from .schema import (
    SCHEMA_VERSION,
    init_db,
    schema_contract_is_valid,
    schema_contract_tables_are_present,
)
from .workspace import load_workspace, path_is_inside, workspace_local_root


@dataclass(frozen=True)
class MemoryResult:
    """Outcome of a local-memory operation that is safe for callers to consume."""

    ready: bool
    db_path: Path
    reason: str | None = None
    backup_path: Path | None = None


class ProjectMemoryRuntime:
    """Own local SQLite state, keeping it outside a shared workspace when present.

    Projects without ``scaleup-workspace.yaml`` retain the E22 layout for
    backwards compatibility. A portable workspace opts into the E26 layout:
    its Markdown/YAML may be synced, while every machine gets an independent
    SQLite database under its local state root.
    """

    def __init__(
        self, project_root: str | Path, *, local_state_root: str | Path | None = None
    ) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        self.workspace_root = self.project_root
        workspace = load_workspace(self.workspace_root)
        self.workspace = workspace.manifest if workspace.ready else None
        self.workspace_error = (
            workspace.reason
            if not workspace.ready
            and (self.workspace_root / "scaleup-workspace.yaml").exists()
            else None
        )
        self.legacy_memory_root = self.project_root / ".scaleup" / "memory"
        if self.workspace is None:
            self.memory_root = self.legacy_memory_root
            self.storage_root = self.project_root
            self.shared_workspace = False
        else:
            state_root = self._default_local_state_root(local_state_root)
            self.memory_root = workspace_local_root(self.workspace, state_root)
            self.storage_root = state_root
            self.shared_workspace = True
        self.db_path = self.memory_root / "escala.db"
        self.backups_root = self.memory_root / "backups"

    def ensure_memory(self) -> MemoryResult:
        """Create or validate this project's database without raising to a coach."""
        try:
            self._assert_memory_layout()
            self._migrate_legacy_database_if_needed()
            connection = init_db(str(self.db_path))
            connection.close()
            return self.health()
        except (OSError, sqlite3.Error, ValueError) as error:
            return self._failure(error)

    def health(self) -> MemoryResult:
        """Check SQLite integrity, expected tables, and the schema version."""
        return self._health_path(self.db_path)

    def backup(self, backup_path: str | Path | None = None) -> MemoryResult:
        """Copy the live database through SQLite's backup API into local state."""
        ready = self.ensure_memory()
        if not ready.ready:
            return ready
        target = self._backup_path(backup_path)
        if target is None:
            return self._failure(
                ValueError("backup path must stay inside local memory")
            )
        temporary = target.with_suffix(".tmp")
        try:
            self._assert_contained(temporary, self.storage_root)
            self._prepare_temporary(temporary)
            target.parent.mkdir(parents=True, exist_ok=True)
            with (
                sqlite3.connect(self.db_path) as source,
                sqlite3.connect(temporary) as destination,
            ):
                source.backup(destination)
            candidate = self._health_path(temporary)
            if not candidate.ready:
                return candidate
            os.replace(temporary, target)
            return MemoryResult(True, self.db_path, backup_path=target)
        except (OSError, sqlite3.Error, ValueError) as error:
            return self._failure(error)
        finally:
            self._cleanup_temporary(temporary)

    def restore(self, backup_path: str | Path | None = None) -> MemoryResult:
        """Restore an offline database while holding SQLite's exclusive lock.

        Callers must stop runtime/DAO activity before invoking this method. The
        lock rejects active SQLite transactions and keeps new SQLite writers out
        through replacement; it is not a coordination mechanism
        for DAOs that do not participate in SQLite locking.
        """
        try:
            self._assert_memory_layout()
        except (OSError, ValueError) as error:
            return self._failure(error)
        source = self._backup_path(backup_path)
        if source is None or not source.is_file():
            return self._failure(ValueError("valid local backup not found"))
        candidate = self._health_path(source)
        if not candidate.ready:
            return candidate
        temporary = self.db_path.with_suffix(".restore.tmp")
        try:
            self._assert_contained(temporary, self.storage_root)
            self._prepare_temporary(temporary)
            self._assert_wal_sidecars_contained()
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            has_live_database = self._live_database_is_sqlite()
            self._checkpoint_wal()
            live_fingerprint = (
                self._database_fingerprint() if has_live_database else None
            )
            with self._exclusive_restore_connection() as live:
                if live is not None and live_fingerprint is not None:
                    self._assert_database_was_not_modified(live_fingerprint)
                with (
                    sqlite3.connect(source) as backup,
                    sqlite3.connect(temporary) as destination,
                ):
                    backup.backup(destination)
                restored = self._health_path(temporary)
                if not restored.ready:
                    return restored
                os.replace(temporary, self.db_path)
                self._remove_wal_sidecars()
            return MemoryResult(True, self.db_path)
        except (OSError, sqlite3.Error, ValueError) as error:
            return self._failure(error)
        finally:
            self._cleanup_temporary(temporary)

    def _health_path(self, path: Path) -> MemoryResult:
        try:
            self._assert_memory_layout()
            self._assert_contained(path, self.storage_root)
            if not path.is_file():
                return self._failure(ValueError("local database does not exist"))
            with sqlite3.connect(self._sqlite_uri(path), uri=True) as connection:
                integrity = connection.execute("PRAGMA integrity_check").fetchone()
                if integrity is None or integrity[0] != "ok":
                    return self._failure(ValueError("SQLite integrity check failed"))
                if not schema_contract_tables_are_present(connection):
                    return self._failure(
                        ValueError("local database schema is incomplete")
                    )
                if not schema_contract_is_valid(connection):
                    return self._failure(
                        ValueError("local database schema structure is invalid")
                    )
                version = connection.execute(
                    "SELECT value FROM _meta WHERE key = 'schema_version'"
                ).fetchone()
                if version is None or int(version[0]) != SCHEMA_VERSION:
                    return self._failure(
                        ValueError("local database schema version is invalid")
                    )
            return MemoryResult(True, self.db_path)
        except (OSError, sqlite3.Error, ValueError) as error:
            return self._failure(error)

    def _backup_path(self, supplied: str | Path | None) -> Path | None:
        path = (
            self.backups_root / "escala-backup.db"
            if supplied is None
            else Path(supplied)
        )
        try:
            self._assert_memory_layout()
            path = path.resolve()
            self._assert_contained(path, self.storage_root)
            self._assert_contained(path, self.backups_root)
        except (OSError, ValueError):
            return None
        return path

    def _assert_memory_layout(self) -> None:
        """Reject a location that could put SQLite inside shared documents."""
        if self.workspace_error:
            raise ValueError("shared workspace manifest is invalid: " + self.workspace_error)
        self._assert_contained(self.memory_root, self.storage_root)
        self._assert_contained(self.db_path, self.storage_root)
        self._assert_contained(self.backups_root, self.storage_root)
        if self.shared_workspace and path_is_inside(self.memory_root, self.workspace_root):
            raise ValueError("local SQLite state must stay outside the shared workspace")

    @contextmanager
    def _exclusive_restore_connection(self) -> Iterator[sqlite3.Connection | None]:
        """Hold the SQLite exclusion required for an offline replacement."""
        if not self.db_path.exists():
            yield None
            return
        with self.db_path.open("rb") as database:
            if database.read(16) != b"SQLite format 3\x00":
                yield None
                return
        with sqlite3.connect(
            self._sqlite_uri(self.db_path), uri=True, isolation_level=None, timeout=0
        ) as connection:
            connection.execute("PRAGMA busy_timeout = 0")
            connection.execute("BEGIN EXCLUSIVE")
            yield connection

    def _checkpoint_wal(self) -> None:
        """Flush WAL before exclusion, failing safely when a user is active."""
        if not self._live_database_is_sqlite() or not any(
            sidecar.exists() for sidecar in self._wal_sidecars()
        ):
            return
        with sqlite3.connect(
            self._sqlite_uri(self.db_path), uri=True, isolation_level=None, timeout=0
        ) as connection:
            connection.execute("PRAGMA busy_timeout = 0")
            checkpoint = connection.execute(
                "PRAGMA wal_checkpoint(TRUNCATE)"
            ).fetchone()
        if checkpoint is None or checkpoint[0] != 0:
            raise sqlite3.OperationalError("cannot checkpoint active local database")

    def _assert_database_was_not_modified(self, expected_fingerprint: bytes) -> None:
        """Detect a writer that committed after the pre-lock checkpoint."""
        wal, _ = self._wal_sidecars()
        if (
            self._database_fingerprint() != expected_fingerprint
            or wal.exists()
            and wal.stat().st_size
        ):
            raise sqlite3.OperationalError("local database changed during restore")

    def _database_fingerprint(self) -> bytes:
        return sha256(self.db_path.read_bytes()).digest()

    def _live_database_is_sqlite(self) -> bool:
        if not self.db_path.exists():
            return False
        with self.db_path.open("rb") as database:
            return database.read(16) == b"SQLite format 3\x00"

    def _wal_sidecars(self) -> tuple[Path, Path]:
        return (
            self.db_path.with_name(f"{self.db_path.name}-wal"),
            self.db_path.with_name(f"{self.db_path.name}-shm"),
        )

    def _assert_wal_sidecars_contained(self) -> None:
        for sidecar in self._wal_sidecars():
            self._assert_contained(sidecar, self.storage_root)

    def _remove_wal_sidecars(self) -> None:
        self._assert_wal_sidecars_contained()
        for sidecar in self._wal_sidecars():
            sidecar.unlink(missing_ok=True)

    @staticmethod
    def _sqlite_uri(path: Path) -> str:
        """Build a SQLite URI without interpreting path characters as query syntax."""
        return f"{path.resolve().as_uri()}?mode=rw"

    @staticmethod
    def _prepare_temporary(path: Path) -> None:
        """Clear an old temporary file, refusing a path that is a directory."""
        if not path.exists():
            return
        if path.is_dir():
            raise ValueError("temporary database path must be a file")
        path.unlink()

    @staticmethod
    def _cleanup_temporary(path: Path) -> None:
        """Best-effort cleanup that cannot mask the operation's MemoryResult."""
        try:
            if path.exists() and not path.is_dir():
                path.unlink()
        except OSError:
            pass

    @staticmethod
    def _assert_contained(path: Path, root: Path) -> None:
        path.resolve().relative_to(root.resolve())

    @staticmethod
    def _default_local_state_root(supplied: str | Path | None) -> Path:
        if supplied is not None:
            return Path(supplied).expanduser().resolve()
        configured = os.environ.get("SCALEUP_LOCAL_STATE_ROOT")
        if configured:
            return Path(configured).expanduser().resolve()
        xdg_state = os.environ.get("XDG_STATE_HOME")
        if xdg_state:
            return Path(xdg_state).expanduser().resolve() / "scaleup" / "workspaces"
        return Path.home() / ".local" / "state" / "scaleup" / "workspaces"

    def _migrate_legacy_database_if_needed(self) -> None:
        """Relocate E22 SQLite safely before a folder becomes shareable.

        A successful conversion leaves an independently verified SQLite copy and
        a backup in local state, then removes only the old DB/WAL/SHM/backups
        from the shared folder. We never delete arbitrary project files.
        """
        if not self.shared_workspace:
            return
        legacy_db = self.legacy_memory_root / "escala.db"
        if not legacy_db.is_file():
            return
        if self.db_path.exists():
            raise ValueError(
                "legacy SQLite is still inside the shared workspace; move it only after verifying the local copy"
            )
        self.memory_root.mkdir(parents=True, exist_ok=True)
        temporary = self.db_path.with_suffix(".migration.tmp")
        self._assert_contained(temporary, self.storage_root)
        self._prepare_temporary(temporary)
        try:
            with (
                sqlite3.connect(self._sqlite_uri(legacy_db), uri=True) as source,
                sqlite3.connect(temporary) as destination,
            ):
                source.backup(destination)
            os.replace(temporary, self.db_path)
            migrated = self._health_path(self.db_path)
            if not migrated.ready:
                self.db_path.unlink(missing_ok=True)
                raise ValueError("legacy local database could not be migrated safely")
            self._archive_and_remove_legacy_memory()
        finally:
            self._cleanup_temporary(temporary)

    def _archive_and_remove_legacy_memory(self) -> None:
        """Preserve E22 memory locally, then remove only known SQLite artifacts."""
        archive_root = self.backups_root / "legacy-e22"
        self._assert_contained(archive_root, self.storage_root)
        archive_root.mkdir(parents=True, exist_ok=True)
        archive = archive_root / "escala-before-workspace-migration.db"
        temporary = archive.with_suffix(".tmp")
        self._assert_contained(temporary, self.storage_root)
        self._prepare_temporary(temporary)
        try:
            with (
                sqlite3.connect(self.db_path) as source,
                sqlite3.connect(temporary) as destination,
            ):
                source.backup(destination)
            if not self._health_path(temporary).ready:
                raise ValueError("could not create a verified local migration backup")
            os.replace(temporary, archive)
            legacy_artifacts = [
                self.legacy_memory_root / "escala.db",
                self.legacy_memory_root / "escala.db-wal",
                self.legacy_memory_root / "escala.db-shm",
            ]
            legacy_backups = self.legacy_memory_root / "backups"
            if legacy_backups.is_dir():
                for candidate in sorted(legacy_backups.glob("*.db")):
                    if candidate.is_file() and path_is_inside(candidate, self.legacy_memory_root):
                        destination = archive_root / f"legacy-{candidate.name}"
                        self._copy_file_atomically(candidate, destination)
                        legacy_artifacts.append(candidate)
            for artifact in legacy_artifacts:
                if artifact.is_file() and path_is_inside(artifact, self.legacy_memory_root):
                    artifact.unlink()
            if legacy_backups.is_dir():
                legacy_backups.rmdir()
            self.legacy_memory_root.rmdir()
        finally:
            self._cleanup_temporary(temporary)

    @staticmethod
    def _copy_file_atomically(source: Path, destination: Path) -> None:
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        try:
            shutil.copy2(source, temporary)
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)

    def _failure(self, error: Exception) -> MemoryResult:
        return MemoryResult(False, self.db_path, reason=str(error))
