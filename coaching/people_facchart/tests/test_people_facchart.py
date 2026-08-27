"""Tests for the FACChart engine (S50.4.2)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from coaching.people_facchart import run  # noqa: E402
from coaching.people_facchart.engine import (  # noqa: E402
    FACChart,
    Function,
    score,
    validate,
)
from coaching.people_facchart.formatter import render_markdown  # noqa: E402


def test_load_on_fresh_company_has_no_chart(tmp_path):
    result = run({"action": "load", "base_path": str(tmp_path)})
    assert result["errors"] == []
    assert result["artifacts"]["state"]["functions"] == []
    assert result["artifacts"]["resuming"] is False


def test_save_and_load_roundtrip(tmp_path):
    base = str(tmp_path)
    chart = {
        "functions": [
            {
                "name": "Sales",
                "accountable": "Ana",
                "kpis": ["Revenue", "Conversion"],
            }
        ]
    }
    save_result = run({"action": "save", "base_path": base, "data": chart})
    assert save_result["errors"] == []
    assert save_result["artifacts"]["state"]["functions"][0]["name"] == "Sales"

    load_result = run({"action": "load", "base_path": base})
    assert load_result["artifacts"]["resuming"] is True
    assert load_result["artifacts"]["state"]["functions"][0]["accountable"] == "Ana"


def test_validation_rejects_empty_kpis():
    chart = FACChart(functions=[Function(name="Sales", accountable="Ana", kpis=[])])
    errors = validate(chart)
    assert any("KPI" in e for e in errors)


def test_validation_rejects_overloaded_person():
    chart = FACChart(
        functions=[
            Function(name="Sales", accountable="Ana", kpis=["A"]),
            Function(name="Marketing", accountable="Ana", kpis=["B"]),
            Function(name="Ops", accountable="Ana", kpis=["C"]),
            Function(name="Finance", accountable="Ana", kpis=["D"]),
        ]
    )
    errors = validate(chart)
    assert any("máximo recomendado" in e for e in errors)


def test_validation_rejects_one_person_for_all():
    chart = FACChart(
        functions=[
            Function(name="Sales", accountable="CEO", kpis=["A"]),
            Function(name="Marketing", accountable="CEO", kpis=["B"]),
        ]
    )
    errors = validate(chart)
    assert any("todas las funciones" in e for e in errors)


def test_score_zero_for_empty_chart():
    assert score(FACChart())["overall"] == 0


def test_score_perfect_for_valid_chart():
    chart = FACChart(
        functions=[
            Function(name="Sales", accountable="Ana", kpis=["Revenue"]),
            Function(name="Ops", accountable="Luis", kpis=["Cost"]),
        ]
    )
    result = score(chart)
    assert result["completeness"] == 100
    assert result["health"] == 100
    assert result["overall"] == 100


def test_export_writes_markdown_to_disk(tmp_path):
    base = str(tmp_path)
    chart = {
        "functions": [
            {
                "name": "Sales",
                "accountable": "Ana",
                "kpis": ["Revenue"],
            }
        ]
    }
    run({"action": "save", "base_path": base, "data": chart})
    result = run({"action": "export", "base_path": base, "company_name": "Acme"})
    md_path = Path(result["artifacts"]["export_path"])
    assert md_path.exists()
    assert "Sales" in md_path.read_text(encoding="utf-8")


def test_render_markdown_shows_pending_marker():
    chart = FACChart(functions=[Function(name="", accountable="Ana", kpis=["Revenue"])])
    markdown = render_markdown(chart)
    assert "[PENDIENTE]" in markdown


def test_unknown_action_is_rejected(tmp_path):
    result = run({"action": "teleport", "base_path": str(tmp_path)})
    assert result["errors"] != []
