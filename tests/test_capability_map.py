"""S67.1 contracts for the source-safe internal MVP capability map."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from validators.capability_map import (
    AuthorizedEvidence,
    CapabilityMapError,
    load_capability_map,
    route_capability,
    validate_capability_map,
)
from validators.procedure_compiler import MVP_PROCEDURE_IDS


ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "capabilities" / "mvp" / "catalog.json"


def _evidence(*kinds: str) -> tuple[AuthorizedEvidence, ...]:
    return tuple(
        AuthorizedEvidence(
            kind=kind,
            receipt=f"receipt.{index:03d}-{kind}",
            status="confirmed",
        )
        for index, kind in enumerate(kinds, start=1)
    )


def test_map_is_closed_to_exactly_six_compiled_mvp_interventions() -> None:
    capability_map = load_capability_map(MAP_PATH)

    assert validate_capability_map(capability_map) == ()
    assert {binding.procedure_id for binding in capability_map.capabilities} == set(
        MVP_PROCEDURE_IDS
    )
    assert len(capability_map.capabilities) == 6
    assert all(
        "cash-tool" not in binding.procedure_id
        for binding in capability_map.capabilities
    )


def test_route_is_explainable_and_carries_only_compiled_evidence() -> None:
    route = route_capability(
        "build-vision-summary",
        _evidence("organization-context", "strategy-evidence"),
    )

    assert route.capability_id == "capability.build-vision-summary"
    assert route.procedure_id == "procedure.build-vision-summary"
    assert route.reason == "intent:build-vision-summary"
    assert route.lifecycle[0] == "route"
    assert route.lifecycle[-1] == "handoff"
    assert route.specialist_profile_ids == ("specialist.strategy.v1",)
    assert route.evidence_refs
    assert all(
        reference.startswith("digest.sha256.") for reference in route.evidence_refs
    )


def test_unknown_intent_and_missing_or_unknown_evidence_fail_closed() -> None:
    with pytest.raises(CapabilityMapError, match="unknown_intent"):
        route_capability("cash-tool", _evidence("company-context", "decision-evidence"))
    with pytest.raises(CapabilityMapError, match="evidence_required"):
        route_capability("diagnose-primary-constraint", ())
    with pytest.raises(CapabilityMapError, match="evidence_missing:company-context"):
        route_capability("diagnose-primary-constraint", _evidence("decision-evidence"))
    with pytest.raises(ValueError, match="status"):
        AuthorizedEvidence(
            kind="company-context",
            receipt="receipt.001-company-context",
            status="unknown",  # type: ignore[arg-type]
        )


def test_aliases_only_resolve_to_the_same_capability_without_own_logic() -> None:
    direct = route_capability(
        "install-meeting-rhythm",
        _evidence("execution-context", "existing-rhythm"),
    )
    via_alias = route_capability(
        "meeting-rhythm",
        _evidence("execution-context", "existing-rhythm"),
    )

    assert via_alias.capability_id == direct.capability_id
    assert via_alias.procedure_id == direct.procedure_id
    assert via_alias.evidence_refs == direct.evidence_refs
    assert via_alias.reason == "alias:meeting-rhythm"
    assert via_alias.resolved_from_alias == "meeting-rhythm"


def test_four_specialist_profiles_use_e45_definitions_and_no_binding_overlaps() -> None:
    capability_map = load_capability_map(MAP_PATH)

    assert {profile.area for profile in capability_map.specialist_profiles} == {
        "cash",
        "execution",
        "people",
        "strategy",
    }
    assert all(
        profile.kind == "role-definition"
        for profile in capability_map.specialist_profiles
    )
    assert all(
        profile.contract_ref == f"e45.specialist.{profile.area}.v1"
        for profile in capability_map.specialist_profiles
    )
    assert all(
        len(binding.specialist_profiles) == len(set(binding.specialist_profiles))
        for binding in capability_map.capabilities
    )


def test_duplicate_alias_or_wrong_evidence_kind_is_rejected_before_routing(
    tmp_path: Path,
) -> None:
    raw = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    raw["capabilities"][1]["aliases"][0] = raw["capabilities"][0]["aliases"][0]
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(CapabilityMapError, match="unambiguous"):
        load_capability_map(invalid)

    raw = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    raw["capabilities"][0]["evidence_kinds"] = ["decision-evidence"]
    invalid.write_text(json.dumps(raw), encoding="utf-8")
    capability_map = load_capability_map(invalid)
    assert validate_capability_map(capability_map) == (
        "evidence_kind_mismatch:procedure.diagnose-primary-constraint",
    )
