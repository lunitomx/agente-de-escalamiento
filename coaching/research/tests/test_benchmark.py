"""Benchmark mode: comparable businesses, one source and date per cell (E83 S83.2).

Synthetic data only. A comparable is a business with the same confirmed offer
and geography; one the owner did not name stays a candidate until he says yes.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from coaching.research import messages
from coaching.research.engine import build_queries, normalize
from coaching.research.flow import run
from coaching.research.models import (
    MAX_COMPARABLES,
    Comparable,
    DecisionOption,
    ResearchFrame,
    SourceRecord,
)
from coaching.research.report import build_report

TODAY = date(2026, 9, 30)


def _frame(**fields: object) -> ResearchFrame:
    data: dict[str, object] = {
        "concern": "Creo que cobro poco",
        "question": "¿Cobro menos que negocios parecidos en Puebla?",
        "decision_informed": "Subir o no el precio del kilo en enero",
        "mode": "benchmark",
        "decision_area": "cash",
        "offer_category": "tortillas de maíz",
        "geography": "Puebla",
        "competitors": ["Tortillería El Sol"],
        "queries": ["precios de tortillas de maíz en Puebla 2026"],
        "confirmed": True,
    }
    data.update(fields)
    return ResearchFrame.model_validate(data)


def _source(
    source_id: str, publisher: str, *, url: bool = True, dated: bool = True
) -> SourceRecord:
    return SourceRecord.model_validate(
        {
            "source_id": source_id,
            "origin": "web" if url else "dueño",
            "title": f"Página {source_id}",
            "publisher": publisher,
            "url": f"https://ejemplo-{source_id}.test/p" if url else None,
            "published_on": (TODAY - timedelta(days=20)).isoformat() if dated else None,
            "consulted_on": TODAY.isoformat(),
            "excerpt": f"Kilo a 24 pesos ({source_id})",
        }
    )


SOURCES = [
    _source("s1", "Tortillería El Sol"),
    _source("s2", "Directorio Puebla"),
    _source("d1", "Cotización que me pasaron", url=False),
]
OPTIONS = [
    DecisionOption(label="A", text="Subir el kilo a 24 pesos en enero"),
    DecisionOption(label="B", text="Mantener el precio y vender por WhatsApp"),
]


def _owner_named(**fields: object) -> Comparable:
    data: dict[str, object] = {
        "name": "Tortillería El Sol",
        "named_by_owner": True,
        "cells": {"precio": {"value": "24 pesos el kilo", "source_id": "s1"}},
    }
    data.update(fields)
    return Comparable.model_validate(data)


def _candidate(**fields: object) -> Comparable:
    data: dict[str, object] = {
        "name": "Molino La Luna",
        "found_in": "s2",
        "why": "Vende tortillas de maíz en Puebla",
    }
    data.update(fields)
    return Comparable.model_validate(data)


def _report(
    comparables: list[Comparable], frame: ResearchFrame | None = None
) -> object:
    return build_report(
        frame=frame or _frame(),
        researched_on=TODAY,
        sources=SOURCES,
        claims=[],
        options=OPTIONS,
        recommendation="A",
        recommendation_reason="estás abajo de los negocios parecidos",
        comparables=comparables,
    )


def test_a_cell_with_a_value_but_no_source_is_an_estimate_and_is_refused() -> None:
    with pytest.raises(ValidationError, match="cell_without_source"):
        _owner_named(cells={"precio": {"value": "unos 25 pesos"}})


def test_a_candidate_needs_where_it_was_found_and_why_it_looks_alike() -> None:
    with pytest.raises(ValidationError, match="candidate_needs_source_and_reason"):
        _candidate(found_in=None)
    with pytest.raises(ValidationError, match="candidate_needs_source_and_reason"):
        _candidate(why=" ")


def test_only_owner_named_or_owner_confirmed_businesses_count() -> None:
    assert _owner_named().counted
    assert _candidate(owner_confirmed=True).counted
    assert not _candidate().counted


def test_at_most_five_comparables() -> None:
    many = [_candidate(name=f"Molino {n}") for n in range(MAX_COMPARABLES + 1)]

    assert MAX_COMPARABLES == 5
    with pytest.raises(ValidationError):
        _report(many)
    assert _report(many[:MAX_COMPARABLES])


def test_comparables_are_unique_by_name() -> None:
    with pytest.raises(ValidationError, match="duplicate_comparable"):
        _report([_candidate(), _candidate(name="molino la  luna")])


def test_comparables_cite_known_sources() -> None:
    with pytest.raises(ValidationError, match="unknown_source"):
        _report([_candidate(found_in="fantasma")])
    with pytest.raises(ValidationError, match="unknown_source"):
        _report([_owner_named(cells={"precio": {"value": "24", "source_id": "x"}})])


def test_owner_named_means_named_in_the_frame() -> None:
    with pytest.raises(ValidationError, match="not_named_by_owner"):
        _report([_owner_named(name="Tortillería Otra")])
    assert _report([_owner_named(name="tortilleria el sol")])


def test_published_numbers_need_a_source_with_a_link() -> None:
    hearsay = {"metricas": {"value": "vende 500 kilos al día", "source_id": "d1"}}
    published = {"metricas": {"value": "vende 500 kilos al día", "source_id": "s1"}}

    with pytest.raises(ValidationError, match="metric_needs_published_source"):
        _report([_owner_named(cells=hearsay)])
    assert _report([_owner_named(cells=published)])


def test_comparables_only_belong_to_the_benchmark_mode() -> None:
    with pytest.raises(ValidationError, match="comparables_only_in_benchmark"):
        _report([_candidate()], frame=_frame(mode="mercado"))


def test_comparables_need_a_confirmed_offer_and_geography() -> None:
    with pytest.raises(ValidationError, match="comparables_need_offer_and_geography"):
        _report([_candidate()], frame=_frame(geography=None))
    with pytest.raises(ValidationError, match="comparables_need_offer_and_geography"):
        _report([_candidate()], frame=_frame(offer_category=" "))


# --- searches for the businesses the owner named (privacy) -------------------

PRIVATE: dict[str, object] = {
    "company_names": ["Tortillería Zorblax"],
    "people": ["Ximena Vrkalova"],
    "figures": ["$987,654"],
}
MARKERS = ["zorblax", "ximena", "vrkalova", "987654"]


def _flat(text: str) -> str:
    return normalize(text).replace(" ", "").replace(",", "").replace(".", "")


def _frame_input(**fields: object) -> dict[str, object]:
    return _frame(confirmed=False, queries=[]).model_dump() | fields


def test_one_search_per_business_the_owner_named_at_most_two() -> None:
    frame = _frame(
        queries=[],
        competitors=["Tortillería El Sol", "Molino La Luna", "Maíz Tres"],
    )

    queries = build_queries(frame)

    assert "precios de Tortillería El Sol en Puebla" in queries
    assert "precios de Molino La Luna en Puebla" in queries
    assert not any("Maíz Tres" in query for query in queries)
    assert len(queries) == 5


def test_other_modes_do_not_search_for_named_businesses() -> None:
    queries = build_queries(_frame(mode="mercado", queries=[]))

    assert not any("El Sol" in query for query in queries)


def test_a_named_business_carrying_the_company_or_its_people_is_not_searched() -> None:
    frame = _frame_input(competitors=["Zorblax Express", "Tacos de Ximena Vrkalova"])

    result = run({"action": "frame", "frame": frame, "private": PRIVATE})

    assert result.frame is not None
    assert sorted(item.reason for item in result.rejected) == ["empresa", "persona"]
    for query in result.frame.queries:
        for marker in MARKERS:
            assert marker not in _flat(query)
    for marker in MARKERS:
        assert marker not in _flat(result.message)


def test_benchmark_without_a_city_or_zone_asks_before_searching() -> None:
    web = run(
        {"action": "frame", "frame": _frame_input(geography=None), "private": PRIVATE}
    )
    offline = run(
        {
            "action": "frame",
            "frame": _frame_input(geography=" ", search_mode="sin_busqueda"),
            "private": PRIVATE,
        }
    )

    for result in (web, offline):
        assert result.errors == ["needs_geography"]
        assert result.message == messages.NEEDS_OFFER
        assert result.frame is None
