"""E84 S84.3: board requests reach escala-dashboard and end in proposals or a pointer."""

from __future__ import annotations

from pathlib import Path

import pytest

from coaching.dashboard.boards import messages
from coaching.dashboard.boards.flow import run
from escala_server.capabilities import load_capability_catalog, route_request

ROOT = Path(__file__).resolve().parents[1]
PROCEDURE = ROOT / "escala-skills" / "escala-dashboard" / "SKILL.md"


def test_dashboard_route_is_first_and_targets_escala_dashboard() -> None:
    catalog = load_capability_catalog(ROOT / "escala-skills" / "catalog.yaml")
    first = catalog.routes[0]
    assert first.id == "dashboard"
    assert first.target == "escala-dashboard"
    assert set(first.keywords) == {"tablero", "dashboard", "grafica", "indicador"}


def test_sales_board_request_ends_in_at_most_two_proposals(tmp_path: Path) -> None:
    phrase = "Tablero de mis ventas"
    assert route_request(phrase).capability_id == "escala-dashboard"
    result = run(
        {
            "action": "recommend",
            "base_path": str(tmp_path),
            "today": "2026-10-01",
            "request": phrase,
        }
    )
    assert result.recommendation is not None
    assert result.recommendation.outcome == "propuestas"
    assert 1 <= len(result.recommendation.proposals) <= 2


def test_a_visual_cash_request_points_to_the_existing_cash_report(
    tmp_path: Path,
) -> None:
    phrase = "Quiero ver mi flujo de caja en una gráfica"
    assert route_request(phrase).capability_id == "escala-dashboard"
    result = run(
        {
            "action": "recommend",
            "base_path": str(tmp_path),
            "today": "2026-10-01",
            "request": phrase,
        }
    )
    assert result.recommendation is not None
    assert result.recommendation.outcome == "existe"
    assert result.recommendation.proposals == []


def _procedure() -> str:
    return PROCEDURE.read_text(encoding="utf-8")


def test_procedure_drives_the_boards_module_and_keeps_progress() -> None:
    text = _procedure()
    assert "name: escala-dashboard" in text
    assert "python3 -m coaching.dashboard.boards" in text
    assert "python3 -m coaching.dashboard\n" in text  # progress view kept
    for action in ("recommend", "decide"):
        assert f'"action": "{action}"' in text


@pytest.mark.parametrize(
    "rule",
    [
        messages.ASK_DECISION,
        "Nunca publiques",
        "una sola pregunta",
        "journey_question",
        "en español",
        ".escala/my-company/tableros/",
    ],
)
def test_procedure_carries_the_rules(rule: str) -> None:
    assert rule in _procedure()


def test_procedure_generates_only_the_accepted_board() -> None:
    text = _procedure()
    assert '"action": "generate"' in text
    assert "paso posterior (S84.4)" not in text


@pytest.mark.parametrize(
    "rule",
    [
        "Muestra `markdown` en el chat",
        "no se guardó",
        "Sólo después de un «sí»",
        "`saved_files` vacío",
    ],
)
def test_procedure_carries_the_generator_rules(rule: str) -> None:
    assert rule in _procedure()
