#!/usr/bin/env python3
"""Audit the authorized S64.1 release with its integrity and coverage receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.ontology_v2 import (  # noqa: E402
    CoverageMatrix,
    load_canonical_release,
    load_canonical_release_integrity_manifest,
    load_coverage_matrix,
    validate_canonical_release_integrity,
    validate_coverage_matrix,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_authorized_release(
    release_path: Path, manifest_path: Path, matrix_path: Path
) -> dict[str, Any]:
    """Return a bounded PASS report or fail closed without source inspection."""
    release = load_canonical_release(release_path)
    manifest = load_canonical_release_integrity_manifest(manifest_path)
    matrix: CoverageMatrix = load_coverage_matrix(matrix_path)
    receipt = validate_canonical_release_integrity(release, manifest)
    if receipt.status != "pass" or receipt.relations_state != "relations-validated":
        raise ValueError("authorized release integrity is not passing")
    validate_coverage_matrix(matrix, release)

    mapped_count = sum(record.status == "mapped" for record in matrix.records)
    review_required_count = sum(
        record.status == "review-required" for record in matrix.records
    )
    excluded_count = sum(record.status == "excluded" for record in matrix.records)
    if (
        mapped_count != receipt.node_count
        or review_required_count != receipt.exclusion_count
    ):
        raise ValueError("authorized release coverage partition is inconsistent")
    if receipt.node_count != 76 or review_required_count != 3 or excluded_count != 0:
        raise ValueError("authorized release has an unexpected approved partition")

    return {
        "audit_id": "s64.4",
        "coverage_matrix_id": matrix.matrix_id,
        "coverage_matrix_sha256": _sha256(matrix_path),
        "excluded_count": excluded_count,
        "exclusion_count": receipt.exclusion_count,
        "integrity_status": receipt.status,
        "mapped_count": mapped_count,
        "manifest_sha256": _sha256(manifest_path),
        "node_count": receipt.node_count,
        "qualified_metric_count": receipt.qualified_metric_count,
        "qualified_rule_count": receipt.qualified_rule_count,
        "qualified_tool_count": receipt.qualified_tool_count,
        "relation_count": receipt.relation_count,
        "release_id": receipt.release_id,
        "release_sha256": _sha256(release_path),
        "review_required_count": review_required_count,
        "schema_version": 1,
        "scope": "authorized-release-only",
        "status": "pass",
    }


def render_fidelity_report(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        rendered = render_fidelity_report(
            audit_authorized_release(args.release, args.manifest, args.matrix)
        )
        if args.check:
            return 0 if args.report.read_text(encoding="utf-8") == rendered else 1
        args.report.write_text(rendered, encoding="utf-8")
        return 0
    except Exception:
        print(
            "canonical fidelity audit: unable to produce a safe passing report",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
