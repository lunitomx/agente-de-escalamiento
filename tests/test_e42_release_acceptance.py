"""Tests for the strict private E42 release-acceptance gate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from validators.e42_release_acceptance import (
    E42ReleaseAcceptanceReceipt,
    validation_errors,
)

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "install",
    "workspace",
    "document-ingestion",
    "meeting-review",
    "cash",
    "strategy",
    "cockpit",
    "action-followup",
]
REQUIREMENTS = [f"REQ-E42-00{number}" for number in range(1, 7)]


def _receipt() -> dict[str, object]:
    run = {
        "environment": "physical",
        "clean_environment": True,
        "source_commit": "a" * 40,
        "export_manifest_sha256": "b" * 64,
        "public_entrypoint": "escala",
        "journey_steps": STEPS,
        "result": "pass",
    }
    return {
        "schema_version": 1,
        "receipt_kind": "e42-clean-hardware-and-human-acceptance",
        "storage": "private-local-only",
        "participant_ref": "owner-001",
        "platform_runs": [
            run | {"run_ref": "mac-run-001", "platform": "macos"},
            run
            | {
                "run_ref": "win-run-001",
                "platform": "windows",
                "environment": "dedicated-vm",
            },
        ],
        "catalog_review": {
            "matches_public_inventory": True,
            "limitations_are_clear": True,
            "excludes_private_or_prohibited_sources": True,
        },
        "requirement_acceptance": [
            {"requirement_id": requirement, "accepted": True}
            for requirement in REQUIREMENTS
        ],
        "release_decision": "accepted",
    }


def test_valid_receipt_passes_and_cli_does_not_echo_contents(tmp_path: Path) -> None:
    data = _receipt()
    receipt = E42ReleaseAcceptanceReceipt.model_validate(data)
    assert validation_errors(receipt) == ()

    path = tmp_path / "private-receipt.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/check_e42_release_acceptance.py"),
            str(path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout == "E42 release acceptance pass\n"
    assert "owner-001" not in result.stdout


def test_invalid_receipt_is_rejected_without_echoing_its_contents(
    tmp_path: Path,
) -> None:
    data = _receipt()
    data["participant_ref"] = "Private Person"
    path = tmp_path / "private-receipt.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/check_e42_release_acceptance.py"),
            str(path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == "E42 release acceptance receipt invalid\n"
    assert "Private Person" not in result.stdout + result.stderr


def test_reservations_keep_the_gate_open() -> None:
    data = _receipt()
    acceptance = data["requirement_acceptance"]
    assert isinstance(acceptance, list)
    acceptance[-1]["accepted"] = False
    data["release_decision"] = "reservations-open"

    receipt = E42ReleaseAcceptanceReceipt.model_validate(data)
    assert validation_errors(receipt) == ("owner acceptance remains open: REQ-E42-006",)


def test_rejects_simulated_or_incomplete_hardware_run() -> None:
    data = _receipt()
    runs = data["platform_runs"]
    assert isinstance(runs, list)
    runs[0]["clean_environment"] = False

    with pytest.raises(ValidationError):
        E42ReleaseAcceptanceReceipt.model_validate(data)
