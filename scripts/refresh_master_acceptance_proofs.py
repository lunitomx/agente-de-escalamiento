#!/usr/bin/env python3
"""Safely refresh hashes for already-proved master-acceptance evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from validators.master_acceptance import (  # noqa: E402
    ProvedProof,
    RequirementEvidenceReceipt,
    acceptance_requirement_declaration_hash,
    load_master_acceptance_ledger,
    master_acceptance_ledger_hash,
    verification_command_hash,
)


class ProofRefreshError(ValueError):
    """A receipt is not safe to promote into the declared proof hash."""


def collect_refreshes(
    repository_root: Path,
    ledger_path: Path,
    *,
    epic: str | None = None,
) -> dict[str, tuple[str, str]]:
    """Return `{requirement_id: (old_hash, new_hash)}` for valid stale proofs.

    This deliberately never promotes an `unproved` requirement. It accepts a
    receipt only when every stable contract attribute and its artifact validate.
    """

    ledger = load_master_acceptance_ledger(ledger_path)
    ledger_hash = master_acceptance_ledger_hash(ledger)
    updates: dict[str, tuple[str, str]] = {}
    errors: list[str] = []

    for requirement in ledger.requirements:
        if epic is not None and requirement.owner.epic != epic:
            continue
        if not isinstance(requirement.proof, ProvedProof):
            continue

        try:
            receipt_path = repository_root / requirement.evidence.receipt_path
            if receipt_path.is_symlink() or not receipt_path.is_file():
                raise ProofRefreshError("receipt is unavailable")
            receipt_bytes = receipt_path.read_bytes()
            if len(receipt_bytes) > ledger.limits.max_receipt_bytes:
                raise ProofRefreshError("receipt exceeds bounded size")
            receipt = RequirementEvidenceReceipt.model_validate(
                json.loads(receipt_bytes)
            )
            if receipt.requirement_id != requirement.id:
                raise ProofRefreshError("requirement id mismatch")
            if receipt.ledger_sha256 != ledger_hash:
                raise ProofRefreshError("ledger semantic hash mismatch")
            if receipt.declaration_sha256 != acceptance_requirement_declaration_hash(
                requirement
            ):
                raise ProofRefreshError("requirement declaration hash mismatch")
            if receipt.command_sha256 != verification_command_hash(
                requirement.evidence.verification_command
            ):
                raise ProofRefreshError("verification command hash mismatch")
            if [
                gate.id for gate in receipt.gate_results
            ] != requirement.evidence.required_gates:
                raise ProofRefreshError("gate declaration mismatch")
            if any(gate.status != "pass" for gate in receipt.gate_results):
                raise ProofRefreshError("a required gate did not pass")
            if receipt.platforms != requirement.platforms:
                raise ProofRefreshError("platform declaration mismatch")
            _require_git_commit(repository_root, receipt.source_commit)

            artifact_path = repository_root / requirement.evidence.artifact_path
            if artifact_path.is_symlink() or not artifact_path.is_file():
                raise ProofRefreshError("artifact is unavailable")
            if (
                hashlib.sha256(artifact_path.read_bytes()).hexdigest()
                != receipt.artifact_sha256
            ):
                raise ProofRefreshError("artifact hash mismatch")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{requirement.id}: {exc}")
            continue

        current_hash = hashlib.sha256(receipt_bytes).hexdigest()
        if current_hash != requirement.proof.receipt_sha256:
            updates[requirement.id] = (requirement.proof.receipt_sha256, current_hash)

    if errors:
        raise ProofRefreshError("invalid proved evidence:\n" + "\n".join(errors))
    return updates


def apply_refreshes(
    ledger_text: str,
    updates: dict[str, tuple[str, str]],
) -> str:
    """Replace only one-line hashes of declared `proved` requirements."""

    refreshed = ledger_text
    for requirement_id, (old_hash, new_hash) in updates.items():
        pattern = re.compile(
            rf"(?ms)(^\s*- id: {re.escape(requirement_id)}\n.*?^\s+proof: \{{state: proved, receipt_sha256: )([0-9a-f]{{64}})(\}}\s*$)"
        )
        match = pattern.search(refreshed)
        if match is None:
            raise ProofRefreshError(f"{requirement_id}: proved proof line not found")
        if match.group(2) != old_hash:
            raise ProofRefreshError(
                f"{requirement_id}: proof hash changed during refresh"
            )
        refreshed = refreshed[: match.start(2)] + new_hash + refreshed[match.end(2) :]
    return refreshed


def _require_git_commit(repository_root: Path, commit: str) -> None:
    completed = subprocess.run(
        ["git", "-C", str(repository_root), "cat-file", "-e", f"{commit}^{{commit}}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ProofRefreshError("receipt source commit is unavailable")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh hashes for already-proved, fully validated evidence receipts."
    )
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument(
        "--ledger",
        type=Path,
        default=ROOT
        / "work/epics/e36-product-truth-ip-governance/master-acceptance-ledger.yaml",
    )
    parser.add_argument("--epic")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    repository_root = args.repo.resolve()
    ledger_path = args.ledger.resolve()
    updates = collect_refreshes(repository_root, ledger_path, epic=args.epic)
    if not updates:
        print("No proved evidence hashes require refresh.")
        return 0
    for requirement_id, (_, new_hash) in sorted(updates.items()):
        print(f"{requirement_id}: {new_hash}")
    if not args.write:
        print("Dry run only. Re-run with --write to update the declared proof hashes.")
        return 0

    text = ledger_path.read_text(encoding="utf-8")
    ledger_path.write_text(apply_refreshes(text, updates), encoding="utf-8")
    print(f"Refreshed {len(updates)} declared proof hashes in {ledger_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
