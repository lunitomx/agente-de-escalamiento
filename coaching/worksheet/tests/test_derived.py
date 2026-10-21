"""S87.7: ``derived_from`` names real sheets and real step ids."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from coaching.core import write_yaml
from coaching.worksheet import (
    derived_errors,
    list_worksheets,
    load_worksheet_content,
    run,
)
from coaching.worksheet.guide import parse_guide

STEPS = [
    {"id": "decision", "question": "¿A qué dices que no?", "how": "h", "example": "e"}
]
TIPS = [{"text": f"t{i}", "source": "Fuente pública"} for i in range(3)]


def _sheet(sheet_id: str, derived: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": sheet_id,
        "guide": {"steps": STEPS},
        "tips": TIPS,
        "derived_from": derived,
    }


def _source(**extra: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "sheet": "worksheet-brand-promise",
        "fields": ["promesa-principal"],
        "into": "promesa",
        "title": "Promesa de marca",
    }
    return {**base, **extra}


def test_derived_source_needs_a_title() -> None:
    source = _source()
    del source["title"]
    with pytest.raises(ValidationError):
        parse_guide(_sheet("worksheet-x", [source]))


def test_self_derivation_is_rejected() -> None:
    with pytest.raises(ValidationError, match="no puede derivar de sí misma"):
        parse_guide(_sheet("worksheet-x", [_source(sheet="worksheet-x")]))


def test_unknown_sheet_is_rejected() -> None:
    content = _sheet("worksheet-x", [_source(sheet="worksheet-nada")])
    assert derived_errors(content) == [
        "derived_from nombra una hoja que no está en el registro: worksheet-nada"
    ]


def test_field_that_is_not_a_step_is_rejected() -> None:
    content = _sheet(
        "worksheet-x",
        [
            _source(
                sheet="worksheet-differentiating-activities",
                fields=["actividades"],
            )
        ],
    )
    assert derived_errors(content) == [
        "derived_from pide el campo actividades, que no es un paso de "
        "worksheet-differentiating-activities"
    ]


def test_valid_sources_have_no_errors() -> None:
    assert derived_errors(_sheet("worksheet-x", [_source()])) == []


def test_every_registered_sheet_passes_derived_check() -> None:
    for sheet in list_worksheets():
        assert derived_errors(load_worksheet_content(sheet)) == [], sheet["id"]


def test_engine_returns_contract_error_for_bad_derived(tmp_path: Path) -> None:
    knowledge = tmp_path / ".escala" / "knowledge"
    write_yaml(
        knowledge / "registry" / "worksheets.yaml",
        {
            "worksheets": [
                {
                    "id": "worksheet-x",
                    "name": "X",
                    "decision": "strategy",
                    "node_path": "strategy/worksheets/x.yaml",
                }
            ]
        },
    )
    write_yaml(
        knowledge / "strategy" / "worksheets" / "x.yaml",
        _sheet("worksheet-x", [_source(sheet="worksheet-nada")]),
    )
    result = run(
        {"action": "start", "worksheet_name": "worksheet-x", "base_path": str(tmp_path)}
    )
    assert result["errors"] == [
        "La hoja worksheet-x no cumple el contrato: derived_from nombra una hoja "
        "que no está en el registro: worksheet-nada"
    ]
