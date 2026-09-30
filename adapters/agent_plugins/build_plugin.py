"""Build ESCALA's minimum self-contained Agent Plugins v1 package offline."""

from __future__ import annotations

import argparse
from contextlib import suppress
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from validators.agent_plugin import (  # noqa: E402
    AGENT_PLUGIN_SCHEMA_URL,
    AUTHORIZED_CATALOG_PATH,
    PUBLIC_SKILL_NAME,
    SKILL_CATALOG_REFERENCE,
    load_agent_plugin,
)


CANONICAL_SKILL_PATH = REPOSITORY_ROOT / "escala-skills" / "escala" / "SKILL.md"
CANONICAL_CATALOG_REFERENCE = "../../capabilities/mvp/catalog.json"


class AgentPluginBuildError(ValueError):
    """Raised before a plugin build can create a partial or unsafe package."""


def _resolve_existing_directory(path: Path, *, reason: str) -> Path:
    if not path.is_absolute():
        raise AgentPluginBuildError(reason)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise AgentPluginBuildError(reason) from exc
    if not resolved.is_dir() or path.is_symlink():
        raise AgentPluginBuildError(reason)
    return resolved


def _validate_output(output: Path, allowed_root: Path) -> tuple[Path, Path]:
    root = _resolve_existing_directory(allowed_root, reason="allowed_root_invalid")
    if not output.is_absolute():
        raise AgentPluginBuildError("output_must_be_absolute")
    if os.path.lexists(output):
        raise AgentPluginBuildError("output_already_exists")
    parent = _resolve_existing_directory(output.parent, reason="output_parent_invalid")
    destination = parent / output.name
    try:
        destination.relative_to(root)
    except ValueError as exc:
        raise AgentPluginBuildError("output_outside_allowed_root") from exc
    return destination, root


def _portable_skill() -> str:
    try:
        skill = CANONICAL_SKILL_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise AgentPluginBuildError("canonical_skill_unavailable") from exc
    if skill.count(CANONICAL_CATALOG_REFERENCE) != 1:
        raise AgentPluginBuildError("canonical_skill_reference_invalid")
    return skill.replace(CANONICAL_CATALOG_REFERENCE, SKILL_CATALOG_REFERENCE)


def _manifest() -> dict[str, str]:
    return {
        "$schema": AGENT_PLUGIN_SCHEMA_URL,
        "name": PUBLIC_SKILL_NAME,
        "version": "1.0.0",
        "description": "Puerta única local de ESCALA para empresarios.",
    }


def _write_json(path: Path, value: dict[str, str]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_agent_plugin(*, output: Path, allowed_root: Path) -> Path:
    """Build and fully validate a new package by an atomic local rename."""

    temporary: Path | None = None
    try:
        destination, root = _validate_output(output, allowed_root)
        temporary = Path(tempfile.mkdtemp(prefix=".escala-plugin-", dir=root))
        skill_root = temporary / "skills" / PUBLIC_SKILL_NAME
        references = skill_root / "references"
        references.mkdir(parents=True)
        _write_json(temporary / "plugin.json", _manifest())
        (skill_root / "SKILL.md").write_text(_portable_skill(), encoding="utf-8")
        shutil.copyfile(AUTHORIZED_CATALOG_PATH, references / "capability-catalog.json")
        load_agent_plugin(temporary)
        os.replace(temporary, destination)
        temporary = None
        return destination
    except AgentPluginBuildError:
        raise
    except OSError as exc:
        raise AgentPluginBuildError("build_filesystem_failure") from exc
    except Exception as exc:
        raise AgentPluginBuildError("build_validation_failed") from exc
    finally:
        if temporary is not None and temporary.exists():
            with suppress(OSError):
                shutil.rmtree(temporary)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build ESCALA Agent Plugins v1 package."
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allowed-root", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        print(build_agent_plugin(output=args.output, allowed_root=args.allowed_root))
    except AgentPluginBuildError as exc:
        print(f"Agent Plugin not created: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
