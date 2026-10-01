"""S84.2 task 4: the saved decision enters the next diagnosis as local evidence."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from coaching.diagnose.models import DiagnosticEvidence
from coaching.journey.decision import choose, load_saved, propose, save_journey
from coaching.journey.diagnosis import load_diagnostic_inputs, to_diagnostic_inputs
from coaching.journey.models import Journey, JourneyEvidence, JourneyStage, StageCount

TODAY = date(2026, 10, 1)


def _journey() -> Journey:
    def count(value: int, origin: str) -> StageCount:
        return StageCount.model_validate(
            {
                "value": value,
                "period": "2026-09",
                "source": "tu cuaderno",
                "origin": origin,
            }
        )

    return Journey(
        built_on=TODAY,
        stages=[
            JourneyStage(stage="se_entera", count=count(300, "supuesto")),
            JourneyStage(stage="pregunta", count=count(120, "dato_con_periodo")),
            JourneyStage(
                stage="compra",
                count=count(18, "dato_con_periodo"),
                friction="tarda en contestar",
                evidence=[JourneyEvidence(origin="supuesto", text="el precio asusta")],
            ),
            JourneyStage(stage="recibe", count=count(18, "dueño_dice")),
            JourneyStage(stage="regresa"),
        ],
    )


def _save(base: Path, label: str = "A") -> None:
    decision = choose(
        propose(_journey(), TODAY, experiment="contestar en 1 hora"), label
    )
    save_journey(base, _journey(), decision, TODAY)


def test_chosen_decision_is_a_local_conversation_fact(tmp_path: Path) -> None:
    _save(tmp_path)
    saved = load_saved(tmp_path)
    assert saved is not None
    inputs = to_diagnostic_inputs(saved, TODAY)
    [fact] = inputs.evidence
    assert isinstance(fact, DiagnosticEvidence)
    assert (fact.source_kind, fact.answer_status) == ("conversation", "fact")
    assert fact.source_ref == ".escala/my-company/journey/2026-10-01-journey.md"
    assert fact.decision == "strategy"
    assert fact.freshness == "current"
    assert "contestar en 1 hora" in str(fact.value)
    assert "http" not in fact.model_dump_json()


def test_supuestos_go_to_assumptions_and_gaps_to_open_questions(tmp_path: Path) -> None:
    _save(tmp_path, "B")
    saved = load_saved(tmp_path)
    assert saved is not None
    inputs = to_diagnostic_inputs(saved, TODAY)
    assert "Supuesto, Te compra: el precio asusta" in inputs.assumptions
    assert "Supuesto, Se entera de ti: unos 300 en sep 2026" in inputs.assumptions
    assert not any("120" in line for line in inputs.assumptions)
    assert "Falta: cuántos en Regresa a comprar" in inputs.open_questions
    assert any(" 15 oct 2026: cuántos" in line for line in inputs.open_questions)
    for line in [*inputs.assumptions, *inputs.open_questions]:
        assert len(line) <= 96 and len(line.split()) <= 12


def test_past_review_by_is_stale_with_a_refresh_offer(tmp_path: Path) -> None:
    _save(tmp_path)
    inputs = load_diagnostic_inputs(tmp_path, date(2027, 1, 15))
    [fact] = inputs.evidence
    assert (fact.freshness, fact.confidence) == ("stale", "low")
    assert inputs.refresh_offers


def test_nothing_saved_gives_empty_inputs(tmp_path: Path) -> None:
    inputs = load_diagnostic_inputs(tmp_path, TODAY)
    assert inputs.evidence == [] and inputs.assumptions == []
