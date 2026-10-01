"""Strengths, weaknesses and trends: outside position against the comparables
the owner confirmed, plus dated trends (E83 S83.4).

Synthetic data only. Owner decisions (2026-09-30): sources count only up to 90
days old; a candidate stays a candidate until the owner says yes.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from coaching.research import messages
from coaching.research.flow import run
from coaching.research.models import (
    Comparable,
    DecisionOption,
    ResearchClaim,
    ResearchFrame,
    ResearchReport,
    SourceRecord,
)
from coaching.research.report import build_report, report_message, save_report

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


# --- comparables of a current benchmark are reused ----------------------------


def _benchmark(
    *, researched_on: date = TODAY, geography: str = "Puebla"
) -> ResearchReport:
    sources = [
        _source("s1", "Diario Uno", age=20 + (TODAY - researched_on).days),
        _source("s2", "Revista Dos", age=80 + (TODAY - researched_on).days),
        SourceRecord.model_validate(
            {
                "source_id": "d1",
                "origin": "dueño",
                "title": "Cotización que le llegó",
                "publisher": "Cliente del dueño",
                "consulted_on": researched_on.isoformat(),
                "excerpt": "El Sol da 10% a fondas",
            }
        ),
    ]
    frame = _frame(
        mode="benchmark",
        decision_area="cash",
        geography=geography,
        queries=[f"precios de tortillas de maíz en {geography} 2026"],
    )
    comparables = [
        Comparable.model_validate(
            {
                "name": "Tortillería El Sol",
                "named_by_owner": True,
                "cells": {
                    "precio": {"value": "24 pesos el kilo", "source_id": "s1"},
                    "paquetes": {"value": "10% a fondas", "source_id": "d1"},
                    "canales": {"value": "pedidos por WhatsApp", "source_id": "s2"},
                },
            }
        ),
        Comparable.model_validate(
            {
                "name": "Tortillería La Estrella",
                "found_in": "s2",
                "why": "vende lo mismo en su zona",
                "owner_confirmed": True,
            }
        ),
        CANDIDATE.model_copy(update={"found_in": "s1"}),
    ]
    return build_report(
        frame=frame,
        researched_on=researched_on,
        sources=sources,
        claims=[],
        options=[
            DecisionOption(label="A", text="Subir 8% el kilo en enero"),
            DecisionOption(label="B", text="Mantener el precio"),
        ],
        recommendation="A",
        recommendation_reason="tu precio está abajo",
        chosen="A",
        comparables=comparables,
    )


def _frame_step(base: Path | None, **fields: object) -> dict[str, object]:
    frame = _frame(queries=[], confirmed=False, competitors=[], **fields)
    context: dict[str, object] = {
        "action": "frame",
        "today": TODAY.isoformat(),
        "frame": frame.model_dump(mode="json"),
        "private": {"company_names": ["Tortillería Zorblax"]},
    }
    if base is not None:
        context["base_path"] = str(base)
    return context


def test_frame_reuses_the_comparables_of_a_current_benchmark(tmp_path: Path) -> None:
    save_report(_benchmark(), tmp_path)

    result = run(_frame_step(tmp_path))

    assert result.errors == []
    names = {item.name: item.counted for item in result.comparables}
    assert names == {
        "Tortillería El Sol": True,
        "Tortillería La Estrella": True,
        "Tortillería La Luna": False,  # a candidate stays a candidate
    }
    assert result.frame is not None
    assert result.frame.competitors == ["Tortillería El Sol"]
    assert "Tortillería El Sol y Tortillería La Estrella" in result.message
    assert "Tortillería La Luna" in result.message
    assert messages.NOT_COUNTED in result.message
    cited = {
        cell.source_id for item in result.comparables for cell in item.cells.values()
    }
    assert cited <= {source.source_id for source in result.sources}


def test_reused_cells_keep_only_sources_up_to_90_days_old(tmp_path: Path) -> None:
    # Researched 30 days ago: s1 is now 50 days old, s2 is 110 days old.
    save_report(_benchmark(researched_on=TODAY - timedelta(days=30)), tmp_path)

    result = run(_frame_step(tmp_path))

    sol = next(item for item in result.comparables if item.name == "Tortillería El Sol")
    assert set(sol.cells) == {"precio", "paquetes"}
    by_id = {source.source_id: source for source in result.sources}
    for item in result.comparables:
        for cell in item.cells.values():
            published = by_id[cell.source_id or ""].published_on
            assert published is None or (TODAY - published).days <= 90
    # A business the owner confirmed keeps where it was found (provenance);
    # what it does is shown only from recent sources.
    assert "Tortillería La Estrella" in {item.name for item in result.comparables}


def test_a_stale_or_other_zone_benchmark_is_not_reused(tmp_path: Path) -> None:
    stale, other = tmp_path / "stale", tmp_path / "other"
    save_report(_benchmark(researched_on=TODAY - timedelta(days=91)), stale)
    save_report(_benchmark(geography="Cholula"), other)

    for base in (stale, other):
        result = run(_frame_step(base))
        assert result.errors == []
        assert result.comparables == []
        assert messages.NEEDS_COMPARABLES in result.message


def test_nothing_is_read_without_a_base_path() -> None:
    result = run(_frame_step(None))

    assert result.errors == []
    assert result.comparables == []


def test_without_search_only_the_owner_sources_come_back(tmp_path: Path) -> None:
    save_report(_benchmark(), tmp_path)

    result = run(_frame_step(tmp_path, search_mode="sin_busqueda"))

    assert result.message.startswith(messages.SEARCH_OFF)
    assert {source.origin for source in result.sources} == {"dueño"}
    sol = next(item for item in result.comparables if item.name == "Tortillería El Sol")
    assert set(sol.cells) == {"paquetes"}
    # Candidates found on a web page are not brought back without search.
    assert "Tortillería La Luna" not in {item.name for item in result.comparables}


def test_reused_comparables_feed_a_valid_strengths_report(tmp_path: Path) -> None:
    save_report(_benchmark(), tmp_path)
    step = run(_frame_step(tmp_path))
    assert step.frame is not None
    frame = step.frame.model_copy(
        update={"confirmed": True, "queries": step.frame.queries}
    )

    report = build_report(
        frame=frame,
        researched_on=TODAY,
        sources=[*step.sources, _source("t1", "Diario Tendencias")],
        claims=[
            _claim(supporting=[step.sources[0].source_id]),
            _claim(
                side="tendencia", against=[], supporting=["t1"], text="Sube el maíz"
            ),
        ],
        options=OPTIONS,
        recommendation="A",
        recommendation_reason="es lo que te distingue",
        comparables=step.comparables,
    )

    assert [claim.side for claim in report.claims] == ["fortaleza", "tendencia"]
