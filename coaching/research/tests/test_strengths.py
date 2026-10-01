"""Strengths, weaknesses and trends: outside position against the comparables
the owner confirmed, plus dated trends (E83 S83.4).

Synthetic data only. Owner decisions (2026-09-30): sources count only up to 90
days old; a candidate stays a candidate until the owner says yes.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from coaching.research.models import (
    Comparable,
    DecisionOption,
    ResearchClaim,
    ResearchFrame,
    ResearchReport,
    SourceRecord,
)
from coaching.research.report import build_report, report_message

TODAY = date(2026, 9, 30)


def _frame(**fields: object) -> ResearchFrame:
    data: dict[str, object] = {
        "concern": "No sé qué viene para las tortillerías",
        "question": "¿Qué tendencias vienen y cómo estoy frente a otros?",
        "decision_informed": "Qué fortaleza apalancar este trimestre",
        "mode": "fortalezas-tendencias",
        "offer_category": "tortillas de maíz",
        "geography": "Puebla",
        "competitors": ["Tortillería El Sol"],
        "queries": ["tendencias de tortillas de maíz en Puebla 2026"],
        "confirmed": True,
    }
    data.update(fields)
    return ResearchFrame.model_validate(data)


def _source(source_id: str, publisher: str, *, age: int | None = 20) -> SourceRecord:
    return SourceRecord.model_validate(
        {
            "source_id": source_id,
            "origin": "web",
            "title": f"Página {source_id}",
            "publisher": publisher,
            "url": f"https://ejemplo-{source_id}.test/p",
            "published_on": None
            if age is None
            else (TODAY - timedelta(days=age)).isoformat(),
            "consulted_on": TODAY.isoformat(),
            "excerpt": f"Cita literal {source_id}",
        }
    )


SOURCES = [
    _source("s1", "Diario Uno"),
    _source("s2", "Revista Dos"),
    _source("s3", "Cámara Tres"),
    _source("old", "Archivo Viejo", age=120),
    _source("nodate", "Blog Sin Fecha", age=None),
]
OPTIONS = [
    DecisionOption(label="A", text="Apalancar la entrega a domicilio"),
    DecisionOption(label="B", text="Atender la subida del maíz"),
]
NAMED = Comparable.model_validate(
    {
        "name": "Tortillería El Sol",
        "named_by_owner": True,
        "cells": {"precio": {"value": "24 pesos el kilo", "source_id": "s1"}},
    }
)
CANDIDATE = Comparable.model_validate(
    {
        "name": "Tortillería La Luna",
        "found_in": "s2",
        "why": "vende lo mismo en Puebla",
    }
)


def _claim(**fields: object) -> ResearchClaim:
    data: dict[str, object] = {
        "text": "El Sol no entrega a domicilio",
        "kind": "dato",
        "supporting": ["s1"],
        "side": "fortaleza",
        "against": ["Tortillería El Sol"],
    }
    data.update(fields)
    return ResearchClaim.model_validate(data)


def _report(
    claims: list[ResearchClaim],
    *,
    frame: ResearchFrame | None = None,
    comparables: list[Comparable] | None = None,
) -> ResearchReport:
    return build_report(
        frame=frame or _frame(),
        researched_on=TODAY,
        sources=SOURCES,
        claims=claims,
        options=OPTIONS,
        recommendation="A",
        recommendation_reason="es lo que te distingue",
        comparables=[NAMED, CANDIDATE] if comparables is None else comparables,
    )


# --- every finding of this mode says its side --------------------------------


def test_a_strength_against_a_confirmed_comparable_is_accepted() -> None:
    report = _report([_claim()])

    assert report.claims[0].side == "fortaleza"
    assert report.claims[0].against == ["Tortillería El Sol"]


def test_a_finding_without_side_is_rejected_in_this_mode() -> None:
    with pytest.raises(ValidationError, match="claim_needs_side"):
        _report([_claim(side=None, against=[])])


def test_a_side_only_belongs_to_this_mode() -> None:
    frame = _frame(mode="mercado", segment=None)
    with pytest.raises(ValidationError, match="side_only_in_fortalezas_tendencias"):
        _report([_claim(against=[])], frame=frame, comparables=[])


@pytest.mark.parametrize("side", ["fortaleza", "debilidad"])
def test_strength_or_weakness_needs_a_comparable(side: str) -> None:
    with pytest.raises(ValidationError, match="needs_a_confirmed_comparable"):
        _report([_claim(side=side, against=[])])


def test_never_against_a_candidate_the_owner_did_not_confirm() -> None:
    with pytest.raises(ValidationError, match="needs_a_confirmed_comparable"):
        _report([_claim(against=["Tortillería La Luna"])])
    with pytest.raises(ValidationError, match="needs_a_confirmed_comparable"):
        _report([_claim(against=["Tortillería Inventada"])])


def test_a_confirmed_candidate_can_be_compared_against() -> None:
    confirmed = CANDIDATE.model_copy(update={"owner_confirmed": True})

    report = _report(
        [_claim(side="debilidad", against=["tortilleria la luna"])],
        comparables=[NAMED, confirmed],
    )

    assert report.claims[0].side == "debilidad"


def test_a_trend_needs_a_recent_dated_source() -> None:
    trend = _claim(side="tendencia", against=[], text="El maíz subió 12% en 2026")

    assert _report([trend.model_copy(update={"supporting": ["s2"]})])
    for stale in (["old"], ["nodate"], []):
        with pytest.raises(ValidationError, match="trend_needs_recent_source"):
            _report([trend.model_copy(update={"supporting": stale})])


def test_a_trend_is_not_against_a_business() -> None:
    with pytest.raises(ValidationError, match="trend_has_no_comparable"):
        _report([_claim(side="tendencia", supporting=["s2"])])


def test_comparables_are_allowed_in_this_mode_and_still_need_offer_and_zone() -> None:
    assert _report([_claim()]).comparables
    with pytest.raises(ValidationError, match="comparables_need_offer_and_geography"):
        _report([_claim()], frame=_frame(geography=None))


def test_trends_alone_need_no_comparables() -> None:
    trend = _claim(side="tendencia", against=[], supporting=["s2"])

    assert _report([trend], comparables=[]).claims[0].side == "tendencia"


def test_the_grader_still_decides_how_sure_each_finding_is() -> None:
    claim = _claim(supporting=["s1", "s2", "s3"], status="confirmado")
    lone = _claim(supporting=["s1"], status="confirmado")

    report = _report([claim, lone.model_copy(update={"text": "Otra cosa breve"})])

    assert [item.status for item in report.claims] == ["confirmado", "por_confirmar"]


# --- the short result says side and against whom ------------------------------


def test_the_result_says_the_side_and_against_whom() -> None:
    trend = _claim(side="tendencia", against=[], supporting=["s2"], text="Sube el maíz")
    weak = _claim(side="debilidad", text="El Sol abre más temprano")

    text = report_message(_report([_claim(), weak, trend]))

    assert "Fortaleza frente a Tortillería El Sol: El Sol no entrega" in text
    assert "Debilidad frente a Tortillería El Sol: El Sol abre más temprano" in text
    assert "Tendencia: Sube el maíz" in text
    assert "Tortillería La Luna" in text  # named as candidate, never tabled
    assert text.rstrip().endswith("¿Cuál tomas?")
