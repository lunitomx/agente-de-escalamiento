"""S68.2 validates structured procedure outputs against compiled E65 contracts."""

from __future__ import annotations

from validators.golden_outputs import validate_golden_output
from validators.procedure_compiler import compile_mvp_procedures


def test_all_six_compiled_outputs_satisfy_their_golden_contract() -> None:
    compiled = compile_mvp_procedures()

    for contract in compiled.contracts:
        assert (
            validate_golden_output(
                procedure_id=contract.id,
                output=contract.output_contract,
                state_updates=contract.state_updates,
                evidence_refs=contract.evidence_refs,
            )
            == ()
        )


def test_missing_questions_or_confirmed_state_fail_golden_output() -> None:
    contract = compile_mvp_procedures().contracts[0]
    missing_questions = contract.output_contract.model_copy(
        update={"open_questions": []}
    )
    confirmed_state = [
        state.model_copy(update={"mode": "confirmed"})
        for state in contract.state_updates
    ]

    assert "unknowns_require_questions" in validate_golden_output(
        procedure_id=contract.id,
        output=missing_questions,
        state_updates=contract.state_updates,
        evidence_refs=contract.evidence_refs,
    )
    assert "state_update_not_proposed" in validate_golden_output(
        procedure_id=contract.id,
        output=contract.output_contract,
        state_updates=confirmed_state,
        evidence_refs=contract.evidence_refs,
    )


def test_wrong_evidence_or_procedure_is_rejected() -> None:
    contract = compile_mvp_procedures().contracts[0]

    assert "procedure_unknown" in validate_golden_output(
        procedure_id="procedure.unknown",
        output=contract.output_contract,
        state_updates=contract.state_updates,
        evidence_refs=contract.evidence_refs,
    )
    assert "evidence_refs_mismatch" in validate_golden_output(
        procedure_id=contract.id,
        output=contract.output_contract,
        state_updates=contract.state_updates,
        evidence_refs=(),
    )
