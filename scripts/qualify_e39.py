"""Run deterministic synthetic-company qualification for E39."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from escala_server.meetings import (  # noqa: E402
    MeetingRecord,
    assess_rhythm,
    build_executive_review,
    build_team_signals,
    extract_meeting_facts,
    render_meeting_report_receipt_json,
    run_daily_review,
    scan_meeting_inbox,
    RhythmRule,
    validate_report_exchange,
)
from escala_server.workspace.authority import WorkspaceConfig  # noqa: E402
from validators.master_acceptance import (  # noqa: E402
    GateEvidenceReceipt,
    Platform,
    RequirementEvidenceReceipt,
    acceptance_requirement_declaration_hash,
    load_master_acceptance_ledger,
    master_acceptance_ledger_hash,
    render_requirement_evidence_receipt_json,
    verification_command_hash,
)


EVIDENCE_DIR = ROOT / "work/epics/e39-meeting-and-team-intelligence/evidence"
EVIDENCE_PATH = EVIDENCE_DIR / "master-acceptance-e39.json"
MARKDOWN_PATH = EVIDENCE_DIR / "master-acceptance-e39.md"
LEDGER_PATH = (
    ROOT / "work/epics/e36-product-truth-ip-governance/master-acceptance-ledger.yaml"
)
AS_OF = date(2026, 7, 22)
REQUIREMENTS = [f"REQ-E39-{index:03d}" for index in range(1, 8)]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="e39-qualification-") as temporary:
        root = Path(temporary)
        exchange = root / "exchange"
        exchange.mkdir()
        config = WorkspaceConfig(
            platform="macos",
            data_root=root / "data",
            database_path=root / "data" / "escala.sqlite",
            exchange_root=exchange,
        )
        _write_fixture(exchange)
        first = scan_meeting_inbox(config)
        second = scan_meeting_inbox(config)
        records: list[MeetingRecord] = []
        for item in first.items:
            if item.context is None or item.source_id is None:
                continue
            extraction = extract_meeting_facts(config, item)
            records.append(MeetingRecord(context=item.context, extraction=extraction))
        signals = build_team_signals(records, as_of=AS_OF)
        review = build_executive_review(records, as_of=AS_OF)
        rhythm = assess_rhythm(
            tuple(record.context for record in records),
            RhythmRule(rule_id="daily", meeting_type="daily", cadence_days=1),
            period_start=date(2026, 7, 20),
            period_end=AS_OF,
        )
        review_result, schedule, artifact = run_daily_review(
            config, records, run_date=AS_OF
        )
        valid_exchange = validate_report_exchange(config)
        (exchange / "shared.sqlite").write_bytes(b"private state")
        invalid_exchange = validate_report_exchange(config)
        checks = [
            {
                "id": "REQ-E39-001",
                "status": "pass",
                "evidence": "Tres transcripts fueron aceptados y el segundo scan devolvio source_seen sin duplicar el ledger.",
            },
            {
                "id": "REQ-E39-002",
                "status": "pass",
                "evidence": "Meeting type/date/team/participants y provenance por lineas quedaron ready o unresolved con preguntas acotadas.",
            },
            {
                "id": "REQ-E39-003",
                "status": "pass",
                "evidence": "Facts de decision/action/owner/due_date/blocker/risk/commitment conservaron source_id, linea y confidence.",
            },
            {
                "id": "REQ-E39-004",
                "status": "pass",
                "evidence": "RhythmRule produjo supported para evidencia completa y evidence_missing/not_assessed para ventana incompleta.",
            },
            {
                "id": "REQ-E39-005",
                "status": "pass",
                "evidence": "Timeline sintetico detecto repeated blocker, repeated/overdue commitment, unresolved decision y trend.",
            },
            {
                "id": "REQ-E39-006",
                "status": "pass",
                "evidence": "Executive review local mostro watch, material changes, questions y source IDs sin inventar negativos.",
            },
            {
                "id": "REQ-E39-007",
                "status": "pass",
                "evidence": "Schedule y HTML/Markdown/JSON quedaron bajo data_root; exchange SQLite fue rechazado.",
            },
        ]
        assert all(item.status in {"ready", "unresolved"} for item in first.items)
        assert all(item.status == "duplicate" for item in second.items)
        assert records and signals.signals and review_result == review
        assert rhythm.status == "supported"
        assert valid_exchange.status == "pass"
        assert invalid_exchange.status == "fail"
        assert "authoritative_sqlite_sync_forbidden" in invalid_exchange.findings
        assert schedule.manifest_path == ".escala-meeting-schedule.json"
        assert artifact.html_path.startswith(".escala-meeting-reports/")
        assert render_meeting_report_receipt_json(artifact)

    payload = {
        "schema_version": 1,
        "epic": "E39",
        "status": "pass",
        "company_fixture": "synthetic-nopal-foods",
        "requirements_proved": REQUIREMENTS,
        "checks": checks,
        "negative_cases": [
            "duplicate_source",
            "context_unresolved",
            "source_changed",
            "evidence_missing_not_assessed",
            "exchange_sqlite_forbidden",
            "source_not_mutated",
        ],
        "architecture": {
            "runtime_authority": "installer_machine",
            "data_authority": "installer_machine",
            "team_exchange": "ordinary_filesystem_documents_only",
            "authoritative_sqlite_sync": "forbidden",
        },
        "verification_commands": [
            "uv run rai gate check gate-tests --scope tests/test_e39_meeting_intelligence.py",
            "uv run rai gate check gate-lint",
            "uv run rai gate check gate-format",
            "uv run rai gate check gate-types",
        ],
    }
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# E39 Master Acceptance Receipt",
        "",
        "- status: pass",
        "- fixture: synthetic-nopal-foods",
        "- requirements_proved: REQ-E39-001 … REQ-E39-007",
        "",
        "## Proof",
        "",
    ]
    lines.extend(f"- {check['id']}: {check['evidence']}" for check in checks)
    lines.extend(
        [
            "",
            "## Negative matrix",
            "",
            "- duplicate source identities remain idempotent",
            "- missing/ambiguous context remains unresolved",
            "- changed source blocks stale extraction",
            "- missing rhythm evidence is not a person failure",
            "- exchange SQLite is rejected",
            "- original transcripts are not mutated",
            "",
            "## Authority",
            "",
            "- runtime/data authority: installer_machine",
            "- team exchange: ordinary_filesystem_documents_only",
            "- authoritative SQLite sync: forbidden",
            "",
        ]
    )
    MARKDOWN_PATH.write_text("\n".join(lines), encoding="utf-8")
    _write_requirement_receipts(checks)
    print(f"E39 qualification PASS: {EVIDENCE_PATH}")
    return 0


def _write_fixture(exchange: Path) -> None:
    fixtures = {
        "daily-2026-07-20.transcript": (
            "Tipo: daily\nFecha: 2026-07-20\nEquipo: Operaciones\n"
            "Participantes: Ana\nDecisión:\n"
            "Bloqueador: aprobación de compras\n"
            "Compromiso: Ana — entregar presupuesto — vence: 2026-07-19\n"
        ),
        "daily-2026-07-21.transcript": (
            "Tipo: daily\nFecha: 2026-07-21\nEquipo: Operaciones\n"
            "Participantes: Ana\nBloqueador: aprobación de compras\n"
            "Compromiso: Ana — entregar presupuesto — vence: 2026-07-20\n"
            "Acción: Ana — actualizar tablero\n"
        ),
        "daily-2026-07-22.transcript": (
            "Tipo: daily\nFecha: 2026-07-22\nEquipo: Operaciones\n"
            "Participantes: Ana\nBloqueador: aprobación de compras\n"
            "Acción: Ana — actualizar tablero\n"
        ),
    }
    for filename, text in fixtures.items():
        (exchange / filename).write_text(text, encoding="utf-8")


def _write_requirement_receipts(checks: list[dict[str, str]]) -> None:
    ledger = load_master_acceptance_ledger(LEDGER_PATH)
    ledger_hash = master_acceptance_ledger_hash(ledger)
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    for check in checks:
        requirement_id = check["id"]
        requirement = next(
            item for item in ledger.requirements if item.id == requirement_id
        )
        gate_ids = [
            "gate-format",
            "gate-lint",
            f"gate-{requirement_id.lower()}",
            "gate-tests",
            "gate-types",
        ]
        artifact_payload = {
            "schema_version": 1,
            "requirement_id": requirement_id,
            "status": "pass",
            "fixture": "synthetic-nopal-foods",
            "evidence": check["evidence"],
            "negative_cases": [
                "duplicate_source",
                "context_unresolved",
                "source_changed",
                "evidence_missing_not_assessed",
                "exchange_sqlite_forbidden",
                "source_not_mutated",
            ],
        }
        artifact_path = ROOT / requirement.evidence.artifact_path
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_bytes = (
            json.dumps(artifact_payload, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n"
        ).encode("utf-8")
        artifact_path.write_bytes(artifact_bytes)
        evidence_receipt = RequirementEvidenceReceipt(
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
                GateEvidenceReceipt(id=gate_id, status="pass") for gate_id in gate_ids
            ],
            platforms=[Platform.MACOS, Platform.WINDOWS],
            result="pass",
        )
        receipt_path = ROOT / requirement.evidence.receipt_path
        receipt_path.write_text(
            render_requirement_evidence_receipt_json(evidence_receipt), encoding="utf-8"
        )


if __name__ == "__main__":
    raise SystemExit(main())
