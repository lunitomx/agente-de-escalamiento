#!/usr/bin/env python3
"""Re-qualify E37's existing local-workspace acceptance evidence."""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.e37_gates import GATE_CLASSES  # noqa: E402
from validators.gate_contract import GateContext  # noqa: E402
from validators.master_acceptance import (  # noqa: E402
    GateEvidenceReceipt,
    RequirementEvidenceReceipt,
    acceptance_requirement_declaration_hash,
    load_master_acceptance_ledger,
    master_acceptance_ledger_hash,
    render_requirement_evidence_receipt_json,
    verification_command_hash,
)


LEDGER_PATH = (
    ROOT / "work/epics/e36-product-truth-ip-governance/master-acceptance-ledger.yaml"
)
REQUIREMENTS = [f"REQ-E37-{index:03d}" for index in range(1, 8)]


def _run(command: list[str]) -> None:
    completed = subprocess.run(
        command, cwd=ROOT, check=False, capture_output=True, text=True
    )
    if completed.returncode != 0:
        raise RuntimeError("E37 qualification command failed")


def _source_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _qualify_current_contract() -> None:
    _run([sys.executable, "-m", "pytest", "tests/test_workspace_authority.py", "-q"])
    _run([sys.executable, "-m", "pytest", "tests/test_workspace_ingestion.py", "-q"])
    _run([sys.executable, "-m", "pytest", "tests/test_workspace_inbox.py", "-q"])
    _run([sys.executable, "-m", "pyright", "--pythonpath", sys.executable])
    quality_scope = ["coaching", "escala_server", "validators", "scripts", "tests"]
    _run([sys.executable, "-m", "ruff", "check", *quality_scope])
    _run([sys.executable, "-m", "ruff", "format", "--check", *quality_scope])
    for requirement_id in REQUIREMENTS:
        gate = GATE_CLASSES[requirement_id]()
        result = gate.evaluate(GateContext(gate_id=gate.gate_id, working_dir=ROOT))
        if not result.passed:
            raise RuntimeError("E37 requirement gate failed")


def _write_receipts() -> None:
    ledger = load_master_acceptance_ledger(LEDGER_PATH)
    ledger_hash = master_acceptance_ledger_hash(ledger)
    source_commit = _source_commit()
    for requirement_id in REQUIREMENTS:
        requirement = next(
            item for item in ledger.requirements if item.id == requirement_id
        )
        artifact_path = ROOT / requirement.evidence.artifact_path
        if artifact_path.is_symlink() or not artifact_path.is_file():
            raise RuntimeError("E37 qualification artifact unavailable")
        artifact_bytes = artifact_path.read_bytes()
        receipt = RequirementEvidenceReceipt(
            schema_version=1,
            requirement_id=requirement_id,
            ledger_sha256=ledger_hash,
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
        (ROOT / requirement.evidence.receipt_path).write_text(
            render_requirement_evidence_receipt_json(receipt), encoding="utf-8"
        )


def main() -> int:
    try:
        _qualify_current_contract()
        _write_receipts()
    except Exception:
        print("E37 qualification: unable to produce passing evidence", file=sys.stderr)
        return 1
    print("E37 qualification PASS: seven existing requirement receipts refreshed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
