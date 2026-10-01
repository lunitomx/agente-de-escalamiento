# pyright: strict
"""S84.4: journey stage counts (S84.2) feed board metrics, with month and source."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from coaching.dashboard.boards.sources import journey_facts, metric_facts
from coaching.evidence.facts import Fact
from coaching.journey.decision import choose, propose, save_journey
from coaching.journey.models import CountOrigin, Journey, JourneyStage, StageCount

TODAY = date(2026, 10, 1)
_STAGES = ("se_entera", "pregunta", "compra", "recibe", "regresa")


def _count(
    value: int,
    period: str = "2026-09",
    origin: CountOrigin = "dato_con_periodo",
    upper: int | None = None,
) -> StageCount:
    return StageCount(
        value=value, upper=upper, period=period, source="tu cuaderno", origin=origin
    )


def _journey(counts: dict[str, StageCount]) -> Journey:
    return Journey(
        built_on=TODAY,
        stages=[JourneyStage(stage=s, count=counts.get(s)) for s in _STAGES],
    )


def _save(base: Path, journey: Journey) -> None:
    decision = propose(journey, TODAY, experiment=None)
    save_journey(base, journey, choose(decision, decision.recommendation), TODAY)


def _by_name(facts: list[Fact]) -> dict[str, Fact]:
    return {fact.metric_definition: fact for fact in facts}


def test_stage_counts_become_metrics_with_month_and_local_source() -> None:
    facts = _by_name(
        journey_facts(_journey({"pregunta": _count(120), "compra": _count(18)}))
    )
    asked = facts["Personas que preguntan"]
    assert asked.value == 120 and asked.comparable
    assert asked.period == "septiembre de 2026"
    assert asked.source == "tu cuaderno"
    assert facts["Clientes que compran"].value == 18


def test_ratio_only_when_both_counts_are_of_the_same_month() -> None:
    same = _by_name(
        journey_facts(_journey({"pregunta": _count(120), "compra": _count(18)}))
    )
    assert same["De cada 10 que preguntan, cuántos compran"].value == 1.5

    mixed = _by_name(
        journey_facts(
            _journey({"pregunta": _count(120), "compra": _count(18, "2026-08")})
        )
    )
    assert "De cada 10 que preguntan, cuántos compran" not in mixed


def test_guesses_and_ranges_are_not_shown_as_numbers() -> None:
    facts = _by_name(
        journey_facts(
            _journey(
                {
                    "pregunta": _count(100, origin="supuesto"),
                    "compra": _count(10, upper=20, origin="dueño_dice"),
                }
            )
        )
    )
    assert not facts["Personas que preguntan"].comparable
    assert not facts["Clientes que compran"].comparable
    assert "De cada 10 que preguntan, cuántos compran" not in facts


def test_no_counts_no_facts() -> None:
    assert journey_facts(_journey({})) == []


def test_metric_facts_reads_the_saved_journey_and_keeps_explicit_facts(
    tmp_path: Path,
) -> None:
    _save(tmp_path, _journey({"pregunta": _count(120), "compra": _count(18)}))
    explicit = Fact(
        metric_definition="Clientes que compran",
        period="septiembre de 2026",
        source="tu sistema de ventas",
        confidence="high",
        value=20,
    )

    facts = _by_name(metric_facts(tmp_path, [explicit]))

    assert facts["Clientes que compran"].value == 20
    assert facts["Personas que preguntan"].value == 120


def test_without_a_saved_journey_only_explicit_facts(tmp_path: Path) -> None:
    assert metric_facts(tmp_path, []) == []


def test_recommend_uses_the_saved_journey_counts(tmp_path: Path) -> None:
    from coaching.dashboard.boards.flow import run

    _save(tmp_path, _journey({"pregunta": _count(120), "compra": _count(18)}))

    result = run(
        {
            "action": "recommend",
            "base_path": str(tmp_path),
            "today": "2026-10-01",
            "request": "Tablero de mis ventas",
        }
    )

    assert result.recommendation is not None
    stages = result.recommendation.proposals[0]
    assert stages.board_id == "ventas-etapas"
    assert stages.feasibility == "se_puede_hoy"
    assert {m.period for m in stages.metrics} == {"septiembre de 2026"}
    assert result.journey_question is None
