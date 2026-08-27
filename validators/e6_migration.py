"""Deterministic disposition map for legacy E6 YAML assets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class LegacyDisposition(_StrictModel):
    legacy_path: str = Field(min_length=1)
    legacy_id: str | None = None
    legacy_type: str | None = None
    disposition: Literal["await-domain-evidence", "support-contract-not-node"]
    canonical_id: None = None
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class E6MigrationMap(_StrictModel):
    schema_version: Literal[1]
    legacy_root: Literal["conocimiento"]
    entries: list[LegacyDisposition]

    @model_validator(mode="after")
    def validate_entries(self) -> E6MigrationMap:
        paths = [entry.legacy_path for entry in self.entries]
        if paths != sorted(paths) or len(paths) != len(set(paths)):
            raise ValueError("migration paths must be unique and sorted")
        if any(
            entry.disposition == "await-domain-evidence" and not entry.legacy_id
            for entry in self.entries
        ):
            raise ValueError("migrable legacy node requires ID")
        return self


def _entry(path: Path, root: Path) -> LegacyDisposition:
    raw = path.read_bytes()
    data = yaml.safe_load(raw)
    relative = path.relative_to(root.parent).as_posix()
    if (
        isinstance(data, dict)
        and data.get("type")
        in {"decision", "concept", "tool", "worksheet", "metric", "stage"}
        and isinstance(data.get("id"), str)
    ):
        disposition = "await-domain-evidence"
        legacy_id = data["id"]
        legacy_type = data["type"]
    else:
        disposition = "support-contract-not-node"
        legacy_id = None
        legacy_type = None
    return LegacyDisposition(
        legacy_path=relative,
        legacy_id=legacy_id,
        legacy_type=legacy_type,
        disposition=disposition,
        sha256=hashlib.sha256(raw).hexdigest(),
    )


def build_e6_migration_map(repository: Path) -> E6MigrationMap:
    legacy_root = repository.resolve() / "conocimiento"
    entries = [
        _entry(path, legacy_root) for path in sorted(legacy_root.rglob("*.yaml"))
    ]
    return E6MigrationMap(schema_version=1, legacy_root="conocimiento", entries=entries)


def render_e6_migration_map(migration_map: E6MigrationMap) -> str:
    return (
        json.dumps(
            migration_map.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def load_and_validate_e6_migration_map(repository: Path, path: Path) -> E6MigrationMap:
    try:
        checked = E6MigrationMap.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("migration map contract invalid") from exc
    expected = build_e6_migration_map(repository)
    if checked != expected:
        raise ValueError("migration map does not match legacy inventory")
    return checked
