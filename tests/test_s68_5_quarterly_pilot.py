from __future__ import annotations

import hashlib

import pytest

from validators.pilot_attestation import (
    QuarterlyPilotAttestation,
    validate_pilot_attestation,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _attestation() -> QuarterlyPilotAttestation:
    return QuarterlyPilotAttestation.model_validate(
        {
            "schema_version": 1,
            "pilot_id": "PILOT-001",
            "authorization_reference": "authorization.sha256." + _digest("authorized"),
            "local_storage_consent": True,
            "repository_content_free": True,
            "stages": [
                {
                    "stage": stage,
                    "artifact_sha256": _digest(stage),
                    "human_outcome": "approved",
                    "reviewer_role": "company-leader",
                }
                for stage in ("diagnosis", "priority", "execution", "review")
            ],
        }
    )


def test_accepts_complete_content_free_human_pilot_attestation() -> None:
    assert validate_pilot_attestation(_attestation()) == ()


def test_rejects_pilot_missing_or_reordering_a_stage() -> None:
    raw = _attestation().model_dump()
    raw["stages"] = list(reversed(raw["stages"]))

    with pytest.raises(ValueError, match="pilot_stages_incomplete_or_reordered"):
        QuarterlyPilotAttestation.model_validate(raw)


def test_flags_duplicate_artifact_proof() -> None:
    raw = _attestation().model_dump()
    raw["stages"][1]["artifact_sha256"] = raw["stages"][0]["artifact_sha256"]

    assert validate_pilot_attestation(QuarterlyPilotAttestation.model_validate(raw)) == (
        "pilot_artifact_hashes_must_be_distinct",
    )
