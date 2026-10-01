# pyright: strict
"""S84.3: board recommender rules, in order (synthetic data only)."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from coaching.dashboard.boards.models import BoardMetric, BoardProposal
from coaching.dashboard.boards.patterns import PATTERNS, detect_area
from coaching.dashboard.boards.recommend import (
    BoardRequest,
    Existing,
    recommend_boards,
)
from coaching.evidence.facts import Fact

TODAY = date(2026, 10, 1)


def _fact(definition: str, *, comparable: bool = True) -> Fact:
    return Fact(
        metric_definition=definition,
        period="septiembre 2026",
        source="whatsapp-business.csv",
        confidence="medium",
        comparable=comparable,
        value=120,
    )


def _request(text: str, **extra: object) -> BoardRequest:
    return BoardRequest.model_validate({"request": text, "today": TODAY, **extra})


# --- Models -----------------------------------------------------------------


def _metric(name: str) -> BoardMetric:
    return BoardMetric(
        metric_definition=name, source="tu cuaderno", period="mes", status="falta"
    )


def test_a_proposal_has_three_to_five_metrics() -> None:
    base = {
        "board_id": "x",
        "title": "X",
        "decision": "d",
        "audience": "tú",
        "cadence": "cada semana",
        "feasibility": "no_ahora",
    }
    with pytest.raises(ValidationError):
        BoardProposal.model_validate({**base, "metrics": [_metric("a"), _metric("b")]})
    with pytest.raises(ValidationError):
        BoardProposal.model_validate(
            {**base, "metrics": [_metric(str(i)) for i in range(6)]}
        )


def test_every_pattern_metric_declares_source_and_period() -> None:
    for pattern in PATTERNS.values():
        assert 3 <= len(pattern.metrics) <= 5
        for metric in pattern.metrics:
            assert metric.source and metric.period


def test_the_team_pattern_never_ranks_individuals() -> None:
    team = [p for p in PATTERNS.values() if p.area == "equipo"]
    assert team
    for pattern in team:
        text = " ".join(
            [pattern.decision, *(m.metric_definition for m in pattern.metrics)]
        ).lower()
        for word in ("ranking", "por persona", "mejor vendedor", "peor"):
            assert word not in text


# --- Area detection ---------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "area"),
    [
        ("Tablero de mis ventas", "ventas"),
        ("Quiero ver mi flujo de caja en una gráfica", "caja"),
        ("tablero de mis prioridades", "ejecucion"),
        ("indicadores del equipo", "equipo"),
        ("un tablero de mi avance", "progreso"),
        ("gráfica de mi competencia", "mercado"),
        ("muéstrame un dashboard", None),
        ("qué indicadores debo ver", None),
    ],
)
def test_detect_area(text: str, area: str | None) -> None:
    assert detect_area(text) == area


# --- Rule 1: no redundancy --------------------------------------------------


def test_a_cash_request_points_to_the_existing_cash_report() -> None:
    result = recommend_boards(
        _request("flujo de caja en una gráfica"),
        facts=[],
        existing=Existing(cash_report=".escala-cash-reports/"),
    )
    assert result.outcome == "existe"
    assert result.proposals == []
    assert result.points_to_existing == ".escala-cash-reports/"
    assert "reporte de caja" in result.message


def test_a_cash_request_without_a_report_still_proposes_no_new_board() -> None:
    result = recommend_boards(
        _request("tablero de mi efectivo"), facts=[], existing=Existing()
    )
    assert result.outcome == "existe"
    assert result.proposals == []
    assert result.points_to_existing is None
    assert "reporte de caja" in result.message


def test_an_execution_request_points_to_the_tracker_when_it_exists() -> None:
    result = recommend_boards(
        _request("tablero de mis prioridades"),
        facts=[],
        existing=Existing(tracker=".escala/my-company/tracker.yaml"),
    )
    assert result.outcome == "existe"
    assert result.points_to_existing == ".escala/my-company/tracker.yaml"


def test_progress_and_research_point_to_what_exists() -> None:
    progress = recommend_boards(
        _request("tablero de mi avance"), facts=[], existing=Existing()
    )
    assert progress.outcome == "existe"
    research = recommend_boards(
        _request("gráfica de mi competencia"),
        facts=[],
        existing=Existing(research=".escala/my-company/research/index.yaml"),
    )
    assert research.outcome == "existe"
    assert research.points_to_existing == ".escala/my-company/research/index.yaml"


def test_market_without_research_has_no_pattern_and_invents_nothing() -> None:
    result = recommend_boards(
        _request("gráfica de mi competencia"), facts=[], existing=Existing()
    )
    assert result.outcome == "sin_patron"
    assert result.proposals == []


# --- Rule 2: start from a decision -----------------------------------------


def test_no_decision_asks_one_question() -> None:
    result = recommend_boards(
        _request("muéstrame un dashboard"), facts=[], existing=Existing()
    )
    assert result.outcome == "pregunta_decision"
    assert result.proposals == []
    assert result.message.count("?") == 1
    assert "decidir" in result.message


def test_the_decision_question_is_asked_only_once() -> None:
    result = recommend_boards(
        _request("muéstrame un dashboard", decision_asked=True),
        facts=[],
        existing=Existing(),
    )
    assert result.outcome == "sin_patron"


def test_the_owner_answer_to_the_question_selects_the_area() -> None:
    result = recommend_boards(
        _request(
            "muéstrame un dashboard", decision="en qué paso se me van los clientes"
        ),
        facts=[],
        existing=Existing(),
    )
    assert result.outcome == "propuestas"


# --- Rule 3/4: proposals, metric state, feasibility -------------------------


def test_sales_board_gives_at_most_two_proposals_with_source_and_period() -> None:
    result = recommend_boards(
        _request("Tablero de mis ventas"), facts=[], existing=Existing()
    )
    assert result.outcome == "propuestas"
    assert 1 <= len(result.proposals) <= 2
    for proposal in result.proposals:
        assert proposal.decision and proposal.audience and proposal.cadence
        for metric in proposal.metrics:
            assert metric.source and metric.period


def test_no_numbers_means_no_ahora_and_every_metric_is_missing() -> None:
    result = recommend_boards(
        _request("Tablero de mis ventas"), facts=[], existing=Existing()
    )
    for proposal in result.proposals:
        assert proposal.feasibility == "no_ahora"
        assert all(m.status == "falta" for m in proposal.metrics)
        assert proposal.missing == [m.metric_definition for m in proposal.metrics]


def test_metric_state_comes_from_the_evidence_dashboard() -> None:
    first = PATTERNS["ventas-etapas"].metrics
    facts = [
        _fact(first[0].metric_definition),
        _fact(first[1].metric_definition, comparable=False),
    ]
    result = recommend_boards(
        _request("Tablero de mis ventas"), facts=facts, existing=Existing()
    )
    proposal = next(p for p in result.proposals if p.board_id == "ventas-etapas")
    states = [m.status for m in proposal.metrics]
    assert states[0] == "conocido"
    assert states[1] == "no_comparable"
    assert proposal.metrics[0].period == "septiembre 2026"
    assert proposal.metrics[0].source == "whatsapp-business.csv"
    assert proposal.feasibility == "necesita_datos"
    assert first[0].metric_definition not in proposal.missing
    assert first[1].metric_definition in proposal.missing


def test_all_metrics_known_is_se_puede_hoy() -> None:
    metrics = PATTERNS["ventas-etapas"].metrics
    facts = [_fact(m.metric_definition) for m in metrics]
    result = recommend_boards(
        _request("Tablero de mis ventas"), facts=facts, existing=Existing()
    )
    proposal = next(p for p in result.proposals if p.board_id == "ventas-etapas")
    assert proposal.feasibility == "se_puede_hoy"
    assert proposal.missing == []


def test_sales_boards_report_they_need_journey_stages_when_counts_miss() -> None:
    result = recommend_boards(
        _request("Tablero de mis ventas"), facts=[], existing=Existing()
    )
    assert result.needs_journey_stages is True
    team = recommend_boards(
        _request("indicadores del equipo"), facts=[], existing=Existing()
    )
    assert team.needs_journey_stages is False


# --- Closing: a decision ------------------------------------------------------


def test_proposals_end_in_an_owner_decision_with_a_recommendation() -> None:
    result = recommend_boards(
        _request("Tablero de mis ventas"), facts=[], existing=Existing()
    )
    codes = [option.code for option in result.options]
    assert codes == ["construir", "esperar", "no"]
    assert result.recommended in codes
    assert result.recommended == "esperar"  # no numbers yet


def test_partial_numbers_recommend_building_with_gaps_shown() -> None:
    metrics = PATTERNS["ventas-etapas"].metrics
    result = recommend_boards(
        _request("Tablero de mis ventas"),
        facts=[_fact(metrics[0].metric_definition)],
        existing=Existing(),
    )
    assert result.recommended == "construir"


# --- Memory: 30 days without re-proposing ------------------------------------


def test_a_recently_declined_board_is_not_proposed_again() -> None:
    result = recommend_boards(
        _request("Tablero de mis ventas"),
        facts=[],
        existing=Existing(),
        declined={"ventas-etapas": date(2026, 9, 20)},
    )
    assert [p.board_id for p in result.proposals] == ["ventas-regresan"]


def test_after_thirty_days_it_can_be_proposed_again() -> None:
    result = recommend_boards(
        _request("Tablero de mis ventas"),
        facts=[],
        existing=Existing(),
        declined={"ventas-etapas": date(2026, 8, 31)},
    )
    assert "ventas-etapas" in [p.board_id for p in result.proposals]


def test_everything_declined_says_so_and_proposes_nothing() -> None:
    result = recommend_boards(
        _request("Tablero de mis ventas"),
        facts=[],
        existing=Existing(),
        declined={"ventas-etapas": TODAY, "ventas-regresan": TODAY},
    )
    assert result.outcome == "pospuesto"
    assert result.proposals == []
    assert result.options == []


# --- Owner-facing language ----------------------------------------------------


def test_owner_text_is_plain_spanish_without_commands() -> None:
    for text in (
        "Tablero de mis ventas",
        "flujo de caja",
        "muéstrame un dashboard",
        "indicadores del equipo",
    ):
        result = recommend_boards(_request(text), facts=[], existing=Existing())
        assert "/escala" not in result.message
        assert "journey" not in result.message.lower()
