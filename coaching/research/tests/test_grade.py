"""Confirmation rules of the research contract (E83 S83.1).

"Confirmado" only with three or more independent dated sources inside the
freshness window; everything else is "por confirmar". Synthetic data only.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from coaching.research.engine import FRESHNESS_DAYS, grade_claim, review_date
from coaching.research.models import (
    DecisionOption,
    ResearchClaim,
    SourceRecord,
)

TODAY = date(2026, 9, 30)


def _source(
    source_id: str,
    publisher: str,
    published_on: date | None = TODAY - timedelta(days=10),
    origin: str = "web",
) -> SourceRecord:
    return SourceRecord.model_validate(
        {
            "source_id": source_id,
            "origin": origin,
            "title": f"Nota {source_id}",
            "publisher": publisher,
            "url": f"https://ejemplo-{source_id}.test/nota"
            if origin == "web"
            else None,
            "published_on": published_on.isoformat() if published_on else None,
            "consulted_on": TODAY.isoformat(),
            "excerpt": f"Cita literal {source_id}",
        }
    )


def _sources(*records: SourceRecord) -> dict[str, SourceRecord]:
    return {record.source_id: record for record in records}


def _claim(
    supporting: list[str],
    contrary: list[str] | None = None,
    kind: str = "dato",
) -> ResearchClaim:
    return ResearchClaim.model_validate(
        {
            "text": "El servicio cuesta entre 400 y 600 pesos en la zona.",
            "kind": kind,
            "supporting": supporting,
            "contrary": contrary or [],
        }
    )


THREE = _sources(
    _source("s1", "Diario Uno"),
    _source("s2", "Revista Dos"),
    _source("s3", "Cámara Tres"),
)


def test_three_independent_dated_sources_confirm_a_fact() -> None:
    graded = grade_claim(_claim(["s1", "s2", "s3"]), THREE, TODAY)

    assert graded.status == "confirmado"
    assert graded.confidence == "alta"


def test_two_sources_stay_por_confirmar() -> None:
    graded = grade_claim(_claim(["s1", "s2"]), THREE, TODAY)

    assert graded.status == "por_confirmar"
    assert graded.confidence == "media"


def test_one_source_is_low_confidence() -> None:
    graded = grade_claim(_claim(["s1"]), THREE, TODAY)

    assert graded.status == "por_confirmar"
    assert graded.confidence == "baja"


def test_same_publisher_counts_once_even_with_different_accents_or_case() -> None:
    sources = _sources(
        _source("s1", "Cámara Tres"),
        _source("s2", "camara tres "),
        _source("s3", "Diario Uno"),
    )

    graded = grade_claim(_claim(["s1", "s2", "s3"]), sources, TODAY)

    assert graded.status == "por_confirmar"


def test_undated_source_does_not_count() -> None:
    sources = _sources(
        _source("s1", "Diario Uno"),
        _source("s2", "Revista Dos"),
        _source("s3", "Cámara Tres", published_on=None),
    )

    assert (
        grade_claim(_claim(["s1", "s2", "s3"]), sources, TODAY).status
        == "por_confirmar"
    )


def test_source_older_than_the_freshness_window_does_not_count() -> None:
    old = TODAY - timedelta(days=FRESHNESS_DAYS + 1)
    sources = _sources(
        _source("s1", "Diario Uno"),
        _source("s2", "Revista Dos"),
        _source("s3", "Cámara Tres", published_on=old),
    )

    assert (
        grade_claim(_claim(["s1", "s2", "s3"]), sources, TODAY).status
        == "por_confirmar"
    )


def test_source_dated_in_the_future_does_not_count() -> None:
    sources = _sources(
        _source("s1", "Diario Uno"),
        _source("s2", "Revista Dos"),
        _source("s3", "Cámara Tres", published_on=TODAY + timedelta(days=5)),
    )

    assert (
        grade_claim(_claim(["s1", "s2", "s3"]), sources, TODAY).status
        == "por_confirmar"
    )


def test_unknown_source_ids_do_not_count() -> None:
    graded = grade_claim(_claim(["s1", "s2", "fantasma"]), THREE, TODAY)

    assert graded.status == "por_confirmar"


@pytest.mark.parametrize("kind", ["supuesto", "inferencia"])
def test_assumptions_and_inferences_are_never_confirmed(kind: str) -> None:
    graded = grade_claim(_claim(["s1", "s2", "s3"], kind=kind), THREE, TODAY)

    assert graded.status == "por_confirmar"
    assert graded.kind == kind


def test_contrary_evidence_caps_confidence_at_media() -> None:
    sources = {**THREE, **_sources(_source("s4", "Blog Cuatro"))}

    graded = grade_claim(_claim(["s1", "s2", "s3"], contrary=["s4"]), sources, TODAY)

    assert graded.status == "confirmado"
    assert graded.confidence == "media"
    assert graded.contrary == ["s4"]


def test_grading_ignores_status_the_agent_claimed() -> None:
    claimed = _claim(["s1"]).model_copy(
        update={"status": "confirmado", "confidence": "alta"}
    )

    graded = grade_claim(claimed, THREE, TODAY)

    assert graded.status == "por_confirmar"
    assert graded.confidence == "baja"


def test_review_date_is_ninety_days_after_research() -> None:
    assert FRESHNESS_DAYS == 90
    assert review_date(TODAY) == date(2026, 12, 29)


def test_web_source_needs_a_url() -> None:
    with pytest.raises(ValidationError):
        SourceRecord.model_validate(
            {
                "source_id": "s1",
                "origin": "web",
                "title": "Sin link",
                "publisher": "Diario",
                "url": None,
                "consulted_on": TODAY.isoformat(),
                "excerpt": "Cita",
            }
        )


@pytest.mark.parametrize("origin", ["modelo", "conocimiento_del_modelo", "memoria"])
def test_model_memory_is_not_a_source_origin(origin: str) -> None:
    with pytest.raises(ValidationError):
        _source("s1", "Diario Uno", origin=origin)


def test_excerpt_is_short_and_required() -> None:
    base = _source("s1", "Diario Uno").model_dump(mode="json")
    with pytest.raises(ValidationError):
        SourceRecord.model_validate({**base, "excerpt": "x" * 301})
    with pytest.raises(ValidationError):
        SourceRecord.model_validate({**base, "excerpt": "   "})


def test_owner_source_may_have_no_url() -> None:
    source = _source("d1", "Cotización que me llegó", origin="dueño")

    assert source.url is None


def test_waiting_option_needs_the_missing_data_and_a_date() -> None:
    with pytest.raises(ValidationError):
        DecisionOption.model_validate(
            {"label": "C", "text": "Todavía no decido", "kind": "esperar"}
        )
    option = DecisionOption.model_validate(
        {
            "label": "C",
            "text": "Todavía no decido",
            "kind": "esperar",
            "missing_data": "Tres cotizaciones de la competencia",
            "by_date": "2026-10-15",
        }
    )
    assert option.by_date == date(2026, 10, 15)
