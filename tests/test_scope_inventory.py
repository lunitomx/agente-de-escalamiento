from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from validators.governance_contract import load_closure_disposition_policy
from validators.scope_inventory import (
    ScopeInventoryError,
    load_scope_inventory,
    validate_scope_inventory,
)

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "governance/scope-inventory.yaml"
CLOSURE_PATH = ROOT / "governance/closure-dispositions.yaml"


def _data() -> dict[str, object]:
    value = yaml.safe_load(INVENTORY_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write(tmp_path: Path, value: dict[str, object]) -> Path:
    path = tmp_path / "scope-inventory.yaml"
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    return path


def test_current_scope_inventory_is_exhaustive() -> None:
    validate_scope_inventory(
        ROOT,
        load_scope_inventory(INVENTORY_PATH),
        load_closure_disposition_policy(CLOSURE_PATH),
    )


def test_missing_legacy_scope_fails_closed(tmp_path: Path) -> None:
    value = deepcopy(_data())
    entries = value["legacy_scopes"]
    assert isinstance(entries, list)
    entries.pop()
    inventory = load_scope_inventory(_write(tmp_path, value))

    with pytest.raises(ScopeInventoryError, match="does not classify"):
        validate_scope_inventory(
            ROOT, inventory, load_closure_disposition_policy(CLOSURE_PATH)
        )


def test_duplicate_or_unsafe_legacy_scope_is_rejected(tmp_path: Path) -> None:
    value = deepcopy(_data())
    entries = value["legacy_scopes"]
    assert isinstance(entries, list)
    entries.append(deepcopy(entries[0]))
    with pytest.raises(ValueError, match="duplicate"):
        load_scope_inventory(_write(tmp_path, value))

    value = deepcopy(_data())
    entries = value["legacy_scopes"]
    assert isinstance(entries, list)
    entries[0]["path"] = "work/epics/e1-test/../scope.md"
    with pytest.raises(ValueError, match="unsafe"):
        load_scope_inventory(_write(tmp_path, value))
