from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

import pytest
from pydantic import ValidationError
import yaml

from validators.governance_contract import (
    closure_disposition_policy_hash,
    load_closure_disposition_policy,
)


ROOT = Path(__file__).resolve().parents[1]
CLOSURE_POLICY_PATH = ROOT / "governance/closure-dispositions.yaml"

EXPECTED_DISPOSITIONS = {
    "active": (False, False, True, True),
    "complete": (True, True, True, False),
    "unresolved/review-required": (False, False, True, False),
    "deferred/backlog": (False, False, True, False),
    "cancelled/absorbed": (True, False, False, False),
    "absorbed/descoped": (True, False, False, False),
    "superseded/discarded": (True, False, False, False),
    "deprecated/discarded": (True, False, False, False),
}


def _policy_data() -> dict[str, Any]:
    data = yaml.safe_load(CLOSURE_POLICY_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _write_policy(tmp_path: Path, data: Any) -> Path:
    path = tmp_path / "closure-dispositions.yaml"
    path.write_text(
        yaml.safe_dump(data, allow_unicode=False, sort_keys=False),
        encoding="utf-8",
    )
    return path


def test_canonical_closure_policy_is_strict_complete_and_stable() -> None:
    first = load_closure_disposition_policy(CLOSURE_POLICY_PATH)
    second = load_closure_disposition_policy(CLOSURE_POLICY_PATH)

    assert first.schema_version == 1
    assert [item.id for item in first.dispositions] == sorted(EXPECTED_DISPOSITIONS)
    assert {
        item.id: (
            item.terminal,
            item.completed,
            item.reviewable,
            item.activation_eligible,
        )
        for item in first.dispositions
    } == EXPECTED_DISPOSITIONS
    assert closure_disposition_policy_hash(first) == (
        closure_disposition_policy_hash(second)
    )
    assert len(closure_disposition_policy_hash(first)) == 64


@pytest.mark.parametrize(
    "mutator",
    [
        lambda data: data.update({"schema_version": 2}),
        lambda data: data.update({"unknown_root": True}),
        lambda data: data["dispositions"][0].update({"unknown": True}),
        lambda data: data["dispositions"][0].update({"terminal": None}),
        lambda data: data["dispositions"][0].pop("reviewable"),
        lambda data: data["dispositions"][1].update(
            {"id": data["dispositions"][0]["id"]}
        ),
        lambda data: data["dispositions"][0].update({"id": "Mixed/Case"}),
        lambda data: data["dispositions"][0].update({"id": "unsafe path"}),
        lambda data: data["dispositions"][1].update({"terminal": False}),
        lambda data: data["dispositions"][1].update({"reviewable": False}),
        lambda data: data["dispositions"][1].update({"activation_eligible": True}),
        lambda data: data["dispositions"][0].update({"terminal": True}),
    ],
)
def test_closure_policy_rejects_unknown_incomplete_or_contradictory_records(
    tmp_path: Path,
    mutator: Callable[[dict[str, Any]], None],
) -> None:
    data = deepcopy(_policy_data())
    mutator(data)

    with pytest.raises(ValidationError):
        load_closure_disposition_policy(_write_policy(tmp_path, data))


@pytest.mark.parametrize("data", [None, [], "active", {}])
def test_closure_policy_rejects_null_or_wrong_root_shapes(
    tmp_path: Path,
    data: Any,
) -> None:
    with pytest.raises(ValidationError):
        load_closure_disposition_policy(_write_policy(tmp_path, data))
