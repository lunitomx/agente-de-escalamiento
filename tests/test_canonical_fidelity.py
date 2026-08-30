from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.audit_canonical_fidelity import audit_authorized_release
from validators.ontology_v2 import (
    load_canonical_release,
    load_canonical_release_integrity_manifest,
    validate_canonical_release_integrity,
)


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "ontology/v2/releases/s64.1.json"
PROJECTION = ROOT / "ontology/v2/releases/s64.4.relationship-projection.json"
MANIFEST = ROOT / "ontology/v2/releases/s64.4.integrity-manifest.json"
MATRIX = ROOT / "ontology/v2/releases/s64.3.coverage.json"
REPORT = ROOT / "ontology/v2/releases/s64.4.fidelity-report.json"
SCRIPT = ROOT / "scripts/audit_canonical_fidelity.py"


def _audit_command(
    report: Path,
    projection: Path = PROJECTION,
    manifest: Path = MANIFEST,
    matrix: Path = MATRIX,
) -> list[str]:
    return [
        sys.executable,
        str(SCRIPT),
        "--release",
        str(RELEASE),
        "--projection",
        str(projection),
        "--manifest",
        str(manifest),
        "--matrix",
        str(matrix),
        "--report",
        str(report),
    ]


def test_authorized_release_audit_is_pass_and_exact() -> None:
    report = audit_authorized_release(RELEASE, PROJECTION, MANIFEST, MATRIX)

    assert report["status"] == "pass"
    assert report["scope"] == "authorized-release-only"
    assert report["integrity_status"] == "pass"
    assert report["node_count"] == report["mapped_count"] == 76
    assert report["exclusion_count"] == report["review_required_count"] == 3
    assert report["excluded_count"] == 0
    assert report["relation_count"] == 9
    assert report["qualified_tool_count"] == 9
    assert report["qualified_rule_count"] == 7
    assert report["qualified_metric_count"] == 1


def test_cli_rebuild_and_checked_report_are_deterministic(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    built = subprocess.run(
        _audit_command(report), check=False, capture_output=True, text=True
    )
    checked = subprocess.run(
        [*_audit_command(REPORT), "--check"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert built.returncode == 0
    assert built.stdout == ""
    assert built.stderr == ""
    assert checked.returncode == 0
    assert checked.stdout == ""
    assert checked.stderr == ""
    assert json.loads(report.read_text(encoding="utf-8"))["status"] == "pass"


def test_audit_fails_closed_for_unassessed_integrity_or_coverage_mismatch(
    tmp_path: Path,
) -> None:
    unassessed = tmp_path / "unassessed.json"
    unassessed.write_text(
        json.dumps({"schema_version": 1, "release_id": "s64.1"}), encoding="utf-8"
    )
    bad_matrix = tmp_path / "bad-matrix.json"
    payload = json.loads(MATRIX.read_text(encoding="utf-8"))
    payload["release_sha256"] = "0" * 64
    bad_matrix.write_text(json.dumps(payload), encoding="utf-8")

    for manifest, matrix in ((unassessed, MATRIX), (MANIFEST, bad_matrix)):
        completed = subprocess.run(
            _audit_command(tmp_path / "report.json", manifest=manifest, matrix=matrix),
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 1
        assert completed.stdout == ""
        assert "canonical fidelity audit" in completed.stderr
        assert "unassessed" not in completed.stderr
        assert "0" * 64 not in completed.stderr


def test_relations_are_exactly_derived_and_each_has_tool_evidence(
    tmp_path: Path,
) -> None:
    release = load_canonical_release(RELEASE)
    manifest_payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    extra_relation = dict(manifest_payload["relations"][2])
    extra_relation["target_id"] = "decision.strategy"
    manifest_payload["relations"].append(extra_relation)
    extra_manifest = tmp_path / "extra-manifest.json"
    extra_manifest.write_text(json.dumps(manifest_payload), encoding="utf-8")

    with pytest.raises(ValueError, match="relations-do-not-exactly-match-contracts"):
        validate_canonical_release_integrity(
            release, load_canonical_release_integrity_manifest(extra_manifest)
        )

    projection_payload = json.loads(PROJECTION.read_text(encoding="utf-8"))
    projection_payload["relationships"][0]["evidence_refs"] = [
        "digest.sha256.unrelated"
    ]
    bad_projection = tmp_path / "bad-projection.json"
    bad_projection.write_text(json.dumps(projection_payload), encoding="utf-8")
    failed = subprocess.run(
        _audit_command(tmp_path / "report.json", projection=bad_projection),
        check=False,
        capture_output=True,
        text=True,
    )
    assert failed.returncode == 1
    assert failed.stdout == ""
    assert "unrelated" not in failed.stderr

    extra_projection = json.loads(PROJECTION.read_text(encoding="utf-8"))
    extra_projection["relationships"].append(
        dict(extra_projection["relationships"][2], target_id="decision.strategy")
    )
    extra_projection_path = tmp_path / "extra-projection.json"
    extra_projection_path.write_text(json.dumps(extra_projection), encoding="utf-8")
    extra = subprocess.run(
        _audit_command(tmp_path / "report.json", projection=extra_projection_path),
        check=False,
        capture_output=True,
        text=True,
    )
    assert extra.returncode == 1
    assert extra.stdout == ""

    missing_provenance = json.loads(MANIFEST.read_text(encoding="utf-8"))
    missing_provenance["relations"][0].pop("evidence_refs")
    missing_manifest = tmp_path / "missing-provenance.json"
    missing_manifest.write_text(json.dumps(missing_provenance), encoding="utf-8")
    missing = subprocess.run(
        _audit_command(tmp_path / "report.json", manifest=missing_manifest),
        check=False,
        capture_output=True,
        text=True,
    )
    assert missing.returncode == 1
    assert missing.stdout == ""

    non_tool = json.loads(MANIFEST.read_text(encoding="utf-8"))
    non_tool["relations"][0]["source_id"] = "decision.cash"
    non_tool_manifest = tmp_path / "non-tool-source.json"
    non_tool_manifest.write_text(json.dumps(non_tool), encoding="utf-8")
    with pytest.raises(ValueError, match="relation-source-is-not-tool"):
        validate_canonical_release_integrity(
            release, load_canonical_release_integrity_manifest(non_tool_manifest)
        )


def test_valid_manifest_mutation_is_rejected_without_matching_projection(
    tmp_path: Path,
) -> None:
    manifest_payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_payload["relations"][0]["evidence_refs"] = [
        manifest_payload["relations"][0]["evidence_refs"][0]
    ]
    manifest_payload["node_contracts"][0]["unit"] = "weeks"
    mutated = tmp_path / "mutated-manifest.json"
    mutated.write_text(json.dumps(manifest_payload), encoding="utf-8")

    failed = subprocess.run(
        _audit_command(tmp_path / "report.json", manifest=mutated),
        check=False,
        capture_output=True,
        text=True,
    )
    assert failed.returncode == 1
    assert failed.stdout == ""
    assert "weeks" not in failed.stderr
