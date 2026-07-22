"""Filesystem-only inbox ledger contracts for the local Escala runtime."""

from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .authority import WorkspaceConfig, validate_workspace
from .ingestion import SourceIngestionError, build_source_identity, profile_source


InboxDisposition = Literal[
    "accepted", "duplicate", "needs_clarification", "quarantined"
]


class _StrictModel(BaseModel):
    """Closed immutable contract for local inbox metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class InboxError(ValueError):
    """Safe inbox failure with a stable code and no machine path."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class InboxConfig(_StrictModel):
    """Scanner configuration; only the workspace machine owns the ledger."""

    workspace: WorkspaceConfig
    max_bytes: int = Field(default=10 * 1024 * 1024, gt=0, le=100 * 1024 * 1024)


class InboxLedgerEntry(_StrictModel):
    """First disposition for one source identity, with relative provenance."""

    source_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    relative_path: str = Field(min_length=1, max_length=512)
    disposition: InboxDisposition
    codes: tuple[str, ...] = ()

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        """Reject machine paths, traversal and NULs at the ledger boundary."""

        if "\x00" in value or Path(value).is_absolute():
            raise ValueError("relative path required")
        normalized = value.replace("\\", "/")
        if normalized == ".." or normalized.startswith("../"):
            raise ValueError("relative path required")
        return normalized


class InboxLedger(_StrictModel):
    """Sorted, versioned local source disposition ledger."""

    schema_version: Literal[1] = 1
    entries: tuple[InboxLedgerEntry, ...] = ()

    @property
    def source_ids(self) -> tuple[str, ...]:
        """Return source IDs in deterministic ledger order."""

        return tuple(entry.source_id for entry in self.entries)

    def by_source_id(self) -> dict[str, InboxLedgerEntry]:
        """Index entries without exposing a mutable internal model."""

        return {entry.source_id: entry for entry in self.entries}


class InboxItemResult(_StrictModel):
    """Safe disposition for one direct exchange entry."""

    relative_path: str = Field(min_length=1, max_length=512)
    disposition: InboxDisposition
    code: str = Field(min_length=1, max_length=100)
    source_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        """Reject absolute and traversal paths from a run result."""

        if "\x00" in value or Path(value).is_absolute():
            raise ValueError("relative path required")
        normalized = value.replace("\\", "/")
        if normalized == ".." or normalized.startswith("../"):
            raise ValueError("relative path required")
        return normalized


class InboxRunResult(_StrictModel):
    """Deterministic scan result; report writing is layered later."""

    run_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    items: tuple[InboxItemResult, ...] = ()
    ledger: InboxLedger = Field(default_factory=InboxLedger)
    ledger_changed: bool = False


def _ledger_path(config: InboxConfig | WorkspaceConfig) -> Path:
    """Return the installer-local ledger path, never an exchange path."""

    workspace = config.workspace if isinstance(config, InboxConfig) else config
    return workspace.data_root.expanduser().resolve(strict=False) / (
        ".escala-inbox-ledger.json"
    )


def load_inbox_ledger(config: InboxConfig | WorkspaceConfig) -> InboxLedger:
    """Load the local ledger, failing closed on corrupt or unsafe JSON."""

    workspace = config.workspace if isinstance(config, InboxConfig) else config
    if validate_workspace(workspace).status != "pass":
        raise InboxError("workspace_invalid")
    path = _ledger_path(config)
    if not path.exists():
        return InboxLedger()
    try:
        return InboxLedger.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise InboxError("ledger_corrupt") from None


def save_inbox_ledger(
    config: InboxConfig | WorkspaceConfig,
    ledger: InboxLedger,
) -> None:
    """Atomically save a sorted ledger under installer-local data_root."""

    workspace = config.workspace if isinstance(config, InboxConfig) else config
    if validate_workspace(workspace).status != "pass":
        raise InboxError("workspace_invalid")
    path = _ledger_path(config)
    entries = tuple(sorted(ledger.entries, key=lambda entry: entry.source_id))
    normalized = ledger.model_copy(update={"entries": entries})
    payload = json.dumps(
        normalized.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    try:
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, path)
    except OSError:
        raise InboxError("ledger_write_failed") from None


def scan_inbox(config: InboxConfig) -> InboxRunResult:
    """Enumerate direct exchange entries without following or moving them."""

    if validate_workspace(config.workspace).status != "pass":
        raise InboxError("workspace_invalid")
    exchange = config.workspace.exchange_root.expanduser().resolve(strict=False)
    if not exchange.exists() or not exchange.is_dir():
        raise InboxError("exchange_missing")
    ledger = load_inbox_ledger(config)
    items: list[InboxItemResult] = []
    try:
        entries = sorted(exchange.iterdir(), key=lambda path: path.name.casefold())
    except OSError:
        raise InboxError("exchange_unreadable") from None

    ledger_entries = list(ledger.entries)
    seen = ledger.by_source_id()
    ledger_changed = False
    for path in entries:
        relative = path.relative_to(exchange).as_posix()
        if path.is_symlink():
            items.append(
                InboxItemResult(
                    relative_path=relative,
                    disposition="quarantined",
                    code="entry_symlink",
                )
            )
            continue
        if path.is_dir():
            items.append(
                InboxItemResult(
                    relative_path=relative,
                    disposition="quarantined",
                    code="entry_directory",
                )
            )
            continue
        try:
            if not path.is_file():
                code = "entry_not_file"
            elif path.stat().st_size > config.max_bytes:
                code = "source_too_large"
            else:
                code = ""
        except OSError:
            code = "entry_unreadable"
        if code:
            items.append(
                InboxItemResult(
                    relative_path=relative,
                    disposition="quarantined",
                    code=code,
                )
            )
            continue

        try:
            identity = build_source_identity(path, exchange)
        except SourceIngestionError as exc:
            items.append(
                InboxItemResult(
                    relative_path=relative,
                    disposition="quarantined",
                    code=exc.code,
                )
            )
            continue
        if identity.source_id in seen:
            items.append(
                InboxItemResult(
                    relative_path=relative,
                    disposition="duplicate",
                    code="source_seen",
                    source_id=identity.source_id,
                )
            )
            continue

        result = profile_source(config.workspace, path)
        if result.status == "ready":
            disposition: InboxDisposition = "accepted"
            result_code = "profile_ready"
        elif result.status == "needs_clarification":
            disposition = "needs_clarification"
            result_code = "material_ambiguity"
        else:
            disposition = "quarantined"
            result_code = result.findings[0] if result.findings else result.status
        item = InboxItemResult(
            relative_path=relative,
            disposition=disposition,
            code=result_code,
            source_id=identity.source_id,
        )
        items.append(item)
        entry = InboxLedgerEntry(
            source_id=identity.source_id,
            relative_path=relative,
            disposition=disposition,
            codes=tuple(sorted({result_code, *result.findings})),
        )
        ledger_entries.append(entry)
        seen[identity.source_id] = entry
        ledger_changed = True

    safe_items = tuple(items)
    if ledger_changed:
        updated_ledger = InboxLedger(entries=tuple(ledger_entries))
        save_inbox_ledger(config, updated_ledger)
    else:
        updated_ledger = ledger
    run_id = hashlib.sha256(
        json.dumps(
            [item.model_dump(mode="json") for item in safe_items],
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return InboxRunResult(
        run_id=run_id,
        items=safe_items,
        ledger=updated_ledger,
        ledger_changed=ledger_changed,
    )
