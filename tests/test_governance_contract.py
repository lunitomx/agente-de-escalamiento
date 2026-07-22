from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

import pytest
from pydantic import ValidationError
import yaml

from validators.governance_contract import (
    EpicIdentityResolutionCode,
    closure_disposition_policy_hash,
    epic_identity_policy_hash,
    load_closure_disposition_policy,
    load_epic_identity_policy,
    load_governance_contract,
    resolve_epic_identity,
    validate_epic_identity_inventory,
)


ROOT = Path(__file__).resolve().parents[1]
CLOSURE_POLICY_PATH = ROOT / "governance/closure-dispositions.yaml"
IDENTITY_POLICY_PATH = ROOT / "governance/epic-identities.yaml"

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

EXPECTED_IDENTITIES = {
    "E1801": (
        "work/epics/e1801-class-to-skill-learning-loop",
        "complete",
        "work/epics/e18-class-to-skill-learning-loop",
    ),
    "E1802": (
        "work/epics/e1802-escala-server",
        "complete",
        "work/epics/e18-escala-server",
    ),
    "E1901": (
        "work/epics/e1901-book-ingestion",
        "deferred/backlog",
        "work/epics/e19-book-ingestion",
    ),
    "E1902": (
        "work/epics/e1902-strategy-core-skills",
        "superseded/discarded",
        "work/epics/e19-strategy-core-skills",
    ),
    "E2001": (
        "work/epics/e2001-contextual-skills",
        "complete",
        "work/epics/e20-contextual-skills",
    ),
    "E2002": (
        "work/epics/e2002-voice-of-customer-evidence-capture",
        "superseded/discarded",
        "work/epics/e20-voice-of-customer-evidence-capture",
    ),
    "E2101": (
        "work/epics/e2101-transcript-intelligence-for-escala",
        "deprecated/discarded",
        "work/epics/e21-transcript-intelligence-for-escala",
    ),
    "E2102": (
        "work/epics/e2102-verne-board-member",
        "complete",
        "work/epics/e21-verne-board-member",
    ),
    "E2201": (
        "work/epics/e2201-validation-drift-governance",
        "superseded/discarded",
        "work/epics/e22-validation-drift-governance",
    ),
    "E2202": (
        "work/epics/e2202-verne-audit",
        "absorbed/descoped",
        "work/epics/e22-verne-audit",
    ),
}

