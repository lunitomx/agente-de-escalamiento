"""S67.4 proves one portable core and a bounded alias migration layer."""

from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from adapters.codex.build_adapter import build_codex_adapter
from scripts.refresh_legacy_skill_aliases import expected_files
from validators.adapter_parity import (
    REPORT_PATH,
    build_parity_report,
    validate_claude_adapter,
    validate_codex_bundle,
    validate_legacy_migration,
    is_exact_legacy_redirect,
    validate_parity_report,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "capabilities" / "mvp" / "catalog.json"
SCRIPT = ROOT / "scripts" / "verify_s67_4_parity.py"


def test_versioned_parity_report_covers_exactly_the_six_portable_routes() -> None:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert validate_parity_report(report) == ()
    assert report == build_parity_report()
    assert report["public_entrypoint"] == "escala"
    assert len(report["capabilities"]) == 6
    assert all(
        set(capability)
        == {
            "aliases",
            "capability_id",
            "evidence_kinds",
            "intent",
            "lifecycle",
            "procedure_id",
            "specialist_profiles",
        }
        for capability in report["capabilities"]
    )


def test_parity_validation_fails_closed_when_a_route_is_edited() -> None:
    stale = deepcopy(build_parity_report())
    stale["capabilities"][0]["procedure_id"] = "procedure.unapproved"

    assert validate_parity_report(stale) == ("parity_report_drift",)


def test_codex_bundle_and_claude_references_resolve_to_the_same_core(
    tmp_path: Path,
) -> None:
    report = build_parity_report()
    destination = tmp_path / "install" / "codex"
    destination.parent.mkdir()
    build_codex_adapter(
        catalog_path=CATALOG,
        output=destination,
        allowed_root=destination.parent,
    )

    assert validate_codex_bundle(destination, report) == ()
    assert validate_claude_adapter(report) == ()
    assert sorted(
        path.parent.name for path in (destination / "skills").glob("*/SKILL.md")
    ) == ["escala"]


def test_legacy_wrapper_rejects_any_extra_logic() -> None:
    expected = next(iter(expected_files().values()))

    assert is_exact_legacy_redirect(expected, expected)
    assert not is_exact_legacy_redirect(
        expected + "\nAplica otra metodología.\n", expected
    )


def test_legacy_migration_is_internal_and_has_no_second_implementation() -> None:
    report = build_parity_report()

    assert validate_legacy_migration(report) == ()
    migration = report["migration"]
    assert migration["catalog_alias_count"] == 39
    assert migration["materialized_wrapper_count"] == 42
    assert migration["public_aliases"] == []
    assert migration["historical_router"] == {
        "catalog": "escala-skills/catalog.yaml",
        "role": "legacy-alias-resolution-only",
    }


def test_parity_script_rejects_report_drift() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "S67.4 parity report synchronized: 6 capabilities" in completed.stdout
