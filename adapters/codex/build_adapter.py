"""Build the project-local Codex adapter without changing user configuration.

The capability catalog stays authoritative.  This module packages a validated,
source-safe projection of it and one public conversational door; it never
routes a business request or installs into a home directory.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from validators.capability_map import (
    CapabilityMapError,
    load_capability_map,
    validate_capability_map,
)


class CodexAdapterError(ValueError):
    """Raised before an unsafe or incomplete adapter can be published."""


_SKILL = """---
name: escala
description: >
  Puerta única de ESCALA para empresarios: entiende una necesidad en lenguaje
  natural, recupera sólo contexto autorizado y coordina la capacidad interna
  correcta sin mostrar comandos ni un catálogo técnico.
---

# ESCALA

Ayuda a la persona a avanzar su empresa con una conversación clara y una sola
pregunta útil cuando falte contexto. Usa únicamente el contrato portable en
`../../core/escala-capability-contract.json`; no expongas su vocabulario
técnico, sus rutas internas ni opciones de implementación.

Antes de proponer o guardar un cambio, confirma el contexto autorizado y la
decisión de la persona. No inventes información, no habilites integraciones y
no cambies configuraciones del entorno.
"""


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
    if output.exists():
        raise CodexAdapterError("output already exists")
    resolved_parent = _resolve_directory(output.parent, name="output parent")
    resolved_output = resolved_parent / output.name
    try:
        resolved_output.relative_to(root)
    except ValueError as exc:
        raise CodexAdapterError("output must be within allowed_root") from exc
    return resolved_output, root


def _load_catalog(catalog_path: Path) -> dict[str, Any]:
    try:
        catalog = load_capability_map(catalog_path)
    except CapabilityMapError as exc:
        raise CodexAdapterError(f"catalog is invalid: {exc}") from exc
    errors = validate_capability_map(catalog)
    if errors:
        raise CodexAdapterError(f"catalog is invalid: {','.join(errors)}")
    try:
        raw = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CodexAdapterError("catalog is unavailable") from exc
    if raw != catalog.model_dump(mode="json"):
        raise CodexAdapterError("catalog is not canonical")
    return raw


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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


def build_codex_adapter(
    *, catalog_path: Path, output: Path, allowed_root: Path
) -> Path:
    """Create a new validated adapter under an explicit, existing root.

    The output must not exist.  All content is written to a private sibling
    directory and atomically renamed only after the complete package validates.
    """

    destination, root = _validate_output(output, allowed_root)
    catalog = _load_catalog(catalog_path)
    temporary = Path(tempfile.mkdtemp(prefix=".escala-codex-", dir=root))
    try:
        (temporary / "core").mkdir()
        (temporary / "skills" / "escala").mkdir(parents=True)
        _write_json(temporary / "core" / "escala-capability-contract.json", catalog)
        _write_json(temporary / "codex-adapter.json", _build_manifest(catalog))
        (temporary / "skills" / "escala" / "SKILL.md").write_text(
            _SKILL, encoding="utf-8"
        )
        _assert_complete(temporary, catalog)
        os.replace(temporary, destination)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
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
