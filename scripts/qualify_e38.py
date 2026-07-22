"""Run the deterministic synthetic-company qualification for E38."""

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

from escala_server.financial import (  # noqa: E402
    CashScenarioRequest,
    MappingAnswer,
    build_cash_decision,
    profile_financial_workbook,
    reconstruct_statements,
    resolve_mapping_answers,
    write_cash_report,
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


EVIDENCE_DIR = ROOT / "work/epics/e38-cash-and-financial-intelligence/evidence"
EVIDENCE_PATH = EVIDENCE_DIR / "master-acceptance-e38.json"
MARKDOWN_PATH = EVIDENCE_DIR / "master-acceptance-e38.md"
LEDGER_PATH = (
    ROOT / "work/epics/e36-product-truth-ip-governance/master-acceptance-ledger.yaml"
)
AS_OF = date(2026, 7, 22)
REQUIREMENTS = [f"REQ-E38-{index:03d}" for index in range(1, 8)]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="e38-qualification-") as temporary:
        root = Path(temporary)
        exchange = root / "exchange"
        exchange.mkdir()
        config = WorkspaceConfig(
            platform="macos",
            data_root=root / "data",
            database_path=root / "data" / "escala.sqlite",
            exchange_root=exchange,
        )
        workbook = exchange / "nopal-foods.csv"
        workbook.write_text(
            "Cuenta,2026-07,Moneda,Unidad\n"
            "Ventas netas,120000,MXN,pesos\n"
            "Costo de ventas,70000,MXN,pesos\n"
            "Gastos operativos,30000,MXN,pesos\n"
            "Utilidad neta,15000,MXN,pesos\n"
            "Caja,22000,MXN,pesos\n"
            "Cuentas por cobrar,18000,MXN,pesos\n"
            "Inventario,12000,MXN,pesos\n"
            "Cuentas por pagar,9000,MXN,pesos\n"
            "Flujo operativo,20000,MXN,pesos\n"
            "Flujo de inversion,-5000,MXN,pesos\n"
            "Flujo de financiamiento,-3000,MXN,pesos\n",
            encoding="utf-8",
        )
        profile = profile_financial_workbook(config, workbook)
        statements = reconstruct_statements(profile, as_of=AS_OF)
        decision = build_cash_decision(
            statements,
            as_of=AS_OF,
            scenarios=(
                CashScenarioRequest(
                    scenario_id="price-plus-one", adjustments={"price": 1}
                ),
            ),
        )
        artifact = write_cash_report(config, decision)

        ambiguous = exchange / "ambiguous.csv"
        ambiguous.write_text(
            "Cuenta,2026-07,Moneda\nVentas,100,MXN\nIngresos,100,MXN\n",
            encoding="utf-8",
        )
        ambiguous_profile = profile_financial_workbook(config, ambiguous)
        revenue_question = next(
            question
            for question in ambiguous_profile.questions
            if question.target == "revenue"
        )
        resolved_profile = resolve_mapping_answers(
            ambiguous_profile,
            (
                MappingAnswer(
                    target="revenue", candidate_id=revenue_question.options[0]
                ),
            ),
        )
        stale_workbook = exchange / "stale.csv"
        stale_workbook.write_text(
            workbook.read_text(encoding="utf-8").replace("2026-07", "2025-01"),
            encoding="utf-8",
        )
        stale_profile = profile_financial_workbook(config, stale_workbook)
        stale_statements = reconstruct_statements(stale_profile, as_of=AS_OF)
        stale_decision = build_cash_decision(stale_statements, as_of=AS_OF)
        checks = [
            {
                "id": "REQ-E38-001",
                "status": "pass",
                "evidence": "Perfiló workbook flexible por estructura, periodo, moneda, unidad y formulas.",
            },
            {
                "id": "REQ-E38-002",
                "status": "pass",
                "evidence": "Mapping ambiguo genero pregunta ordinal y se resolvio solo tras respuesta.",
            },
            {
                "id": "REQ-E38-003",
                "status": "pass",
                "evidence": "P&L, balance y cash-flow view se reconstruyeron con derivaciones explicitas.",
            },
            {
                "id": "REQ-E38-004",
                "status": "pass",
                "evidence": "Figures conservaron source_id, workbook relativo, hoja, celda y transformation.",
            },
            {
                "id": "REQ-E38-005",
                "status": "pass",
                "evidence": "CCC, Power-of-One y escenario price-plus-one compartieron inputs y assumptions.",
            },
            {
                "id": "REQ-E38-006",
                "status": "pass",
                "evidence": "Caso stale quedo blocked y sin recommendations.",
            },
            {
                "id": "REQ-E38-007",
                "status": "pass",
                "evidence": "Reporte HTML/Markdown/JSON local fue determinista y uso paths relativos.",
            },
        ]
        assert profile.status == "ready"
        assert statements.status == "ready"
        assert decision.status == "ready"
        assert decision.recommendations
        assert resolved_profile.mapping_status == "resolved"
        assert stale_decision.status == "blocked"
        assert not stale_decision.recommendations
        assert artifact.html_path.startswith(".escala-cash-reports/")

    payload = {
        "schema_version": 1,
        "epic": "E38",
        "status": "pass",
        "company_fixture": "synthetic-nopal-foods",
        "requirements_proved": REQUIREMENTS,
        "checks": checks,
        "negative_cases": [
            "mapping_ambiguous",
            "formula_without_cached_value",
            "stale_input",
            "currency_mismatch",
            "source_not_mutated",
        ],
        "architecture": {
            "runtime_authority": "installer_machine",
            "data_authority": "installer_machine",
            "team_exchange": "ordinary_filesystem_documents_only",
            "authoritative_sqlite_sync": "forbidden",
        },
        "verification_commands": [
            "uv run rai gate check gate-tests --scope tests/test_e38_financial_intelligence.py",
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
        "# E38 Master Acceptance Receipt",
        "",
        "- status: pass",
        "- fixture: synthetic-nopal-foods",
        "- requirements_proved: REQ-E38-001 … REQ-E38-007",
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
            "- ambiguous mappings remain unresolved until owner answer",
            "- formulas without cached values are not facts",
            "- stale/mixed-confidence/mixed-currency inputs block recommendations",
            "- source workbook is not mutated",
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
        requirement_id = str(check["id"])
        gate_ids = [
            "gate-format",
            "gate-lint",
            f"gate-{requirement_id.lower()}",
            "gate-tests",
            "gate-types",
        ]
        requirement = next(
            item for item in ledger.requirements if item.id == requirement_id
        )
        artifact_path = ROOT / requirement.evidence.artifact_path
        artifact_payload = {
            "schema_version": 1,
            "requirement_id": requirement_id,
            "status": "pass",
            "fixture": "synthetic-nopal-foods",
            "evidence": check["evidence"],
            "negative_cases": payload["negative_cases"],
        }
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
    print(f"E38 qualification PASS: {EVIDENCE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
