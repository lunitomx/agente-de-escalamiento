"""Tests for task board validators."""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / ".scaleup" / "agent"))
from validators.tasks import find_overdue, parse_tasks, validate_task_board


BOARD_TEMPLATE = """# Tareas y Compromisos

## En Progreso

- [ ] Completar Core Values <!-- decision:people node:core-values-worksheet due:2026-05-01 -->
- [ ] Revisar CCC <!-- decision:cash due:2026-04-20 -->

## Próximo

- [ ] Crear OPSP <!-- decision:strategy node:opsp -->

## Completado

- [x] Diagnóstico inicial <!-- decision:people completed:2026-04-25 -->
"""


class TestParseTasks:
    def test_parses_all_sections(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "tasks.md"
        p.write_text(BOARD_TEMPLATE)
        tasks = parse_tasks(p)
        assert len(tasks["En Progreso"]) == 2
        assert len(tasks["Próximo"]) == 1
        assert len(tasks["Completado"]) == 1

    def test_extracts_metadata(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "tasks.md"
        p.write_text(BOARD_TEMPLATE)
        tasks = parse_tasks(p)
        t = tasks["En Progreso"][0]
        assert t["decision"] == "people"
        assert t["node"] == "core-values-worksheet"
        assert t["due"] == "2026-05-01"

    def test_missing_file(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "missing.md"
        tasks = parse_tasks(p)
        assert all(len(v) == 0 for v in tasks.values())

    def test_task_without_metadata(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "tasks.md"
        p.write_text("## En Progreso\n\n- [ ] Simple task\n\n## Próximo\n\n## Completado\n")
        tasks = parse_tasks(p)
        assert tasks["En Progreso"][0]["decision"] == ""


class TestValidateTaskBoard:
    def test_valid_board(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "tasks.md"
        p.write_text(BOARD_TEMPLATE)
        assert validate_task_board(p) == []

    def test_missing_section(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "tasks.md"
        p.write_text("## En Progreso\n\n## Completado\n")
        errors = validate_task_board(p)
        assert any("Próximo" in e for e in errors)

    def test_invalid_decision(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "tasks.md"
        p.write_text("## En Progreso\n\n- [ ] Bad <!-- decision:marketing -->\n\n## Próximo\n\n## Completado\n")
        errors = validate_task_board(p)
        assert any("invalid decision" in e for e in errors)

    def test_invalid_due_date(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "tasks.md"
        p.write_text("## En Progreso\n\n- [ ] Bad <!-- due:tomorrow -->\n\n## Próximo\n\n## Completado\n")
        errors = validate_task_board(p)
        assert any("invalid due date" in e for e in errors)


class TestFindOverdue:
    def test_finds_overdue(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "tasks.md"
        p.write_text(BOARD_TEMPLATE)
        overdue = find_overdue(p)
        assert len(overdue) == 1
        assert "CCC" in overdue[0]["description"]

    def test_no_overdue(self, tmp_path: pathlib.Path) -> None:
        p = tmp_path / "tasks.md"
        p.write_text("## En Progreso\n\n- [ ] Future <!-- due:2099-01-01 -->\n\n## Próximo\n\n## Completado\n")
        assert find_overdue(p) == []
