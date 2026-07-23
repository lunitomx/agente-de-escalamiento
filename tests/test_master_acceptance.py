from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable

import pytest
from pydantic import ValidationError
import yaml

from validators.governance_contract import (
    closure_disposition_policy_hash,
    epic_identity_policy_hash,
    load_closure_disposition_policy,
    load_epic_identity_policy,
)
from validators.master_acceptance import (
    AcceptanceMode,
    ContractStatus,
    GateEvidenceReceipt,
    MasterAcceptanceError,
    MasterAcceptanceLedger,
    MasterAcceptanceReceipt,
    MissionReadiness,
    RequirementEvidenceReceipt,
    acceptance_requirement_declaration_hash,
    build_master_acceptance_receipt,
    load_master_acceptance_ledger,
    master_acceptance_ledger_hash,
    render_master_acceptance_json,
    render_master_acceptance_markdown,
    render_master_acceptance_receipt_json,
    render_master_acceptance_receipt_markdown,
    render_requirement_evidence_receipt_json,
    validate_master_acceptance_authorities,
    verification_command_hash,
    write_master_acceptance_receipts,
)
from validators.public_export import (
    load_public_export_policy,
    public_export_policy_hash,
)


ROOT = Path(__file__).resolve().parents[1]
CLOSURE_POLICY_PATH = ROOT / "governance/closure-dispositions.yaml"
IDENTITY_POLICY_PATH = ROOT / "governance/epic-identities.yaml"
PUBLIC_EXPORT_POLICY_PATH = ROOT / "governance/public-export.yaml"
LEDGER_PATH = (
    ROOT / "work/epics/e36-product-truth-ip-governance/master-acceptance-ledger.yaml"
)
LEDGER_MARKDOWN_PATH = (
    ROOT / "work/epics/e36-product-truth-ip-governance/master-acceptance-ledger.md"
)
SCRIPT = ROOT / "scripts/check_master_acceptance.py"
BASELINE_JSON_PATH = (
    ROOT / "work/epics/e36-product-truth-ip-governance/stories/"
    "s36.6-evidence/baseline.json"
)
BASELINE_MARKDOWN_PATH = (
    ROOT / "work/epics/e36-product-truth-ip-governance/stories/"
    "s36.6-evidence/baseline.md"
)

EXPECTED_COUNTS = {
    "E37": 7,
    "E38": 7,
    "E39": 7,
    "E40": 8,
    "E41": 7,
    "E42": 6,
}
EXPECTED_EPICS = {
    "E37": (
        "local-workspace-flexible-ingestion",
        ("S37.1", "S37.2", "S37.3"),
    ),
    "E38": (
        "cash-and-financial-intelligence",
        ("S38.1", "S38.2", "S38.3", "S38.4"),
    ),
    "E39": (
        "meeting-and-team-intelligence",
        ("S39.1", "S39.2", "S39.3", "S39.4"),
    ),
    "E40": (
        "executive-cockpit-and-coaching",
        ("S40.1", "S40.2", "S40.3", "S40.4"),
    ),
    "E41": (
        "local-installation-and-lifecycle",
        ("S41.1", "S41.2", "S41.3", "S41.4"),
    ),
    "E42": (
        "product-qualification-and-functional-catalog",
        ("S42.1", "S42.2", "S42.3", "S42.4"),
    ),
}
EXPECTED_OWNER_STORIES = {
    "E37": (1, 1, 2, 2, 2, 3, 3),
    "E38": (1, 1, 2, 2, 3, 3, 4),
    "E39": (1, 1, 2, 2, 3, 3, 4),
    "E40": (1, 1, 2, 3, 3, 4, 2, 4),
    "E41": (1, 1, 2, 3, 3, 2, 4),
    "E42": (1, 2, 1, 3, 4, 4),
}
EXPECTED_SOURCE_IDS = {
    "SRC-CASH-001",
    "SRC-COACH-001",
    "SRC-COCKPIT-001",
    "SRC-EVIDENCE-001",
    "SRC-INGEST-001",
    "SRC-INSTALL-001",
    "SRC-LOCAL-001",
    "SRC-MEETING-001",
    "SRC-QUALIFY-001",
    "SRC-SHARING-001",
    "SRC-SQLITE-001",
    "SRC-CATALOG-001",
}


