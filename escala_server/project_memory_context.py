"""Read-only, project-scoped recovery of verified business context."""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .project_memory import ProjectMemoryRuntime

_PROFILE_SOURCE = ".scaleup/agent/memory/company-profile.yaml"
_PROFILE_SOURCE_KIND = "company-profile"
_IMPORT_SCHEMA = 1
_FACT_PREFIXES = ("profile.focus.", "diagnosis.", "profile.")
_SENSITIVE_KEY_PARTS = frozenset(
    {"api", "credential", "key", "password", "secret", "token"}
)


@dataclass(frozen=True)
class ContextItem:
    """A compact, verified item that a later UX adapter may present."""

    key: str
    value: str
    source: str
    observed_at: str
    kind: Literal["fact", "change"]
    confirmed: bool = True


@dataclass(frozen=True)
class SessionRecoveryResult:
    """Read-only context outcome; technical reason remains internal."""

    ready: bool
    items: tuple[ContextItem, ...] = ()
    reason: str | None = None
    user_message: None = None


class ProjectMemorySessionContext:
    """Recover only ledger-verified facts and worksheet metadata for one root."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        self.runtime = ProjectMemoryRuntime(self.project_root)

    def load(self) -> SessionRecoveryResult:
        """Return a bounded context without creating, changing, or repairing data."""
        health = self.runtime.health()
        if not health.ready:
            return self._fallback(health.reason)
        try:
            with sqlite3.connect(self._read_only_uri(health.db_path), uri=True) as db:
                profile_applied_at = self._verified_profile_application(db)
                if profile_applied_at is None or not self._has_company(db):
                    return SessionRecoveryResult(True)
                items = [
                    *self._verified_facts(db),
                    *self._verified_changes(db),
                ]
                return SessionRecoveryResult(True, tuple(self._rank(items)[:5]))
        except (OSError, sqlite3.Error, TypeError, ValueError) as error:
            return self._fallback(str(error))

    @staticmethod
    def _read_only_uri(path: Path) -> str:
        return f"{path.resolve().as_uri()}?mode=ro"

    @staticmethod
    def _fallback(reason: str | None) -> SessionRecoveryResult:
        return SessionRecoveryResult(False, reason=reason or "local memory unavailable")

    @staticmethod
    def _has_company(db: sqlite3.Connection) -> bool:
        return db.execute("SELECT 1 FROM companies LIMIT 1").fetchone() is not None

    @staticmethod
    def _verified_profile_application(db: sqlite3.Connection) -> str | None:
        row = db.execute(
            """SELECT applications.applied_at
            FROM migration_applications AS applications
            JOIN migration_sources AS sources
              ON sources.relative_path = applications.relative_path
             AND sources.content_sha256 = applications.content_sha256
             AND sources.import_schema = applications.import_schema
             AND sources.source_kind = applications.source_kind
            WHERE applications.relative_path = ?
              AND applications.source_kind = ?
              AND applications.import_schema = ?
            ORDER BY applications.id DESC
            LIMIT 1""",
            (_PROFILE_SOURCE, _PROFILE_SOURCE_KIND, _IMPORT_SCHEMA),
        ).fetchone()
        return (
            row[0] if row is not None and isinstance(row[0], str) and row[0] else None
        )

    def _verified_facts(self, db: sqlite3.Connection) -> list[ContextItem]:
        facts: list[ContextItem] = []
        for key, raw_value, observed_at in db.execute(
            "SELECT key, value, updated_at FROM memory_facts ORDER BY key"
        ):
            if not isinstance(observed_at, str) or not observed_at:
                continue
            if not self._allowed_fact_key(key):
                continue
            value = self._brief_scalar(raw_value)
            if value is not None:
                facts.append(
                    ContextItem(
                        key=key,
                        value=value,
                        source=_PROFILE_SOURCE,
                        observed_at=observed_at,
                        kind="fact",
                    )
                )
        return facts

    @staticmethod
    def _allowed_fact_key(key: object) -> bool:
        if not isinstance(key, str) or not key.startswith(_FACT_PREFIXES):
            return False
        return not any(part in _SENSITIVE_KEY_PARTS for part in key.split("."))

    @staticmethod
    def _brief_scalar(raw_value: object) -> str | None:
        if not isinstance(raw_value, str):
            return None
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            return None
        if isinstance(value, str):
            return value.strip() or None
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float) and math.isfinite(value):
            return str(value)
        return None

    def _verified_changes(self, db: sqlite3.Connection) -> list[ContextItem]:
        changes: list[ContextItem] = []
        rows = db.execute(
            """SELECT category, tool, data, updated_at
            FROM worksheets
            WHERE id IN (
                SELECT MAX(id) FROM worksheets GROUP BY category, tool
            )
            ORDER BY category, tool"""
        )
        for category, tool, raw_data, observed_at in rows:
            envelope = self._worksheet_envelope(raw_data)
            if (
                envelope is None
                or not isinstance(category, str)
                or not category
                or not isinstance(tool, str)
                or not tool
                or not isinstance(observed_at, str)
                or not observed_at
                or not self._worksheet_application_exists(db, envelope)
            ):
                continue
            source_kind, relative_path, _ = envelope
            changes.append(
                ContextItem(
                    key=f"{source_kind}:{category}/{tool}",
                    value=f"{source_kind}: {category}/{tool}",
                    source=relative_path,
                    observed_at=observed_at,
                    kind="change",
                )
            )
        return changes

    @staticmethod
    def _worksheet_envelope(raw_data: object) -> tuple[str, str, str] | None:
        if not isinstance(raw_data, str):
            return None
        try:
            payload = json.loads(raw_data)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        source_kind = payload.get("source_kind")
        relative_path = payload.get("relative_path")
        content_sha256 = payload.get("content_sha256")
        if not all(
            isinstance(value, str) and value
            for value in (source_kind, relative_path, content_sha256)
        ):
            return None
        return source_kind, relative_path, content_sha256

    @staticmethod
    def _worksheet_application_exists(
        db: sqlite3.Connection, envelope: tuple[str, str, str]
    ) -> bool:
        source_kind, relative_path, content_sha256 = envelope
        return (
            db.execute(
                """SELECT 1
                FROM migration_applications AS applications
                JOIN migration_sources AS sources
                  ON sources.relative_path = applications.relative_path
                 AND sources.content_sha256 = applications.content_sha256
                 AND sources.import_schema = applications.import_schema
                 AND sources.source_kind = applications.source_kind
                WHERE applications.relative_path = ?
                  AND applications.content_sha256 = ?
                  AND applications.source_kind = ?
                  AND applications.import_schema = ?
                LIMIT 1""",
                (relative_path, content_sha256, source_kind, _IMPORT_SCHEMA),
            ).fetchone()
            is not None
        )

    @staticmethod
    def _rank(items: list[ContextItem]) -> list[ContextItem]:
        """Apply a stable priority/date/key ordering without any model inference."""
        ordered = sorted(items, key=lambda item: item.key)
        ordered.sort(key=lambda item: item.observed_at, reverse=True)
        ordered.sort(key=lambda item: ProjectMemorySessionContext._priority(item))
        return ordered

    @staticmethod
    def _priority(item: ContextItem) -> int:
        if item.kind == "change":
            return 3
        if item.key.startswith("profile.focus."):
            return 0
        if item.key.startswith("diagnosis."):
            return 1
        return 2
