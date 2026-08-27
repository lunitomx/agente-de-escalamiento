"""Strict inventory for canonical, legacy, and story-level epic scopes."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
import yaml

from validators.governance_contract import ClosureDispositionPolicy

_EPIC_ID = re.compile(r"^E[1-9][0-9]*$")
_SAFE_PATH = re.compile(
    r"^work/epics/e[1-9][0-9]*-[a-z0-9-]+(?:/stories/[a-z0-9.-]+)?/scope\.md$"
)


class ScopeInventoryError(ValueError):
    """Raised when a scope is not classified by the governance inventory."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class LegacyScopeEntry(_StrictModel):
    path: str = Field(min_length=1, max_length=512)
    kind: Literal["archived_epic", "story_scope"]
    legacy_id: str
    disposition: str = Field(min_length=3, max_length=128)
    evidence: str = Field(min_length=3, max_length=128)

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        if _SAFE_PATH.fullmatch(value) is None:
            raise ValueError("scope inventory path is unsafe")
        if ".." in PurePosixPath(value).parts:
            raise ValueError("scope inventory path traverses a parent")
        return value

    @field_validator("legacy_id")
    @classmethod
    def validate_legacy_id(cls, value: str) -> str:
        if _EPIC_ID.fullmatch(value) is None:
            raise ValueError("legacy scope requires an epic ID")
        return value

    @model_validator(mode="after")
    def validate_kind_shape(self) -> "LegacyScopeEntry":
        nested = "/stories/" in self.path
        if (self.kind == "story_scope") != nested:
            raise ValueError("scope kind must match whether the path is a story scope")
        return self


class ScopeInventory(_StrictModel):
    schema_version: Literal[1]
    legacy_scopes: list[LegacyScopeEntry] = Field(min_length=1)

    @field_validator("legacy_scopes")
    @classmethod
    def validate_unique_paths(
        cls, values: list[LegacyScopeEntry]
    ) -> list[LegacyScopeEntry]:
        paths = [item.path for item in values]
        if len(paths) != len(set(paths)):
            raise ValueError("scope inventory has duplicate paths")
        return sorted(values, key=lambda item: item.path)


def load_scope_inventory(path: Path) -> ScopeInventory:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ScopeInventoryError("scope inventory root must be a mapping")
    return ScopeInventory.model_validate(raw)


def validate_scope_inventory(
    repo_root: Path,
    inventory: ScopeInventory,
    closure_policy: ClosureDispositionPolicy,
) -> None:
    """Require every noncanonical root and every story scope to be classified."""

    allowed_dispositions = {item.id for item in closure_policy.dispositions}
    entries = {item.path: item for item in inventory.legacy_scopes}
    if any(item.disposition not in allowed_dispositions for item in entries.values()):
        raise ScopeInventoryError("scope inventory references unknown disposition")

    expected: dict[str, Literal["archived_epic", "story_scope"]] = {}
    for scope_path in sorted((repo_root / "work/epics").glob("**/scope.md")):
        relative = scope_path.relative_to(repo_root).as_posix()
        text = scope_path.read_text(encoding="utf-8")
        nested = "/stories/" in relative
        epic_id = _frontmatter_value(text, "epic_id")
        if nested:
            expected[relative] = "story_scope"
        elif epic_id is None:
            expected[relative] = "archived_epic"
        elif _EPIC_ID.fullmatch(epic_id) is None:
            raise ScopeInventoryError("canonical root scope has an unsafe epic ID")
        elif _frontmatter_value(text, "status") is None:
            raise ScopeInventoryError("canonical root scope lacks a status")

    if set(entries) != set(expected):
        missing = sorted(set(expected) - set(entries))
        extra = sorted(set(entries) - set(expected))
        raise ScopeInventoryError(
            "scope inventory does not classify every legacy/story scope: "
            f"missing={missing}; extra={extra}"
        )
    if any(entries[path].kind != kind for path, kind in expected.items()):
        raise ScopeInventoryError("scope inventory kind disagrees with filesystem")


def _frontmatter_value(text: str, key: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    closing = text.find("\n---\n", 4)
    if closing < 0:
        return None
    for line in text[4:closing].splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip("'").strip('"') or None
    return None
