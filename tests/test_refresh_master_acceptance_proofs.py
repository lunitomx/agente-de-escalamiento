from __future__ import annotations

import pytest

from scripts.refresh_master_acceptance_proofs import ProofRefreshError, apply_refreshes


def test_apply_refreshes_replaces_only_the_declared_proved_hash() -> None:
    old_hash = "a" * 64
    new_hash = "b" * 64
    ledger = f"""requirements:
  - id: REQ-E40-001
    proof: {{state: proved, receipt_sha256: {old_hash}}}
  - id: REQ-E42-001
    proof: {{state: unproved, blockers: [evidence.missing]}}
"""

    refreshed = apply_refreshes(
        ledger,
        {"REQ-E40-001": (old_hash, new_hash)},
    )

    assert new_hash in refreshed
    assert old_hash not in refreshed
    assert "REQ-E42-001" in refreshed
    assert "state: unproved" in refreshed


def test_apply_refreshes_refuses_changed_or_unproved_proof_lines() -> None:
    ledger = """requirements:
  - id: REQ-E40-001
    proof: {state: unproved, blockers: [evidence.missing]}
"""

    with pytest.raises(ProofRefreshError, match="proved proof line not found"):
        apply_refreshes(ledger, {"REQ-E40-001": ("a" * 64, "b" * 64)})
