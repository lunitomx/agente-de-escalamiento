"""S67.2 contract tests for the local, one-door Codex adapter."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest  # type: ignore[reportMissingImports]

from adapters.codex.build_adapter import CodexAdapterError, build_codex_adapter


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "capabilities" / "mvp" / "catalog.json"


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_clean_adapter_has_exactly_one_public_door_and_core_parity(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "install" / "codex"
    destination.parent.mkdir()

    build_codex_adapter(
        catalog_path=CATALOG,
        output=destination,
        allowed_root=tmp_path / "install",
    )

    manifest = _read_json(destination / "codex-adapter.json")
    core = _read_json(destination / "core" / "escala-capability-contract.json")
    source = _read_json(CATALOG)
    public_skills = sorted(
        path.parent.name for path in (destination / "skills").glob("*/SKILL.md")
    )

    assert public_skills == ["escala"]
    assert manifest["public_skills"] == ["escala"]
    assert manifest["capability_catalog_id"] == source["catalog_id"]
    assert core == source
    assert manifest["security"] == {
        "credentials_required": False,
        "global_install": False,
        "mcp_enabled": False,
    }


def test_public_door_hides_internal_route_names_and_platform_details(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "install" / "codex"
    destination.parent.mkdir()
    build_codex_adapter(
        catalog_path=CATALOG,
        output=destination,
        allowed_root=tmp_path / "install",
    )

    skill = (destination / "skills" / "escala" / "SKILL.md").read_text(encoding="utf-8")
    source = _read_json(CATALOG)
    capabilities = cast(list[dict[str, object]], source["capabilities"])
    forbidden = [
        item
        for capability in capabilities
        for item in (
            str(capability["id"]),
            str(capability["procedure_id"]),
            *cast(list[str], capability["intents"]),
            *cast(list[str], capability["aliases"]),
        )
    ]

    assert "codex" not in skill.lower()
    assert "mcp" not in skill.lower()
    assert "credential" not in skill.lower()
    assert all(item not in skill for item in forbidden)


def test_relative_or_outside_destination_is_rejected_before_writes(
    tmp_path: Path,
) -> None:
    root = tmp_path / "allowed"
    root.mkdir()
    for destination in (Path("relative"), tmp_path / "outside"):
        with pytest.raises(CodexAdapterError, match="output"):
            build_codex_adapter(
                catalog_path=CATALOG,
                output=destination,
                allowed_root=root,
            )
        assert not destination.exists()


def test_cli_builds_the_same_local_adapter(tmp_path: Path) -> None:
    allowed_root = tmp_path / "install"
    allowed_root.mkdir()
    output = allowed_root / "escala"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "adapters" / "codex" / "build_adapter.py"),
            "--catalog",
            str(CATALOG),
            "--allowed-root",
            str(allowed_root),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == str(output)
    assert (output / "skills" / "escala" / "SKILL.md").is_file()


def test_mutated_but_valid_catalog_is_not_an_authorized_e67_authority(
    tmp_path: Path,
) -> None:
    allowed_root = tmp_path / "install"
    allowed_root.mkdir()
    mutated = tmp_path / "catalog.json"
    raw = _read_json(CATALOG)
    capabilities = cast(list[dict[str, object]], raw["capabilities"])
    first = capabilities[0]
    aliases = cast(list[str], first["aliases"])
    aliases[0] = "diagnostic"
    mutated.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    destination = allowed_root / "escala"

    with pytest.raises(CodexAdapterError, match="approved E67 authority"):
        build_codex_adapter(
            catalog_path=mutated,
            output=destination,
            allowed_root=allowed_root,
        )

    assert not destination.exists()
    assert list(allowed_root.glob(".escala-codex-*")) == []


def test_dangling_symlink_destination_is_rejected_and_cli_is_clean(
    tmp_path: Path,
) -> None:
    allowed_root = tmp_path / "install"
    allowed_root.mkdir()
    destination = allowed_root / "escala"
    destination.symlink_to(tmp_path / "missing")

    with pytest.raises(CodexAdapterError, match="symlink"):
        build_codex_adapter(
            catalog_path=CATALOG,
            output=destination,
            allowed_root=allowed_root,
        )

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "adapters" / "codex" / "build_adapter.py"),
            "--catalog",
            str(CATALOG),
            "--allowed-root",
            str(allowed_root),
            "--output",
            str(destination),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert destination.is_symlink()
    assert completed.returncode == 2
    assert "Traceback" not in completed.stderr
    assert "symlink" in completed.stdout


def test_existing_destination_and_invalid_catalog_never_publish_partial_output(
    tmp_path: Path,
) -> None:
    allowed_root = tmp_path / "install"
    allowed_root.mkdir()
    existing = allowed_root / "existing"
    existing.mkdir()
    marker = existing / "user-data.txt"
    marker.write_text("keep", encoding="utf-8")

    with pytest.raises(CodexAdapterError, match="already exists"):
        build_codex_adapter(
            catalog_path=CATALOG,
            output=existing,
            allowed_root=allowed_root,
        )
    assert marker.read_text(encoding="utf-8") == "keep"

    invalid = tmp_path / "invalid-catalog.json"
    invalid.write_text("{not-json", encoding="utf-8")
    rejected = allowed_root / "rejected"
    with pytest.raises(CodexAdapterError, match="catalog"):
        build_codex_adapter(
            catalog_path=invalid,
            output=rejected,
            allowed_root=allowed_root,
        )
    assert not rejected.exists()
    assert list(allowed_root.glob(".escala-codex-*")) == []
