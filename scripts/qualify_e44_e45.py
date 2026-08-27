"""Run an honest, deterministic technical qualification for E44 and E45.

This fixture proves the local contracts and their safety boundaries.  It does
not stand in for the entrepreneur pilot, the acceptance retrospective, or the
comparison against a real single-coach intervention required to close either
epic.
"""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from escala_server.outcome_learning import (  # noqa: E402
    OutcomeLearningLedger,
    render_learning_cockpit_html,
)
from escala_server.specialist_team import review  # noqa: E402


AS_OF = date(2026, 8, 27)
EVIDENCE_DIR = ROOT / "work/epics/e44-outcome-learning-and-accountability/evidence"
EVIDENCE_PATH = EVIDENCE_DIR / "e44-e45-technical-qualification.json"
MARKDOWN_PATH = EVIDENCE_DIR / "e44-e45-technical-qualification.md"


def run_qualification() -> dict[str, Any]:
    """Exercise the public, business-safe contracts using only synthetic data."""
    with tempfile.TemporaryDirectory(prefix="e44-e45-qualification-") as temporary:
        ledger = OutcomeLearningLedger(Path(temporary), "synthetic-company")
        completed_areas: list[str] = []
        for area, cadence in (
            ("people", "daily"),
            ("strategy", "monthly"),
            ("execution", "weekly"),
            ("cash", "quarterly"),
        ):
            cycle = ledger.register_decision(
                recommendation=f"Revisar el foco de {area}.",
                decision=f"Probar una acción reversible de {area}.",
                area=area,
                status="accepted",
                decided_by="Dueño sintético",
                reason="Fixture de calificación técnica.",
                evidence_ids=(f"evidence-{area}",),
                today=AS_OF,
            )
            action = ledger.add_action(
                cycle["id"],
                description=f"Ejecutar compromiso de {area}.",
                owner="Responsable sintético",
                review_on=AS_OF,
                cadence=cadence,  # type: ignore[arg-type]
                expected_result=f"Resultado verificable de {area}.",
                metric=f"Métrica de {area}",
            )
            result = ledger.record_result(
                cycle["id"],
                action["id"],
                status="observed",
                observed=f"Observación sintética de {area}.",
                evidence_ids=(f"result-{area}",),
                interpretation="La observación requiere revisión humana.",
                today=AS_OF,
            )
            learning = ledger.confirm_learning(
                cycle["id"],
                result["id"],
                statement=f"Lección revisada de {area}.",
                status="confirmed",
                confirmed_by="Dueño sintético",
                confidence=75,
                people_consent=area == "people",
                today=AS_OF,
            )
            assert result["causality"] == "unconfirmed"
            assert learning["causality"] == "not_claimed"
            completed_areas.append(area)

        pending = ledger.register_decision(
            recommendation="Revisar la cadencia de Execution.",
            decision="Esperar una medición adicional.",
            area="execution",
            status="accepted",
            decided_by="Dueño sintético",
            reason="Aún no hay evidencia suficiente.",
            today=AS_OF,
        )
        pending_action = ledger.add_action(
            pending["id"],
            description="Esperar el siguiente corte operativo.",
            owner="Responsable sintético",
            review_on=AS_OF,
            cadence="weekly",
            expected_result="Tener la medición completa.",
        )
        no_result = ledger.record_result(
            pending["id"],
            pending_action["id"],
            status="no_result_yet",
            observed=None,
            today=AS_OF,
        )
        cockpit = ledger.cockpit(AS_OF)
        cockpit_html = render_learning_cockpit_html(cockpit)
        reusable = ledger.reusable_learnings(AS_OF)
        assert no_result["status"] == "no_result_yet"
        assert len(reusable) == 4
        assert all(item["causality"] == "not_claimed" for item in reusable)
        assert "cycle:" not in cockpit_html and "action:" not in cockpit_html

    simple = review(
        {
            "areas": ["cash"],
            "evidence": [
                {
                    "areas": ["cash"],
                    "source_id": "cash-periodic-report",
                    "period": "2026-Q2",
                    "unit": "MXN",
                }
            ],
            "claims": [{"topic": "cobranza", "position": "verificar"}],
        }
    )
    missing_financial_context = review(
        {
            "areas": ["cash", "execution"],
            "material_risk": True,
            "evidence": [
                {"areas": ["cash"], "source_id": "cash-without-period"},
                {"areas": ["execution"], "source_id": "ops-weekly"},
            ],
            "claims": [],
        }
    )
    disagreement = review(
        {
            "areas": ["people", "strategy", "execution"],
            "owner_requests_cross_review": True,
            "evidence": [
                {"areas": ["people"], "source_id": "roles-approved"},
                {"areas": ["strategy"], "source_id": "market-dated"},
                {"areas": ["execution"], "source_id": "commitments-weekly"},
            ],
            "claims": [
                {"topic": "canal-prioritario", "position": "probar"},
                {"topic": "canal-prioritario", "position": "proteger"},
            ],
        }
    )
    assert simple["route"]["mode"] == "single_specialist"
    assert not simple["verification"]["blocked"]
    assert missing_financial_context["verification"]["blocked"]
    assert missing_financial_context["route"]["mode"] == "team"
    assert disagreement["route"]["mode"] == "team"
    assert len(disagreement["disagreements"]) == 1

    return {
        "schema_version": 1,
        "status": "pass",
        "fixture": "synthetic-local-company",
        "e44": {
            "completed_decision_areas": completed_areas,
            "confirmed_reusable_learnings": len(reusable),
            "no_result_yet_is_allowed": no_result["status"] == "no_result_yet",
            "causality_is_not_claimed": True,
            "cockpit_hides_internal_ids": True,
        },
        "e45": {
            "simple_case": {
                "mode": simple["route"]["mode"],
                "roles": list(simple["route"]["roles"]),
            },
            "missing_cash_context": {
                "mode": missing_financial_context["route"]["mode"],
                "blocked": missing_financial_context["verification"]["blocked"],
                "context_receipts": missing_financial_context["context_receipts"],
            },
            "cross_decision_disagreement": {
                "mode": disagreement["route"]["mode"],
                "roles": list(disagreement["route"]["roles"]),
                "disagreements": len(disagreement["disagreements"]),
                "context_receipts": disagreement["context_receipts"],
            },
        },
        "not_proved": [
            "entrepreneur_pilot",
            "owner_acceptance_retrospective",
            "value_comparison_against_a_real_single_coach",
            "platform_packaging_in_E67",
        ],
        "verification_commands": [
            "uv run python scripts/qualify_e44_e45.py",
            "uv run pytest tests/test_outcome_learning.py tests/test_specialist_team.py tests/test_qualify_e44_e45.py -q",
            "uv run ruff check scripts/qualify_e44_e45.py tests/test_qualify_e44_e45.py",
            "uv run pyright scripts/qualify_e44_e45.py",
        ],
    }


def main() -> int:
    receipt = run_qualification()
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = [
        "# E44/E45 Technical Qualification Receipt",
        "",
        "- status: pass",
        "- fixture: synthetic-local-company",
        "- scope: deterministic local contracts only",
        "",
        "## Demonstrated",
        "",
        "- E44 completes one confirmed learning per decision area with People consent.",
        "- E44 preserves a valid `no_result_yet` state and does not claim causality.",
        "- E44 cockpit output hides storage identifiers.",
        "- E45 keeps a simple Cash request single-specialist.",
        "- E45 blocks Cash evidence lacking period or unit before synthesis.",
        "- E45 surfaces a cross-decision disagreement without choosing by majority.",
        "",
        "## Not a closure substitute",
        "",
        *[f"- {item}" for item in receipt["not_proved"]],
        "",
    ]
    MARKDOWN_PATH.write_text("\n".join(markdown), encoding="utf-8")
    print(f"E44/E45 technical qualification PASS: {EVIDENCE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
