from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Callable

import pytest
from pydantic import ValidationError
import yaml

from validators.export import REQUIRED_SECTIONS, validate_export
from validators.public_boundary import load_public_boundary_policy
from validators.public_export import (
    ArtifactManifest,
    PublicExportPolicy,
    ThirdPartyInventory,
    build_package_metadata,
    load_public_export_policy,
    load_third_party_inventory,
    public_export_policy_hash,
    render_package_metadata,
    render_third_party_notices,
    third_party_inventory_hash,
    validate_export_selections,
)


ROOT = Path(__file__).resolve().parents[1]
EXPORT_POLICY_PATH = ROOT / "governance/public-export.yaml"
THIRD_PARTY_PATH = ROOT / "governance/third-party.yaml"
PUBLIC_BOUNDARY_PATH = ROOT / "governance/public-boundary.yaml"
LICENSE_PATH = ROOT / "LICENSE"


def _yaml_data(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_canonical_export_and_dependency_contracts_load_deterministically() -> None:
    first = load_public_export_policy(EXPORT_POLICY_PATH)
    second = load_public_export_policy(EXPORT_POLICY_PATH)
    inventory = load_third_party_inventory(THIRD_PARTY_PATH)

    assert first.schema_version == 1
    assert first.product.id == "escala"
    assert first.product.version == "1.0.0"
    assert first.source.required_ref == "explicit_full_head_commit"
    assert first.source.allowed_git_modes == ["100644", "100755"]
    assert first.local_only.runtime_mode == "local_machine_only"
    assert first.local_only.team_sharing == "ordinary_filesystem_documents_only"
    assert first.license.human_review_status == "required"
    assert first.license.approval_evidence_status == "absent"
    assert first.license.publication_authorized is False
    assert first.license.allowed_artifact_use == "internal_technical_validation_only"
    assert public_export_policy_hash(first) == public_export_policy_hash(second)
    assert len(public_export_policy_hash(first)) == 64
    assert third_party_inventory_hash(inventory) == first.bindings.third_party.sha256
    assert len(third_party_inventory_hash(inventory)) == 64
    assert len(inventory.entries) == 13
    assert [entry.id for entry in inventory.entries] == sorted(
        entry.id for entry in inventory.entries
    )


def test_canonical_selection_is_explicit_and_excludes_internal_families() -> None:
    policy = load_public_export_policy(EXPORT_POLICY_PATH)
    boundary = load_public_boundary_policy(PUBLIC_BOUNDARY_PATH)
    selection_paths = {selection.path for selection in policy.selections}

    assert {
        "LICENSE",
        "README.md",
        "install.sh",
        "pyproject.toml",
        "scripts/escala-server",
        "conocimiento",
        "escala-skills",
        "escala_server/static",
        "templates",
        "validators/export.py",
        "validators/session.py",
    } <= selection_paths
    assert not any(
        "/tests" in path or path.startswith("tests") for path in selection_paths
    )
    assert not any(
        path.startswith(
            (
                ".agents",
                ".claude",
                ".codex-plugin",
                ".raise",
                ".scaleup",
                "escala-agent",
                "governance",
                "packages",
                "work",
                "escala_server/data",
            )
        )
        for path in selection_paths
    )
    assert (
        not {
            "coaching/class_intake.py",
            "coaching/class_report.py",
            "coaching/pattern_extraction.py",
            "coaching/skill_deltas.py",
            "validators/epic_closure.py",
            "validators/exposure_inventory.py",
            "validators/governance_contract.py",
            "validators/public_boundary.py",
            "validators/public_export.py",
            "validators/repository_truth.py",
        }
        & selection_paths
    )

    validate_export_selections(policy, boundary)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda data: data.update({"unknown_root": True}),
        lambda data: data.update({"schema_version": 2}),
        lambda data: data["license"].update({"license_status": None}),
        lambda data: data["license"].update({"publication_authorized": True}),
        lambda data: data["local_only"].update({"hosted_product_service": "allowed"}),
        lambda data: data["source"].update({"allowed_git_modes": ["100644"]}),
        lambda data: data["selections"][0].update({"unknown": True}),
        lambda data: data["generated_paths"].update(
            {"manifest": data["generated_paths"]["package_metadata"]}
        ),
    ],
)
def test_export_policy_rejects_unknown_null_incomplete_or_contradictory_data(
    mutator: Callable[[dict[str, Any]], None],
) -> None:
    data = _yaml_data(EXPORT_POLICY_PATH)
    mutator(data)

    with pytest.raises(ValidationError):
        PublicExportPolicy.model_validate(data)


@pytest.mark.parametrize("case", ["casefold", "file_under_tree", "nested_tree"])
def test_export_policy_rejects_duplicate_or_overlapping_selections(case: str) -> None:
    data = _yaml_data(EXPORT_POLICY_PATH)
    selections = data["selections"]
    assert isinstance(selections, list)
    if case == "casefold":
        selections.append(
            {"path": "readme.md", "kind": "file", "role": "operator_documentation"}
        )
    elif case == "file_under_tree":
        selections.append(
            {
                "path": "conocimiento/private.yaml",
                "kind": "file",
                "role": "business_knowledge",
            }
        )
    else:
        selections.append(
            {
                "path": "escala_server/static/shared",
                "kind": "tree",
                "role": "local_runtime",
            }
        )

    with pytest.raises(ValidationError):
        PublicExportPolicy.model_validate(data)


