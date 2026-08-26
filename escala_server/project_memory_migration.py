"""Idempotent import of project-local ScaleUp business artifacts."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .project_memory import ProjectMemoryRuntime

IMPORT_SCHEMA = 1


@dataclass(frozen=True)
class MigrationResult:
    ready: bool
    db_path: Path
    imported: dict[str, int] = field(default_factory=dict)
    skipped: dict[str, str] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    sources: tuple[str, ...] = ()
    reason: str | None = None


@dataclass(frozen=True)
class _Snapshot:
    relative_path: str
    source_kind: str
    payload: Any
    digest: str
    category: str | None = None
    tool: str | None = None


class ProjectMemoryMigrator:
    """Migrate only a fixed allowlist of business-owned files for one root."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        self.runtime = ProjectMemoryRuntime(self.project_root)

    def migrate(self) -> MigrationResult:
        runtime = self.runtime.ensure_memory()
        if not runtime.ready:
            return MigrationResult(False, runtime.db_path, reason=runtime.reason)
        imported: dict[str, int] = defaultdict(int)
        skipped: dict[str, str] = {}
        errors: dict[str, str] = {}
        snapshots = self._discover(skipped, errors)
        for snapshot in snapshots:
            try:
                with sqlite3.connect(runtime.db_path) as connection:
                    connection.execute("BEGIN")
                    self._ensure_application_ledger(connection)
                    if self._already_imported(connection, snapshot):
                        skipped[snapshot.relative_path] = "unchanged"
                        continue
                    connection.execute(
                        "INSERT OR IGNORE INTO migration_sources (relative_path, content_sha256, "
                        "import_schema, source_kind) VALUES (?, ?, ?, ?)",
                        (
                            snapshot.relative_path,
                            snapshot.digest,
                            IMPORT_SCHEMA,
                            snapshot.source_kind,
                        ),
                    )
                    application = connection.execute(
                        "INSERT INTO migration_applications (relative_path, content_sha256, "
                        "import_schema, source_kind) VALUES (?, ?, ?, ?)",
                        (
                            snapshot.relative_path,
                            snapshot.digest,
                            IMPORT_SCHEMA,
                            snapshot.source_kind,
                        ),
                    )
                    application_id = application.lastrowid
                    applied_at = connection.execute(
                        "SELECT applied_at FROM migration_applications WHERE id = ?",
                        (application_id,),
                    ).fetchone()[0]
                    self._apply(connection, snapshot, application_id, applied_at)
                imported[snapshot.source_kind] += 1
            except (sqlite3.Error, ValueError, TypeError) as error:
                errors[snapshot.relative_path] = str(error)
        return MigrationResult(
            True,
            runtime.db_path,
            dict(imported),
            skipped,
            errors,
            tuple(item.relative_path for item in snapshots),
        )

    def _discover(
        self, skipped: dict[str, str], errors: dict[str, str]
    ) -> list[_Snapshot]:
        candidates: list[tuple[Path, str, str | None, str | None]] = [
            (
                self.project_root / ".scaleup/agent/memory/company-profile.yaml",
                "company-profile",
                None,
                None,
            ),
            (
                self.project_root / ".scaleup/my-company/pulse-history.yaml",
                "pulse-history",
                "diagnosis",
                "pulse-history",
            ),
        ]
        for directory, kind, category in (
            ("context", "context", "context"),
            ("worksheets", "worksheet", None),
        ):
            base = self.project_root / ".scaleup/my-company" / directory
            try:
                self._safe_relative(base)
            except ValueError as error:
                errors[self._relative(base)] = str(error)
                continue
            if base.exists() and base.is_dir():
                candidates.extend(
                    (path, kind, category, path.stem if category else None)
                    for path in sorted(base.glob("*.yaml"))
                )
        opsp = self.project_root / "work/strategy/opsp.md"
        opsp_relative = self._relative(opsp)
        if not opsp.exists():
            skipped[opsp_relative] = "missing"
        if opsp.exists() and self._valid_opsp(opsp, skipped, errors):
            candidates.append((opsp, "opsp", "strategy", "opsp"))
        else:
            candidates.extend(
                (
                    self.project_root / ".scaleup/my-company" / name,
                    "legacy-plan",
                    category,
                    tool,
                )
                for name, category, tool in (
                    ("annual-goal.md", "strategy", "annual-goal"),
                    ("quarterly-focus.md", "execution", "quarterly-focus"),
                )
            )
        snapshots = []
        for path, kind, category, tool in candidates:
            relative = self._relative(path)
            try:
                relative = self._safe_relative(path)
                if not path.exists():
                    skipped[relative] = "missing"
                    continue
                payload, digest = self._read(path, require_frontmatter=kind == "opsp")
                if kind in {"company-profile", "worksheet"} and not isinstance(
                    payload, dict
                ):
                    raise ValueError(f"{kind} must be a YAML mapping")
                if kind == "worksheet":
                    category = str(payload.get("decision") or "worksheet")
                    tool = str(payload.get("id") or path.stem)
                snapshots.append(
                    _Snapshot(relative, kind, payload, digest, category, tool)
                )
            except (
                OSError,
                UnicodeDecodeError,
                ValueError,
                TypeError,
                yaml.YAMLError,
            ) as error:
                errors[relative] = str(error)
        return snapshots

    def _valid_opsp(
        self, path: Path, skipped: dict[str, str], errors: dict[str, str]
    ) -> bool:
        relative = self._relative(path)
        try:
            relative = self._safe_relative(path)
            if not path.exists():
                return False
            frontmatter = self._frontmatter(path.read_text(encoding="utf-8"))
            if frontmatter.get("schema") != "tool-opsp":
                skipped[relative] = "unsupported schema"
                return False
            return True
        except (
            OSError,
            UnicodeDecodeError,
            ValueError,
            TypeError,
            yaml.YAMLError,
        ) as error:
            errors[relative] = str(error)
            return False

    def _read(
        self, path: Path, *, require_frontmatter: bool = False
    ) -> tuple[Any, str]:
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if path.suffix == ".md":
            text = raw.decode("utf-8")
            return {
                "frontmatter": (
                    self._frontmatter(text)
                    if require_frontmatter
                    else (self._frontmatter(text) if text.startswith("---\n") else {})
                ),
                "text": text,
            }, digest
        payload = yaml.safe_load(raw) or {}
        if not isinstance(payload, (dict, list)):
            raise TypeError("YAML source must be a mapping or list")
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), default=str
        )
        return json.loads(canonical), hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def _safe_relative(self, path: Path) -> str:
        """Reject symlinked paths before discovery reads or expands them."""
        relative = path.relative_to(self.project_root)
        current = self.project_root
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                raise ValueError("source path contains a symlink")
        return relative.as_posix()

    @staticmethod
    def _frontmatter(text: str) -> dict[str, Any]:
        if not text.startswith("---\n"):
            raise ValueError("Markdown frontmatter is required")
        _, raw, _ = text.split("---", 2)
        payload = yaml.safe_load(raw) or {}
        if not isinstance(payload, dict):
            raise TypeError("Markdown frontmatter must be a mapping")
        return payload

    def _relative(self, path: Path) -> str:
        return path.relative_to(self.project_root).as_posix()

    @staticmethod
    def _ensure_application_ledger(connection: sqlite3.Connection) -> None:
        """Seed the application history when upgrading an existing database."""
        connection.execute(
            """INSERT INTO migration_applications (
                relative_path, content_sha256, import_schema, source_kind
            )
            SELECT relative_path, content_sha256, import_schema, source_kind
            FROM migration_sources
            WHERE NOT EXISTS (SELECT 1 FROM migration_applications)"""
        )

    @staticmethod
    def _already_imported(connection: sqlite3.Connection, snapshot: _Snapshot) -> bool:
        latest = connection.execute(
            """SELECT content_sha256 FROM migration_applications
            WHERE relative_path=? AND import_schema=?
            ORDER BY id DESC LIMIT 1""",
            (snapshot.relative_path, IMPORT_SCHEMA),
        ).fetchone()
        if latest is None or latest[0] != snapshot.digest:
            return False
        if snapshot.source_kind != "company-profile":
            return True
        application = connection.execute(
            """SELECT id FROM migration_applications
            WHERE relative_path=? AND content_sha256=? AND import_schema=?
              AND source_kind=? ORDER BY id DESC LIMIT 1""",
            (
                snapshot.relative_path,
                snapshot.digest,
                IMPORT_SCHEMA,
                snapshot.source_kind,
            ),
        ).fetchone()
        if application is None:
            return False
        fact_count = connection.execute(
            """SELECT COUNT(*) FROM memory_facts
            WHERE key LIKE 'profile.%' OR key LIKE 'diagnosis.%'"""
        ).fetchone()[0]
        if fact_count == 0:
            return True
        linked_count = connection.execute(
            """SELECT COUNT(*) FROM migration_fact_applications
            WHERE migration_application_id = ?""",
            (application[0],),
        ).fetchone()[0]
        return linked_count == fact_count

    def _apply(
        self,
        connection: sqlite3.Connection,
        snapshot: _Snapshot,
        application_id: int,
        applied_at: str,
    ) -> None:
        if snapshot.source_kind == "company-profile":
            self._apply_profile(connection, snapshot, application_id, applied_at)
            return
        assert snapshot.category is not None and snapshot.tool is not None
        version = connection.execute(
            "SELECT COALESCE(MAX(version), 0) + 1 FROM worksheets WHERE category=? AND tool=?",
            (snapshot.category, snapshot.tool),
        ).fetchone()[0]
        payload = json.dumps(
            {
                "source_kind": snapshot.source_kind,
                "relative_path": snapshot.relative_path,
                "content_sha256": snapshot.digest,
                "payload": snapshot.payload,
            },
            sort_keys=True,
        )
        connection.execute(
            "INSERT INTO worksheets (category, tool, data, version) VALUES (?, ?, ?, ?)",
            (snapshot.category, snapshot.tool, payload, version),
        )

    def _apply_profile(
        self,
        connection: sqlite3.Connection,
        snapshot: _Snapshot,
        application_id: int,
        applied_at: str,
    ) -> None:
        if not isinstance(snapshot.payload, dict):
            raise TypeError("company-profile must be a YAML mapping")
        payload = snapshot.payload
        company = (
            payload.get("company") if isinstance(payload.get("company"), dict) else {}
        )
        company_id = hashlib.sha256(
            f"{self.project_root}:{snapshot.relative_path}".encode()
        ).hexdigest()[:24]
        connection.execute(
            "INSERT INTO companies (id, name, industry, metadata) VALUES (?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET name=excluded.name, industry=excluded.industry, metadata=excluded.metadata, updated_at=datetime('now')",
            (
                company_id,
                str(company.get("name") or "Unnamed company"),
                str(company.get("industry") or ""),
                json.dumps(payload, sort_keys=True),
            ),
        )
        connection.executemany(
            "DELETE FROM memory_facts WHERE key LIKE ?",
            (
                (f"{prefix}%",)
                for prefix in ("profile.", "diagnosis.", "profile.focus.")
            ),
        )
        connection.execute(
            "DELETE FROM migration_fact_applications WHERE fact_key LIKE 'profile.%' "
            "OR fact_key LIKE 'diagnosis.%'"
        )
        for prefix, values in (
            ("profile", company),
            ("diagnosis", payload.get("scores", {})),
            ("profile.focus", payload.get("focus", {})),
        ):
            if isinstance(values, dict):
                for key, value in values.items():
                    if value not in (None, "", [], {}, 0):
                        fact_key = f"{prefix}.{key}"
                        fact_value = json.dumps(value, sort_keys=True)
                        connection.execute(
                            """INSERT INTO memory_facts (key, value, created_at, updated_at)
                            VALUES (?, ?, ?, ?)
                            ON CONFLICT(key) DO UPDATE SET value=excluded.value,
                            updated_at=excluded.updated_at""",
                            (fact_key, fact_value, applied_at, applied_at),
                        )
                        connection.execute(
                            """INSERT INTO migration_fact_applications (
                                fact_key, value_sha256, migration_application_id, applied_at
                            ) VALUES (?, ?, ?, ?)""",
                            (
                                fact_key,
                                hashlib.sha256(fact_value.encode()).hexdigest(),
                                application_id,
                                applied_at,
                            ),
                        )
