from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

from validators.ontology_v2 import (
    CanonicalReleaseIntegrityManifest,
    load_canonical_release,
    render_canonical_release_integrity_receipt,
    validate_canonical_release_integrity,
)


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "ontology/v2/releases/s64.1.json"
SCRIPT = ROOT / "scripts/check_canonical_release_integrity.py"


def test_s64_1_without_manifest_reports_no_relations_published() -> None:
    receipt = validate_canonical_release_integrity(load_canonical_release(RELEASE))

    assert receipt.status == "not-assessed"
    assert receipt.relations_state == "no-relations-published"
    assert receipt.relation_count == 0
    assert receipt.qualified_tool_count == 0
    assert "canonical_name" not in render_canonical_release_integrity_receipt(receipt)


def test_manifest_rejects_hanging_and_duplicate_relations() -> None:
    release = load_canonical_release(RELEASE)
    base = {
        "schema_version": 1,
        "release_id": "s64.1",
        "relations": [
            {
                "source_id": "tool.face",
                "target_id": "decision.people",
                "relation_type": "belongs-to-decision",
                "evidence_refs": [
                    "digest.sha256.04a4a553f240a712c831cee697661ebe6e685fef16b9aece75e515ade87ad0c6"
                ],
            }
        ],
        "node_contracts": [],
    }
    with pytest.raises(ValueError, match="published-node-missing-integrity-contract"):
        validate_canonical_release_integrity(
            release, CanonicalReleaseIntegrityManifest.model_validate(base)
        )
    with pytest.raises(ValueError, match="duplicate release relation"):
        CanonicalReleaseIntegrityManifest.model_validate(
            {**base, "relations": [base["relations"][0], base["relations"][0]]}
        )
    unknown = {
        **base,
        "relations": [
            {
                "source_id": "tool.face",
                "target_id": "decision.unknown",
                "relation_type": "belongs-to-decision",
                "evidence_refs": [
                    "digest.sha256.04a4a553f240a712c831cee697661ebe6e685fef16b9aece75e515ade87ad0c6"
                ],
            }
        ],
    }
    with pytest.raises(ValueError, match="relation-references-unknown-node"):
        validate_canonical_release_integrity(
            release, CanonicalReleaseIntegrityManifest.model_validate(unknown)
        )


def test_manifest_requires_every_qualified_node_and_kind_specific_metadata() -> None:
    release = load_canonical_release(RELEASE)
    contracts = [
        {
            "canonical_id": node.canonical_id,
            "decision_ids": ["decision.people"] if node.kind.value == "tool" else [],
            "evidence_refs": node.evidence_refs if node.kind.value == "rule" else [],
            "definition_ref": node.evidence_refs[0]
            if node.kind.value == "metric"
            else None,
            "unit": "days" if node.kind.value == "metric" else None,
        }
        for node in release.nodes
        if node.kind.value in {"tool", "rule", "metric"}
    ]
    relations = [
        {
            "source_id": node.canonical_id,
            "target_id": "decision.people",
            "relation_type": "belongs-to-decision",
            "evidence_refs": node.evidence_refs,
        }
        for node in release.nodes
        if node.kind.value == "tool"
    ]
    manifest = CanonicalReleaseIntegrityManifest.model_validate(
        {
            "schema_version": 1,
            "release_id": "s64.1",
            "relations": relations,
            "node_contracts": contracts,
        }
    )
    receipt = validate_canonical_release_integrity(release, manifest)
    assert receipt.relations_state == "relations-validated"
    assert receipt.qualified_tool_count == 9
    assert receipt.qualified_rule_count == 7
    assert receipt.qualified_metric_count == 1

    by_id = {
        contract["canonical_id"]: index for index, contract in enumerate(contracts)
    }
    for canonical_id, field, expected in (
        ("tool.face", "decision_ids", "tool-missing-decision"),
        ("rule.face-gap-signals", "evidence_refs", "rule-missing-evidence"),
        ("metric.cash-conversion-cycle", "definition_ref", "metric-missing-definition"),
        ("metric.cash-conversion-cycle", "unit", "metric-missing-unit"),
    ):
        invalid = [dict(contract) for contract in contracts]
        invalid[by_id[canonical_id]][field] = (
            [] if field.endswith("ids") or field.endswith("refs") else None
        )
        candidate = CanonicalReleaseIntegrityManifest.model_validate(
            {
                "schema_version": 1,
                "release_id": "s64.1",
                "relations": relations,
                "node_contracts": invalid,
            }
        )
        with pytest.raises(ValueError, match=expected):
            validate_canonical_release_integrity(release, candidate)

    missing_relation = CanonicalReleaseIntegrityManifest.model_validate(
        {
            "schema_version": 1,
            "release_id": "s64.1",
            "relations": relations[1:],
            "node_contracts": contracts,
        }
    )
    with pytest.raises(ValueError, match="relations-do-not-exactly-match-contracts"):
        validate_canonical_release_integrity(release, missing_relation)

    unknown_evidence = [dict(contract) for contract in contracts]
    unknown_evidence[by_id["rule.face-gap-signals"]]["evidence_refs"] = [
        "digest.sha256.unknown"
    ]
    with pytest.raises(ValueError, match="rule-references-unknown-evidence"):
        validate_canonical_release_integrity(
            release,
            CanonicalReleaseIntegrityManifest.model_validate(
                {
                    "schema_version": 1,
                    "release_id": "s64.1",
                    "relations": relations,
                    "node_contracts": unknown_evidence,
                }
            ),
        )

    for canonical_id, field, value, expected in (
        (
            "tool.face",
            "evidence_refs",
            ["digest.sha256.unrelated"],
            "tool-has-inapplicable-field",
        ),
        (
            "metric.cash-conversion-cycle",
            "evidence_refs",
            ["digest.sha256.unrelated"],
            "metric-has-inapplicable-field",
        ),
    ):
        invalid = [dict(contract) for contract in contracts]
        invalid[by_id[canonical_id]][field] = value
        with pytest.raises(ValueError, match=expected):
            validate_canonical_release_integrity(
                release,
                CanonicalReleaseIntegrityManifest.model_validate(
                    {
                        "schema_version": 1,
                        "release_id": "s64.1",
                        "relations": relations,
                        "node_contracts": invalid,
                    }
                ),
            )


def test_cli_receipt_is_bounded_and_manifest_errors_do_not_echo_input(
    tmp_path: Path,
) -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--release", str(RELEASE), "--format", "json"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert '"status": "not-assessed"' in completed.stdout
    assert '"relations_state": "no-relations-published"' in completed.stdout
    assert "Who What When" not in completed.stdout
    assert completed.stderr == ""

    malformed = tmp_path / "manifest.json"
    malformed.write_text(
        '{"schema_version": 1, "release_id": "s64.1", "working_text": "private"}',
        encoding="utf-8",
    )
    failed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--release",
            str(RELEASE),
            "--relations",
            str(malformed),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert failed.returncode == 1
    assert failed.stdout == ""
    assert "private" not in failed.stderr
