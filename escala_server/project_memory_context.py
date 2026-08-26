"""Read-only, project-scoped recovery of verified business context."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .project_memory import ProjectMemoryRuntime

_PROFILE_SOURCE = ".scaleup/agent/memory/company-profile.yaml"
_PROFILE_SOURCE_KIND = "company-profile"
_MAX_FACT_VALUE_LENGTH = 240
_MAX_WORKSHEET_METADATA_LENGTH = 96
_MAX_SOURCE_PATH_LENGTH = 240
_WORKSHEET_SOURCE_KINDS = frozenset(
    {"context", "worksheet", "opsp", "legacy-plan", "pulse-history"}
)
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

    def _verified_facts(self, db: sqlite3.Connection) -> list[ContextItem]:
        facts: list[ContextItem] = []
        rows = db.execute(
            """SELECT facts.key, facts.value, facts.updated_at,
                      applications.applied_at, provenance.value_sha256
            FROM memory_facts AS facts
            JOIN migration_fact_applications AS provenance
              ON provenance.fact_key = facts.key
            JOIN migration_applications AS applications
              ON applications.id = provenance.migration_application_id
            JOIN migration_sources AS sources
              ON sources.relative_path = applications.relative_path
             AND sources.content_sha256 = applications.content_sha256
             AND sources.import_schema = applications.import_schema
             AND sources.source_kind = applications.source_kind
            WHERE applications.id = (
                SELECT id FROM migration_applications
                WHERE relative_path = ? AND source_kind = ? AND import_schema = ?
                ORDER BY id DESC LIMIT 1
            )
            ORDER BY facts.key""",
            (_PROFILE_SOURCE, _PROFILE_SOURCE_KIND, _IMPORT_SCHEMA),
        )
        for key, raw_value, updated_at, applied_at, value_sha256 in rows:
            if (
                updated_at != applied_at
                or not isinstance(applied_at, str)
                or not applied_at
            ):
                continue
            if not isinstance(raw_value, str) or not isinstance(value_sha256, str):
                continue
            if hashlib.sha256(raw_value.encode()).hexdigest() != value_sha256:
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
                        observed_at=applied_at,
                        kind="fact",
                    )
                )
        return facts

    @staticmethod
    def _allowed_fact_key(key: object) -> bool:
        if not isinstance(key, str) or not key.startswith(_FACT_PREFIXES):
            return False
        normalized = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", key)
        normalized = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", normalized).lower()
        tokens = set(re.split(r"[^a-z0-9]+", normalized))
        return not bool(tokens & _SENSITIVE_KEY_PARTS)

    @staticmethod
    def _brief_scalar(raw_value: object) -> str | None:
        if not isinstance(raw_value, str):
            return None
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            return None
        if isinstance(value, str):
            result = value.strip()
        elif isinstance(value, bool):
            result = str(value).lower()
        elif (
            isinstance(value, int) or isinstance(value, float) and math.isfinite(value)
        ):
            result = str(value)
        else:
            return None
        return result if result and len(result) <= _MAX_FACT_VALUE_LENGTH else None

    def _verified_changes(self, db: sqlite3.Connection) -> list[ContextItem]:
        changes: list[ContextItem] = []
        rows = db.execute(
            """SELECT category, tool, data
            FROM worksheets
            WHERE id IN (
                SELECT MAX(id) FROM worksheets GROUP BY category, tool
            )
            ORDER BY category, tool"""
        )
        for category, tool, raw_data in rows:
            envelope = self._worksheet_envelope(raw_data)
            if envelope is None or not self._safe_worksheet_metadata(
                category, tool, envelope
            ):
                continue
            source_kind, relative_path, _ = envelope
            applied_at = self._verified_worksheet_application(db, envelope)
            if applied_at is None:
                continue
            changes.append(
                ContextItem(
                    key=f"{source_kind}:{category}/{tool}",
                    value=f"{source_kind}: {category}/{tool}",
                    source=relative_path,
                    observed_at=applied_at,
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
    def _safe_worksheet_metadata(
        category: object, tool: object, envelope: tuple[str, str, str]
    ) -> bool:
        source_kind, relative_path, _ = envelope
        values = (source_kind, category, tool)
        if source_kind not in _WORKSHEET_SOURCE_KINDS:
            return False
        if not all(
            isinstance(value, str)
            and value
            and len(value) <= _MAX_WORKSHEET_METADATA_LENGTH
            and re.fullmatch(r"[A-Za-z0-9_-]+", value)
            and ProjectMemorySessionContext._allowed_fact_key(f"profile.{value}")
            for value in values
        ):
            return False
        path = Path(relative_path)
        return (
            len(relative_path) <= _MAX_SOURCE_PATH_LENGTH
            and not path.is_absolute()
            and ".." not in path.parts
        )

    @staticmethod
    def _verified_worksheet_application(
        db: sqlite3.Connection, envelope: tuple[str, str, str]
    ) -> str | None:
        source_kind, relative_path, content_sha256 = envelope
        row = db.execute(
            """SELECT applications.applied_at
            FROM migration_applications AS applications
            JOIN migration_sources AS sources
              ON sources.relative_path = applications.relative_path
             AND sources.content_sha256 = applications.content_sha256
             AND sources.import_schema = applications.import_schema
             AND sources.source_kind = applications.source_kind
            WHERE applications.id = (
                SELECT id FROM migration_applications
                WHERE relative_path = ? AND import_schema = ?
                ORDER BY id DESC LIMIT 1
            )
              AND applications.content_sha256 = ?
              AND applications.source_kind = ?""",
            (relative_path, _IMPORT_SCHEMA, content_sha256, source_kind),
        ).fetchone()
        return (
            row[0] if row is not None and isinstance(row[0], str) and row[0] else None
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
