from __future__ import annotations
from pathlib import Path
import json
import subprocess
import sys
from validators.e6_migration import (
    load_and_validate_e6_migration_map,
)
from validators.ontology_v2 import load_canonical_release

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "ontology/v2/e6-migration-map.json"
SCRIPT = ROOT / "scripts/check_e6_migration_map.py"
RELEASE = ROOT / "ontology/v2/releases/s64.1.json"


def test_map_covers_every_legacy_yaml_with_explicit_disposition() -> None:
    migration_map = load_and_validate_e6_migration_map(ROOT, MAP)
    assert len(migration_map.entries) == 82
    assert (
        sum(e.disposition == "await-domain-evidence" for e in migration_map.entries)
        == 78
    )
    assert (
        sum(e.disposition == "support-contract-not-node" for e in migration_map.entries)
        == 4
    )
    assert all(e.canonical_id is None for e in migration_map.entries)


def test_map_detects_legacy_mutation(tmp_path: Path) -> None:
    data = json.loads(MAP.read_text(encoding="utf-8"))
    data["entries"][0]["sha256"] = "0" * 64
    altered = tmp_path / "map.json"
    altered.write_text(json.dumps(data), encoding="utf-8")
    try:
        load_and_validate_e6_migration_map(ROOT, altered)
    except ValueError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError("expected mismatch")


def test_cli_emits_count_only_receipt() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(ROOT), "--map", str(MAP)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Legacy assets: 82" in result.stdout
    assert "cash-acceleration" not in result.stdout


def test_s64_1_release_coexists_without_promoting_e6_entries() -> None:
    migration_map = load_and_validate_e6_migration_map(ROOT, MAP)
    release = load_canonical_release(RELEASE)
    legacy_ids = {entry.legacy_id for entry in migration_map.entries}
    promoted = {node.canonical_id for node in release.nodes}
    assert len(migration_map.entries) == 82
    assert all(entry.canonical_id is None for entry in migration_map.entries)
    assert legacy_ids.isdisjoint(promoted)
