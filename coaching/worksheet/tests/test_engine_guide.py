"""S87.2 T6: the engine walks guided steps and save writes the view."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from coaching.core import read_yaml, write_yaml
from coaching.worksheet import run

SHEET = "worksheet-core-customer"


def _run(base: Path, action: str, **extra: Any) -> dict[str, Any]:
    return run(
        {"action": action, "worksheet_name": SHEET, "base_path": str(base), **extra}
    )


def test_step_after_start_shows_the_first_guided_step(tmp_path: Path) -> None:
    started = _run(tmp_path, "start")
    assert started["errors"] == []
    assert started["artifacts"]["total_steps"] == 7
    out = _run(tmp_path, "step")["output"]
    assert "### Paso 2: ¿Quiénes son tus 5 mejores clientes" in out
    assert "**Cómo llenarlo:**" in out
    assert "**Ejemplo:** Tortillería El Sol" in out
    assert "(fuente: work/research/e87-tips/core-customer.md#f1)" in out


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
