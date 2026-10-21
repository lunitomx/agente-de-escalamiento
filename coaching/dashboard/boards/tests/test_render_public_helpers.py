"""S87.2 T4: the board renderer shares its helpers with the worksheet view."""

from __future__ import annotations

from pathlib import Path

from coaching.dashboard.boards.render import BASE_CSS, HIDDEN, atomic_write, safe_text


def test_safe_text_hides_links() -> None:
    assert safe_text("ver http://x.mx") == HIDDEN
    assert safe_text("Tortillería El Sol") == "Tortillería El Sol"


def test_base_css_has_no_external_reference() -> None:
    assert "url(" not in BASE_CSS and "@import" not in BASE_CSS


def test_atomic_write_creates_parent_and_file(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b.txt"
    atomic_write(target, "hola\n")
    assert target.read_text(encoding="utf-8") == "hola\n"
