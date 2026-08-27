from pathlib import Path

from coaching.evidence import run
from coaching.evidence.dashboard import (
    MetricRequirement,
    build_evidence_dashboard,
    format_evidence_dashboard,
)
from coaching.evidence.facts import Fact, save_fact


def test_dashboard_separates_known_noncomparable_and_pending() -> None:
    dashboard = build_evidence_dashboard(
        [
            Fact(
                metric_definition="Ingreso",
                period="2026-07",
                source="ERP",
                confidence="high",
                value=100,
                decision="cash",
            ),
            Fact(
                metric_definition="Gasto",
                period="2026-07",
                source="Ads",
                confidence="medium",
                value=20,
                comparable=False,
                decision="cash",
            ),
        ],
        [
            MetricRequirement(
                metric_definition="Ingreso",
                decision="cash",
                question="¿Confirmas el ingreso?",
            ),
            MetricRequirement(
                metric_definition="Cobros",
                decision="cash",
                question="¿Cuánto cobraste realmente?",
            ),
        ],
    )
    assert [fact.metric_definition for fact in dashboard.known] == ["Ingreso"]
    assert [fact.metric_definition for fact in dashboard.not_comparable] == ["Gasto"]
    assert [gap.metric_definition for gap in dashboard.pending] == ["Cobros"]
    rendered = format_evidence_dashboard(dashboard)
    assert "no es una calificación" in rendered
    assert "Datos no comparables" in rendered
    assert "¿Cuánto cobraste realmente?" in rendered


def test_dashboard_run_is_local_and_never_emits_a_score(tmp_path: Path) -> None:
    save_fact(
        tmp_path,
        Fact(
            metric_definition="Ingreso",
            period="2026-07",
            source="ERP",
            confidence="high",
            value=100,
            decision="cash",
        ),
    )
    result = run(
        {
            "base_path": str(tmp_path),
            "action": "facts_dashboard",
            "requested_metrics": [
                {
                    "metric_definition": "Ingreso",
                    "decision": "cash",
                    "question": "¿Confirmas el ingreso?",
                }
            ],
        }
    )
    assert result["errors"] == []
    assert result["artifacts"]["summary"]["score"] is None
    assert result["artifacts"]["summary"]["known_count"] == 1
