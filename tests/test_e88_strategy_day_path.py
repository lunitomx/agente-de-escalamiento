"""E88 · El dueño recorre el Strategy Day 2026 de punta a punta (S88.6).

Llena las hojas en el orden de `tests/fixtures/workbook-2026-coverage.yaml`:
cada guardado nombra la siguiente hoja, el último no; cada hoja deja su vista y
los 10 prompts del taller aparecen. Un caso empieza con SWT ya completada (PAT-227).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from coaching.core import read_yaml, write_yaml
from coaching.worksheet import find_worksheet, load_worksheet_content, name_es, run
from coaching.worksheet.guide import parse_guide
from tests.test_e88_workbook_coverage import exercise_sheets, load_coverage

FOLDER = Path(".escala") / "my-company" / "worksheets"


def _call(base: Path, sheet: str, action: str, **extra: Any) -> dict[str, Any]:
    return run(
        {"action": action, "worksheet_name": sheet, "base_path": str(base), **extra}
    )


def _content(sheet: str) -> dict[str, Any]:
    worksheet = find_worksheet(sheet)
    assert worksheet is not None, sheet
    return load_worksheet_content(worksheet)


def _step_ids(sheet: str) -> list[str]:
    guide = parse_guide(_content(sheet))
    assert guide is not None, sheet
    return [step.id for step in guide.guide.steps]


def _prompt_text(sheet: str, prompt: str) -> str:
    """Texto del prompt de un ejercicio: el `ai_prompt` (`main`) o un extra por título."""
    content = _content(sheet)
    if prompt == "main":
        return str(content["ai_prompt"]["text"])
    found = [p for p in content.get("extra_prompts", []) if p["title"] == prompt]
    assert len(found) == 1, (sheet, prompt)
    return str(found[0]["text"])


def _walk(base: Path) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    """Llena cada hoja del recorrido: (hoja, salida de start, salida de save)."""
    walked: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for sheet in exercise_sheets(load_coverage()):
        started = _call(base, sheet, "start")
        assert started["errors"] == [], sheet
        _call(base, sheet, "step")
        for step_id in _step_ids(sheet):
            _call(base, sheet, "step", fields={step_id: f"Respuesta de {step_id}"})
        saved = _call(base, sheet, "save")
        assert saved["errors"] == [], sheet
        walked.append((sheet, started, saved))
    return walked


def _assert_path(
    base: Path, walked: list[tuple[str, dict[str, Any], dict[str, Any]]]
) -> None:
    sheets = [sheet for sheet, _, _ in walked]
    assert sheets == exercise_sheets(load_coverage())
    for (sheet, _, saved), following in zip(walked, sheets[1:]):
        worksheet = find_worksheet(following)
        assert worksheet is not None
        title = name_es(worksheet)
        assert saved["artifacts"]["next_sheet"] == {"id": following, "title": title}
        assert f"Siguiente hoja: {title}." in saved["output"], sheet
    last = walked[-1][2]
    assert "next_sheet" not in last["artifacts"]
    assert "Siguiente hoja" not in last["output"]
    for sheet, _, saved in walked:
        view = saved["artifacts"]["view"]
        assert Path(view["html"]).is_file(), sheet
        assert Path(view["md"]).is_file(), sheet
        state = read_yaml(base / FOLDER / f"{sheet}.yaml")
        assert state["status"] == "completed", sheet


def test_owner_walks_the_strategy_day_in_order(tmp_path: Path) -> None:
    walked = _walk(tmp_path)

    _assert_path(tmp_path, walked)
    assert len(walked) == 8
    assert sum("next_sheet" in saved["artifacts"] for _, _, saved in walked) == 7


def test_the_ten_prompts_show_on_the_path(tmp_path: Path) -> None:
    walked = {sheet: (started, saved) for sheet, started, saved in _walk(tmp_path)}
    exercises = load_coverage()["exercises"]
    assert len(exercises) == 10
    for exercise in exercises:
        sheet, prompt = str(exercise["sheet"]), str(exercise["prompt"])
        started, saved = walked[sheet]
        md = Path(saved["artifacts"]["view"]["md"]).read_text(encoding="utf-8")
        opening = _prompt_text(sheet, prompt)[:40]
        assert opening in md, exercise["name"]
        if prompt != "main":
            # Los prompts de arranque se ven en el Paso 1, antes de llenar nada.
            assert prompt in started["output"], exercise["name"]
            assert prompt in md, exercise["name"]


def test_swt_already_completed_is_reopened_and_the_path_goes_on(
    tmp_path: Path,
) -> None:
    old = {
        "worksheet_id": "worksheet-swt",
        "worksheet_name": "SWT Analysis Worksheet",
        "decision": "strategy",
        "fields": {"fortalezas": "Masa antes de las 7 (2025)"},
        "completed": "2025-11-20",
        "status": "completed",
    }
    (tmp_path / FOLDER).mkdir(parents=True)
    write_yaml(tmp_path / FOLDER / "worksheet-swt.yaml", old)

    walked = _walk(tmp_path)

    swt_start = walked[0][1]
    assert "Ya llenaste esta hoja el 2025-11-20." in swt_start["output"]
    backups = sorted((tmp_path / FOLDER).glob("worksheet-swt-*.yaml"))
    assert len(backups) == 1
    assert read_yaml(backups[0]) == old
    _assert_path(tmp_path, walked)
    new = read_yaml(tmp_path / FOLDER / "worksheet-swt.yaml")
    assert new["fields"]["ideas"] == "Respuesta de ideas"
