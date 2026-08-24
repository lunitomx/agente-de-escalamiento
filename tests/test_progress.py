"""Acceptance coverage for the novice-facing progress dashboard."""
from __future__ import annotations

from coaching.core import write_yaml
from coaching.opsp import run as run_opsp
from coaching.progress import run as run_progress


COMPLETE_PLAN = {
    "company_name": "Taller Norte",
    "core_values": ["Honestidad", "Calidad", "Aprender"],
    "purpose": "Hacer más fácil el trabajo de talleres independientes.",
    "bhag": "Ser la red líder de talleres del norte.",
    "bhag_date": "2040-12-31",
    "sandbox": {"market": "Norte de México"},
    "brand_promise": {"promise": "Diagnóstico en 24 horas", "kpi": "% entregado en 24 horas"},
    "quarter": "Q3 2026",
    "critical_number": "90% de diagnósticos en 24 horas",
    "year": "2026",
    "annual_revenue": "$12M MXN",
    "annual_profit": "$2M MXN",
    "annual_priorities": [{"priority": "Abrir dos sucursales", "owner": "Ana", "kpi": "2 aperturas"}],
    "quarterly_priorities": [{"priority": "Reducir tiempos", "owner": "Luis", "kpi": "90% en 24 horas"}],
}


def test_completed_opsp_is_counted_and_progress_stays_novice_friendly(tmp_path):
    write_yaml(
        tmp_path / ".scaleup" / "agent" / "memory" / "company-profile.yaml",
        {"company": {"name": "Taller Norte"}, "scores": {"people": 3, "strategy": 2, "execution": 4, "cash": 3}},
    )
    saved = run_opsp({"base_path": tmp_path, "updated_at": "2026-08-24", "data": COMPLETE_PLAN, "complete": True})
    assert saved["artifacts"]["status"] == "completed"

    first = run_progress({"base_path": tmp_path})
    resumed = run_progress({"base_path": tmp_path})

    assert first["artifacts"]["completed_worksheets"] == 1
    assert first["artifacts"]["per_decision"]["strategy"] == {"score": 2, "total": 4, "completed": 1}
    assert "**Estrategia:** 1/4 (25%)" in first["output"]
    assert "✅ Plan de la empresa en una hoja" in first["output"]
    assert resumed["artifacts"] == first["artifacts"]
    for forbidden in ("OPSP", "Worksheet", "SWT Analysis", "7 Strata", "KPI Development", "Cash Conversion Cycle", "intermediate"):
        assert forbidden not in first["output"]
    assert "### Siguiente paso" in first["output"]
    assert "Fortalezas, retos y cambios del mercado" in first["output"]
