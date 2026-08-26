"""Project-scoped, local SQLite runtime for ScaleUp business memory."""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path

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

    _required_tables = frozenset({"_meta", "companies", "memory_facts", "entities"})

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        self.memory_root = self.project_root / ".scaleup" / "memory"
        self.db_path = self.memory_root / "escala.db"
        self.backups_root = self.memory_root / "backups"

    def ensure_memory(self) -> MemoryResult:
        """Create or validate this project's database without raising to a coach."""
        try:
            self._assert_contained(self.db_path, self.memory_root)
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
            return self._failure(ValueError("backup path must stay inside project memory"))
        temporary = target.with_suffix(".tmp")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path) as source, sqlite3.connect(temporary) as destination:
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
        """Atomically replace the live DB only after a healthy backup is available."""
        source = self._backup_path(backup_path)
        if source is None or not source.is_file():
            return self._failure(ValueError("valid local backup not found"))
        candidate = self._health_path(source)
        if not candidate.ready:
            return candidate
        temporary = self.db_path.with_suffix(".restore.tmp")
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(source) as backup, sqlite3.connect(temporary) as destination:
                backup.backup(destination)
            restored = self._health_path(temporary)
            if not restored.ready:
                return restored
            os.replace(temporary, self.db_path)
            return self.health()
        except (OSError, sqlite3.Error, ValueError) as error:
            return self._failure(error)
        finally:
            temporary.unlink(missing_ok=True)

    def _health_path(self, path: Path) -> MemoryResult:
        try:
            self._assert_contained(path, self.memory_root)
            if not path.is_file():
                return self._failure(ValueError("local database does not exist"))
            with sqlite3.connect(f"file:{path}?mode=rw", uri=True) as connection:
                integrity = connection.execute("PRAGMA integrity_check").fetchone()
                if integrity is None or integrity[0] != "ok":
                    return self._failure(ValueError("SQLite integrity check failed"))
                tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if not self._required_tables.issubset(tables):
                    return self._failure(ValueError("local database schema is incomplete"))
                version = connection.execute("SELECT value FROM _meta WHERE key = 'schema_version'").fetchone()
                if version is None or int(version[0]) != SCHEMA_VERSION:
                    return self._failure(ValueError("local database schema version is invalid"))
            return MemoryResult(True, self.db_path)
        except (OSError, sqlite3.Error, ValueError) as error:
            return self._failure(error)

    def _backup_path(self, supplied: str | Path | None) -> Path | None:
        path = self.backups_root / "escala-backup.db" if supplied is None else Path(supplied)
        try:
            path = path.resolve()
            self._assert_contained(path, self.backups_root)
        except ValueError:
            return None
        return path

    @staticmethod
    def _assert_contained(path: Path, root: Path) -> None:
        path.resolve().relative_to(root.resolve())

    def _failure(self, error: Exception) -> MemoryResult:
        return MemoryResult(False, self.db_path, reason=str(error))
