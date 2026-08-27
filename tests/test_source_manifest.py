from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest
import yaml

from validators.public_boundary import (
    PublicPathDisposition,
    classify_public_path,
    load_public_boundary_policy,
)
from validators.source_authority import load_source_registry
from validators.source_manifest import (
    ContentType,
    SourceManifestError,
    build_source_manifest,
    build_source_manifest_receipt,
    load_source_manifest,
    render_source_manifest_jsonl,
    source_manifest_hash,
    validate_source_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "sources/source-registry.yaml"
MANIFEST_PATH = ROOT / "sources/source-manifest.jsonl"
BUILD_SCRIPT = ROOT / "scripts/build_source_manifest.py"
CHECK_SCRIPT = ROOT / "scripts/check_source_manifest.py"


def _registry_data(content: bytes) -> dict[str, Any]:
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
                        "path": "private-source.md",
                        "sha256": hashlib.sha256(content).hexdigest(),
                        "line_count": content.count(b"\n"),
                    }
                ],
            }
        ],
    }


def _write_fixture_registry(tmp_path: Path, content: bytes) -> Path:
    (tmp_path / "private-source.md").write_bytes(content)
    registry_path = tmp_path / "source-registry.yaml"
    registry_path.write_text(
        yaml.safe_dump(_registry_data(content), sort_keys=False), encoding="utf-8"
    )
    return registry_path


def test_canonical_manifest_covers_every_private_source_line_without_text() -> None:
    registry = load_source_registry(REGISTRY_PATH)
    manifest = load_source_manifest(MANIFEST_PATH)

    validate_source_manifest(ROOT, registry, manifest)
    receipt = build_source_manifest_receipt(ROOT, REGISTRY_PATH, MANIFEST_PATH)
    rendered = render_source_manifest_jsonl(manifest)

    assert receipt.status == "pass"
    assert receipt.unit_count == 407
    assert receipt.excluded_line_count == 0
    assert source_manifest_hash(manifest) == receipt.manifest_sha256
    assert "Additional Praise" not in rendered
    assert "source_line_count" in rendered


def test_source_authority_artifacts_are_explicitly_denied_from_clean_export() -> None:
    policy = load_public_boundary_policy(ROOT / "governance/public-boundary.yaml")

    assert (
        classify_public_path(policy, "sources/source-registry.yaml")
        is PublicPathDisposition.DENIED
    )
    assert (
        classify_public_path(policy, "sources/source-manifest.jsonl")
        is PublicPathDisposition.DENIED
    )


def test_heading_builder_records_preamble_as_exclusion_and_preserves_coverage(
    tmp_path: Path,
) -> None:
    content = b"preamble\n# Definition\nbody\n## Warning\nbody\n"
    registry_path = _write_fixture_registry(tmp_path, content)
    registry = load_source_registry(registry_path)

    manifest = build_source_manifest(tmp_path, registry, "fixture-source")

    assert [(item.line_start, item.line_end) for item in manifest.units] == [
        (1, 1),
        (2, 3),
        (4, 5),
    ]
    assert [item.content_type for item in manifest.units] == [
        ContentType.EXCLUSION,
        ContentType.DEFINITION,
        ContentType.WARNING,
    ]
    assert manifest.units[0].exclusion_reason == "no_structural_heading"


def test_manifest_validation_rejects_tampered_unit_hash(tmp_path: Path) -> None:
    content = b"# Definition\nbody\n"
    registry_path = _write_fixture_registry(tmp_path, content)
    registry = load_source_registry(registry_path)
    manifest = build_source_manifest(tmp_path, registry, "fixture-source")
    data = manifest.model_dump(mode="json")
    data["units"][0]["sha256"] = "0" * 64
    manifest_path = tmp_path / "source-manifest.jsonl"
    manifest_path.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                {key: value for key, value in data.items() if key != "units"},
                *data["units"],
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(SourceManifestError, match="unit hash mismatch"):
        build_source_manifest_receipt(tmp_path, registry_path, manifest_path)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda data: data["units"][0].update({"line_start": 2}),
        lambda data: data["units"].append(deepcopy(data["units"][0])),
        lambda data: data.update({"source_line_count": 1}),
        lambda data: data["units"][0].update({"exclusion_reason": "unexpected"}),
    ],
)
def test_manifest_contract_rejects_gaps_duplicates_and_invalid_exclusions(
    tmp_path: Path, mutator: Any
) -> None:
    content = b"# Definition\nbody\n"
    registry_path = _write_fixture_registry(tmp_path, content)
    registry = load_source_registry(registry_path)
    data = build_source_manifest(tmp_path, registry, "fixture-source").model_dump(
        mode="json"
    )
    mutator(data)
    manifest_path = tmp_path / "source-manifest.jsonl"
    rows = [
        {key: value for key, value in data.items() if key != "units"},
        *data["units"],
    ]
    manifest_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    with pytest.raises(SourceManifestError):
        load_source_manifest(manifest_path)


def test_build_and_check_clis_emit_only_private_structural_metadata(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "source-manifest.jsonl"
    built = subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            "--repo",
            str(ROOT),
            "--registry",
            str(REGISTRY_PATH),
            "--source-id",
            "scaling-up-llamaparse-2014",
            "--output",
            str(manifest_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    checked = subprocess.run(
        [
            sys.executable,
            str(CHECK_SCRIPT),
            "--repo",
            str(ROOT),
            "--registry",
            str(REGISTRY_PATH),
            "--manifest",
            str(manifest_path),
            "--format",
            "json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert built.returncode == 0
    assert checked.returncode == 0
    assert "source text" not in built.stdout
    assert '"status": "pass"' in checked.stdout
    assert "Additional Praise" not in manifest_path.read_text(encoding="utf-8")


def test_heading_builder_recognizes_named_historical_case_sections(
    tmp_path: Path,
) -> None:
    content = b"# Perceptionist's Ping\ncase narrative\n"
    registry_path = _write_fixture_registry(tmp_path, content)
    registry = load_source_registry(registry_path)

    manifest = build_source_manifest(tmp_path, registry, "fixture-source")

    assert manifest.units[0].content_type is ContentType.HISTORICAL_EXAMPLE
