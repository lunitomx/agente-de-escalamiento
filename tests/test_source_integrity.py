from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from validators.source_integrity import (
    SourceIntegrityError,
    build_source_integrity_receipt,
    render_source_integrity_json,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "sources/source-registry.yaml"
MANIFEST = ROOT / "sources/source-manifest.jsonl"
POLICY = ROOT / "governance/public-boundary.yaml"
SCRIPT = ROOT / "scripts/check_source_integrity.py"


def test_canonical_private_source_integrity_receipt_is_bounded() -> None:
    receipt = build_source_integrity_receipt(ROOT, REGISTRY, MANIFEST, POLICY)
    rendered = render_source_integrity_json(receipt)

    assert receipt.status == "pass"
    assert receipt.unit_count == 407
    assert receipt.source_artifacts_explicitly_denied is True
    assert receipt.private_only is True
    assert "Additional Praise" not in rendered
    assert "scaling_up_llamaparse" not in rendered


def test_integrity_fails_when_source_surfaces_lose_explicit_denial(
    tmp_path: Path,
) -> None:
    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    policy["path_rules"] = [
        rule for rule in policy["path_rules"] if rule["id"] != "deny.source_authority"
    ]
    altered = tmp_path / "public-boundary.yaml"
    altered.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")

    with pytest.raises(SourceIntegrityError, match="explicitly denied"):
        build_source_integrity_receipt(ROOT, REGISTRY, MANIFEST, altered)


def test_integrity_cli_emits_only_safe_receipt() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo",
            str(ROOT),
            "--registry",
            str(REGISTRY),
            "--manifest",
            str(MANIFEST),
            "--policy",
            str(POLICY),
            "--format",
            "json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert '"status": "pass"' in completed.stdout
    assert "Additional Praise" not in completed.stdout
    assert completed.stderr == ""
