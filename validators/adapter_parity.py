"""Deterministic S67.4 evidence for the portable ESCALA adapter contract.

The six-route JSON catalog is the authority for new installations.  The older
YAML catalog remains only as a bounded compatibility source for legacy aliases;
this module deliberately reports that distinction instead of silently merging
two different contracts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from escala_server.capabilities import (
    load_capability_catalog,
    load_legacy_aliases,
    public_install_skills,
)
from scripts.refresh_legacy_skill_aliases import expected_files
from validators.capability_map import load_capability_map, validate_capability_map


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPOSITORY_ROOT / "capabilities" / "mvp" / "catalog.json"
CANONICAL_SKILL_PATH = REPOSITORY_ROOT / "escala-skills" / "escala" / "SKILL.md"
CANONICAL_CATALOG_REFERENCE = "../../capabilities/mvp/catalog.json"
CODEX_CATALOG_REFERENCE = "../../core/escala-capability-contract.json"
CLAUDE_ADAPTER_PATH = REPOSITORY_ROOT / "adapters" / "claude" / "adapter.json"
CLAUDE_SKILLS_ROOT = REPOSITORY_ROOT / ".claude" / "skills"
LEGACY_ROOTS = (
    REPOSITORY_ROOT / ".claude" / "legacy-skills",
    REPOSITORY_ROOT / ".agents" / "legacy-skills",
)
DISCOVERABLE_SKILL_ROOTS = (
    REPOSITORY_ROOT / ".claude" / "skills",
    REPOSITORY_ROOT / ".agents" / "skills",
)
REPORT_PATH = REPOSITORY_ROOT / "reports" / "e67" / "s67.4-parity.json"
_PUBLIC_ENTRYPOINT = "escala"
_LEGACY_GLOB = "scale" + "up-*/SKILL.md"


class AdapterParityError(ValueError):
    """Raised when the checked-in portable adapter contract is inconsistent."""


def _relative(path: Path) -> str:
    try:
        return path.relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError:
        return path.name


def _read_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdapterParityError(f"unavailable:{_relative(path)}") from exc
    if not isinstance(raw, dict):
        raise AdapterParityError(f"invalid_object:{_relative(path)}")
    return raw


def _portable_catalog() -> tuple[dict[str, Any], Any]:
    raw = _read_json(CATALOG_PATH)
    capability_map = load_capability_map(CATALOG_PATH)
    if raw != capability_map.model_dump(mode="json"):
        raise AdapterParityError("catalog_not_canonical")
    errors = validate_capability_map(capability_map)
    if errors:
        raise AdapterParityError("catalog_drift:" + ",".join(errors))
    return raw, capability_map


def _claude_manifest() -> dict[str, Any]:
    manifest = _read_json(CLAUDE_ADAPTER_PATH)
    expected = {
        "schema_version": 1,
        "platform": "claude-code",
        "public_entrypoint": _PUBLIC_ENTRYPOINT,
        "core_skill": "../../escala-skills/escala/SKILL.md",
        "core_capability_catalog": "../../capabilities/mvp/catalog.json",
        "local_state": "consent-required",
        "managed_instruction_file": "CLAUDE.md",
        "remote_extensions": {"enabled_by_default": False},
    }
    if manifest != expected:
        raise AdapterParityError("claude_manifest_drift")
    if (CLAUDE_ADAPTER_PATH.parent / manifest["core_skill"]).resolve() != (
        REPOSITORY_ROOT / "escala-skills" / "escala" / "SKILL.md"
    ):
        raise AdapterParityError("claude_core_skill_drift")
    if (CLAUDE_ADAPTER_PATH.parent / manifest["core_capability_catalog"]).resolve() != (
        CATALOG_PATH
    ):
        raise AdapterParityError("claude_catalog_drift")
    return manifest


def is_exact_legacy_redirect(content: str, expected: str) -> bool:
    """A legacy wrapper may only be the exact generated compatibility redirect."""
    return content == expected


def _legacy_migration() -> dict[str, Any]:
    catalog = load_capability_catalog()
    aliases = load_legacy_aliases(catalog)
    alias_map = {alias.alias: alias for alias in aliases}
    try:
        expected_wrappers = expected_files()
    except ValueError as exc:
        raise AdapterParityError("legacy_wrapper_surface_drift") from exc
    wrapper_paths = tuple(sorted(expected_wrappers))
    wrapper_names = {path.parent.name for path in wrapper_paths}
    if wrapper_names != set(alias_map):
        raise AdapterParityError("legacy_wrapper_surface_drift")
    discovered_aliases = [
        path
        for root in DISCOVERABLE_SKILL_ROOTS
        if root.is_dir()
        for path in root.glob(_LEGACY_GLOB)
    ]
    if discovered_aliases:
        raise AdapterParityError("legacy_alias_publicly_discoverable")
    for path, expected_content in expected_wrappers.items():
        content = path.read_text(encoding="utf-8")
        if not is_exact_legacy_redirect(content, expected_content):
            raise AdapterParityError(
                f"legacy_wrapper_not_redirect_only:{_relative(path)}"
            )
    if public_install_skills(catalog) != (_PUBLIC_ENTRYPOINT,):
        raise AdapterParityError("legacy_catalog_public_surface_drift")
    return {
        "catalog_alias_count": len(aliases),
        "historical_router": {
            "catalog": "escala-skills/catalog.yaml",
            "role": "legacy-alias-resolution-only",
        },
        "materialized_wrapper_count": len(wrapper_paths),
        "public_aliases": [],
        "wrapper_roots": [_relative(path) for path in LEGACY_ROOTS],
    }


def build_parity_report() -> dict[str, Any]:
    """Derive the only accepted S67.4 report from checked-in contracts."""
    catalog, capability_map = _portable_catalog()
    claude = _claude_manifest()
    capabilities = [
        {
            "aliases": list(binding.aliases),
            "capability_id": binding.id,
            "evidence_kinds": list(binding.evidence_kinds),
            "intent": binding.intents[0],
            "lifecycle": list(capability_map.lifecycle),
            "procedure_id": binding.procedure_id,
            "specialist_profiles": list(binding.specialist_profiles),
        }
        for binding in capability_map.capabilities
    ]
    return {
        "adapters": {
            "claude": {
                "core_capability_catalog": _relative(
                    (
                        CLAUDE_ADAPTER_PATH.parent / claude["core_capability_catalog"]
                    ).resolve()
                ),
                "core_skill": _relative(
                    (CLAUDE_ADAPTER_PATH.parent / claude["core_skill"]).resolve()
                ),
                "manifest": _relative(CLAUDE_ADAPTER_PATH),
                "public_entrypoint": claude["public_entrypoint"],
            },
            "codex": {
                "builder": "adapters/codex/build_adapter.py",
                "core_capability_contract": "core/escala-capability-contract.json",
                "public_entrypoint": _PUBLIC_ENTRYPOINT,
            },
        },
        "capabilities": capabilities,
        "migration": _legacy_migration(),
        "portable_core": {
            "catalog": _relative(CATALOG_PATH),
            "catalog_id": catalog["catalog_id"],
            "lifecycle": list(capability_map.lifecycle),
            "skill": "escala-skills/escala/SKILL.md",
        },
        "public_entrypoint": _PUBLIC_ENTRYPOINT,
        "schema_version": 1,
        "story_id": "S67.4",
    }


def validate_parity_report(report: object) -> tuple[str, ...]:
    """Return a stable error instead of accepting a stale hand-written report."""
    if not isinstance(report, dict):
        return ("parity_report_invalid",)
    try:
        expected = build_parity_report()
    except AdapterParityError as exc:
        return (str(exc),)
    if report != expected:
        return ("parity_report_drift",)
    return ()


def validate_codex_bundle(bundle: Path, report: dict[str, Any]) -> tuple[str, ...]:
    """Check a fresh Codex projection against the portable report."""
    errors: list[str] = []
    try:
        manifest = _read_json(bundle / "codex-adapter.json")
        core = _read_json(bundle / "core" / "escala-capability-contract.json")
        catalog, _ = _portable_catalog()
    except AdapterParityError as exc:
        return (str(exc),)
    public_skills = sorted(
        path.parent.name for path in (bundle / "skills").glob("*/SKILL.md")
    )
    expected_skill = CANONICAL_SKILL_PATH.read_text(encoding="utf-8").replace(
        CANONICAL_CATALOG_REFERENCE, CODEX_CATALOG_REFERENCE
    )
    generated_skill = (bundle / "skills" / _PUBLIC_ENTRYPOINT / "SKILL.md").read_text(
        encoding="utf-8"
    )
    if core != catalog:
        errors.append("codex_core_catalog_drift")
    if generated_skill != expected_skill:
        errors.append("codex_public_skill_drift")
    if manifest.get("public_skills") != [_PUBLIC_ENTRYPOINT] or public_skills != [
        _PUBLIC_ENTRYPOINT
    ]:
        errors.append("codex_public_surface_drift")
    if manifest.get("capability_catalog_id") != report["portable_core"]["catalog_id"]:
        errors.append("codex_catalog_identity_drift")
    if (
        manifest.get("capability_contract")
        != report["adapters"]["codex"]["core_capability_contract"]
    ):
        errors.append("codex_contract_path_drift")
    return tuple(errors)


def validate_claude_adapter(report: dict[str, Any]) -> tuple[str, ...]:
    """Check Claude references and the checkout's clean public skill surface."""
    errors: list[str] = []
    try:
        manifest = _claude_manifest()
    except AdapterParityError as exc:
        return (str(exc),)
    try:
        skills = sorted(path.name for path in CLAUDE_SKILLS_ROOT.iterdir())
    except OSError:
        return ("claude_public_surface_unavailable",)
    if skills != [_PUBLIC_ENTRYPOINT]:
        errors.append("claude_public_surface_drift")
    if not (CLAUDE_SKILLS_ROOT / _PUBLIC_ENTRYPOINT).is_symlink():
        errors.append("claude_public_skill_not_linked")
    if manifest["public_entrypoint"] != report["public_entrypoint"]:
        errors.append("claude_public_entrypoint_drift")
    if report["adapters"]["claude"]["core_capability_catalog"] != _relative(
        CATALOG_PATH
    ):
        errors.append("claude_catalog_report_drift")
    return tuple(errors)


def validate_legacy_migration(report: dict[str, Any]) -> tuple[str, ...]:
    """Validate aliases remain internal redirects and match the recorded report."""
    try:
        expected = _legacy_migration()
    except AdapterParityError as exc:
        return (str(exc),)
    if report.get("migration") != expected:
        return ("legacy_migration_report_drift",)
    return ()
