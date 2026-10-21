"""S87.9: the owner fills the One-Page Personal Plan from start to view."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from coaching.core import read_yaml
from coaching.worksheet import get_completed_ids, run

SHEET = "worksheet-oppp"


def _run(base: Path, action: str, **extra: Any) -> dict[str, Any]:
    return run(
        {"action": action, "worksheet_name": SHEET, "base_path": str(base), **extra}
    )


def _row(**areas: str) -> list[str]:
    return [f"{area}: {text}" for area, text in areas.items()]


ANSWERS: dict[str, Any] = {
    "vision-10-25-anos": _row(
        Relación="viajamos juntos dos veces al año",
        Familia="mis hijos dirigen dos sucursales",
        Amigos="mis compadres siguen en la mesa del domingo",
        Salud="corro un medio maratón a los 60",
        Trabajo="la tortillería funciona sin mí",
        Dinero="vivo de las rentas de los locales",
        Diversión="pesco en Valle de Bravo cada mes",
        Espiritual="sirvo en la parroquia",
    ),
    "metas-un-ano": _row(
        Relación="una cita a solas cada viernes",
        Familia="Cenar con ellos cada domingo",
        Amigos="una comida al mes con mis compadres",
        Salud="bajar 6 kilos",
        Trabajo="un encargado por turno",
        Dinero="ahorrar 3 meses de gastos de la casa",
        Diversión="dos fines de semana fuera",
        Espiritual="un retiro al año",
    ),
    "empezar": _row(
        Relación="apagar el celular en la cena",
        Familia="tarea con los niños los martes",
        Amigos="llamar a uno cada semana",
        Salud="caminar 30 minutos a las 6 am",
        Trabajo="junta de 15 minutos diaria",
        Dinero="revisar gastos cada lunes",
        Diversión="clase de guitarra",
        Espiritual="10 minutos de silencio al despertar",
    ),
    "dejar": _row(
        Relación="discutir por WhatsApp",
        Familia="llegar tarde a la comida",
        Amigos="cancelar a última hora",
        Salud="refresco en la comida",
        Trabajo="contestar WhatsApp del negocio después de las 9 pm",
        Dinero="prestar sin fecha de pago",
        Diversión="ver series hasta la 1 am",
        Espiritual="saltarme la misa del domingo",
    ),
    "tablero-de-vision": [
        "Salud: foto de un medio maratón; obstáculo 'salgo tarde'; "
        "plan 'si cierro después de las 8, corro a las 6 am'",
    ],
}


@pytest.fixture
def filled(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    started = _run(tmp_path, "start")
    assert started["errors"] == []
    assert started["artifacts"]["total_steps"] == len(ANSWERS) + 2
    first = _run(tmp_path, "step")["output"]
    assert "### Paso 2: ¿Cómo quieres que sea tu vida en 10 a 25 años" in first
    assert "**Ejemplo:** Tortillería El Sol" in first
    assert "(fuente: Investigación ESCALA (nota interna f2))" in first
    last: dict[str, Any] = {}
    for step_id, answer in ANSWERS.items():
        last = _run(tmp_path, "step", fields={step_id: answer})
        assert last["errors"] == []
    return tmp_path, last


def test_last_row_shows_final_review_and_nothing_is_completed(
    filled: tuple[Path, dict[str, Any]],
) -> None:
    base, last = filled
    assert "### Revisión Final" in last["output"]
    assert "Cenar con ellos cada domingo" in last["output"]
    state = read_yaml(base / ".escala/my-company/worksheets" / f"{SHEET}.yaml")
    assert state["status"] == "in_progress"
    assert get_completed_ids(base) == []


def test_final_review_joins_list_answers_like_the_saved_view(
    filled: tuple[Path, dict[str, Any]],
) -> None:
    _, last = filled
    review = last["output"]
    assert (
        "Relación: viajamos juntos dos veces al año; "
        "Familia: mis hijos dirigen dos sucursales" in review
    )
    assert "['" not in review
    assert "']" not in review


def test_save_writes_the_plan_and_opens_a_grid_of_five_cards(
    filled: tuple[Path, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    base, _ = filled
    monkeypatch.setattr(sys, "platform", "darwin")
    result = _run(base, "save")
    assert result["errors"] == []
    company = base / ".escala" / "my-company"
    stamp = date.today().isoformat()
    html = company / "vistas" / f"{stamp}-{SHEET}.html"
    md = company / "vistas" / f"{stamp}-{SHEET}.md"
    saved = read_yaml(company / "worksheets" / f"{SHEET}.yaml")
    assert saved["fields"] == ANSWERS
    assert result["artifacts"]["view"]["open_cmd"] == ["open", str(html)]
    assert get_completed_ids(base) == [SHEET]
    page = html.read_text(encoding="utf-8")
    assert "<div class='canvas'>" in page
    assert page.count("<section class='card'>") == 5
    for title in ("En 10 a 25 años", "Este año", "Empezar", "Dejar"):
        assert f"<h2>{title}</h2>" in page
    assert "<h2>Tablero de visión</h2>" in page
    assert "Cenar con ellos cada domingo" in md.read_text(encoding="utf-8")
