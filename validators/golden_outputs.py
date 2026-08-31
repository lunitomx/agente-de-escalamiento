"""Golden assertions for structured ESCALA procedure outputs."""

from __future__ import annotations

from typing import Sequence

from validators.procedure_compiler import compile_mvp_procedures
from validators.procedure_contract import ProcedureOutputContract, StateUpdate


def validate_golden_output(
    *,
    procedure_id: str,
    output: ProcedureOutputContract,
    state_updates: Sequence[StateUpdate],
    evidence_refs: Sequence[str],
) -> tuple[str, ...]:
    """Return stable assertion IDs for one candidate procedure artifact.

    This validates structure and consent boundaries, not wording or a model's
    fluency. The compiled E65 contract is the only authority.
    """

    contracts = {
        contract.id: contract for contract in compile_mvp_procedures().contracts
    }
    contract = contracts.get(procedure_id)
    if contract is None:
        return ("procedure_unknown",)
    errors: list[str] = []
    if tuple(evidence_refs) != tuple(contract.evidence_refs):
        errors.append("evidence_refs_mismatch")
    values = (
        output.artifact,
        output.owner,
        output.kpi,
        output.who_what_when,
        output.review_cadence,
    )
    if any(value.status == "unknown" for value in values) and not output.open_questions:
        errors.append("unknowns_require_questions")
    expected_states = {(state.id, state.path) for state in contract.state_updates}
    actual_states = {(state.id, state.path) for state in state_updates}
    if actual_states != expected_states:
        errors.append("state_updates_mismatch")
    if any(
        state.mode != "proposed" or state.confirmation is not None
        for state in state_updates
    ):
        errors.append("state_update_not_proposed")
    return tuple(sorted(errors))
