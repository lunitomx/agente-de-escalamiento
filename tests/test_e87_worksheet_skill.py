"""S87.2 T7: the worksheet skill opens the saved view and has no stale paths."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "escala-skills" / "escala-worksheet" / "SKILL.md"


def _text() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_skill_runs_the_open_command_from_the_view() -> None:
    text = _text()
    for token in ("artifacts.view", "open_cmd", "`open ", "`xdg-open "):
        assert token in text, token


def test_skill_has_the_markdown_fallback() -> None:
    text = _text()
    assert "`.md`" in text
    assert "null" in text


def test_skill_shows_guided_parts() -> None:
    text = _text()
    for token in ("Cómo llenarlo", "Ejemplo", "Tips"):
        assert token in text, token


def test_skill_has_no_stale_paths() -> None:
    text = _text()
    assert ".escala/agent/validators/" not in text
    assert ".escala/coaching/" not in text


def test_skill_says_the_canvas_reads_saved_sheets_and_shows_the_prompt() -> None:
    text = _text()
    assert "worksheet-strategy-canvas" in text
    assert "lee las hojas guardadas" in text
    assert "Prompt para tu asistente de IA" in text
