"""Tests for the Fact provenance contract."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from coaching.evidence.facts import (
    Fact,
    delete_fact,
    get_fact,
    load_facts,
    save_fact,
)


def test_fact_requires_metric_definition() -> None:
    with pytest.raises(ValidationError):
        Fact(
            metric_definition="",
            period="2026-07",
            source="test",
            confidence="high",
            value=1,
        )


def test_fact_requires_source() -> None:
    with pytest.raises(ValidationError):
        Fact(
            metric_definition="Ingreso",
            period="2026-07",
            source="",
            confidence="high",
            value=1,
        )


def test_fact_requires_period() -> None:
    with pytest.raises(ValidationError):
        Fact(
            metric_definition="Ingreso",
            period="",
            source="test",
            confidence="high",
            value=1,
        )


def test_save_and_load_fact(tmp_path: Path) -> None:
    fact = Fact(
        metric_definition="Ingreso atribuible mensual",
        period="2026-07",
        basis_date="2026-07-31",
        source="export_plataforma_julio.csv",
        confidence="high",
        comparable=True,
        value=125000,
        unit="MXN",
        decision="cash",
    )
    path = save_fact(tmp_path, fact)
    assert path.exists()
    assert path == tmp_path / ".escala" / "agent" / "memory" / "facts.yaml"

    loaded = load_facts(tmp_path)
    assert len(loaded) == 1
    assert loaded[0].metric_definition == "Ingreso atribuible mensual"
    assert loaded[0].value == 125000
    assert loaded[0].decision == "cash"


def test_load_facts_filtered_by_decision(tmp_path: Path) -> None:
    cash_fact = Fact(
        metric_definition="Ingreso",
        period="2026-07",
        source="test",
        confidence="high",
        value=1,
        decision="cash",
    )
    people_fact = Fact(
        metric_definition="Empleados",
        period="2026-07",
        source="test",
        confidence="medium",
        value=15,
        decision="people",
    )
    save_fact(tmp_path, cash_fact)
    save_fact(tmp_path, people_fact)

    cash_loaded = load_facts(tmp_path, decision="cash")
    assert len(cash_loaded) == 1
    assert cash_loaded[0].decision == "cash"


def test_get_fact_by_id(tmp_path: Path) -> None:
    fact = Fact(
        metric_definition="Ingreso",
        period="2026-07",
        source="test",
        confidence="high",
        value=1,
    )
    save_fact(tmp_path, fact)
    found = get_fact(tmp_path, fact.fact_id)
    assert found is not None
    assert found.fact_id == fact.fact_id

    missing = get_fact(tmp_path, "missing-id")
    assert missing is None


def test_save_updates_existing_fact(tmp_path: Path) -> None:
    fact = Fact(
        metric_definition="Ingreso",
        period="2026-07",
        source="test",
        confidence="high",
        value=100,
    )
    save_fact(tmp_path, fact)
    fact.value = 200
    save_fact(tmp_path, fact)

    loaded = load_facts(tmp_path)
    assert len(loaded) == 1
    assert loaded[0].value == 200
    assert loaded[0].updated_at >= loaded[0].created_at


def test_delete_fact(tmp_path: Path) -> None:
    fact = Fact(
        metric_definition="Ingreso",
        period="2026-07",
        source="test",
        confidence="high",
        value=1,
    )
    save_fact(tmp_path, fact)
    assert delete_fact(tmp_path, fact.fact_id) is True
    assert load_facts(tmp_path) == []
    assert delete_fact(tmp_path, fact.fact_id) is False


def test_fact_persistence_is_local_only(tmp_path: Path) -> None:
    fact = Fact(
        metric_definition="Ingreso",
        period="2026-07",
        source="conversacion_onboarding",
        confidence="medium",
        value=1,
    )
    path = save_fact(tmp_path, fact)
    assert str(path).startswith(str(tmp_path))
