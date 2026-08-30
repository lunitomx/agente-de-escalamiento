from __future__ import annotations

from copy import deepcopy
import inspect
from pathlib import Path

import pytest

import validators.procedure_contract as procedure_contract
from pydantic import ValidationError

from validators.procedure_contract import (
    ProcedureContract,
    _trusted_workspace_root,
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


def test_known_value_requires_company_evidence_consent_and_human_confirmation() -> None:
    payload = _valid_payload()
    output = payload["output_contract"]
    assert isinstance(output, dict)
    artifact = output["artifact"]
    assert isinstance(artifact, dict)
    artifact.update({"status": "known", "value": "confirmed artifact"})
    with pytest.raises(
        ValidationError, match="known value requires an allowed typed origin"
    ):
        ProcedureContract.model_validate(payload)

    artifact["origin"] = "model-hypothesis"
    with pytest.raises(
        ValidationError, match="known value requires an allowed typed origin"
    ):
        ProcedureContract.model_validate(payload)

    artifact["origin"] = "company-local"
    with pytest.raises(
        ValidationError,
        match="known value requires evidence, consent, and human confirmation",
    ):
        ProcedureContract.model_validate(payload)

    artifact.update(
        {
            "origin": "company-local",
            "evidence_ids": ["fact.authorized.context"],
            "consent_receipt": "consent.memory.authorized",
            "confirmed_by": "person.company.owner",
        }
    )
    contract = ProcedureContract.model_validate(payload)
    with pytest.raises(ValueError, match="requires trusted registry"):
        validate_procedure_against_release(contract, load_canonical_release(RELEASE))

    artifact["evidence_ids"] = ["fact.fake"]
    with pytest.raises(ValueError, match="requires trusted registry"):
        validate_procedure_against_release(
            ProcedureContract.model_validate(payload), load_canonical_release(RELEASE)
        )
    with pytest.raises(TypeError):
        validate_procedure_against_release(  # type: ignore[call-arg]
            ProcedureContract.model_validate(payload),
            load_canonical_release(RELEASE),
            base_path=ROOT,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("objective", "https://example.test/private-source"),
        ("objective", "state/company/secret.yaml"),
        ("objective", "source_id private-passage"),
        (
            "objective",
            "one two three four five six seven eight nine ten eleven twelve thirteen",
        ),
    ],
)
def test_contract_text_is_bounded_and_cannot_be_a_locator_or_passage(
    field: str, value: str
) -> None:
    payload = _valid_payload()
    payload[field] = value
    with pytest.raises(ValidationError, match="unsafe procedure objective"):
        ProcedureContract.model_validate(payload)


def test_confirmed_state_updates_require_a_typed_human_consent_record() -> None:
    payload = _valid_payload()
    update = payload["state_updates"][0]  # type: ignore[index]
    update["mode"] = "confirmed"
    with pytest.raises(ValidationError, match="requires a human consent record"):
        ProcedureContract.model_validate(payload)

    update["confirmation"] = {
        "record_id": "confirmation.current-quarter.owner",
        "origin": "company-local",
        "consent_receipt": "consent.memory.authorized",
        "confirmed_by": "person.company.owner",
    }
    assert (
        ProcedureContract.model_validate(payload).state_updates[0].mode == "confirmed"
    )


def test_canonical_who_what_when_label_remains_valid() -> None:
    payload = _valid_payload()
    payload["interview_questions"][0]["prompt"] = "Who/What/When"  # type: ignore[index]
    assert (
        ProcedureContract.model_validate(payload).interview_questions[0].prompt
        == "Who/What/When"
    )


def test_public_release_validation_does_not_accept_a_forged_registry_argument() -> None:
    parameters = inspect.signature(validate_procedure_against_release).parameters
    assert "registry" not in parameters
    assert "base_path" not in parameters
    payload = _valid_payload()
    output = payload["output_contract"]
    assert isinstance(output, dict)
    artifact = output["artifact"]
    assert isinstance(artifact, dict)
    artifact.update(
        {
            "status": "known",
            "value": "confirmed artifact",
            "origin": "company-local",
            "evidence_ids": ["fact.fake"],
            "consent_receipt": "consent.fake",
            "confirmed_by": "person.fake",
        }
    )
    with pytest.raises(ValueError, match="requires trusted registry"):
        validate_procedure_against_release(
            ProcedureContract.model_validate(payload), load_canonical_release(RELEASE)
        )


def test_chdir_cannot_replace_the_trusted_project_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_root = tmp_path / "forged-workspace"
    fake_root.mkdir()
    monkeypatch.chdir(fake_root)
    assert _trusted_workspace_root() == ROOT.resolve()

    payload = _valid_payload()
    output = payload["output_contract"]
    assert isinstance(output, dict)
    artifact = output["artifact"]
    assert isinstance(artifact, dict)
    artifact.update(
        {
            "status": "known",
            "value": "forged artifact",
            "origin": "company-local",
            "evidence_ids": ["fact.fake"],
            "consent_receipt": "consent.fake",
            "confirmed_by": "person.fake",
        }
    )
    with pytest.raises(ValueError, match="requires trusted registry"):
        validate_procedure_against_release(
            ProcedureContract.model_validate(payload), load_canonical_release(RELEASE)
        )


def test_missing_scaleup_identity_rejects_workspace_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_root = tmp_path / "without-scaleup-identity"
    fake_root.mkdir()
    monkeypatch.setattr(procedure_contract, "_TRUSTED_PROJECT_ROOT", fake_root)
    with pytest.raises(ValueError, match="trusted workspace identity is invalid"):
        procedure_contract._trusted_workspace_root()
