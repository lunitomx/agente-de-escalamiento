"""S87.2 T6: the engine walks guided steps and save writes the view."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from coaching.core import read_yaml, write_yaml
from coaching.worksheet import get_completed_ids, run

SHEET = "worksheet-core-customer"


def _run(base: Path, action: str, **extra: Any) -> dict[str, Any]:
    return run(
        {"action": action, "worksheet_name": SHEET, "base_path": str(base), **extra}
    )


def test_step_after_start_shows_the_first_guided_step(tmp_path: Path) -> None:
    started = _run(tmp_path, "start")
    assert started["errors"] == []
    assert started["artifacts"]["total_steps"] == 13
    out = _run(tmp_path, "step")["output"]
    assert "### Paso 2: ¿Quiénes son tus 5 mejores clientes" in out
    assert "**Cómo llenarlo:**" in out
    assert "**Ejemplo:** Tortillería El Sol" in out


def test_resume_shows_the_same_guided_step(tmp_path: Path) -> None:
    _run(tmp_path, "start")
    _run(tmp_path, "step")
    out = _run(tmp_path, "resume")["output"]
    assert "### Paso 2: ¿Quiénes son tus 5 mejores clientes" in out
    assert "**Ejemplo:**" in out


def test_each_step_saves_its_answer_and_shows_the_next(tmp_path: Path) -> None:
    _run(tmp_path, "start")
    _run(tmp_path, "step")
    out = _run(tmp_path, "step", fields={"top-5-clientes": "Doña Mari"})["output"]
    assert "### Paso 3: ¿Qué quieren, qué necesitan y qué temen" in out
    state = read_yaml(tmp_path / ".escala/my-company/worksheets" / f"{SHEET}.yaml")
    assert state["fields"] == {"top-5-clientes": "Doña Mari"}


def test_legacy_sheet_start_is_unchanged(tmp_path: Path) -> None:
    out = run(
        {
            "action": "start",
            "worksheet_name": "worksheet-face",
            "base_path": str(tmp_path),
        }
    )["output"]
    assert "### Paso 1: Información General" in out
    assert "Responde con 'listo' para empezar." in out


def test_legacy_sheet_step_shows_the_first_field(tmp_path: Path) -> None:
    run(
        {
            "action": "start",
            "worksheet_name": "worksheet-face",
            "base_path": str(tmp_path),
        }
    )
    out = run(
        {
            "action": "step",
            "worksheet_name": "worksheet-face",
            "base_path": str(tmp_path),
        }
    )["output"]
    assert out.startswith("### Paso 2: Functions list")
    assert "Completa este campo" in out


def _seed_invalid(base: Path) -> None:
    knowledge = base / ".escala" / "knowledge"
    write_yaml(
        knowledge / "registry" / "worksheets.yaml",
        {"worksheets": [{"id": "bad-ws", "name": "Bad", "node_path": "s/bad.yaml"}]},
    )
    write_yaml(
        knowledge / "s" / "bad.yaml",
        {"guide": {"steps": [{"id": "a", "question": "¿A?", "how": "x"}]}, "tips": []},
    )


def test_invalid_guide_returns_error_without_state(tmp_path: Path) -> None:
    _seed_invalid(tmp_path)
    result = run(
        {"action": "start", "worksheet_name": "bad-ws", "base_path": str(tmp_path)}
    )
    assert len(result["errors"]) == 1
    assert result["errors"][0].startswith("La hoja bad-ws no cumple el contrato:")
    assert not (tmp_path / ".escala" / "my-company").exists()


def test_invalid_guide_save_returns_error(tmp_path: Path) -> None:
    _seed_invalid(tmp_path)
    result = run(
        {"action": "save", "worksheet_name": "bad-ws", "base_path": str(tmp_path)}
    )
    assert result["errors"][0].startswith("La hoja bad-ws no cumple el contrato:")


@pytest.mark.parametrize(
    ("platform", "opener"), [("darwin", "open"), ("linux", "xdg-open")]
)
def test_save_writes_yaml_html_md_and_open_cmd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, platform: str, opener: str
) -> None:
    monkeypatch.setattr(sys, "platform", platform)
    _run(tmp_path, "start")
    _run(tmp_path, "step")
    _run(tmp_path, "step", fields={"top-5-clientes": "Doña Mari"})
    result = _run(tmp_path, "save")
    assert result["errors"] == []
    company = tmp_path / ".escala" / "my-company"
    stamp = date.today().isoformat()
    html = company / "vistas" / f"{stamp}-{SHEET}.html"
    md = company / "vistas" / f"{stamp}-{SHEET}.md"
    assert (company / "worksheets" / f"{SHEET}.yaml").is_file()
    assert html.is_file() and md.is_file()
    view = result["artifacts"]["view"]
    assert view == {"html": str(html), "md": str(md), "open_cmd": [opener, str(html)]}
    assert f"Vista lista: {html}" in result["output"]
    assert "Doña Mari" in md.read_text(encoding="utf-8")


def test_save_on_other_platform_has_no_open_cmd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    _run(tmp_path, "start")
    assert _run(tmp_path, "save")["artifacts"]["view"]["open_cmd"] is None


def _fill_all(base: Path) -> dict[str, Any]:
    """start, 'listo', then one answer per guided step; returns the last step."""
    _run(base, "start")
    _run(base, "step")
    last: dict[str, Any] = {}
    for step_id, answer in ANSWERS.items():
        last = _run(base, "step", fields={step_id: answer})
    return last


ANSWERS: dict[str, str] = {
    "top-5-clientes": "Doña Mari, Don Beto",
    "atributos": "Pagan a tiempo y piden diario",
    "top-atributos": "Piden diario",
    "quien-es": "Dueños de fondas a 3 km",
    "necesidad": "No quedarse sin tortilla a mediodía",
    "chequeo-promesa": "Tortilla caliente antes de las 11",
    "persona-ejemplo": "Doña Mari, 52 años, Fonda La Esquina",
    "prueba-quien": "Mamás que compran 2 kg antes de las 8",
    "mejor-en": "Tortilla caliente que no se rompe",
    "diferente-en": "Pedido fijo sin llamar",
    "raro-o-malo": "No venden por kilo después de las 14:00",
}


def test_last_answer_shows_final_review_and_does_not_complete(
    tmp_path: Path,
) -> None:
    content_steps = run(
        {"action": "start", "worksheet_name": SHEET, "base_path": str(tmp_path)}
    )["artifacts"]["total_steps"]
    assert content_steps == len(ANSWERS) + 2
    last = _fill_all(tmp_path)
    out = last["output"]
    assert last["errors"] == []
    assert "### Revisión Final" in out
    assert "**¿Quiénes son tus 5 mejores clientes" in out
    assert "Doña Mari, Don Beto" in out
    assert "top-5-clientes" not in out
    assert "confirmar" in out
    state = read_yaml(tmp_path / ".escala/my-company/worksheets" / f"{SHEET}.yaml")
    assert state["status"] == "in_progress"
    assert get_completed_ids(tmp_path) == []
    again = _run(tmp_path, "step")["output"]
    assert "### Revisión Final" in again
    assert get_completed_ids(tmp_path) == []


def test_confirm_save_completes_once_with_view_and_no_backup(
    tmp_path: Path,
) -> None:
    _fill_all(tmp_path)
    result = _run(tmp_path, "save")
    assert result["errors"] == []
    assert result["artifacts"]["backup_path"] is None
    worksheets = tmp_path / ".escala/my-company/worksheets"
    assert sorted(p.name for p in worksheets.glob("*.yaml")) == [f"{SHEET}.yaml"]
    assert get_completed_ids(tmp_path) == [SHEET]
    assert read_yaml(worksheets / f"{SHEET}.yaml")["fields"] == ANSWERS
    md = Path(result["artifacts"]["view"]["md"]).read_text(encoding="utf-8")
    assert "Tortilla caliente antes de las 11" in md


def test_tip_source_shows_a_readable_label_not_a_repo_path(tmp_path: Path) -> None:
    _run(tmp_path, "start")
    out = _run(tmp_path, "step")["output"]
    assert "work/research" not in out
    assert "(fuente: Investigación ESCALA (nota interna f1))" in out


def test_a_backup_does_not_count_the_sheet_twice(tmp_path: Path) -> None:
    _fill_all(tmp_path)
    _run(tmp_path, "save")
    second = _run(tmp_path, "save")
    assert second["artifacts"]["backup_path"] is not None
    assert get_completed_ids(tmp_path) == [SHEET]


SHEET_DA = "worksheet-differentiating-activities"
ANSWERS_DA: dict[str, str] = {
    "competidores": "Home Depot, tlapalería de la esquina",
    "eje-personas": "Maestro asesora; HD cajero; esquina dueño solo",
    "eje-producto": "Refacciones viejas; HD solo nuevo",
    "eje-operaciones": "Entrega mismo día; HD 48 h",
    "eje-terminos": "Crédito 30 días; los demás contado",
    "actividades-elegidas": "Entrega mismo día, asesoría, crédito",
    "como-se-refuerzan": "El crédito trae constructores que piden entrega",
    "que-dejas-de-hacer": "No vendemos jardinería",
}


def _run_da(base: Path, action: str, **extra: Any) -> dict[str, Any]:
    return run(
        {"action": action, "worksheet_name": SHEET_DA, "base_path": str(base), **extra}
    )


def test_differentiating_activities_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    started = _run_da(tmp_path, "start")
    assert started["errors"] == []
    assert started["artifacts"]["total_steps"] == len(ANSWERS_DA) + 2 == 10
    first = _run_da(tmp_path, "step")["output"]
    assert "### Paso 2: ¿Contra quién te compara tu Cliente central?" in first
    assert "**Ejemplo:** Ferretería La Llave" in first
    last: dict[str, Any] = {}
    for step_id, answer in ANSWERS_DA.items():
        last = _run_da(tmp_path, "step", fields={step_id: answer})
    assert last["errors"] == []
    assert "### Revisión Final" in last["output"]
    worksheets = tmp_path / ".escala/my-company/worksheets"
    assert read_yaml(worksheets / f"{SHEET_DA}.yaml")["status"] == "in_progress"
    assert get_completed_ids(tmp_path) == []

    result = _run_da(tmp_path, "save")
    assert result["errors"] == []
    assert result["artifacts"]["backup_path"] is None
    assert read_yaml(worksheets / f"{SHEET_DA}.yaml")["fields"] == ANSWERS_DA
    assert get_completed_ids(tmp_path) == [SHEET_DA]
    stamp = date.today().isoformat()
    vistas = tmp_path / ".escala" / "my-company" / "vistas"
    html = vistas / f"{stamp}-{SHEET_DA}.html"
    md = vistas / f"{stamp}-{SHEET_DA}.md"
    assert html.is_file() and md.is_file()
    assert result["artifacts"]["view"]["open_cmd"] == ["open", str(html)]
    text = md.read_text(encoding="utf-8")
    assert "Home Depot" in text
    assert "En qué eres distinto" in text


def test_core_customer_end_to_end_writes_view_and_open_cmd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    _fill_all(tmp_path)
    result = _run(tmp_path, "save")
    assert result["errors"] == []
    view = result["artifacts"]["view"]
    assert Path(view["html"]).is_file() and Path(view["md"]).is_file()
    assert view["open_cmd"] == ["open", view["html"]]
    md = Path(view["md"]).read_text(encoding="utf-8")
    assert "Lo que ve tu Cliente central" in md
    assert "No venden por kilo después de las 14:00" in md
