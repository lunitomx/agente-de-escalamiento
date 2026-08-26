"""Project-scoped, local SQLite runtime for ScaleUp business memory."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from .schema import SCHEMA_VERSION, init_db


@dataclass(frozen=True)
class MemoryResult:
    """Outcome of a local-memory operation that is safe for callers to consume."""

    ready: bool
    db_path: Path
    reason: str | None = None
    backup_path: Path | None = None


class ProjectMemoryRuntime:
    """Own the SQLite database belonging to one project, never a global home path."""

    _required_tables = frozenset(
        {
            "_meta",
            "companies",
            "worksheets",
            "sessions",
            "changes_log",
            "memory_facts",
            "entities",
            "relationships",
        }
    )

    _required_columns: ClassVar[dict] = {
        "_meta": {"key": ("TEXT", 1), "value": ("TEXT", 0)},
        "companies": {
            "id": ("TEXT", 1),
            "name": ("TEXT", 0),
            "industry": ("TEXT", 0),
            "metadata": ("TEXT", 0),
            "created_at": ("TEXT", 0),
            "updated_at": ("TEXT", 0),
        },
        "worksheets": {
            "id": ("INTEGER", 1),
            "category": ("TEXT", 0),
            "tool": ("TEXT", 0),
            "data": ("TEXT", 0),
            "session_id": ("TEXT", 0),
            "version": ("INTEGER", 0),
            "created_at": ("TEXT", 0),
            "updated_at": ("TEXT", 0),
        },
        "sessions": {
            "id": ("TEXT", 1),
            "company_id": ("TEXT", 0),
            "status": ("TEXT", 0),
            "metadata": ("TEXT", 0),
            "created_at": ("TEXT", 0),
            "updated_at": ("TEXT", 0),
        },
        "changes_log": {
            "id": ("INTEGER", 1),
            "company_id": ("TEXT", 0),
            "session_id": ("TEXT", 0),
            "category": ("TEXT", 0),
            "tool": ("TEXT", 0),
            "field": ("TEXT", 0),
            "old_value": ("TEXT", 0),
            "new_value": ("TEXT", 0),
            "diff_type": ("TEXT", 0),
            "created_at": ("TEXT", 0),
        },
        "memory_facts": {
            "id": ("INTEGER", 1),
            "key": ("TEXT", 0),
            "value": ("TEXT", 0),
            "created_at": ("TEXT", 0),
            "updated_at": ("TEXT", 0),
        },
        "entities": {
            "id": ("INTEGER", 1),
            "type": ("TEXT", 0),
            "name": ("TEXT", 0),
            "properties": ("TEXT", 0),
            "created_at": ("TEXT", 0),
            "updated_at": ("TEXT", 0),
        },
        "relationships": {
            "id": ("INTEGER", 1),
            "source_entity_id": ("INTEGER", 0),
            "target_entity_id": ("INTEGER", 0),
            "relation_type": ("TEXT", 0),
            "properties": ("TEXT", 0),
            "created_at": ("TEXT", 0),
        },
    }
    _required_indexes: ClassVar[dict] = {
        "idx_worksheets_category_tool": ("worksheets", ("category", "tool")),
        "idx_worksheets_category_version": ("worksheets", ("category", "version")),
        "idx_worksheets_session": ("worksheets", ("session_id",)),
        "idx_sessions_company": ("sessions", ("company_id",)),
        "idx_changes_log_session": ("changes_log", ("session_id",)),
        "idx_changes_log_company": ("changes_log", ("company_id",)),
        "idx_memory_facts_key": ("memory_facts", ("key",)),
        "idx_entities_type": ("entities", ("type",)),
        "idx_relationships_source": ("relationships", ("source_entity_id",)),
        "idx_relationships_target": ("relationships", ("target_entity_id",)),
        "idx_relationships_type": ("relationships", ("relation_type",)),
    }

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        self.memory_root = self.project_root / ".scaleup" / "memory"
        self.db_path = self.memory_root / "escala.db"
        self.backups_root = self.memory_root / "backups"

    def ensure_memory(self) -> MemoryResult:
        """Create or validate this project's database without raising to a coach."""
        try:
            self._assert_memory_layout()
            connection = init_db(str(self.db_path))
            connection.close()
            return self.health()
        except (OSError, sqlite3.Error, ValueError) as error:
            return self._failure(error)

    def health(self) -> MemoryResult:
        """Check SQLite integrity, expected tables, and the schema version."""
        return self._health_path(self.db_path)

    def backup(self, backup_path: str | Path | None = None) -> MemoryResult:
        """Copy the live database through SQLite's backup API into project data."""
        ready = self.ensure_memory()
        if not ready.ready:
            return ready
        target = self._backup_path(backup_path)
        if target is None:
            return self._failure(
                ValueError("backup path must stay inside project memory")
            )
        temporary = target.with_suffix(".tmp")
        try:
            self._assert_contained(temporary, self.project_root)
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
            temporary.unlink(missing_ok=True)

    def restore(self, backup_path: str | Path | None = None) -> MemoryResult:
        """Restore an offline database while holding SQLite's exclusive lock.

        Callers must stop runtime/DAO activity before invoking this method. The
        lock rejects active SQLite transactions and keeps new SQLite writers out
        through checkpoint and replacement; it is not a coordination mechanism
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
            self._assert_contained(temporary, self.project_root)
            self._assert_wal_sidecars_contained()
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with self._exclusive_restore_connection() as live:
                self._checkpoint_wal(live)
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
            temporary.unlink(missing_ok=True)

    def _health_path(self, path: Path) -> MemoryResult:
        try:
            self._assert_memory_layout()
            self._assert_contained(path, self.project_root)
            if not path.is_file():
                return self._failure(ValueError("local database does not exist"))
            with sqlite3.connect(f"file:{path}?mode=rw", uri=True) as connection:
                integrity = connection.execute("PRAGMA integrity_check").fetchone()
                if integrity is None or integrity[0] != "ok":
                    return self._failure(ValueError("SQLite integrity check failed"))
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
                if not self._required_tables.issubset(tables):
                    return self._failure(
                        ValueError("local database schema is incomplete")
                    )
                if not self._schema_structure_is_valid(connection):
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
            self._assert_contained(path, self.project_root)
            self._assert_contained(path, self.backups_root)
        except (OSError, ValueError):
            return None
        return path

    def _assert_memory_layout(self) -> None:
        """Reject symlinked memory paths that would escape this project."""
        self._assert_contained(self.memory_root, self.project_root)
        self._assert_contained(self.db_path, self.project_root)
        self._assert_contained(self.backups_root, self.project_root)

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
            f"file:{self.db_path}?mode=rw", uri=True, isolation_level=None, timeout=0
        ) as connection:
            connection.execute("PRAGMA busy_timeout = 0")
            connection.execute("BEGIN EXCLUSIVE")
            yield connection

    def _checkpoint_wal(self, connection: sqlite3.Connection | None) -> None:
        """Flush WAL while restore's exclusion is held, or fail safely if busy."""
        if connection is None or not any(
            sidecar.exists() for sidecar in self._wal_sidecars()
        ):
            return
        checkpoint = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        if checkpoint is None or checkpoint[0] != 0:
            raise sqlite3.OperationalError("cannot checkpoint active local database")

    def _schema_structure_is_valid(self, connection: sqlite3.Connection) -> bool:
        for table, expected_columns in self._required_columns.items():
            actual_columns = {
                row[1]: (row[2].upper(), row[5])
                for row in connection.execute(f"PRAGMA table_info({table})")
            }
            if actual_columns != expected_columns:
                return False
        for name, (table, expected_columns) in self._required_indexes.items():
            index = next(
                (
                    row
                    for row in connection.execute(f"PRAGMA index_list({table})")
                    if row[1] == name and row[2] == 0
                ),
                None,
            )
            if index is None:
                return False
            columns = tuple(
                row[2] for row in connection.execute(f"PRAGMA index_info({name})")
            )
            if columns != expected_columns:
                return False
        for index in connection.execute("PRAGMA index_list(memory_facts)"):
            if index[2] != 1:
                continue
            columns = tuple(
                row[2] for row in connection.execute(f"PRAGMA index_info({index[1]})")
            )
            if columns == ("key",):
                return True
        return False

    def _wal_sidecars(self) -> tuple[Path, Path]:
        return (
            self.db_path.with_name(f"{self.db_path.name}-wal"),
            self.db_path.with_name(f"{self.db_path.name}-shm"),
        )

    def _assert_wal_sidecars_contained(self) -> None:
        for sidecar in self._wal_sidecars():
            self._assert_contained(sidecar, self.project_root)

    def _remove_wal_sidecars(self) -> None:
        self._assert_wal_sidecars_contained()
        for sidecar in self._wal_sidecars():
            sidecar.unlink(missing_ok=True)

    @staticmethod
    def _assert_contained(path: Path, root: Path) -> None:
        path.resolve().relative_to(root.resolve())

    def _failure(self, error: Exception) -> MemoryResult:
        return MemoryResult(False, self.db_path, reason=str(error))
