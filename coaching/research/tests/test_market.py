"""Market mode: demand, customers, competitors and a size that is never a lone
number (E83 S83.3).

Synthetic data only. Owner decisions (2026-09-30): one freshness window of 90
days for every mode; the size is "por confirmar" without three independent
recent sources; words naming a type of business ("tortillería", "taller") are
never private company words, so a competitor sharing them can be searched.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from coaching.research.engine import check_queries, is_own_company, normalize
from coaching.research.models import (
    DecisionOption,
    MarketSize,
    PrivateTerms,
    ResearchFrame,
    ResearchReport,
    SourceRecord,
)
from coaching.research.report import build_report

COMPANY = "Tortillería Zorblax"
PRIVATE = PrivateTerms(
    company_names=[COMPANY], people=["Ximena Vrkalova"], figures=["$987,654"]
)


def _frame(**fields: object) -> ResearchFrame:
    data: dict[str, object] = {
        "concern": "No sé si abrir otra sucursal",
        "question": "¿Hay clientes suficientes para otra sucursal en Cholula?",
        "decision_informed": "Abrir o no una sucursal en Cholula este año",
        "mode": "mercado",
        "offer_category": "tortillas de maíz",
        "segment": "fondas y restaurantes",
        "geography": "Cholula",
        "horizon": "2026",
    }
    data.update(fields)
    return ResearchFrame.model_validate(data)


def _check(
    queries: list[str], private: PrivateTerms = PRIVATE, **fields: object
) -> tuple[list[str], list[str]]:
    frame = _frame(**fields).model_copy(update={"queries": queries})
    result = check_queries(frame, private)
    return result.accepted, [item.reason for item in result.rejected]


# --- business-type words are never private (privacy, both sides) -------------


@pytest.mark.parametrize(
    "query",
    [
        "precios de Tortillería El Sol en Cholula",
        "tortillería El Sol Cholula opiniones",
        "TORTILLERIA LA LUNA cholula",
        "tortillería en Cholula 2026",
    ],
)
def test_a_competitor_sharing_the_type_of_business_is_searched(query: str) -> None:
    accepted, rejected = _check([query])

    assert accepted == [query]
    assert rejected == []


@pytest.mark.parametrize(
    "query",
    [
        "precios Tortillería Zorblax Cholula",
        "zorblax cholula",
        "tortilleria zorblax",
        "Tortillería Zor​blax Cholula",  # zero-width space
        "Tortillería Z o r b l a x",
        "Tortillería Zоrblax",  # Cyrillic o
    ],
)
def test_the_company_name_and_its_distinctive_words_stay_blocked(query: str) -> None:
    accepted, rejected = _check([query])

    assert accepted == []
    assert rejected and rejected[0] in ("empresa", "caracteres")


def test_the_full_name_stays_blocked_even_when_made_only_of_business_words() -> None:
    private = PrivateTerms(company_names=["Taller Mecánico"])

    accepted, rejected = _check(
        ["taller mecánico en Cholula", "talleres en Cholula", "taller en Cholula"],
        private,
    )

    assert accepted == ["talleres en Cholula", "taller en Cholula"]
    assert rejected == ["empresa"]


@pytest.mark.parametrize(
    ("company", "competitor"),
    [
        ("Panadería La Esperanza", "Panadería El Trigo"),
        ("Consultorio Dental Vrano", "Consultorio Dental Sonrisa"),
        ("Restaurante Qulimbo", "Restaurante Los Arcos"),
        ("Talleres Mecánicos Yxtla", "Talleres Mecánicos Rápidos"),
        ("Farmacias Kavora", "Farmacias San Pablo"),
    ],
)
def test_business_words_pass_and_the_distinctive_word_does_not(
    company: str, competitor: str
) -> None:
    private = PrivateTerms(company_names=[company])
    distinctive = company.split()[-1]

    accepted, rejected = _check(
        [f"{competitor} Cholula", f"{distinctive} Cholula"], private
    )

    assert accepted == [f"{competitor} Cholula"]
    assert rejected == ["empresa"]


def test_business_words_do_not_exempt_people_or_figures() -> None:
    private = PrivateTerms(people=["Paloma Salón"], figures=["$987,654"])

    accepted, rejected = _check(
        ["Paloma Salón Cholula", "tortillería con ventas de 987654"], private
    )

    assert accepted == []
    assert rejected == ["persona", "cifra"]


def test_what_is_checked_is_what_is_sent_with_business_words() -> None:
    raw = "precios de  Tortillería​ El Sol en Cholula"

    accepted, _ = _check([raw])

    assert accepted == ["precios de Tortillería El Sol en Cholula"]


def test_a_branch_of_the_own_company_is_recognized_by_its_distinctive_word() -> None:
    frame = _frame()

    assert is_own_company("Zorblax Centro", frame, PRIVATE)
    assert is_own_company("Tortillería Zorblax Cholula", frame, PRIVATE)
    assert not is_own_company("Tortillería El Sol", frame, PRIVATE)
    assert normalize("Tortillería") == "tortilleria"


# --- the size: a range with method and assumptions, or "no estimable" --------

TODAY = date(2026, 9, 30)


def _source(source_id: str, publisher: str, *, age_days: int = 20) -> SourceRecord:
    return SourceRecord(
        source_id=source_id,
        origin="web",
        title=f"Nota {source_id}",
        publisher=publisher,
        url=f"https://ejemplo-{source_id}.test/mercado",
        published_on=TODAY - timedelta(days=age_days),
        consulted_on=TODAY,
        excerpt=f"En Cholula se venden miles de kilos al día ({source_id})",
    )


SOURCES = [
    _source("c1", "Cámara de la Tortilla de Puebla"),
    _source("p1", "Diario de Cholula"),
    _source("r1", "Reporte de la Industria del Maíz"),
    _source("old", "Censo antiguo", age_days=400),
]
OPTIONS = [
    DecisionOption(label="A", text="Abrir la sucursal en Cholula en enero"),
    DecisionOption(label="B", text="Crecer primero con fondas de mi zona"),
]


def _size(**fields: object) -> MarketSize:
    data: dict[str, object] = {
        "kind": "estimado",
        "low": 120000,
        "high": 180000,
        "unit": "kilos de tortilla al mes",
        "method": "fondas de Cholula por kilos que compra cada una",
        "assumptions": ["cada fonda compra entre 40 y 60 kilos al mes"],
        "supporting": ["c1", "p1", "r1"],
    }
    data.update(fields)
    return MarketSize.model_validate(data)


def _report(
    size: MarketSize | None, frame: ResearchFrame | None = None
) -> ResearchReport:
    return build_report(
        frame=frame or _frame(confirmed=True, queries=[]),
        researched_on=TODAY,
        sources=SOURCES,
        claims=[],
        options=OPTIONS,
        recommendation="A",
        recommendation_reason="hay fondas suficientes en Cholula",
        market_size=size,
    )


def test_a_size_is_never_a_lone_number() -> None:
    with pytest.raises(ValidationError, match="size_needs_a_range"):
        _size(low=150000, high=150000)
    with pytest.raises(ValidationError, match="size_needs_a_range"):
        _size(high=None)
    with pytest.raises(ValidationError, match="size_needs_a_range"):
        _size(low=180000, high=120000)


def test_a_size_says_how_it_was_calculated_and_what_it_assumes() -> None:
    with pytest.raises(ValidationError, match="size_needs_unit_and_method"):
        _size(method=" ")
    with pytest.raises(ValidationError, match="size_needs_unit_and_method"):
        _size(unit=None)
    with pytest.raises(ValidationError, match="size_needs_assumptions"):
        _size(assumptions=[])
    with pytest.raises(ValidationError, match="size_needs_sources"):
        _size(supporting=[])


def test_not_estimable_says_what_data_would_allow_it_and_carries_no_number() -> None:
    with pytest.raises(ValidationError, match="not_estimable_needs_missing_data"):
        MarketSize(kind="no_estimable")
    with pytest.raises(ValidationError, match="not_estimable_has_no_number"):
        MarketSize(
            kind="no_estimable", missing_data="cuántas fondas hay", low=Decimal(1)
        )
    assert MarketSize(kind="no_estimable", missing_data="cuántas fondas hay en Cholula")


def test_sources_that_disagree_are_never_averaged() -> None:
    figures = [
        {"value": 100000, "source_id": "c1"},
        {"value": 200000, "source_id": "p1"},
    ]
    with pytest.raises(ValidationError, match="size_range_must_cover_every_source"):
        _size(low=140000, high=160000, figures=figures)  # the average, dressed up
    assert _size(low=100000, high=200000, figures=figures)


def test_a_size_is_confirmed_only_with_three_recent_independent_sources() -> None:
    confirmed = _report(_size())
    two = _report(_size(supporting=["c1", "p1", "old"]))

    assert confirmed.market_size is not None
    assert confirmed.market_size.status == "confirmado"
    assert two.market_size is not None
    assert two.market_size.status == "por_confirmar"  # 400 days old does not count


def test_the_grader_ignores_a_status_set_by_hand() -> None:
    report = _report(_size(supporting=["c1"], status="confirmado", confidence="alta"))

    assert report.market_size is not None
    assert report.market_size.status == "por_confirmar"
    assert report.market_size.confidence == "baja"


def test_disagreeing_sources_cap_the_confidence() -> None:
    figures = [
        {"value": 120000, "source_id": "c1"},
        {"value": 180000, "source_id": "p1"},
        {"value": 150000, "source_id": "r1"},
    ]
    report = _report(_size(supporting=[], figures=figures))

    assert report.market_size is not None
    assert report.market_size.status == "confirmado"
    assert report.market_size.confidence == "media"


def test_no_size_without_a_confirmed_segment_and_geography() -> None:
    for missing in ({"segment": None}, {"geography": " "}):
        frame = _frame(confirmed=True, queries=[], **missing)
        with pytest.raises(ValidationError, match="size_needs_segment_and_geography"):
            _report(_size(), frame)


def test_without_segment_or_geography_the_size_is_not_estimable_yet() -> None:
    report = _report(None, _frame(confirmed=True, queries=[], segment=None))

    assert report.market_size is not None
    assert report.market_size.kind == "no_estimable"
    assert report.market_size.missing_data == "tipo de cliente"


def test_with_segment_and_geography_the_size_must_be_stated() -> None:
    with pytest.raises(ValidationError, match="mercado_needs_size"):
        _report(None)


def test_a_size_belongs_only_to_the_market_mode_and_cites_known_sources() -> None:
    with pytest.raises(ValidationError, match="size_only_in_mercado"):
        _report(_size(), _frame(confirmed=True, queries=[], mode="benchmark"))
    with pytest.raises(ValidationError, match="unknown_source"):
        _report(_size(supporting=["zz"]))
