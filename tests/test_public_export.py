from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
from typing import Any, Callable

import pytest
from pydantic import ValidationError
import yaml

from validators.export import REQUIRED_SECTIONS, validate_export
from validators.public_boundary import load_public_boundary_policy
from validators.public_export import (
    ArtifactManifest,
    ArtifactRole,
    ExportBuildFailure,
    ExportSourceSelection,
    PublicExportPolicy,
    SelectionKind,
    ThirdPartyInventory,
    build_public_export,
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


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return completed.stdout.strip()


def _write_fixture_policy(
    repository: Path,
    selections: list[dict[str, str]],
) -> None:
    policy_data = _yaml_data(EXPORT_POLICY_PATH)
    policy_data["selections"] = selections
    governance = repository / "governance"
    governance.mkdir(parents=True, exist_ok=True)
    (governance / "public-export.yaml").write_text(
        yaml.safe_dump(policy_data, sort_keys=False),
        encoding="utf-8",
    )
    (governance / "third-party.yaml").write_text(
        THIRD_PARTY_PATH.read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def _create_git_fixture(
    tmp_path: Path,
    *,
    selections: list[dict[str, str]] | None = None,
) -> tuple[Path, str, PublicExportPolicy, ThirdPartyInventory]:
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init", "--quiet")
    _git(repository, "config", "user.email", "tests@example.invalid")
    _git(repository, "config", "user.name", "ESCALA Tests")
    _git(repository, "config", "core.filemode", "true")
    (repository / "README.md").write_bytes(b"committed product\n")
    executable = repository / "bin/run"
    executable.parent.mkdir()
    executable.write_bytes(b"#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    _write_fixture_policy(
        repository,
        selections
        or [
            {
                "path": "README.md",
                "kind": "file",
                "role": "operator_documentation",
            },
            {"path": "bin/run", "kind": "file", "role": "local_runtime"},
        ],
    )
    _git(repository, "add", ".")
    _git(repository, "commit", "--quiet", "-m", "fixture")
    commit = _git(repository, "rev-parse", "HEAD")
    policy = load_public_export_policy(repository / "governance/public-export.yaml")
    inventory = load_third_party_inventory(repository / "governance/third-party.yaml")
    return repository, commit, policy, inventory


def _add_index_entry(
    repository: Path,
    *,
    mode: str,
    path: str,
    object_id: str | None = None,
) -> None:
    if object_id is None:
        completed = subprocess.run(
            ["git", "-C", str(repository), "hash-object", "-w", "--stdin"],
            input=b"fixture payload\n",
            check=True,
            capture_output=True,
            timeout=10,
        )
        object_id = completed.stdout.decode("ascii").strip()
    _git(repository, "update-index", "--add", "--cacheinfo", mode, object_id, path)
    _git(repository, "commit", "--quiet", "-m", f"add {mode} fixture")


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


def test_builder_reads_full_head_git_objects_and_writes_deterministic_manifest(
    tmp_path: Path,
) -> None:
    repository, commit, policy, inventory = _create_git_fixture(tmp_path)
    destination = tmp_path / "artifact"

    result = build_public_export(
        repository=repository,
        destination=destination,
        source_commit=commit,
        policy=policy,
        inventory=inventory,
    )

    assert result.source_commit == commit
    assert result.technical_artifact_status == "built_not_verified"
    assert result.human_legal_review_status == "required"
    assert result.publication_authorized is False
    assert (destination / "README.md").read_bytes() == b"committed product\n"
    assert stat.S_IMODE((destination / "README.md").stat().st_mode) == 0o644
    assert stat.S_IMODE((destination / "bin/run").stat().st_mode) == 0o755
    assert (destination / "ESCALA-PACKAGE.json").is_file()
    assert (destination / "THIRD_PARTY_NOTICES.md").is_file()
    assert (destination / "ESCALA-MANIFEST.json").is_file()
    manifest_payload = json.loads(
        (destination / "ESCALA-MANIFEST.json").read_text(encoding="utf-8")
    )
    manifest_paths = [entry["path"] for entry in manifest_payload["entries"]]
    assert manifest_paths == sorted(manifest_paths)
    assert "ESCALA-MANIFEST.json" not in manifest_paths
    assert (
        result.manifest_sha256
        == hashlib.sha256(
            (destination / "ESCALA-MANIFEST.json").read_bytes()
        ).hexdigest()
    )


def test_builder_ignores_modified_and_untracked_worktree_content(
    tmp_path: Path,
) -> None:
    repository, commit, policy, inventory = _create_git_fixture(tmp_path)
    (repository / "README.md").write_bytes(b"dirty worktree content\n")
    (repository / "untracked-secret.txt").write_bytes(b"not for export\n")

    destination = tmp_path / "artifact"
    build_public_export(
        repository=repository,
        destination=destination,
        source_commit=commit,
        policy=policy,
        inventory=inventory,
    )

    assert (destination / "README.md").read_bytes() == b"committed product\n"
    assert not (destination / "untracked-secret.txt").exists()


@pytest.mark.parametrize("source_kind", ["symbolic", "abbreviated", "missing"])
def test_builder_rejects_non_full_or_missing_source_refs(
    tmp_path: Path,
    source_kind: str,
) -> None:
    repository, commit, policy, inventory = _create_git_fixture(tmp_path)
    source_commit = {
        "symbolic": "HEAD",
        "abbreviated": commit[:12],
        "missing": "f" * 40,
    }[source_kind]

    with pytest.raises(ValueError) as error:
        build_public_export(
            repository=repository,
            destination=tmp_path / f"artifact-{source_kind}",
            source_commit=source_commit,
            policy=policy,
            inventory=inventory,
        )

    assert str(error.value) in {
        ExportBuildFailure.INVALID_SOURCE_REF.value,
        ExportBuildFailure.SOURCE_OBJECT_MISSING.value,
    }


def test_builder_rejects_noncurrent_commit_and_blob_object(tmp_path: Path) -> None:
    repository, first_commit, policy, inventory = _create_git_fixture(tmp_path)
    (repository / "README.md").write_bytes(b"second commit\n")
    _git(repository, "add", "README.md")
    _git(repository, "commit", "--quiet", "-m", "second")
    blob_id = _git(repository, "rev-parse", "HEAD:README.md")

    for source_commit, expected in (
        (first_commit, ExportBuildFailure.NON_CURRENT_COMMIT.value),
        (blob_id, ExportBuildFailure.SOURCE_NOT_COMMIT.value),
    ):
        with pytest.raises(ValueError, match=expected):
            build_public_export(
                repository=repository,
                destination=tmp_path / f"artifact-{expected}",
                source_commit=source_commit,
                policy=policy,
                inventory=inventory,
            )


def test_builder_rejects_missing_selection_or_committed_contract_mismatch(
    tmp_path: Path,
) -> None:
    missing_selection = [
        {"path": "missing.txt", "kind": "file", "role": "local_runtime"}
    ]
    repository, commit, policy, inventory = _create_git_fixture(
        tmp_path,
        selections=missing_selection,
    )
    with pytest.raises(ValueError, match=ExportBuildFailure.MISSING_SELECTION.value):
        build_public_export(
            repository=repository,
            destination=tmp_path / "artifact-missing",
            source_commit=commit,
            policy=policy,
            inventory=inventory,
        )

    changed_policy = policy.model_copy(
        update={
            "selections": [
                ExportSourceSelection(
                    path="README.md",
                    kind=SelectionKind.FILE,
                    role=ArtifactRole.OPERATOR_DOCUMENTATION,
                )
            ]
        }
    )
    with pytest.raises(
        ValueError, match=ExportBuildFailure.POLICY_SOURCE_MISMATCH.value
    ):
        build_public_export(
            repository=repository,
            destination=tmp_path / "artifact-policy",
            source_commit=commit,
            policy=changed_policy,
            inventory=inventory,
        )

    inventory_data = inventory.model_dump(mode="json")
    inventory_data["entries"][0]["purpose"] = "Changed outside the source commit."
    changed_inventory = ThirdPartyInventory.model_validate(inventory_data)
    with pytest.raises(
        ValueError, match=ExportBuildFailure.INVENTORY_SOURCE_MISMATCH.value
    ):
        build_public_export(
            repository=repository,
            destination=tmp_path / "artifact-inventory",
            source_commit=commit,
            policy=policy,
            inventory=changed_inventory,
        )


def test_builder_rejects_generated_file_directory_collision(tmp_path: Path) -> None:
    selections = [
        {
            "path": "ESCALA-PACKAGE.json/source.txt",
            "kind": "file",
            "role": "local_runtime",
        }
    ]
    repository, _, policy, inventory = _create_git_fixture(
        tmp_path,
        selections=selections,
    )
    _add_index_entry(
        repository,
        mode="100644",
        path="ESCALA-PACKAGE.json/source.txt",
    )
    commit = _git(repository, "rev-parse", "HEAD")

    with pytest.raises(
        ValueError, match=ExportBuildFailure.GENERATED_PATH_COLLISION.value
    ):
        build_public_export(
            repository=repository,
            destination=tmp_path / "artifact-generated-collision",
            source_commit=commit,
            policy=policy,
            inventory=inventory,
        )


@pytest.mark.parametrize(
    ("entry_kind", "expected"),
    [
        ("unsafe", ExportBuildFailure.UNSAFE_GIT_PATH),
        ("casefold", ExportBuildFailure.CASE_COLLISION),
        ("symlink", ExportBuildFailure.UNSUPPORTED_GIT_ENTRY),
        ("submodule", ExportBuildFailure.UNSUPPORTED_GIT_ENTRY),
    ],
)
def test_builder_rejects_unsafe_ambiguous_or_nonregular_selected_git_entries(
    tmp_path: Path,
    entry_kind: str,
    expected: ExportBuildFailure,
) -> None:
    selections = [{"path": "payload", "kind": "tree", "role": "local_runtime"}]
    repository, _, policy, inventory = _create_git_fixture(
        tmp_path,
        selections=selections,
    )
    if entry_kind == "unsafe":
        _add_index_entry(repository, mode="100644", path="payload/bad\\name")
    elif entry_kind == "casefold":
        _add_index_entry(repository, mode="100644", path="payload/Case.txt")
        _add_index_entry(repository, mode="100644", path="payload/case.txt")
    elif entry_kind == "symlink":
        _add_index_entry(repository, mode="120000", path="payload/link")
    else:
        parent_commit = _git(repository, "rev-parse", "HEAD")
        _add_index_entry(
            repository,
            mode="160000",
            path="payload/submodule",
            object_id=parent_commit,
        )
    commit = _git(repository, "rev-parse", "HEAD")

    with pytest.raises(ValueError, match=expected.value):
        build_public_export(
            repository=repository,
            destination=tmp_path / f"artifact-{entry_kind}",
            source_commit=commit,
            policy=policy,
            inventory=inventory,
        )


@pytest.mark.parametrize(
    ("destination_kind", "expected"),
    [
        ("existing", ExportBuildFailure.DESTINATION_EXISTS),
        ("symlink", ExportBuildFailure.DESTINATION_SYMLINK),
        ("repository", ExportBuildFailure.DESTINATION_IN_REPOSITORY),
        ("synchronized", ExportBuildFailure.DESTINATION_SYNCHRONIZED),
        ("outside_temp", ExportBuildFailure.DESTINATION_OUTSIDE_TEMP),
    ],
)
def test_builder_rejects_unsafe_destination(
    tmp_path: Path,
    destination_kind: str,
    expected: ExportBuildFailure,
) -> None:
    repository, commit, policy, inventory = _create_git_fixture(tmp_path)
    destination = tmp_path / f"artifact-{destination_kind}"
    if destination_kind == "existing":
        destination.mkdir()
    elif destination_kind == "symlink":
        target = tmp_path / "symlink-target"
        target.mkdir()
        os.symlink(target, destination)
    elif destination_kind == "repository":
        destination = repository / "artifact"
    elif destination_kind == "synchronized":
        synchronized = tmp_path / "OneDrive"
        synchronized.mkdir()
        destination = synchronized / "artifact"
    else:
        destination = ROOT.parent / "__escala_t3_outside_temp__"
        assert not destination.exists()

    with pytest.raises(ValueError, match=expected.value):
        build_public_export(
            repository=repository,
            destination=destination,
            source_commit=commit,
            policy=policy,
            inventory=inventory,
        )
