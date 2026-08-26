"""Acceptance tests for the source-aware Business Pulse experience."""

from __future__ import annotations

import json
import threading
import urllib.request

from coaching.core import write_yaml
from coaching.opsp import run as run_opsp
from escala_server.business_pulse import BusinessPulseHandler
from escala_server.handlers import WorksheetsHandler
from escala_server.project_memory import ProjectMemoryRuntime
from escala_server.server import EscalaRequestHandler, make_server


def _profile(root, *, cash=2):
    write_yaml(
        root / ".scaleup" / "agent" / "memory" / "company-profile.yaml",
        {
            "company": {
                "name": "Taller Norte",
                "industry": "Servicios automotrices",
            },
            "scores": {
                "people": 4,
                "strategy": 3,
                "execution": 2,
                "cash": cash,
            },
            "focus": {"current_decision": "execution"},
        },
    )


def _plan(root, *, critical_number="90% de entregas puntuales"):
    result = run_opsp(
        {
            "base_path": root,
            "updated_at": "2026-08-26",
            "complete": True,
            "data": {
                "company_name": "Taller Norte",
                "core_values": ["Servicio", "Calidad", "Aprendizaje"],
                "purpose": "Hacer confiable el mantenimiento de cada vehículo",
                "bhag": "Ser la red de talleres más recomendada del norte",
                "bhag_date": "2040-12-31",
                "sandbox": {"market": "Norte de México"},
                "brand_promise": {
                    "promise": "Diagnóstico en 24 horas",
                    "kpi": "% entregado en 24 horas",
                },
                "quarter": "Q3 2026",
                "critical_number": critical_number,
                "year": "2026",
                "annual_revenue": "$12M MXN",
                "annual_profit": "$2M MXN",
                "annual_priorities": [
                    {"priority": "Abrir sede", "owner": "Ana", "kpi": "1 sede"}
                ],
                "quarterly_priorities": [
                    {
                        "priority": "Reducir retrasos",
                        "owner": "Luis",
                        "kpi": "90% puntual",
                        "status": "En curso",
                    }
                ],
            },
        }
    )
    assert result["artifacts"]["status"] == "completed"


def _handler(root):
    memory = ProjectMemoryRuntime(root).ensure_memory()
    assert memory.ready
    return BusinessPulseHandler(str(memory.db_path), project_root=root), memory.db_path


def test_empty_pulse_is_actionable_and_never_invents_company_numbers(tmp_path):
    handler, _ = _handler(tmp_path)

    data = handler.get()["data"]

    assert data["state"] == "empty"
    assert data["synthetic"] is False
    assert data["company"]["name"] is None
    assert all(item["score"] is None and item["source"] is None for item in data["decisions"])
    assert {item["label"] for item in data["actions"]} >= {
        "Iniciar diagnóstico",
        "Crear plan en una hoja",
        "Modelar efectivo",
    }


def test_diagnosis_and_plan_refresh_with_source_and_date(tmp_path):
    _profile(tmp_path, cash=2)
    _plan(tmp_path)
    handler, _ = _handler(tmp_path)

    first = handler.get()["data"]
    cash = next(item for item in first["decisions"] if item["id"] == "cash")
    assert first["company"]["name"] == "Taller Norte"
    assert cash["score"] == 2
    assert cash["source"]["path"].endswith("company-profile.yaml")
    assert cash["source"]["observed_at"]
    assert first["priority"]["decision"] == "execution"
    assert first["plan"]["critical_number"] == "90% de entregas puntuales"
    assert first["plan"]["completion"] == {"complete": 7, "total": 7, "percent": 100}
    assert first["plan"]["source"]["path"] == "work/strategy/opsp.md"

    _profile(tmp_path, cash=4)
    _plan(tmp_path, critical_number="95% de entregas puntuales")
    refreshed = handler.get()["data"]
    refreshed_cash = next(item for item in refreshed["decisions"] if item["id"] == "cash")
    assert refreshed_cash["score"] == 4
    assert refreshed["plan"]["critical_number"] == "95% de entregas puntuales"
    assert refreshed["refresh"]["changed"] == 2


def test_power_of_one_is_real_local_persisted_data(tmp_path):
    handler, db_path = _handler(tmp_path)
    variables = {
        "price": {"current": 100, "adjusted": 105},
        "volume": {"current": 1000, "adjusted": 1100},
    }
    WorksheetsHandler(str(db_path)).save_worksheet(
        "cash", "power-of-one", {"variables": variables, "currency": "MXN"}
    )

    data = handler.get()["data"]

    assert data["power_of_one"]["available"] is True
    assert data["power_of_one"]["source"]["type"] == "local_worksheet"
    assert any(item["type"] == "local_worksheet" for item in data["timeline"])


def test_synthetic_demo_is_explicit_and_does_not_write_company_rows(tmp_path):
    handler, db_path = _handler(tmp_path)

    demo = handler.get(demo="true")["data"]

    assert demo["mode"] == "synthetic_demo"
    assert demo["synthetic"] is True
    assert demo["company"]["source"]["type"] == "synthetic_demo"
    import sqlite3

    with sqlite3.connect(db_path) as db:
        assert db.execute("SELECT COUNT(*) FROM companies").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM worksheets").fetchone()[0] == 0


def test_http_api_and_static_business_pulse_are_served(tmp_path):
    _profile(tmp_path)
    handler, db_path = _handler(tmp_path)
    del handler
    EscalaRequestHandler.log_message = lambda *args: None
    server = make_server(
        host="127.0.0.1",
        port=0,
        static_root="escala_server/static",
        db_path=str(db_path),
        project_root=str(tmp_path),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        pulse = json.loads(urllib.request.urlopen(base + "/api/business-pulse").read())
        html = urllib.request.urlopen(base + "/").read().decode("utf-8")
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

    assert pulse["status"] == "ok"
    assert pulse["data"]["company"]["name"] == "Taller Norte"
    assert "Business Pulse" in html