def _authority_data() -> dict[str, dict[str, str]]:
    return {
        "closure_dispositions": {
            "path": "governance/closure-dispositions.yaml",
            "sha256": closure_disposition_policy_hash(
                load_closure_disposition_policy(CLOSURE_POLICY_PATH)
            ),
            "hash_kind": "semantic",
        },
        "epic_identities": {
            "path": "governance/epic-identities.yaml",
            "sha256": epic_identity_policy_hash(
                load_epic_identity_policy(IDENTITY_POLICY_PATH)
            ),
            "hash_kind": "semantic",
        },
        "public_export": {
            "path": "governance/public-export.yaml",
            "sha256": public_export_policy_hash(
                load_public_export_policy(PUBLIC_EXPORT_POLICY_PATH)
            ),
            "hash_kind": "semantic",
        },
    }


def _ledger_data() -> dict[str, Any]:
    source_requirements = [
        {
            "id": f"SRC-E{epic[1:]}",
            "statement": f"Approved observable outcome for {epic}.",
        }
        for epic in EXPECTED_COUNTS
    ]
    epics = [
        {
            "id": epic,
            "slug": slug,
            "title": f"Planned epic {epic}",
            "stories": [
                {"id": story, "title": f"Planned story {story}"} for story in stories
            ],
            "requirement_count": EXPECTED_COUNTS[epic],
        }
        for epic, (slug, stories) in EXPECTED_EPICS.items()
    ]
    requirements: list[dict[str, Any]] = []
    for epic, count in EXPECTED_COUNTS.items():
        slug, stories = EXPECTED_EPICS[epic]
        for index in range(1, count + 1):
            requirement_id = f"REQ-{epic}-{index:03d}"
            story = stories[(index - 1) % len(stories)]
            evidence_root = f"work/epics/e{epic[1:]}-{slug}/evidence"
            requirements.append(
                {
                    "id": requirement_id,
                    "owner": {"epic": epic, "story": story},
                    "source_ids": [f"SRC-E{epic[1:]}"],
                    "acceptance": f"Observable acceptance for {requirement_id}.",
                    "evidence": {
                        "artifact_path": f"{evidence_root}/{requirement_id}.json",
                        "receipt_path": (
                            f"{evidence_root}/{requirement_id}.receipt.json"
                        ),
                        "verification_command": [
                            ".venv/bin/rai",
                            "gate",
                            "check",
                            f"gate-{requirement_id.lower()}",
                        ],
                        "required_gates": [
                            "gate-format",
                            "gate-lint",
                            f"gate-{requirement_id.lower()}",
                            "gate-tests",
                            "gate-types",
                        ],
                    },
                    "platforms": ["macos", "windows"],
                    "architecture": {
                        "runtime_authority": "installer_machine",
                        "data_authority": "installer_machine",
                        "team_exchange": "ordinary_filesystem_documents_only",
                        "authoritative_sqlite_sync": "forbidden",
                    },
                    "delivery_disposition": "active",
                    "proof": {
                        "state": "unproved",
                        "blockers": ["evidence.missing"],
                    },
                }
            )
    return {
        "schema_version": 1,
        "mission_id": "escala-local-v2-plan-maestro-2607202112",
        "authorities": _authority_data(),
        "source_requirements": source_requirements,
        "epics": epics,
        "requirements": requirements,
        "limits": {
            "max_acceptance_chars": 2048,
            "max_command_tokens": 16,
            "max_receipt_bytes": 65536,
        },
    }


def _write_ledger(tmp_path: Path, data: Any) -> Path:
    path = tmp_path / "master-acceptance-ledger.yaml"
    path.write_text(
        yaml.safe_dump(data, allow_unicode=False, sort_keys=False),
        encoding="utf-8",
    )
    return path


