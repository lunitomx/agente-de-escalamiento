"""Portable, shared business-workspace contract for ScaleUp.

The workspace is a normal folder users may sync with their preferred provider.
Only human-readable documents belong there.  SQLite state is deliberately kept
outside it by :mod:`escala_server.project_memory`.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import yaml


MANIFEST_NAME = "scaleup-workspace.yaml"
WORKSPACE_SCHEMA = 1
AREAS = frozenset(("cash", "people", "strategy", "execution"))
CANONICAL_DIRECTORIES = (
    "company",
    "areas/cash",
    "areas/people",
    "areas/strategy",
    "areas/execution",
    "plans",
    "cadence",
    "decisions",
    "contributions",
)


class WorkspaceValidationError(ValueError):
    """Raised when a shared workspace would be unsafe or ambiguous."""


@dataclass(frozen=True)
class WorkspaceManifest:
    """The deliberately small, portable identity of a shared workspace."""

    workspace_id: str
    name: str
    schema_version: int = WORKSPACE_SCHEMA


@dataclass(frozen=True)
class WorkspaceResult:
    """Safe result for create/open/doctor operations."""

    ready: bool
    root: Path
    manifest: WorkspaceManifest | None = None
    reason: str | None = None


def create_workspace(
    root: str | Path, name: str, *, workspace_id: str | None = None
) -> WorkspaceResult:
    """Create an empty portable workspace without configuring a sync provider."""
    workspace_root = Path(root).expanduser().resolve()
    try:
        manifest = WorkspaceManifest(
            workspace_id=_validate_workspace_id(workspace_id or str(uuid4())),
            name=_validate_name(name),
        )
        manifest_path = workspace_root / MANIFEST_NAME
        if manifest_path.exists():
            existing = load_workspace(workspace_root)
            return WorkspaceResult(
                False,
                workspace_root,
                existing.manifest,
                "workspace already exists; open it instead of overwriting it",
            )
        workspace_root.mkdir(parents=True, exist_ok=True)
        _assert_contained(manifest_path, workspace_root)
        for relative in CANONICAL_DIRECTORIES:
            directory = workspace_root / relative
            _assert_contained(directory, workspace_root)
            directory.mkdir(parents=True, exist_ok=True)
        _write_yaml_atomically(
            manifest_path,
            {
                "schema_version": manifest.schema_version,
                "workspace_id": manifest.workspace_id,
                "name": manifest.name,
            },
        )
        return WorkspaceResult(True, workspace_root, manifest)
    except (OSError, WorkspaceValidationError, yaml.YAMLError) as error:
        return WorkspaceResult(False, workspace_root, reason=str(error))


def load_workspace(root: str | Path) -> WorkspaceResult:
    """Load and strictly validate a workspace manifest without writing anything."""
    workspace_root = Path(root).expanduser().resolve()
    manifest_path = workspace_root / MANIFEST_NAME
    try:
        _assert_contained(manifest_path, workspace_root)
        if not manifest_path.is_file():
            raise WorkspaceValidationError("scaleup-workspace.yaml was not found")
        payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise WorkspaceValidationError("workspace manifest must be a YAML mapping")
        allowed = {"schema_version", "workspace_id", "name"}
        unknown = set(payload) - allowed
        if unknown:
            raise WorkspaceValidationError(
                "workspace manifest has unsupported fields: " + ", ".join(sorted(unknown))
            )
        if set(payload) != allowed:
            raise WorkspaceValidationError("workspace manifest is missing required fields")
        schema_version = payload["schema_version"]
        if schema_version != WORKSPACE_SCHEMA:
            raise WorkspaceValidationError("unsupported workspace schema version")
        manifest = WorkspaceManifest(
            workspace_id=_validate_workspace_id(payload["workspace_id"]),
            name=_validate_name(payload["name"]),
            schema_version=schema_version,
        )
        return WorkspaceResult(True, workspace_root, manifest)
    except (
        OSError,
        TypeError,
        WorkspaceValidationError,
        yaml.YAMLError,
    ) as error:
        return WorkspaceResult(False, workspace_root, reason=str(error))


def workspace_local_root(
    workspace: WorkspaceManifest, local_state_root: str | Path
) -> Path:
    """Return the per-machine state directory and reject a shared location."""
    state_root = Path(local_state_root).expanduser().resolve()
    local_root = state_root / workspace.workspace_id
    return local_root


def path_is_inside(path: Path, root: Path) -> bool:
    """Return containment without leaking a ValueError to product code."""
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _validate_workspace_id(value: Any) -> str:
    if not isinstance(value, str):
        raise WorkspaceValidationError("workspace_id must be text")
    try:
        return str(UUID(value))
    except (TypeError, ValueError) as error:
        raise WorkspaceValidationError("workspace_id must be a UUID") from error


def _validate_name(value: Any) -> str:
    if not isinstance(value, str):
        raise WorkspaceValidationError("workspace name must be text")
    name = value.strip()
    if not 1 <= len(name) <= 120:
        raise WorkspaceValidationError("workspace name must contain 1 to 120 characters")
    if any(character in name for character in ("\n", "\r", "\x00")):
        raise WorkspaceValidationError("workspace name contains unsafe characters")
    return name


def _write_yaml_atomically(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    _assert_contained(temporary, path.parent)
    try:
        temporary.write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=True), encoding="utf-8"
        )
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _assert_contained(path: Path, root: Path) -> None:
    path.resolve().relative_to(root.resolve())


_DOCUMENT_SUFFIXES = frozenset((".yaml", ".yml", ".md"))
_SECRET_NAME = re.compile(r"(?:api[_-]?key|password|secret|token|private[_-]?key)", re.I)
_SECRET_VALUE = re.compile(r"(?:api[_-]?key|password|secret|token)\s*[:=]", re.I)
_CONFLICT_COPY = re.compile(r"(?:conflict|conflicted copy|copia en conflicto)", re.I)
_ALLOWED_CANONICAL_ROOTS = frozenset(
    ("company", "areas", "plans", "cadence", "decisions", "contributions")
)


@dataclass(frozen=True)
class ContributionResult:
    """Result of an append-only business contribution."""

    ready: bool
    path: Path | None = None
    contribution_id: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class WorkspaceIndexResult:
    """Outcome of a local index/rebuild of a portable workspace."""

    ready: bool
    db_path: Path
    digest: str = ""
    indexed: tuple[str, ...] = ()
    changed: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    errors: dict[str, str] = field(default_factory=dict)
    reason: str | None = None


@dataclass(frozen=True)
class WorkspaceDoctorResult:
    """Non-technical health view of portable and local workspace state."""

    ready: bool
    state: str
    message: str
    db_path: Path | None = None
    shared_database_artifacts: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()


@dataclass(frozen=True)
class _DocumentSnapshot:
    relative_path: str
    content_sha256: str
    document_kind: str
    lifecycle: str
    owner: str | None
    base_sha256: str | None
    payload: dict[str, Any]
    confirmed: bool


def create_contribution(
    root: str | Path,
    *,
    area: str,
    author: str,
    role: str,
    source: str,
    content: Any,
    status: str = "proposed",
    target: str | None = None,
    base_sha256: str | None = None,
    contribution_id: str | None = None,
) -> ContributionResult:
    """Append a contribution without ever replacing a canonical document.

    A contribution remains a normal YAML file so a person can inspect, share,
    or recover it with standard tools. Sensitive values are deliberately
    rejected before the shared file is written.
    """
    workspace = load_workspace(root)
    if not workspace.ready or workspace.manifest is None:
        return ContributionResult(False, reason=workspace.reason)
    try:
        normalized_area = _validate_area(area)
        normalized_author = _validate_short_text(author, "author")
        normalized_role = _validate_short_text(role, "role")
        normalized_source = _validate_short_text(source, "source")
        if status not in {"proposed", "confirmed"}:
            raise WorkspaceValidationError("contribution status must be proposed or confirmed")
        normalized_target = _validate_target(target, workspace.root)
        normalized_base = _validate_digest(base_sha256, "base_sha256")
        if normalized_target is None and normalized_base is not None:
            raise WorkspaceValidationError("base_sha256 requires a canonical target")
        identifier = _validate_workspace_id(contribution_id or str(uuid4()))
        payload = {
            "schema_version": WORKSPACE_SCHEMA,
            "id": identifier,
            "area": normalized_area,
            "author": normalized_author,
            "role": normalized_role,
            "source": normalized_source,
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "status": status,
            "target": normalized_target,
            "base_sha256": normalized_base,
            "content": content,
        }
        _assert_no_sensitive_data(payload)
        target_path = workspace.root / "contributions" / normalized_area / f"{identifier}.yaml"
        _assert_contained(target_path, workspace.root)
        if target_path.exists():
            raise WorkspaceValidationError("contribution id already exists; contributions are append-only")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        _write_yaml_atomically(target_path, payload)
        return ContributionResult(True, target_path, identifier)
    except (OSError, TypeError, WorkspaceValidationError, yaml.YAMLError) as error:
        return ContributionResult(False, reason=str(error))


@dataclass(frozen=True)
class ReconciliationResult:
    """Outcome of an explicit, auditable canonical-document reconciliation."""

    ready: bool
    target_path: Path | None = None
    record_path: Path | None = None
    reason: str | None = None


def reconcile_canonical_document(
    root: str | Path,
    *,
    target: str,
    owner: str,
    content: dict[str, Any],
    resolved_contribution_ids: tuple[str, ...] = (),
    confirm: bool = False,
) -> ReconciliationResult:
    """Create a confirmed revision only after an explicit human confirmation.

    The previous canonical payload and the resolved contribution IDs are first
    preserved in an append-only decision record. This function never runs as a
    side effect of indexing or sync; callers must pass ``confirm=True``.
    """
    workspace = load_workspace(root)
    if not workspace.ready:
        return ReconciliationResult(False, reason=workspace.reason)
    try:
        if not confirm:
            raise WorkspaceValidationError("explicit confirmation is required to reconcile a canonical document")
        assert workspace.manifest is not None
        relative_target = _validate_target(target, workspace.root)
        assert relative_target is not None
        if not relative_target.endswith((".yaml", ".yml")):
            raise WorkspaceValidationError("reconciliation currently requires a YAML canonical document")
        target_path = workspace.root / relative_target
        _assert_contained(target_path, workspace.root)
        previous = _read_document_payload(target_path) if target_path.is_file() else {}
        if previous:
            existing_owner = previous.get("owner")
            if isinstance(existing_owner, str) and existing_owner.strip() != owner.strip():
                raise WorkspaceValidationError("only the declared owner can confirm this canonical revision")
        normalized_owner = _validate_short_text(owner, "owner")
        if not isinstance(content, dict):
            raise WorkspaceValidationError("canonical content must be a mapping")
        if {"owner", "status", "schema_version", "resolved_contribution_ids"} & set(content):
            raise WorkspaceValidationError("canonical content cannot replace protected reconciliation fields")
        resolved = tuple(_validate_workspace_id(item) for item in resolved_contribution_ids)
        if len(set(resolved)) != len(resolved):
            raise WorkspaceValidationError("resolved contribution IDs must be unique")
        revision_id = str(uuid4())
        previous_sha = _sha256_file(target_path) if target_path.is_file() else None
        record_path = workspace.root / "decisions" / "reconciliations" / f"{revision_id}.yaml"
        _assert_contained(record_path, workspace.root)
        revision = {
            "schema_version": WORKSPACE_SCHEMA,
            "owner": normalized_owner,
            "status": "confirmed",
            "revision_id": revision_id,
            "target": relative_target,
            "previous_sha256": previous_sha,
            "resolved_contribution_ids": list(resolved),
            "previous": previous,
            "replacement": content,
        }
        canonical = {
            "schema_version": WORKSPACE_SCHEMA,
            "owner": normalized_owner,
            "status": "confirmed",
            "revision_id": revision_id,
            "based_on_reconciliation": record_path.relative_to(workspace.root).as_posix(),
            **content,
        }
        _assert_no_sensitive_data(revision)
        _assert_no_sensitive_data(canonical)
        record_path.parent.mkdir(parents=True, exist_ok=True)
        _write_yaml_atomically(record_path, revision)
        _write_yaml_atomically(target_path, canonical)
        return ReconciliationResult(True, target_path, record_path)
    except (OSError, TypeError, WorkspaceValidationError, yaml.YAMLError) as error:
        return ReconciliationResult(False, reason=str(error))


class WorkspaceIndexer:
    """Build a disposable local index from the shared, human-readable files."""

    def __init__(
        self, root: str | Path, *, local_state_root: str | Path | None = None
    ) -> None:
        self.workspace_result = load_workspace(root)
        self.workspace_root = self.workspace_result.root
        self.local_state_root = local_state_root
        self.runtime = None
        if self.workspace_result.ready:
            # Local import prevents the contract module from circularly importing
            # the runtime that itself needs manifest validation.
            from .project_memory import ProjectMemoryRuntime

            self.runtime = ProjectMemoryRuntime(
                self.workspace_root, local_state_root=local_state_root
            )

    def rebuild(self) -> WorkspaceIndexResult:
        """Reconcile local SQLite with the current shared folder, idempotently."""
        if not self.workspace_result.ready or self.workspace_result.manifest is None:
            return WorkspaceIndexResult(
                False,
                Path(),
                reason=self.workspace_result.reason or "workspace is unavailable",
            )
        assert self.runtime is not None
        memory = self.runtime.ensure_memory()
        if not memory.ready:
            return WorkspaceIndexResult(False, memory.db_path, reason=memory.reason)
        snapshots, errors, conflicts = self._discover()
        indexed: list[str] = []
        changed: list[str] = []
        removed: list[str] = []
        workspace_id = self.workspace_result.manifest.workspace_id
        try:
            with sqlite3.connect(memory.db_path) as connection:
                connection.execute("BEGIN")
                prior = {
                    row[0]: (row[1], row[2])
                    for row in connection.execute(
                        "SELECT relative_path, content_sha256, lifecycle "
                        "FROM workspace_documents WHERE workspace_id = ?",
                        (workspace_id,),
                    )
                }
                present = {item.relative_path for item in snapshots}
                for snapshot in snapshots:
                    previous = prior.get(snapshot.relative_path)
                    if previous is None:
                        indexed.append(snapshot.relative_path)
                    elif previous != (snapshot.content_sha256, snapshot.lifecycle):
                        changed.append(snapshot.relative_path)
                    connection.execute(
                        """INSERT INTO workspace_documents (
                            workspace_id, relative_path, content_sha256, document_kind,
                            lifecycle, owner, base_sha256, content_json, removed_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
                        ON CONFLICT(workspace_id, relative_path) DO UPDATE SET
                            content_sha256=excluded.content_sha256,
                            document_kind=excluded.document_kind,
                            lifecycle=excluded.lifecycle,
                            owner=excluded.owner,
                            base_sha256=excluded.base_sha256,
                            content_json=excluded.content_json,
                            indexed_at=datetime('now'),
                            removed_at=NULL""",
                        (
                            workspace_id,
                            snapshot.relative_path,
                            snapshot.content_sha256,
                            snapshot.document_kind,
                            snapshot.lifecycle,
                            snapshot.owner,
                            snapshot.base_sha256,
                            _canonical_json(snapshot.payload),
                        ),
                    )
                    self._replace_facts(connection, workspace_id, snapshot)
                for relative_path, (_, lifecycle) in prior.items():
                    if relative_path in present or lifecycle == "removed":
                        continue
                    removed.append(relative_path)
                    connection.execute(
                        """UPDATE workspace_documents
                        SET lifecycle='removed', removed_at=datetime('now'), indexed_at=datetime('now')
                        WHERE workspace_id=? AND relative_path=?""",
                        (workspace_id, relative_path),
                    )
                    self._delete_facts(connection, workspace_id, relative_path)
                connection.commit()
        except (sqlite3.Error, ValueError, TypeError) as error:
            return WorkspaceIndexResult(False, memory.db_path, reason=str(error))
        digest = self._digest(snapshots)
        return WorkspaceIndexResult(
            True,
            memory.db_path,
            digest=digest,
            indexed=tuple(sorted(indexed)),
            changed=tuple(sorted(changed)),
            removed=tuple(sorted(removed)),
            conflicts=tuple(sorted(conflicts)),
            errors=dict(sorted(errors.items())),
        )

    def doctor(self) -> WorkspaceDoctorResult:
        """Explain what a non-technical user can do next without writing files."""
        if not self.workspace_result.ready:
            return WorkspaceDoctorResult(
                False,
                "blocked",
                "No pude abrir la carpeta compartida: "
                + (self.workspace_result.reason or "manifest inválido"),
            )
        artifacts = tuple(sorted(self._shared_database_artifacts()))
        if artifacts:
            return WorkspaceDoctorResult(
                False,
                "blocked",
                "Hay una base SQLite dentro de la carpeta compartida. Muévela fuera y vuelve a abrir ScaleUp.",
                shared_database_artifacts=artifacts,
            )
        assert self.runtime is not None
        health = self.runtime.health()
        if not health.ready:
            return WorkspaceDoctorResult(
                True,
                "attention",
                "La carpeta está lista. Este equipo aún necesita reconstruir su memoria local.",
                db_path=health.db_path,
            )
        result = self.rebuild()
        if not result.ready:
            return WorkspaceDoctorResult(
                False,
                "attention",
                "La carpeta está lista, pero no pude actualizar la memoria local: "
                + (result.reason or "error desconocido"),
                db_path=health.db_path,
            )
        if result.conflicts:
            return WorkspaceDoctorResult(
                True,
                "attention",
                "Encontré cambios que necesitan conciliación; conservé todas las versiones.",
                db_path=result.db_path,
                conflicts=result.conflicts,
            )
        return WorkspaceDoctorResult(
            True,
            "ready",
            "La carpeta compartida y la memoria local de este equipo están listas.",
            db_path=result.db_path,
        )

    def _discover(self) -> tuple[list[_DocumentSnapshot], dict[str, str], set[str]]:
        snapshots: list[_DocumentSnapshot] = []
        errors: dict[str, str] = {}
        for path in sorted(self.workspace_root.rglob("*")):
            if not path.is_file() or path.name == MANIFEST_NAME or path.suffix.lower() not in _DOCUMENT_SUFFIXES:
                continue
            try:
                relative = path.resolve().relative_to(self.workspace_root.resolve()).as_posix()
                if relative.split("/", 1)[0] not in _ALLOWED_CANONICAL_ROOTS:
                    continue
                snapshots.append(self._read_document(path, relative))
            except (OSError, TypeError, WorkspaceValidationError, yaml.YAMLError) as error:
                relative = _safe_relative_for_error(path, self.workspace_root)
                errors[relative] = str(error)
                snapshots.append(
                    _DocumentSnapshot(
                        relative,
                        _sha256_file(path),
                        "unknown",
                        "invalid",
                        None,
                        None,
                        {},
                        False,
                    )
                )

        canonical_hashes = {
            item.relative_path: item.content_sha256
            for item in snapshots
            if item.document_kind == "canonical" and item.lifecycle == "active"
        }
        resolved_ids: set[str] = set()
        for item in snapshots:
            if not (
                item.document_kind == "canonical"
                and item.relative_path.startswith("decisions/reconciliations/")
            ):
                continue
            value = item.payload.get("resolved_contribution_ids", [])
            if isinstance(value, list) and all(isinstance(entry, str) for entry in value):
                resolved_ids.update(value)

        conflicts: set[str] = set()
        seen_contribution_ids: dict[str, str] = {}
        for item in snapshots:
            if item.lifecycle == "conflict":
                conflicts.add(item.relative_path)
            if item.document_kind != "contribution":
                continue
            contribution_id = str(item.payload.get("id", ""))
            previous = seen_contribution_ids.get(contribution_id)
            if previous is not None:
                conflicts.update((previous, item.relative_path))
            else:
                seen_contribution_ids[contribution_id] = item.relative_path
            target = item.payload.get("target")
            if (
                contribution_id not in resolved_ids
                and isinstance(target, str)
                and item.base_sha256 is not None
                and canonical_hashes.get(target) != item.base_sha256
            ):
                conflicts.add(item.relative_path)

        if conflicts:
            snapshots = [
                _DocumentSnapshot(
                    item.relative_path,
                    item.content_sha256,
                    item.document_kind,
                    "conflict" if item.relative_path in conflicts else item.lifecycle,
                    item.owner,
                    item.base_sha256,
                    item.payload,
                    False if item.relative_path in conflicts else item.confirmed,
                )
                for item in snapshots
            ]
        return snapshots, errors, conflicts

    def _read_document(self, path: Path, relative: str) -> _DocumentSnapshot:
        payload = _read_document_payload(path)
        _assert_no_sensitive_data(payload)
        digest = _sha256_file(path)
        if _CONFLICT_COPY.search(path.name):
            return _DocumentSnapshot(relative, digest, "unknown", "conflict", None, None, payload, False)
        if relative.startswith("contributions/"):
            return _contribution_snapshot(relative, digest, payload)
        return _canonical_snapshot(relative, digest, payload)

    def _replace_facts(
        self, connection: sqlite3.Connection, workspace_id: str, snapshot: _DocumentSnapshot
    ) -> None:
        self._delete_facts(connection, workspace_id, snapshot.relative_path)
        if snapshot.lifecycle != "active" or not snapshot.confirmed:
            return
        prefix = _fact_prefix(workspace_id, snapshot.relative_path)
        for key, value in _flatten_payload(snapshot.payload):
            connection.execute(
                """INSERT INTO workspace_facts (workspace_id, relative_path, fact_key, value, confirmed)
                VALUES (?, ?, ?, ?, 1)""",
                (workspace_id, snapshot.relative_path, key, value),
            )
            connection.execute(
                """INSERT INTO memory_facts (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')""",
                (prefix + key, value),
            )

    def _delete_facts(self, connection: sqlite3.Connection, workspace_id: str, relative_path: str) -> None:
        connection.execute(
            "DELETE FROM workspace_facts WHERE workspace_id=? AND relative_path=?",
            (workspace_id, relative_path),
        )
        connection.execute(
            "DELETE FROM memory_facts WHERE key LIKE ? ESCAPE '\\'",
            (_like_prefix(_fact_prefix(workspace_id, relative_path)),),
        )

    @staticmethod
    def _digest(snapshots: list[_DocumentSnapshot]) -> str:
        entries = [
            f"{item.relative_path}\x00{item.content_sha256}"
            for item in snapshots
            if item.lifecycle == "active" and item.confirmed
        ]
        return hashlib.sha256("\n".join(sorted(entries)).encode("utf-8")).hexdigest()

    def _shared_database_artifacts(self) -> list[str]:
        artifacts: list[str] = []
        for path in self.workspace_root.rglob("*"):
            if not path.is_file():
                continue
            name = path.name.lower()
            if name.endswith((".db", ".db-wal", ".db-shm", ".sqlite", ".sqlite-wal", ".sqlite-shm")):
                artifacts.append(path.relative_to(self.workspace_root).as_posix())
        return artifacts


def _canonical_snapshot(relative: str, digest: str, payload: dict[str, Any]) -> _DocumentSnapshot:
    if not isinstance(payload, dict):
        raise WorkspaceValidationError("canonical document must be a YAML mapping or Markdown frontmatter")
    owner = payload.get("owner")
    status = payload.get("status")
    if not isinstance(owner, str) or not owner.strip():
        raise WorkspaceValidationError("canonical document needs a responsible owner")
    if status != "confirmed":
        raise WorkspaceValidationError("canonical document must be explicitly confirmed")
    return _DocumentSnapshot(
        relative,
        digest,
        "canonical",
        "active",
        owner.strip(),
        _validate_digest(payload.get("base_sha256"), "base_sha256"),
        payload,
        True,
    )


def _contribution_snapshot(relative: str, digest: str, payload: dict[str, Any]) -> _DocumentSnapshot:
    if not isinstance(payload, dict):
        raise WorkspaceValidationError("contribution must be a YAML mapping")
    required = {"schema_version", "id", "area", "author", "role", "source", "created_at", "status", "content"}
    missing = required - set(payload)
    if missing:
        raise WorkspaceValidationError("contribution is missing: " + ", ".join(sorted(missing)))
    if payload["schema_version"] != WORKSPACE_SCHEMA:
        raise WorkspaceValidationError("unsupported contribution schema version")
    _validate_workspace_id(payload["id"])
    _validate_area(payload["area"])
    _validate_short_text(payload["author"], "author")
    _validate_short_text(payload["role"], "role")
    _validate_short_text(payload["source"], "source")
    if payload["status"] not in {"proposed", "confirmed"}:
        raise WorkspaceValidationError("contribution status must be proposed or confirmed")
    target = payload.get("target")
    base = _validate_digest(payload.get("base_sha256"), "base_sha256")
    if target is None and base is not None:
        raise WorkspaceValidationError("base_sha256 requires a canonical target")
    return _DocumentSnapshot(
        relative,
        digest,
        "contribution",
        "active",
        None,
        base,
        payload,
        payload["status"] == "confirmed",
    )


def _read_document_payload(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        payload = yaml.safe_load(raw)
        if not isinstance(payload, dict):
            raise WorkspaceValidationError("YAML document must be a mapping")
        return payload
    frontmatter, content = _markdown_frontmatter(raw)
    if not frontmatter:
        raise WorkspaceValidationError("Markdown document needs YAML frontmatter")
    return {**frontmatter, "body": content.strip()}


def _markdown_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    if not raw.startswith("---\n"):
        return {}, raw
    delimiter = raw.find("\n---\n", 4)
    if delimiter < 0:
        raise WorkspaceValidationError("Markdown frontmatter is not closed")
    metadata = yaml.safe_load(raw[4:delimiter])
    if not isinstance(metadata, dict):
        raise WorkspaceValidationError("Markdown frontmatter must be a mapping")
    return metadata, raw[delimiter + 5 :]


def _validate_area(value: Any) -> str:
    if not isinstance(value, str) or value not in AREAS:
        raise WorkspaceValidationError("area must be cash, people, strategy or execution")
    return value


def _validate_short_text(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise WorkspaceValidationError(f"{label} must be text")
    cleaned = value.strip()
    if not 1 <= len(cleaned) <= 160 or any(char in cleaned for char in ("\n", "\r", "\x00")):
        raise WorkspaceValidationError(f"{label} is invalid")
    return cleaned


def _validate_target(value: str | None, root: Path) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise WorkspaceValidationError("target must be a relative canonical document path")
    candidate = (root / value).resolve()
    if not path_is_inside(candidate, root):
        raise WorkspaceValidationError("target must stay inside the workspace")
    relative = candidate.relative_to(root.resolve()).as_posix()
    if relative.split("/", 1)[0] not in _ALLOWED_CANONICAL_ROOTS - {"contributions"}:
        raise WorkspaceValidationError("target must be a canonical document")
    return relative


def _validate_digest(value: Any, label: str) -> str | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise WorkspaceValidationError(f"{label} must be a SHA-256 digest")
    return value


def _assert_no_sensitive_data(value: Any, path: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            if _SECRET_NAME.search(key_text):
                raise WorkspaceValidationError("sensitive data must stay local and is not indexed")
            _assert_no_sensitive_data(child, f"{path}.{key_text}" if path else key_text)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_sensitive_data(child, f"{path}[{index}]")
    elif isinstance(value, str) and _SECRET_VALUE.search(value):
        raise WorkspaceValidationError("sensitive data must stay local and is not indexed")


def _flatten_payload(value: Any, prefix: str = "") -> list[tuple[str, str]]:
    ignored = {"schema_version", "id", "author", "role", "source", "created_at", "status", "target", "base_sha256", "owner"}
    if isinstance(value, dict):
        values: list[tuple[str, str]] = []
        for key in sorted(value):
            if key in ignored:
                continue
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            values.extend(_flatten_payload(value[key], child_prefix))
        return values
    if isinstance(value, list):
        return [(prefix, _canonical_json(value))] if prefix else []
    if value is None or not prefix:
        return []
    return [(prefix, _canonical_json(value))]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _fact_prefix(workspace_id: str, relative_path: str) -> str:
    return f"workspace.{workspace_id}.{relative_path}:"


def _like_prefix(prefix: str) -> str:
    return prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_relative_for_error(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)
