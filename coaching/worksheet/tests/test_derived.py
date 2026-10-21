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


# --- the canvas reads saved sheets (D4-D6) ---------------------------------

CANVAS = "worksheet-strategy-canvas"
SAVED: dict[str, dict[str, str]] = {
    "worksheet-core-customer": {
        "quien-es": "Dueñas de fondas a 3 km de la sucursal",
        "necesidad": "Masa lista antes de las 7 a. m.",
    },
    "worksheet-brand-promise": {
        "promesa-principal": "Masa antes de las 7 o no la pagas",
    },
    "worksheet-differentiating-activities": {
        "actividades-elegidas": "Reparto propio en moto; molino de piedra",
    },
}
SANDBOX_QUESTIONS = {
    "donde": "¿En qué zonas vas a competir y en cuáles no?",
    "que": "¿Cuáles son tus 3 a 5 categorías de producto o servicio?",
    "canales": "¿A quién le vendes y por qué canales?",
}


def _missing_sandbox(field: str) -> str:
    """The "Falta" line for a sandbox field: its question and the sheet's name."""
    return (
        f"Falta: {SANDBOX_QUESTIONS[field]} Llena la hoja Caja de arena "
        "con /escala-worksheet worksheet-sandbox"
    )


def _seed_saved(base: Path, saved: dict[str, dict[str, str]]) -> dict[Path, bytes]:
    folder = base / ".escala" / "my-company" / "worksheets"
    written: dict[Path, bytes] = {}
    for sheet_id, fields in saved.items():
        path = folder / f"{sheet_id}.yaml"
        write_yaml(
            path,
            {"worksheet_id": sheet_id, "fields": fields, "status": "completed"},
        )
        written[path] = path.read_bytes()
    return written


def _canvas(base: Path, action: str, **extra: Any) -> dict[str, Any]:
    return run(
        {"action": action, "worksheet_name": CANVAS, "base_path": str(base), **extra}
    )


def test_canvas_start_shows_three_blocks_and_missing_sandbox(tmp_path: Path) -> None:
    _seed_saved(tmp_path, SAVED)
    started = run(
        {
            "action": "start",
            "worksheet_name": "lienzo de estrategia",
            "base_path": str(tmp_path),
        }
    )
    assert started["errors"] == []
    assert started["artifacts"]["worksheet"]["id"] == CANVAS
    assert started["artifacts"]["total_steps"] == 3
    out = started["output"]
    assert "Esto ya llenaste:" in out
    for title in ("Cliente central", "Promesa de marca", "Actividades diferenciadoras"):
        assert f"## {title}" in out
    assert "Masa antes de las 7 o no la pagas" in out
    assert "Reparto propio en moto" in out
    assert "## Caja de arena" in out
    for field in ("donde", "que", "canales"):
        assert _missing_sandbox(field) in out
    assert "de worksheet-sandbox" not in out
    assert "Falta: donde" not in out
    assert "Contexto del modelo de negocio" not in out


def test_canvas_in_progress_source_counts_as_missing(tmp_path: Path) -> None:
    _seed_saved(tmp_path, SAVED)
    folder = tmp_path / ".escala" / "my-company" / "worksheets"
    write_yaml(
        folder / "worksheet-sandbox.yaml",
        {
            "worksheet_id": "worksheet-sandbox",
            "fields": {"donde": "GDL"},
            "status": "in_progress",
        },
    )
    out = _canvas(tmp_path, "start")["output"]
    assert _missing_sandbox("donde") in out


def test_canvas_saved_view_has_derived_blocks_then_own_section(
    tmp_path: Path,
) -> None:
    written = _seed_saved(tmp_path, SAVED)
    _canvas(tmp_path, "start")
    _canvas(tmp_path, "step")
    review = _canvas(
        tmp_path, "step", fields={"decision": "No a surtir a un súper de Monterrey"}
    )["output"]
    assert "### Revisión Final" in review
    assert "**Prompt para tu asistente de IA:**" in review
    result = _canvas(tmp_path, "save")
    assert result["errors"] == []
    view = result["artifacts"]["view"]
    page = Path(view["html"]).read_text(encoding="utf-8")
    md = Path(view["md"]).read_text(encoding="utf-8")
    assert "<div class='canvas'>" in page
    titles = [
        "Cliente central",
        "Promesa de marca",
        "Actividades diferenciadoras",
        "Caja de arena",
        "Lo que decides",
    ]
    md_order = [md.index(f"## {t}") for t in titles]
    html_order = [page.index(f"<h2>{t}</h2>") for t in titles]
    assert md_order == sorted(md_order)
    assert html_order == sorted(html_order)
    assert _missing_sandbox("donde") in md
    assert _missing_sandbox("donde") in page
    assert "Contexto del modelo de negocio" not in md
    assert "No a surtir a un súper de Monterrey" in md
    for path, data in written.items():
        assert path.read_bytes() == data, path


def test_canvas_shows_optional_bmc_when_saved(tmp_path: Path) -> None:
    _seed_saved(
        tmp_path,
        {
            **SAVED,
            "worksheet-bmc": {"segmentos": "Fondas", "propuesta-de-valor": "Masa"},
        },
    )
    out = _canvas(tmp_path, "start")["output"]
    assert "## Contexto del modelo de negocio" in out
    assert "Fondas" in out
