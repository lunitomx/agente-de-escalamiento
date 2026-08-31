"""Offline, fail-closed validation for ESCALA's Agent Plugins v1 package."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from validators.capability_map import (
    CapabilityMapError,
    load_capability_map,
    validate_capability_map,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
AUTHORIZED_CATALOG_PATH = REPOSITORY_ROOT / "capabilities" / "mvp" / "catalog.json"
AGENT_PLUGIN_SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
PUBLIC_SKILL_NAME = "escala"
SKILL_CATALOG_REFERENCE = "references/capability-catalog.json"
PACKAGE_FILES = frozenset(
    {
        "plugin.json",
        f"skills/{PUBLIC_SKILL_NAME}/SKILL.md",
        f"skills/{PUBLIC_SKILL_NAME}/{SKILL_CATALOG_REFERENCE}",
    }
)
_PLUGIN_NAME = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
_PRIVATE_MARKERS = (
    ".scaleup/",
    ".agents/",
    ".claude/",
    ".codex/",
    "sqlite",
    "mcp",
    "oauth",
    "credential",
)


class AgentPluginError(ValueError):
    """A source-neutral validation failure for a portable agent plugin."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class PluginManifest(_StrictModel):
    schema_url: str = Field(alias="$schema")
    name: str
    version: str
    description: str

    @field_validator("schema_url")
    @classmethod
    def validate_schema_url(cls, value: str) -> str:
        if value != AGENT_PLUGIN_SCHEMA_URL:
            raise ValueError("plugin schema is invalid")
        return value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not _PLUGIN_NAME.fullmatch(value) or len(value) > 64:
            raise ValueError("plugin name is invalid")
        if value != PUBLIC_SKILL_NAME:
            raise ValueError("plugin name must preserve ESCALA's public door")
        return value

    @field_validator("version", "description")
    @classmethod
    def validate_nonempty_text(cls, value: str) -> str:
        if not value or value != value.strip():
            raise ValueError("manifest text is invalid")
        return value


@dataclass(frozen=True)
class AgentPluginPackage:
    """A structural fixture that E68 can use without semantic claims."""

    root: Path
    skill_name: str
    capability_catalog_id: str


def _resolve_root(path: Path) -> Path:
    if not path.is_absolute():
        raise AgentPluginError("package_root_must_be_absolute")
    try:
        root = path.resolve(strict=True)
    except OSError as exc:
        raise AgentPluginError("package_unavailable") from exc
    if not root.is_dir() or path.is_symlink():
        raise AgentPluginError("package_root_invalid")
    return root


def discover_public_skills(root: Path) -> tuple[str, ...]:
    """Discover only direct ``skills/<name>/SKILL.md`` children per v1."""

    skills_root = root / "skills"
    if not skills_root.is_dir() or skills_root.is_symlink():
        return ()
    return tuple(
        sorted(
            child.name
            for child in skills_root.iterdir()
            if child.is_dir()
            and not child.is_symlink()
            and (child / "SKILL.md").is_file()
        )
    )


def _validate_no_symlinks(root: Path) -> None:
    if any(path.is_symlink() for path in root.rglob("*")):
        raise AgentPluginError("symlink_forbidden")


def _validate_surface(root: Path) -> None:
    actual = {
        path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
    }
    if actual != PACKAGE_FILES:
        raise AgentPluginError("package_surface_invalid")
    if discover_public_skills(root) != (PUBLIC_SKILL_NAME,):
        raise AgentPluginError("public_skill_discovery_invalid")


def _load_manifest(root: Path) -> PluginManifest:
    try:
        raw = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
        return PluginManifest.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise AgentPluginError("manifest_invalid") from exc


def _validate_skill(root: Path) -> None:
    skill_path = root / "skills" / PUBLIC_SKILL_NAME / "SKILL.md"
    try:
        skill = skill_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AgentPluginError("skill_unavailable") from exc
    if skill.count(SKILL_CATALOG_REFERENCE) != 1 or "../" in skill:
        raise AgentPluginError("skill_reference_invalid")
    lowered = skill.casefold()
    if any(marker in lowered for marker in _PRIVATE_MARKERS):
        raise AgentPluginError("private_content_forbidden")
    target = (skill_path.parent / SKILL_CATALOG_REFERENCE).resolve(strict=False)
    try:
        target.relative_to(skill_path.parent.resolve(strict=True))
    except ValueError as exc:
        raise AgentPluginError("skill_reference_escapes_package") from exc


def _load_catalog(root: Path) -> str:
    package_path = root / "skills" / PUBLIC_SKILL_NAME / SKILL_CATALOG_REFERENCE
    try:
        expected = AUTHORIZED_CATALOG_PATH.read_bytes()
        actual = package_path.read_bytes()
    except OSError as exc:
        raise AgentPluginError("catalog_unavailable") from exc
    if (
        hashlib.sha256(actual).digest() != hashlib.sha256(expected).digest()
        or actual != expected
    ):
        raise AgentPluginError("catalog_drift")
    try:
        catalog = load_capability_map(package_path)
    except CapabilityMapError as exc:
        raise AgentPluginError("catalog_invalid") from exc
    if validate_capability_map(catalog):
        raise AgentPluginError("catalog_invalid")
    return catalog.catalog_id


def load_agent_plugin(path: Path) -> AgentPluginPackage:
    """Validate the complete minimal package and return an E68-safe fixture."""

    root = _resolve_root(path)
    _validate_no_symlinks(root)
    _validate_surface(root)
    _load_manifest(root)
    _validate_skill(root)
    return AgentPluginPackage(
        root=root,
        skill_name=PUBLIC_SKILL_NAME,
        capability_catalog_id=_load_catalog(root),
    )
