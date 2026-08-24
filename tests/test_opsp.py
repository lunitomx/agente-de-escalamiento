"""OPSP persistence and validation acceptance tests."""
from __future__ import annotations

from coaching.opsp import ARTIFACT_PATH, load_opsp_knowledge, run, validate_opsp
from coaching.router import run as route


COMPLETE_PLAN = {
    "company_name": "Taller Norte",
    "core_values": [{"name": "Honestidad"}, {"name": "Calidad"}, {"name": "Aprender"}],
    "purpose": "Hacer más fácil el trabajo de talleres independientes.",
    "bhag": "Ser la red líder de talleres del norte.",
    "bhag_date": "2040-12-31",
    "sandbox": {"market": "Norte de México", "customer_segment": "Talleres independientes"},
    "brand_promise": {"promise": "Diagnóstico en 24 horas", "kpi": "% entregado en 24 horas"},
    "quarter": "Q3 2026",
    "critical_number": "90% de diagnósticos en 24 horas",
    "year": "2026",
    "annual_revenue": "$12M MXN",
    "annual_profit": "$2M MXN",
    "annual_priorities": [{"priority": "Abrir dos sucursales", "owner": "Ana", "kpi": "2 aperturas"}],
    "quarterly_priorities": [{"priority": "Reducir tiempos", "owner": "Luis", "kpi": "90% en 24 horas", "status": "on_track"}],
}


def test_clean_project_natural_intent_to_valid_resumable_opsp(tmp_path):
    routed = route({"action": "frontdoor", "message": "Quiero hacer mi plan en una hoja", "base_path": tmp_path})
    assert routed["artifacts"]["intent"] == "opsp"
    assert routed["artifacts"]["handoff"] == "coaching.opsp"

    first = run({"base_path": tmp_path, "updated_at": "2026-08-24", "data": {"company_name": "Taller Norte", "core_values": COMPLETE_PLAN["core_values"]}})
    artifact = tmp_path / ARTIFACT_PATH
    assert first["errors"] == []
    assert first["artifacts"]["knowledge_id"] == "tool-opsp"
    assert artifact.is_file()
    assert validate_opsp(artifact) == []

    resumed = run({"base_path": tmp_path, "updated_at": "2026-08-25", "data": {key: value for key, value in COMPLETE_PLAN.items() if key not in {"company_name", "core_values"}}, "complete": True})
    assert resumed["errors"] == []
    assert resumed["artifacts"]["status"] == "completed"
    assert resumed["artifacts"]["data"]["core_values"] == COMPLETE_PLAN["core_values"]
    assert validate_opsp(artifact) == []
    text = artifact.read_text(encoding="utf-8")
    assert "# One-Page Strategic Plan (OPSP)" in text
    assert "Taller Norte" in text


def test_opsp_uses_canonical_knowledge_record(tmp_path):
    knowledge = load_opsp_knowledge(tmp_path)
    assert knowledge["id"] == "tool-opsp"
    assert knowledge["name_es"].startswith("Plan Estrategico")


def test_incomplete_completion_stays_resumable_and_asks_for_next_fact(tmp_path):
    result = run({
        "base_path": tmp_path,
        "updated_at": "2026-08-24",
        "data": {"company_name": "Taller Norte", "purpose": COMPLETE_PLAN["purpose"]},
        "complete": True,
    })
    artifact = tmp_path / ARTIFACT_PATH
    assert result["artifacts"]["status"] == "in_progress"
    assert "aún faltan datos" in result["output"]
    assert result["output"].endswith("?")
    assert result["artifacts"]["data"]["purpose"] == COMPLETE_PLAN["purpose"]
    assert validate_opsp(artifact) == []


def test_completed_opsp_requires_actionable_annual_and_quarterly_priorities(tmp_path):
    incomplete = dict(COMPLETE_PLAN)
    incomplete["annual_priorities"] = [{"priority": "Abrir dos sucursales"}]
    incomplete["quarterly_priorities"] = []
    result = run({"base_path": tmp_path, "updated_at": "2026-08-24", "data": incomplete, "complete": True})
    assert result["artifacts"]["status"] == "in_progress"
    assert any("annual priority 1 missing: owner, kpi" in error for error in result["errors"])
    assert any("at least one quarterly priority" in error for error in result["errors"])
