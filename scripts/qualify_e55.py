"""Run a deterministic, local acceptance qualification for E55."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from coaching.evidence import run as evidence_run  # noqa: E402
from coaching.evidence.facts import Fact, load_facts  # noqa: E402
from coaching.welcome import run as welcome_run  # noqa: E402


EVIDENCE_DIR = ROOT / "work/epics/e55-onboarding-multifuente-conciliacion/evidence"
EVIDENCE_PATH = EVIDENCE_DIR / "e55-qualification.json"
MARKDOWN_PATH = EVIDENCE_DIR / "e55-qualification.md"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="e55-qualification-") as temporary:
        base = Path(temporary) / "empresa-sintetica"
        fact = {
            "metric_definition": "Ingreso",
            "period": "2026-07",
            "source": "erp-julio.csv",
            "confidence": "high",
            "value": 120000,
            "decision": "cash",
        }
        first_turn = welcome_run(
            {
                "action": "adaptive_conversation",
                "message": "Necesito entender mi cash.",
                "base_path": str(base),
            }
        )
        rejected_write = welcome_run(
            {
                "action": "adaptive_conversation",
                "message": "Necesito entender mi cash.",
                "confirmed_facts": [fact],
                "base_path": str(base),
            }
        )
        assert rejected_write["errors"]
        assert load_facts(base) == []
        accepted_write = welcome_run(
            {
                "action": "adaptive_conversation",
                "message": "Necesito entender mi cash.",
                "confirmed_facts": [fact],
                "persist_authorized": True,
                "base_path": str(base),
            }
        )
        reconciliation = evidence_run(
            {
                "action": "cash_reconciliation",
                "measurements": [
                    {
                        "measurement_id": "cobro-banco",
                        "kind": "collection",
                        "value": 100.0,
                        "currency": "MXN",
                        "period": "2026-07",
                        "basis_date": "2026-07-31",
                        "source": "banco-julio.csv",
                    },
                    {
                        "measurement_id": "compra-erp",
                        "kind": "purchase",
                        "value": 100.0,
                        "currency": "MXN",
                        "period": "2026-07",
                        "basis_date": "2026-07-31",
                        "source": "compras-julio.csv",
                    },
                ],
            }
        )
        entities = evidence_run(
            {
                "action": "entity_resolution",
                "candidates": [
                    {
                        "candidate_id": "cliente-erp",
                        "entity_type": "customer",
                        "name": "Acme SA",
                        "primary_id": "RFC-123",
                        "source": "erp.csv",
                    },
                    {
                        "candidate_id": "cliente-crm",
                        "entity_type": "customer",
                        "name": "ACME Internacional",
                        "primary_id": "RFC-123",
                        "source": "crm.csv",
                    },
                ],
            }
        )
        parking_lot = evidence_run(
            {
                "action": "decision_map",
                "base_path": str(base),
                "decision": "cash",
                "requested_metrics": [
                    {
                        "metric_definition": "Cobros",
                        "decision": "cash",
                        "question": "¿Cuánto cobraste realmente?",
                    }
                ],
            }
        )

        dashboard = first_turn["artifacts"]["evidence_dashboard"]
        reconciliation_findings = reconciliation["artifacts"]["reconciliation"][
            "findings"
        ]
        entity_resolutions = entities["artifacts"]["resolutions"]
        parking_path = Path(parking_lot["artifacts"]["path"])
        checks = [
            {
                "id": "E55-01",
                "evidence": "Welcome creates a no-score local evidence dashboard and asks one Cash question.",
            },
            {
                "id": "E55-02",
                "evidence": "Confirmed facts fail closed without authorization, then persist locally with provenance.",
            },
            {
                "id": "E55-03",
                "evidence": "Collection and purchase remain incompatible; no ratio is produced.",
            },
            {
                "id": "E55-04",
                "evidence": "Same-ID, different-name customers remain ambiguous rather than merging.",
            },
            {
                "id": "E55-05",
                "evidence": "Missing evidence becomes a local open parking-lot item.",
            },
        ]
        assert first_turn["errors"] == []
        assert first_turn["output"].count("?") == 1
        assert "score" not in dashboard
        assert accepted_write["errors"] == []
        assert accepted_write["output"].startswith("¿Cuánto cobraste")
        persisted = load_facts(base)
        assert len(persisted) == 1
        assert (
            persisted[0].metric_definition
            == Fact.model_validate(fact).metric_definition
        )
        assert reconciliation["errors"] == []
        assert any(item["kind"] == "incompatible" for item in reconciliation_findings)
        assert entities["errors"] == []
        assert entity_resolutions[0]["status"] == "ambiguous"
        assert parking_lot["errors"] == []
        assert parking_path.is_relative_to(base)
        assert parking_lot["artifacts"]["decision_map"]["items"][0]["status"] == "open"

    payload = {
        "schema_version": 1,
        "epic": "E55",
        "status": "pass",
        "fixture": "synthetic-local-company",
        "checks": checks,
        "negative_cases": [
            "fact_write_without_explicit_authorization",
            "score_before_diagnosis",
            "cross-nature-financial-comparison",
            "same-id-different-name-entity-fusion",
            "nonlocal-evidence-parking-lot",
        ],
        "verification_commands": [
            "uv run pytest coaching/evidence/tests coaching/welcome/tests -q",
            "uv run pyright coaching/evidence coaching/welcome",
            "uv run ruff check coaching/evidence coaching/welcome",
        ],
    }
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_lines = [
        "# E55 Qualification Receipt",
        "",
        "- status: pass",
        "- fixture: synthetic-local-company",
        "",
        "## Checks",
        "",
        *[f"- {item['id']}: {item['evidence']}" for item in checks],
        "",
        "## Boundaries demonstrated",
        "",
        "- No score before diagnosis.",
        "- No fact persistence without explicit authorization.",
        "- No comparison between incompatible financial natures.",
        "- No aggressive entity fusion.",
        "- Decision-map artifact stays inside the synthetic local company directory.",
        "",
    ]
    MARKDOWN_PATH.write_text("\n".join(markdown_lines), encoding="utf-8")
    print(f"E55 qualification PASS: {EVIDENCE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
