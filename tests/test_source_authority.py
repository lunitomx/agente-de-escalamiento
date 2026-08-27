from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest
import yaml

from validators.source_authority import (
    SourceAuthorityError,
    build_source_authority_receipt,
    load_source_registry,
    render_source_authority_json,
    render_source_authority_markdown,
    source_registry_hash,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "sources/source-registry.yaml"
SCRIPT = ROOT / "scripts/check_source_authority.py"


def _registry_data(source_path: str, content: bytes) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "sources": [
            {
                "source_id": "fixture-source",
                "source_kind": "third_party_methodology",
                "edition": "fixture",
                "acquired_via": "locally_provided",
                "rights_status": "review_required",
                "rights_evidence": [],
                "distribution_state": "private_only",
                "last_reviewed": "2026-08-27",
                "artifacts": [
                    {
                        "role": "primary",
                        "path": source_path,
                        "sha256": hashlib.sha256(content).hexdigest(),
                        "line_count": content.count(b"\n"),
                    }
                ],
            }
        ],
    }


def _write_registry(path: Path, data: dict[str, Any]) -> Path:
    registry = path / "source-registry.yaml"
    registry.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return registry


def test_canonical_private_source_registry_has_a_stable_receipt() -> None:
    first = build_source_authority_receipt(ROOT, REGISTRY_PATH)
    second = build_source_authority_receipt(ROOT, REGISTRY_PATH)

    assert first == second
    assert first.source_ids == ["scaling-up-llamaparse-2014"]
    assert first.source_count == 1
    assert first.artifact_count == 2
    assert first.all_private_only is True
    assert first.all_rights_unresolved is True
    assert len(first.registry_sha256) == 64
    assert (
        source_registry_hash(load_source_registry(REGISTRY_PATH))
        == first.registry_sha256
    )
    assert "scaling_up_llamaparse" not in render_source_authority_json(first)
    assert "scaling_up_llamaparse" not in render_source_authority_markdown(first)


def test_source_authority_rejects_a_changed_private_artifact(tmp_path: Path) -> None:
    artifact = tmp_path / "private-source.md"
    artifact.write_bytes(b"first line\nsecond line\n")
    registry = _write_registry(
        tmp_path, _registry_data("private-source.md", artifact.read_bytes())
    )

    assert build_source_authority_receipt(tmp_path, registry).status == "pass"
    artifact.write_bytes(b"mutated\n")

    with pytest.raises(SourceAuthorityError, match="hash mismatch"):
        build_source_authority_receipt(tmp_path, registry)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda data: data.update({"unknown_root": True}),
        lambda data: data["sources"][0].update({"rights_status": "documented"}),
        lambda data: data["sources"][0].update({"distribution_state": "public"}),
        lambda data: data["sources"][0]["artifacts"][0].update(
            {"path": "../escape.md"}
        ),
        lambda data: data["sources"][0]["artifacts"].append(
            deepcopy(data["sources"][0]["artifacts"][0])
        ),
    ],
)
def test_source_registry_rejects_unproven_rights_or_unsafe_contracts(
    tmp_path: Path, mutator: Any
) -> None:
    content = b"fixture\n"
    (tmp_path / "private-source.md").write_bytes(content)
    data = _registry_data("private-source.md", content)
    mutator(data)

    with pytest.raises(SourceAuthorityError):
        load_source_registry(_write_registry(tmp_path, data))


def test_cli_emits_a_bounded_receipt_without_private_paths() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo",
            str(ROOT),
            "--registry",
            str(REGISTRY_PATH),
            "--format",
            "json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert '"status": "pass"' in completed.stdout
    assert "scaling_up_llamaparse" not in completed.stdout
    assert completed.stderr == ""