def _git(repository: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _initialize_authority_repository(repository: Path) -> str:
    governance = repository / "governance"
    governance.mkdir(parents=True)
    for source in (
        CLOSURE_POLICY_PATH,
        IDENTITY_POLICY_PATH,
        PUBLIC_EXPORT_POLICY_PATH,
    ):
        (governance / source.name).write_bytes(source.read_bytes())
    _git(repository, "init", "-q")
    _git(repository, "config", "user.email", "tests@example.invalid")
    _git(repository, "config", "user.name", "Tests")
    _git(repository, "add", "governance")
    _git(repository, "commit", "-q", "-m", "authority baseline")
    return _git(repository, "rev-parse", "HEAD")


def test_strict_master_acceptance_contract_is_complete_and_stable(
    tmp_path: Path,
) -> None:
    ledger_path = _write_ledger(tmp_path, _ledger_data())

    first = load_master_acceptance_ledger(ledger_path)
    second = load_master_acceptance_ledger(ledger_path)

    assert first.schema_version == 1
    assert [item.id for item in first.epics] == list(EXPECTED_COUNTS)
    assert len(first.requirements) == 42
    assert [item.id for item in first.requirements] == [
        f"REQ-{epic}-{index:03d}"
        for epic, count in EXPECTED_COUNTS.items()
        for index in range(1, count + 1)
    ]
    assert all(item.proof.state == "unproved" for item in first.requirements)
    assert master_acceptance_ledger_hash(first) == master_acceptance_ledger_hash(second)
    assert len(master_acceptance_ledger_hash(first)) == 64


@pytest.mark.parametrize(
    "mutator",
    [
        lambda data: data.update({"schema_version": 2}),
        lambda data: data.update({"unknown_root": True}),
        lambda data: data["requirements"][0].update({"unknown": True}),
        lambda data: data["requirements"][0].update({"acceptance": None}),
        lambda data: data["requirements"][1].update(
            {"id": data["requirements"][0]["id"]}
        ),
        lambda data: data["requirements"][0]["owner"].update({"epic": "E38"}),
        lambda data: data["requirements"][0]["owner"].update({"story": "S38.1"}),
        lambda data: data["requirements"][0]["evidence"].update(
            {"artifact_path": "../private.json"}
        ),
        lambda data: data["requirements"][0]["evidence"].update(
            {"verification_command": ["python", "-c", "import os;os.system('x')"]}
        ),
        lambda data: data["requirements"][0]["evidence"].update(
            {"required_gates": ["gate-types", "gate-tests"]}
        ),
        lambda data: data["requirements"][0]["architecture"].update(
            {"runtime_authority": "hosted_service"}
        ),
        lambda data: data["requirements"][0].update(
            {"proof": {"state": "proved", "blockers": []}}
        ),
        lambda data: data["requirements"][0].update(
            {
                "proof": {
                    "state": "unproved",
                    "blockers": ["evidence.failed", "evidence.stale"],
                }
            }
        ),
        lambda data: data["epics"][0].update({"requirement_count": 6}),
        lambda data: data["requirements"].pop(),
        lambda data: data["source_requirements"].append(
            {"id": "SRC-UNUSED", "statement": "Unmapped source."}
        ),
    ],
)
def test_master_acceptance_rejects_incomplete_contradictory_or_unsafe_data(
    mutator: Callable[[dict[str, Any]], None],
) -> None:
    data = deepcopy(_ledger_data())
    mutator(data)

    with pytest.raises(ValidationError):
        MasterAcceptanceLedger.model_validate(data)


@pytest.mark.parametrize("data", [None, [], "ledger", {}])
def test_master_acceptance_rejects_null_or_wrong_root_shapes(data: Any) -> None:
    with pytest.raises(ValidationError):
        MasterAcceptanceLedger.model_validate(data)


def test_master_acceptance_authorities_are_semantically_bound(
    tmp_path: Path,
) -> None:
    ledger = load_master_acceptance_ledger(_write_ledger(tmp_path, _ledger_data()))

    snapshot = validate_master_acceptance_authorities(ROOT, ledger)

    assert snapshot.closure_dispositions_sha256 == (
        ledger.authorities.closure_dispositions.sha256
    )
    assert snapshot.epic_identities_sha256 == ledger.authorities.epic_identities.sha256
    assert snapshot.public_export_sha256 == ledger.authorities.public_export.sha256
    assert snapshot.runtime_authority == "installer_machine"
    assert snapshot.authoritative_sqlite_sync == "forbidden"
    assert snapshot.human_legal_review_status == "required"
    assert snapshot.publication_authorized is False


def test_master_acceptance_rejects_authority_hash_drift(tmp_path: Path) -> None:
    data = _ledger_data()
    data["authorities"]["public_export"]["sha256"] = "a" * 64
    ledger = load_master_acceptance_ledger(_write_ledger(tmp_path, data))

    with pytest.raises(MasterAcceptanceError, match="authority contract mismatch"):
        validate_master_acceptance_authorities(ROOT, ledger)


@pytest.mark.parametrize(
    "disposition",
    ["unresolved/review-required", "deferred/backlog"],
)
def test_reviewable_unproved_dispositions_remain_valid_but_not_proved(
    tmp_path: Path,
    disposition: str,
) -> None:
    data = _ledger_data()
    data["requirements"][0]["delivery_disposition"] = disposition
    data["requirements"][0]["proof"] = {
        "state": "unproved",
        "blockers": ["evidence.failed"],
    }
    ledger = load_master_acceptance_ledger(_write_ledger(tmp_path, data))

    validate_master_acceptance_authorities(ROOT, ledger)
    receipt = build_master_acceptance_receipt(
        ROOT,
        ledger,
        mode=AcceptanceMode.READINESS,
        epic_filter="E37",
    )

    assert receipt.mission_readiness is MissionReadiness.UNPROVED
    assert receipt.blocking_requirements[0].rule_id == "evidence.failed"


def test_canonical_master_acceptance_ledger_matches_approved_plan() -> None:
    ledger = load_master_acceptance_ledger(LEDGER_PATH)

    assert ledger.mission_id == "escala-local-v2-plan-maestro-2607202112"
    assert {item.id for item in ledger.source_requirements} == EXPECTED_SOURCE_IDS
    assert [(item.id, item.slug, item.requirement_count) for item in ledger.epics] == [
        (epic, slug, EXPECTED_COUNTS[epic])
        for epic, (slug, _) in EXPECTED_EPICS.items()
    ]
    assert len(ledger.requirements) == 42
    assert {item.id: item.owner.story for item in ledger.requirements} == {
        f"REQ-{epic}-{index:03d}": f"S{epic[1:]}.{story_index}"
        for epic, owners in EXPECTED_OWNER_STORIES.items()
        for index, story_index in enumerate(owners, start=1)
    }
    proved_ids = {
        item.id for item in ledger.requirements if item.proof.state == "proved"
    }
    assert proved_ids == {
        *(f"REQ-E37-{index:03d}" for index in range(1, 8)),
        *(f"REQ-E38-{index:03d}" for index in range(1, 8)),
        *(f"REQ-E39-{index:03d}" for index in range(1, 8)),
        *(f"REQ-E40-{index:03d}" for index in range(1, 9)),
        *(f"REQ-E41-{index:03d}" for index in range(1, 8)),
    }
    assert all(
        [blocker.value for blocker in item.proof.blockers] == ["evidence.missing"]
        for item in ledger.requirements
        if item.proof.state == "unproved"
    )
    assert next(
        item for item in ledger.requirements if item.id == "REQ-E41-001"
    ).platforms == ["macos"]
    assert next(
        item for item in ledger.requirements if item.id == "REQ-E41-002"
    ).platforms == ["windows"]
    assert "without adapting them to an ESCALA template" in next(
        item.acceptance for item in ledger.requirements if item.id == "REQ-E37-003"
    )
    assert "profit-and-loss statement, balance sheet, and cash-flow view" in next(
        item.acceptance for item in ledger.requirements if item.id == "REQ-E38-003"
    )
    assert "synthetic entrepreneur/company" in next(
        item.acceptance for item in ledger.requirements if item.id == "REQ-E42-001"
    )
    assert "Spanish PDF" in next(
        item.acceptance for item in ledger.requirements if item.id == "REQ-E42-005"
    )


def test_canonical_ledger_rendering_is_deterministic_and_matches_human_view() -> None:
    ledger = load_master_acceptance_ledger(LEDGER_PATH)

    first_json = render_master_acceptance_json(ledger)
    first_markdown = render_master_acceptance_markdown(ledger)

    assert first_json == render_master_acceptance_json(ledger)
    assert first_markdown == render_master_acceptance_markdown(ledger)
    assert first_markdown == LEDGER_MARKDOWN_PATH.read_text(encoding="utf-8")
    assert first_markdown.count("| `REQ-E") == 42
    assert first_markdown.count(".receipt.json`") == 42
    assert first_markdown.count("`evidence.missing`") == 6
    assert "| Requirement | Owner | Sources | Acceptance |" in first_markdown
    assert "**Contract inventory:** 42 requirements across 6 epics." in first_markdown
    assert "**Initial proof posture:** 36 proved, 6 unproved." in first_markdown
    combined = first_json + first_markdown
    for forbidden in (str(ROOT), "https://", "S36-PRIVATE-SENTINEL"):
        assert forbidden not in combined


def test_master_ledger_hash_excludes_external_receipt_content_address() -> None:
    first_data = _ledger_data()
    first_data["requirements"][0]["delivery_disposition"] = "complete"
    first_data["requirements"][0]["proof"] = {
        "state": "proved",
        "receipt_sha256": "a" * 64,
    }
    second_data = deepcopy(first_data)
    second_data["requirements"][0]["proof"]["receipt_sha256"] = "b" * 64

    first = MasterAcceptanceLedger.model_validate(first_data)
    second = MasterAcceptanceLedger.model_validate(second_data)

    assert master_acceptance_ledger_hash(first) == master_acceptance_ledger_hash(second)


def test_canonical_baseline_receipt_is_pass_but_truthfully_unproved() -> None:
    ledger = load_master_acceptance_ledger(LEDGER_PATH)

    receipt = build_master_acceptance_receipt(
        ROOT,
        ledger,
        mode=AcceptanceMode.BASELINE,
    )
    first_json = render_master_acceptance_receipt_json(receipt)
    first_markdown = render_master_acceptance_receipt_markdown(receipt)

    assert receipt.contract_status is ContractStatus.PASS
    assert receipt.mission_readiness is MissionReadiness.UNPROVED
    assert receipt.epic_filter is None
    assert receipt.epic_count == 6
    assert receipt.requirement_count == 42
    assert receipt.proved_count == 36
    assert receipt.unproved_count == 6
    assert receipt.proved_ids == [
        *(f"REQ-E37-{index:03d}" for index in range(1, 8)),
        *(f"REQ-E38-{index:03d}" for index in range(1, 8)),
        *(f"REQ-E39-{index:03d}" for index in range(1, 8)),
        *(f"REQ-E40-{index:03d}" for index in range(1, 9)),
        *(f"REQ-E41-{index:03d}" for index in range(1, 8)),
    ]
    assert [item.requirement_id for item in receipt.blocking_requirements] == [
        item.id for item in ledger.requirements if item.proof.state == "unproved"
    ]
    assert {item.rule_id for item in receipt.blocking_requirements} == {
        "evidence.missing"
    }
    assert first_json == render_master_acceptance_receipt_json(receipt)
    assert first_markdown == render_master_acceptance_receipt_markdown(receipt)
    assert len(first_json.encode()) <= ledger.limits.max_receipt_bytes
    assert len(first_markdown.encode()) <= ledger.limits.max_receipt_bytes
    combined = first_json + first_markdown
    for forbidden in (str(ROOT), "https://", "S36-PRIVATE-SENTINEL"):
        assert forbidden not in combined


def test_exact_requirement_receipts_can_prove_one_filtered_epic(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    source_commit = _initialize_authority_repository(repository)
    data = _ledger_data()
    unproved_ledger = MasterAcceptanceLedger.model_validate(data)
    ledger_sha256 = master_acceptance_ledger_hash(unproved_ledger)

    for requirement_data in data["requirements"]:
        if requirement_data["owner"]["epic"] != "E37":
            continue
        requirement = next(
            item
            for item in unproved_ledger.requirements
            if item.id == requirement_data["id"]
        )
        artifact_path = repository / requirement.evidence.artifact_path
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_bytes = f"qualified artifact for {requirement.id}\n".encode()
        artifact_path.write_bytes(artifact_bytes)
        evidence_receipt = RequirementEvidenceReceipt(
            schema_version=1,
            requirement_id=requirement.id,
            ledger_sha256=ledger_sha256,
            declaration_sha256=acceptance_requirement_declaration_hash(requirement),
            source_commit=source_commit,
            artifact_sha256=hashlib.sha256(artifact_bytes).hexdigest(),
            command_sha256=verification_command_hash(
                requirement.evidence.verification_command
            ),
            gate_results=[
                GateEvidenceReceipt(id=gate_id, status="pass")
                for gate_id in requirement.evidence.required_gates
            ],
            platforms=requirement.platforms,
            result="pass",
        )
        receipt_bytes = render_requirement_evidence_receipt_json(
            evidence_receipt
        ).encode()
        receipt_path = repository / requirement.evidence.receipt_path
        receipt_path.write_bytes(receipt_bytes)
        requirement_data["delivery_disposition"] = "complete"
        requirement_data["proof"] = {
            "state": "proved",
            "receipt_sha256": hashlib.sha256(receipt_bytes).hexdigest(),
        }

    proved_ledger = MasterAcceptanceLedger.model_validate(data)
    receipt = build_master_acceptance_receipt(
        repository,
        proved_ledger,
        mode=AcceptanceMode.READINESS,
        epic_filter="E37",
    )

    assert receipt.contract_status is ContractStatus.PASS
    assert receipt.mission_readiness is MissionReadiness.PROVED
    assert receipt.epic_filter == "E37"
    assert receipt.epic_count == 1
    assert receipt.requirement_count == receipt.proved_count == 7
    assert receipt.unproved_count == 0
    assert receipt.proved_ids == [f"REQ-E37-{index:03d}" for index in range(1, 8)]
    assert receipt.blocking_requirements == []


def test_stale_or_failed_proof_is_reported_without_false_contract_failure(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    _initialize_authority_repository(repository)
    data = _ledger_data()
    data["requirements"][0]["delivery_disposition"] = "complete"
    data["requirements"][0]["proof"] = {
        "state": "proved",
        "receipt_sha256": "a" * 64,
    }
    ledger = MasterAcceptanceLedger.model_validate(data)

    receipt = build_master_acceptance_receipt(
        repository,
        ledger,
        mode=AcceptanceMode.READINESS,
        epic_filter="E37",
    )

    assert receipt.contract_status is ContractStatus.PASS
    assert receipt.mission_readiness is MissionReadiness.UNPROVED
    assert receipt.proved_count == 0
    assert receipt.unproved_count == 7
    assert receipt.blocking_requirements[0].requirement_id == "REQ-E37-001"
    assert receipt.blocking_requirements[0].rule_id == "evidence.missing"


def test_master_acceptance_writers_are_explicit_and_non_overwriting(
    tmp_path: Path,
) -> None:
    ledger = load_master_acceptance_ledger(LEDGER_PATH)
    receipt = build_master_acceptance_receipt(
        ROOT,
        ledger,
        mode=AcceptanceMode.BASELINE,
    )
    json_output = tmp_path / "receipts/baseline.json"
    markdown_output = tmp_path / "receipts/baseline.md"

    write_master_acceptance_receipts(
        receipt,
        max_receipt_bytes=ledger.limits.max_receipt_bytes,
        json_output=json_output,
        markdown_output=markdown_output,
    )

    assert json_output.read_text(encoding="utf-8") == (
        render_master_acceptance_receipt_json(receipt)
    )
    assert markdown_output.read_text(encoding="utf-8") == (
        render_master_acceptance_receipt_markdown(receipt)
    )
    with pytest.raises(FileExistsError):
        write_master_acceptance_receipts(
            receipt,
            max_receipt_bytes=ledger.limits.max_receipt_bytes,
            json_output=json_output,
        )

    broken_symlink = tmp_path / "receipts/broken-link.json"
    broken_symlink.symlink_to(tmp_path / "missing-target.json")
    with pytest.raises(FileExistsError):
        write_master_acceptance_receipts(
            receipt,
            max_receipt_bytes=ledger.limits.max_receipt_bytes,
            json_output=broken_symlink,
        )


def test_master_acceptance_cli_has_truthful_modes_and_one_safe_failure(
    tmp_path: Path,
) -> None:
    outputs: list[tuple[bytes, bytes, str]] = []
    for label in ("first", "second"):
        json_output = tmp_path / label / "baseline.json"
        markdown_output = tmp_path / label / "baseline.md"
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo",
                str(ROOT),
                "--ledger",
                str(LEDGER_PATH),
                "--mode",
                "baseline",
                "--format",
                "json",
                "--json-output",
                str(json_output),
                "--markdown-output",
                str(markdown_output),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0
        assert completed.stderr == ""
        assert json.loads(completed.stdout)["mission_readiness"] == "unproved"
        outputs.append(
            (
                json_output.read_bytes(),
                markdown_output.read_bytes(),
                completed.stdout,
            )
        )
    assert outputs[0] == outputs[1]

    readiness = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo",
            str(ROOT),
            "--ledger",
            str(LEDGER_PATH),
            "--mode",
            "readiness",
            "--epic",
            "E37",
            "--format",
            "text",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert readiness.returncode == 0
    assert readiness.stderr == ""
    assert "Mission readiness: `proved`" in readiness.stdout
    assert "Epic filter: `E37`" in readiness.stdout

    corrupt = tmp_path / "S36-PRIVATE-SENTINEL.yaml"
    corrupt.write_text("schema_version: [", encoding="utf-8")
    failed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo",
            str(ROOT),
            "--ledger",
            str(corrupt),
            "--mode",
            "baseline",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert failed.returncode == 1
    assert failed.stdout == ""
    assert (
        failed.stderr
        == "master acceptance: unable to produce a safe contract receipt\n"
    )
    assert "S36-PRIVATE-SENTINEL" not in failed.stderr


def test_versioned_real_baseline_matches_current_contract_semantics() -> None:
    ledger = load_master_acceptance_ledger(LEDGER_PATH)
    baseline = MasterAcceptanceReceipt.model_validate_json(
        BASELINE_JSON_PATH.read_text(encoding="utf-8")
    )
    current = build_master_acceptance_receipt(
        ROOT,
        ledger,
        mode=AcceptanceMode.BASELINE,
    )

    assert baseline.contract_status is ContractStatus.PASS
    assert baseline.mission_readiness is MissionReadiness.UNPROVED
    assert baseline.requirement_count == 42
    assert baseline.unproved_count == 6
    assert baseline.proved_count == 36
    assert render_master_acceptance_receipt_json(baseline) == (
        BASELINE_JSON_PATH.read_text(encoding="utf-8")
    )
    assert render_master_acceptance_receipt_markdown(baseline) == (
        BASELINE_MARKDOWN_PATH.read_text(encoding="utf-8")
    )
    assert (
        baseline.model_copy(
            update={
                "verifier_source_commit": current.verifier_source_commit,
                "ledger_markdown_sha256": current.ledger_markdown_sha256,
            }
        )
        == current
    )
    source_ledger = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "show",
            (
                f"{baseline.verifier_source_commit}:work/epics/"
                "e36-product-truth-ip-governance/master-acceptance-ledger.yaml"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    source_markdown = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "show",
            (
                f"{baseline.verifier_source_commit}:work/epics/"
                "e36-product-truth-ip-governance/master-acceptance-ledger.md"
            ),
        ],
        check=True,
        capture_output=True,
    )
    source_data: Any = yaml.safe_load(source_ledger.stdout)
    source_model = MasterAcceptanceLedger.model_validate(source_data)
    assert master_acceptance_ledger_hash(source_model) == baseline.ledger_sha256
    assert hashlib.sha256(source_markdown.stdout).hexdigest() == (
        baseline.ledger_markdown_sha256
    )
