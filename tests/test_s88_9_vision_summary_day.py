"""S88.9 · El Resumen de visión cierra el Strategy Day sin pedir hojas de fuera (ESCALA-128).

Hallazgos 1 y 2 del ensayo de las 8 hojas (18-nov-2026):
1. Pedía «Cliente central» como prerrequisito; esa hoja no se hace en el taller.
2. Volvía a preguntar propósito y meta grande sin mostrar lo ya llenado.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from coaching.worksheet import find_worksheet
from tests.test_e88_strategy_day_path import _call, _step_ids
from tests.test_e88_workbook_coverage import exercise_sheets, load_coverage

VISION_SUMMARY = "worksheet-vision-summary"


def _fill(base: Path, sheet: str, answers: dict[str, str]) -> None:
    _call(base, sheet, "start")
    _call(base, sheet, "step")
    for step_id in _step_ids(sheet):
        default = f"Respuesta de {step_id}"
        _call(base, sheet, "step", fields={step_id: answers.get(step_id, default)})
    assert _call(base, sheet, "save")["errors"] == [], sheet


def test_day_sheets_only_require_sheets_done_earlier_that_day() -> None:
    sheets = exercise_sheets(load_coverage())
    for position, sheet in enumerate(sheets):
        worksheet = find_worksheet(sheet)
        assert worksheet is not None, sheet
        for prereq in worksheet.get("prerequisites", []):
            assert prereq in sheets[:position], (sheet, prereq)


def test_vision_summary_requires_purpose_and_big_goal() -> None:
    worksheet = find_worksheet(VISION_SUMMARY)
    assert worksheet is not None
    assert worksheet["prerequisites"] == ["worksheet-core-purpose", "worksheet-bhag"]


def test_vision_summary_shows_what_the_day_already_filled(tmp_path: Path) -> None:
    answers: dict[str, dict[str, str]] = {
        "worksheet-swt": {"tendencias-2026": "Pedidos por WhatsApp con IA."},
        "worksheet-differentiating-activities": {
            "actividades-elegidas": "Masa madre de 48 horas; entrega antes de las 7."
        },
        "worksheet-core-purpose": {"proposito": "Pan que vuelve a reunir."},
        "worksheet-bhag": {"meta-grande": "10,000 mesas al día para 2040."},
    }
    for sheet in exercise_sheets(load_coverage()):
        if sheet == VISION_SUMMARY:
            break
        _fill(tmp_path, sheet, answers.get(sheet, {}))
    started: dict[str, Any] = _call(tmp_path, VISION_SUMMARY, "start")
    assert started["errors"] == []
    output = started["output"]
    assert "Esto ya llenaste:" in output
    for sheet_answers in answers.values():
        for text in sheet_answers.values():
            assert text in output, text
    assert "Cliente central" not in output