EXPECTED_AMBIGUITIES = {
    "E18": ("E1801", "E1802"),
    "E19": ("E1901", "E1902"),
    "E20": ("E2001", "E2002"),
    "E21": ("E2101", "E2102"),
    "E22": ("E2201", "E2202"),
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


def _identity_data() -> dict[str, Any]:
    data = yaml.safe_load(IDENTITY_POLICY_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _write_identity_policy(tmp_path: Path, data: Any) -> Path:
    path = tmp_path / "epic-identities.yaml"
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


def test_canonical_identity_policy_is_complete_unique_and_stable() -> None:
    first = load_epic_identity_policy(IDENTITY_POLICY_PATH)
    second = load_epic_identity_policy(IDENTITY_POLICY_PATH)

    assert first.schema_version == 1
    assert {
        item.canonical_id: (
            item.folder,
            item.closure_disposition,
            item.legacy_folder_aliases[0],
        )
        for item in first.identities
    } == EXPECTED_IDENTITIES
    assert {
        item.alias: tuple(item.canonical_ids) for item in first.ambiguous_aliases
    } == EXPECTED_AMBIGUITIES
    assert epic_identity_policy_hash(first) == epic_identity_policy_hash(second)
    assert len(epic_identity_policy_hash(first)) == 64


@pytest.mark.parametrize(
    "mutator",
    [
        lambda data: data.update({"schema_version": 2}),
        lambda data: data.update({"unknown_root": True}),
        lambda data: data["identities"][0].update({"unknown": True}),
        lambda data: data["identities"][0].update({"canonical_id": None}),
        lambda data: data["identities"][1].update(
            {"canonical_id": data["identities"][0]["canonical_id"]}
        ),
        lambda data: data["identities"][1].update(
            {"folder": data["identities"][0]["folder"]}
        ),
        lambda data: data["identities"][1].update(
            {"legacy_folder_aliases": data["identities"][0]["legacy_folder_aliases"]}
        ),
        lambda data: data["identities"][0].update({"folder": "../unsafe"}),
        lambda data: data["identities"][0].update(
            {"folder": "work/epics/e9999-wrong-id"}
        ),
        lambda data: data["ambiguous_aliases"][1].update(
            {"alias": data["ambiguous_aliases"][0]["alias"]}
        ),
        lambda data: data["ambiguous_aliases"][0].update(
            {"canonical_ids": ["E1801", "E9999"]}
        ),
        lambda data: data["ambiguous_aliases"][0].update({"canonical_ids": ["E1801"]}),
        lambda data: data["ambiguous_aliases"].pop(),
    ],
)
def test_identity_policy_rejects_unknown_duplicate_unsafe_or_incomplete_maps(
    tmp_path: Path,
    mutator: Callable[[dict[str, Any]], None],
) -> None:
    data = deepcopy(_identity_data())
    mutator(data)

    with pytest.raises(ValidationError):
        load_epic_identity_policy(_write_identity_policy(tmp_path, data))


def test_governance_contract_rejects_unknown_cross_policy_disposition(
    tmp_path: Path,
) -> None:
    data = deepcopy(_identity_data())
    data["identities"][0]["closure_disposition"] = "unknown/disposition"

    with pytest.raises(ValidationError):
        load_governance_contract(
            CLOSURE_POLICY_PATH,
            _write_identity_policy(tmp_path, data),
        )


@pytest.mark.parametrize(
    ("reference", "canonical_id"),
    [(canonical_id, canonical_id) for canonical_id in sorted(EXPECTED_IDENTITIES)]
    + [
        (folder, canonical_id)
        for canonical_id, (folder, _, _) in sorted(EXPECTED_IDENTITIES.items())
    ]
    + [
        (legacy, canonical_id)
        for canonical_id, (_, _, legacy) in sorted(EXPECTED_IDENTITIES.items())
    ],
)
def test_identity_resolution_accepts_only_exact_unique_references(
    reference: str,
    canonical_id: str,
) -> None:
    contract = load_governance_contract(CLOSURE_POLICY_PATH, IDENTITY_POLICY_PATH)

    result = resolve_epic_identity(contract, reference)

    assert result.code is EpicIdentityResolutionCode.RESOLVED
    assert result.canonical_id == canonical_id
    assert result.candidates == []


@pytest.mark.parametrize(
    ("reference", "candidates"),
    sorted(EXPECTED_AMBIGUITIES.items()),
)
def test_bare_legacy_ids_are_explicitly_ambiguous(
    reference: str,
    candidates: tuple[str, str],
) -> None:
    contract = load_governance_contract(CLOSURE_POLICY_PATH, IDENTITY_POLICY_PATH)

    result = resolve_epic_identity(contract, reference.lower())

    assert result.code is EpicIdentityResolutionCode.AMBIGUOUS
    assert result.canonical_id is None
    assert result.candidates == list(candidates)


def test_unknown_safe_reference_fails_closed_without_first_match() -> None:
    contract = load_governance_contract(CLOSURE_POLICY_PATH, IDENTITY_POLICY_PATH)

    result = resolve_epic_identity(contract, "E9999")

    assert result.code is EpicIdentityResolutionCode.UNKNOWN
    assert result.canonical_id is None
    assert result.candidates == []


@pytest.mark.parametrize(
    "reference",
    ["", "../E1801", "/work/epics/e1801-x", "E18 maybe", "https://invalid"],
)
def test_unsafe_identity_references_are_rejected(reference: str) -> None:
    contract = load_governance_contract(CLOSURE_POLICY_PATH, IDENTITY_POLICY_PATH)

    with pytest.raises(ValueError):
        resolve_epic_identity(contract, reference)


def test_real_identity_inventory_has_all_ten_canonical_scopes_only() -> None:
    contract = load_governance_contract(CLOSURE_POLICY_PATH, IDENTITY_POLICY_PATH)

    inventory = validate_epic_identity_inventory(ROOT, contract)

    assert inventory.canonical_ids == sorted(EXPECTED_IDENTITIES)
    assert inventory.canonical_scope_paths == [
        f"{folder}/scope.md" for folder, _, _ in sorted(EXPECTED_IDENTITIES.values())
    ]
    assert inventory.legacy_scope_paths_present == []
    assert inventory.duplicate_graph_ids == []
