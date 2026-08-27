from pathlib import Path

from coaching.evidence import run
from coaching.evidence.dashboard import MetricRequirement, build_evidence_dashboard
from coaching.evidence.decision_map import build_decision_map, save_decision_map
from coaching.evidence.facts import Fact


def test_decision_map_turns_gaps_and_noncomparable_facts_into_open_work(
    tmp_path: Path,
):
    dashboard = build_evidence_dashboard(
        [
            Fact(
                metric_definition="Cobros",
                period="2026-07",
                source="banco.csv",
                confidence="medium",
                value=100,
                comparable=False,
                decision="cash",
            )
        ],
        [
            MetricRequirement(
                metric_definition="Ingreso",
                decision="cash",
                question="¿Cuál es tu ingreso?",
            )
        ],
    )
    decision_map = build_decision_map(dashboard, decision="cash")
    assert [item.title for item in decision_map.items] == [
        "Completar: Ingreso",
        "Aclarar comparabilidad: Cobros",
    ]
    path = save_decision_map(tmp_path, decision_map)
    assert path == tmp_path / ".escala" / "agent" / "memory" / "decision-map.yaml"


def test_decision_map_run_persists_only_local_evidence_work(tmp_path: Path):
    result = run(
        {
            "base_path": str(tmp_path),
            "action": "decision_map",
            "decision": "cash",
            "requested_metrics": [
                {
                    "metric_definition": "Cobros",
                    "decision": "cash",
                    "question": "¿Cuánto cobraste?",
                }
            ],
        }
    )
    assert result["errors"] == []
    assert result["artifacts"]["path"].startswith(str(tmp_path))
    assert result["artifacts"]["decision_map"]["items"][0]["status"] == "open"