@pytest.mark.parametrize(
    "unsafe_path",
    ["/private/file", "../private", "safe/../private", "safe\\private", "tree/**"],
)
def test_export_policy_rejects_unsafe_selection_paths(unsafe_path: str) -> None:
    data = _yaml_data(EXPORT_POLICY_PATH)
    data["selections"][0]["path"] = unsafe_path

    with pytest.raises(ValidationError):
        PublicExportPolicy.model_validate(data)


@pytest.mark.parametrize(
    "case", ["extra", "duplicate", "missing_parent", "cycle", "import"]
)
def test_third_party_inventory_rejects_incomplete_or_ambiguous_graph(case: str) -> None:
    data = _yaml_data(THIRD_PARTY_PATH)
    entries = data["entries"]
    assert isinstance(entries, list)
    if case == "extra":
        entries[0]["unknown"] = True
    elif case == "duplicate":
        entries[1]["id"] = entries[0]["id"]
    elif case == "missing_parent":
        target = next(
            entry for entry in entries if entry["relationship"] == "transitive"
        )
        target["parents"] = ["missing-dependency"]
    elif case == "cycle":
        pydantic = next(entry for entry in entries if entry["id"] == "pydantic")
        annotated = next(entry for entry in entries if entry["id"] == "annotated-types")
        pydantic["relationship"] = "transitive"
        pydantic["parents"] = ["annotated-types"]
        annotated["parents"] = ["pydantic"]
    else:
        pydantic = next(entry for entry in entries if entry["id"] == "pydantic")
        pyyaml = next(entry for entry in entries if entry["id"] == "pyyaml")
        pyyaml["import_names"] = list(pydantic["import_names"])

    with pytest.raises(ValidationError):
        ThirdPartyInventory.model_validate(data)


def test_package_metadata_and_notices_are_deterministic_and_truthful() -> None:
    policy = load_public_export_policy(EXPORT_POLICY_PATH)
    inventory = load_third_party_inventory(THIRD_PARTY_PATH)
    metadata = build_package_metadata(
        policy,
        inventory,
        source_commit="a" * 40,
    )

    first_json = render_package_metadata(metadata)
    second_json = render_package_metadata(metadata)
    first_notices = render_third_party_notices(inventory)
    second_notices = render_third_party_notices(inventory)

    assert first_json == second_json
    assert first_notices == second_notices
    payload = json.loads(first_json)
    assert payload["technical_artifact_status"] == "not_verified"
    assert payload["human_legal_review_status"] == "required"
    assert payload["publication_authorized"] is False
    assert payload["source_commit"] == "a" * 40
    assert "Chart.js" in first_notices
    assert "@kurkle/color" in first_notices
    assert "MIT" in first_notices
    assert "http://" not in first_notices
    assert "https://" not in first_notices


def test_artifact_manifest_rejects_self_reference_or_unsorted_entries() -> None:
    payload = {
        "schema_version": 1,
        "product_id": "escala",
        "product_version": "1.0.0",
        "source_commit": "a" * 40,
        "export_policy_sha256": "b" * 64,
        "public_boundary_policy_sha256": "c" * 64,
        "third_party_inventory_sha256": "d" * 64,
        "entries": [
            {
                "path": "README.md",
                "mode": "100644",
                "size_bytes": 10,
                "sha256": "e" * 64,
            }
        ],
    }
    manifest = ArtifactManifest.model_validate(payload)
    assert manifest.entries[0].path == "README.md"

    self_referential = deepcopy(payload)
    self_referential["entries"][0]["path"] = "ESCALA-MANIFEST.json"
    with pytest.raises(ValidationError):
        ArtifactManifest.model_validate(self_referential)

    unsorted = deepcopy(payload)
    unsorted["entries"].append(
        {
            "path": "LICENSE",
            "mode": "100644",
            "size_bytes": 10,
            "sha256": "f" * 64,
        }
    )
    with pytest.raises(ValidationError):
        ArtifactManifest.model_validate(unsorted)


def test_interim_license_has_no_educational_or_noncommercial_contradiction() -> None:
    content = LICENSE_PATH.read_text(encoding="utf-8")

    assert "Todos los derechos reservados" in content
    assert "revisión legal" in content
    assert "publicación" in content
    assert "exclusivamente con fines educativos" not in content
    assert "No está autorizado el uso comercial" not in content
    assert "recurso educativo abierto" not in content


def test_action_plan_export_validator_keeps_its_existing_contract(
    tmp_path: Path,
) -> None:
    action_plan = tmp_path / "action-plan.md"
    action_plan.write_text("\n".join(REQUIRED_SECTIONS), encoding="utf-8")

    assert validate_export(action_plan) == []
    assert validate_export(tmp_path / "missing.md")
