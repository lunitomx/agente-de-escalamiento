"""S84.2 task 3: the journey ends in one decision, saved only after the yes."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from coaching.journey.decision import (
    JourneyDecision,
    choose,
    load_saved,
    propose,
    save_journey,
)
from coaching.journey.models import Journey, JourneyStage, StageCount

TODAY = date(2026, 10, 1)


def _journey(with_loss: bool = True) -> Journey:
    counts: dict[str, int] = {"pregunta": 120, "compra": 18} if with_loss else {}
    stages = [
        JourneyStage(
            stage=stage,
            count=None
            if stage not in counts
            else StageCount(
                value=counts[stage],
                period="2026-09",
                source="tu cuaderno",
                origin="dato_con_periodo",
            ),
        )
        for stage in ("se_entera", "pregunta", "compra", "recibe", "regresa")
    ]
    return Journey(built_on=TODAY, stages=stages)


def test_with_a_loss_and_an_experiment_recommends_the_experiment() -> None:
    decision = propose(_journey(), TODAY, experiment="responder en menos de 1 hora")
    assert [option.label for option in decision.options] == ["A", "B"]
    first, wait = decision.options
    assert first.kind == "decidir"
    assert "14 días" in first.text and "«Te compra»" in first.text
    assert wait.kind == "esperar" and wait.by_date == date(2026, 10, 15)
    assert wait.missing_data == "cuántos en «Se entera de ti»"
    assert decision.recommendation == "A"


def test_without_a_loss_recommends_getting_the_missing_data() -> None:
    decision = propose(_journey(with_loss=False), TODAY, experiment=None)
    assert {option.kind for option in decision.options} == {"decidir", "esperar"}
    wait = next(option for option in decision.options if option.kind == "esperar")
    assert decision.recommendation == wait.label
    assert all("14 días" not in option.text for option in decision.options)


def test_experiment_lasts_7_to_14_days() -> None:
    with pytest.raises(ValueError):
        propose(_journey(), TODAY, experiment="x", days=30)
    assert (
        "7 días" in propose(_journey(), TODAY, experiment="x", days=7).options[0].text
    )


def test_recommendation_must_be_an_option() -> None:
    decision = propose(_journey(), TODAY, experiment="x")
    with pytest.raises(ValidationError):
        JourneyDecision.model_validate({**decision.model_dump(), "recommendation": "Z"})
    with pytest.raises(ValueError):
        choose(decision, "Z")
    assert choose(decision, "b").chosen == "B"


def test_nothing_is_saved_without_a_chosen_option(tmp_path: Path) -> None:
    decision = propose(_journey(), TODAY, experiment="x")
    with pytest.raises(ValueError, match="needs_chosen_option"):
        save_journey(tmp_path, _journey(), decision, TODAY)
    assert not (tmp_path / ".escala").exists()


def test_save_writes_under_my_company_journey_with_review_in_90_days(
    tmp_path: Path,
) -> None:
    decision = choose(propose(_journey(), TODAY, experiment="contestar rápido"), "A")
    paths = save_journey(tmp_path, _journey(), decision, TODAY)
    rel = sorted(path.relative_to(tmp_path).as_posix() for path in paths)
    assert rel == [
        ".escala/my-company/journey/2026-10-01-journey.md",
        ".escala/my-company/journey/journey.yaml",
    ]
    saved = load_saved(tmp_path)
    assert saved is not None
    assert saved.review_by == date(2026, 12, 30)
    assert saved.reference == ".escala/my-company/journey/2026-10-01-journey.md"
    assert saved.decision.chosen == "A"
    text = (tmp_path / saved.reference).read_text(encoding="utf-8")
    assert "Elegiste: A)" in text and "falta" in text


def test_unreadable_saved_journey_is_none(tmp_path: Path) -> None:
    folder = tmp_path / ".escala" / "my-company" / "journey"
    folder.mkdir(parents=True)
    (folder / "journey.yaml").write_text(": : :", encoding="utf-8")
    assert load_saved(tmp_path) is None
