"""Build the project-local Codex adapter without changing user configuration.

The capability catalog stays authoritative.  This module packages a validated,
source-safe projection of it and one public conversational door; it never
routes a business request or installs into a home directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from contextlib import suppress
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
AUTHORIZED_CATALOG_PATH = REPOSITORY_ROOT / "capabilities" / "mvp" / "catalog.json"
CANONICAL_SKILL_PATH = REPOSITORY_ROOT / "escala-skills" / "escala" / "SKILL.md"
CANONICAL_CATALOG_REFERENCE = "../../capabilities/mvp/catalog.json"
CODEX_CATALOG_REFERENCE = "../../core/escala-capability-contract.json"
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from validators.capability_map import (  # noqa: E402
    CapabilityMapError,
    load_capability_map,
    validate_capability_map,
)


class CodexAdapterError(ValueError):
    """Raised before an unsafe or incomplete adapter can be published."""


def _resolve_directory(path: Path, *, name: str) -> Path:
    if not path.is_absolute():
        raise CodexAdapterError(f"{name} must be an absolute path")
    try:
        return path.resolve(strict=True)
    except OSError as exc:
        raise CodexAdapterError(f"{name} is unavailable") from exc


def _validate_output(output: Path, allowed_root: Path) -> tuple[Path, Path]:
    root = _resolve_directory(allowed_root, name="allowed_root")
    if not root.is_dir():
        raise CodexAdapterError("allowed_root must be a directory")
    if not output.is_absolute():
        raise CodexAdapterError("output must be an absolute path")
    if os.path.lexists(output) or output.is_symlink():
        raise CodexAdapterError("output already exists or is a symlink")
    resolved_parent = _resolve_directory(output.parent, name="output parent")
    resolved_output = resolved_parent / output.name
    try:
        resolved_output.relative_to(root)
    except ValueError as exc:
        raise CodexAdapterError("output must be within allowed_root") from exc
    return resolved_output, root


def _load_catalog(catalog_path: Path) -> dict[str, Any]:
    """Load only the exact, approved E67 catalog projection.

    A structurally valid lookalike is not authority.  The adapter accepts a
    copied input only when its bytes, parsed content, and catalog identity all
    match the checked-in E67 authority exactly.
    """

    try:
        authority_bytes = AUTHORIZED_CATALOG_PATH.read_bytes()
        input_bytes = catalog_path.read_bytes()
        authority_raw = json.loads(authority_bytes)
        raw = json.loads(input_bytes)
    except (OSError, json.JSONDecodeError) as exc:
        raise CodexAdapterError("catalog is unavailable") from exc
    if input_bytes != authority_bytes:
        raise CodexAdapterError("catalog does not match approved E67 authority")
    if raw != authority_raw or raw.get("catalog_id") != authority_raw.get("catalog_id"):
        raise CodexAdapterError(
            "catalog identity does not match approved E67 authority"
        )
    if hashlib.sha256(input_bytes).digest() != hashlib.sha256(authority_bytes).digest():
        raise CodexAdapterError("catalog digest does not match approved E67 authority")
    try:
        catalog = load_capability_map(catalog_path)
    except CapabilityMapError as exc:
        raise CodexAdapterError(f"catalog is invalid: {exc}") from exc
    errors = validate_capability_map(catalog)
    if errors:
        raise CodexAdapterError(f"catalog is invalid: {','.join(errors)}")
    if raw != catalog.model_dump(mode="json"):
        raise CodexAdapterError("catalog is not canonical")
    return raw


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _portable_skill() -> str:
    """Project the one public skill without duplicating its methodology.

    The generated Codex package places its catalog under ``core/`` while the
    repository skill reaches it through ``capabilities/mvp``. Rewriting that
    single relative reference is packaging, not adapter-local behavior.
    """
    try:
        source = CANONICAL_SKILL_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise CodexAdapterError("canonical public skill is unavailable") from exc
    if source.count(CANONICAL_CATALOG_REFERENCE) != 1:
        raise CodexAdapterError(
            "canonical public skill has an invalid catalog reference"
        )
    return source.replace(CANONICAL_CATALOG_REFERENCE, CODEX_CATALOG_REFERENCE)


def _build_manifest(catalog: dict[str, Any]) -> dict[str, Any]:
    return {
        "adapter": "codex",
        "capability_catalog_id": catalog["catalog_id"],
        "capability_contract": "core/escala-capability-contract.json",
        "public_skills": ["escala"],
        "schema_version": 1,
        "security": {
            "credentials_required": False,
            "global_install": False,
            "mcp_enabled": False,
        },
        "skill_root": "skills/escala",
    }


def _assert_complete(directory: Path, catalog: dict[str, Any]) -> None:
    expected = {
        "codex-adapter.json",
        "core/escala-capability-contract.json",
        "skills/escala/SKILL.md",
    }
    actual = {
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*")
        if path.is_file()
    }
    if actual != expected:
        raise CodexAdapterError("adapter output has an unexpected surface")
    core = json.loads(
        (directory / "core" / "escala-capability-contract.json").read_text(
            encoding="utf-8"
        )
    )
    if core != catalog:
        raise CodexAdapterError("adapter core does not match catalog")
    manifest = json.loads(
        (directory / "codex-adapter.json").read_text(encoding="utf-8")
    )
    if manifest != _build_manifest(catalog):
        raise CodexAdapterError("adapter manifest is invalid")


def _cleanup_temporary(temporary: Path | None) -> None:
    if temporary is not None and temporary.exists():
        with suppress(OSError):
            shutil.rmtree(temporary)


def build_codex_adapter(
    *, catalog_path: Path, output: Path, allowed_root: Path
) -> Path:
    """Create a new validated adapter under an explicit, existing root.

    The output must not exist.  All content is written to a private sibling
    directory and atomically renamed only after the complete package validates.
    """

    temporary: Path | None = None
    try:
        destination, root = _validate_output(output, allowed_root)
        catalog = _load_catalog(catalog_path)
        temporary = Path(tempfile.mkdtemp(prefix=".escala-codex-", dir=root))
        (temporary / "core").mkdir()
        (temporary / "skills" / "escala").mkdir(parents=True)
        _write_json(temporary / "core" / "escala-capability-contract.json", catalog)
        _write_json(temporary / "codex-adapter.json", _build_manifest(catalog))
        (temporary / "skills" / "escala" / "SKILL.md").write_text(
            _portable_skill(), encoding="utf-8"
        )
        _assert_complete(temporary, catalog)
        os.replace(temporary, destination)
    except CodexAdapterError:
        _cleanup_temporary(temporary)
        raise
    except OSError as exc:
        _cleanup_temporary(temporary)
        raise CodexAdapterError("filesystem operation failed") from exc
    except Exception:
        _cleanup_temporary(temporary)
        raise
    return destination


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the local, single-door ESCALA adapter for Codex."
    )
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allowed-root", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        build_codex_adapter(
            catalog_path=args.catalog,
            output=args.output,
            allowed_root=args.allowed_root,
        )
    except CodexAdapterError as exc:
        print(f"Codex adapter not created: {exc}")
        return 2
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
