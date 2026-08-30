from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from scripts.audit_canonical_fidelity import audit_authorized_release


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "ontology/v2/releases/s64.1.json"
MANIFEST = ROOT / "ontology/v2/releases/s64.4.integrity-manifest.json"
MATRIX = ROOT / "ontology/v2/releases/s64.3.coverage.json"
REPORT = ROOT / "ontology/v2/releases/s64.4.fidelity-report.json"
SCRIPT = ROOT / "scripts/audit_canonical_fidelity.py"


def _audit_command(
    report: Path, manifest: Path = MANIFEST, matrix: Path = MATRIX
) -> list[str]:
    return [
        sys.executable,
        str(SCRIPT),
        "--release",
        str(RELEASE),
        "--manifest",
        str(manifest),
        "--matrix",
        str(matrix),
        "--report",
        str(report),
    ]


def test_authorized_release_audit_is_pass_and_exact() -> None:
    report = audit_authorized_release(RELEASE, MANIFEST, MATRIX)

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
            _audit_command(tmp_path / "report.json", manifest, matrix),
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 1
        assert completed.stdout == ""
        assert "canonical fidelity audit" in completed.stderr
        assert "unassessed" not in completed.stderr
        assert "0" * 64 not in completed.stderr
