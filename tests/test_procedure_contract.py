from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from validators.procedure_contract import (
    ProcedureContract,
    load_procedure_contract,
    validate_procedure_against_release,
)
from validators.ontology_v2 import load_canonical_release


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/procedure_contract/valid.yaml"
RELEASE = ROOT / "ontology/v2/releases/s64.1.json"


def _valid_payload() -> dict[str, object]:
    return ProcedureContract.model_validate(
        load_procedure_contract(FIXTURE).model_dump(mode="python")
    ).model_dump(mode="python")


def test_valid_contract_is_complete_unknown_safe_and_release_bounded() -> None:
    contract = load_procedure_contract(FIXTURE)

    assert contract.version == "1.0.0"
    assert contract.output_contract.artifact.status == "unknown"
    assert contract.output_contract.owner.status == "unknown"
    assert contract.output_contract.kpi.status == "unknown"
    assert contract.output_contract.who_what_when.status == "unknown"
    assert contract.output_contract.review_cadence.status == "unknown"
    assert contract.output_contract.assumptions == []
    assert contract.output_contract.open_questions
    validate_procedure_against_release(contract, load_canonical_release(RELEASE))


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (
            lambda payload: payload.pop("non_trigger"),
            "non_trigger",
        ),
        (
            lambda payload: payload["steps"][0].pop("id"),  # type: ignore[index]
            "id",
        ),
        (
            lambda payload: payload["output_contract"].pop("review_cadence"),  # type: ignore[index]
            "review_cadence",
        ),
        (
            lambda payload: payload.__setitem__(
                "evidence_refs", ["source.raw.passage"]
            ),
            "opaque reference",
        ),
        (
            lambda payload: payload.__setitem__("provenance", "unmarked"),
            "provenance",
        ),
    ],
)
def test_contract_fails_closed_when_required_shape_is_missing_or_unsafe(
    mutate: object, match: str
) -> None:
    payload = deepcopy(_valid_payload())
    mutate(payload)  # type: ignore[operator]

    with pytest.raises(ValidationError, match=match):
        ProcedureContract.model_validate(payload)


def test_unknown_values_require_a_follow_up_question() -> None:
    payload = _valid_payload()
    output = payload["output_contract"]
    assert isinstance(output, dict)
    output["open_questions"] = []

    with pytest.raises(
        ValidationError, match="unknown output values require open questions"
    ):
        ProcedureContract.model_validate(payload)


def test_rejects_evidence_that_is_not_in_authorized_release() -> None:
    payload = _valid_payload()
    payload["evidence_refs"] = [
        "digest.sha256.ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    ]
    contract = ProcedureContract.model_validate(payload)

    with pytest.raises(ValueError, match="unknown release evidence"):
        validate_procedure_against_release(contract, load_canonical_release(RELEASE))


def test_no_raw_source_or_silent_unknown_fields_are_accepted() -> None:
    payload = _valid_payload()
    payload["source_text"] = "verbatim source passage"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ProcedureContract.model_validate(payload)

    payload = _valid_payload()
    output = payload["output_contract"]
    assert isinstance(output, dict)
    artifact = output["artifact"]
    assert isinstance(artifact, dict)
    artifact["status"] = "known"
    artifact["value"] = None
    with pytest.raises(ValidationError, match="known value requires a non-empty value"):
        ProcedureContract.model_validate(payload)
