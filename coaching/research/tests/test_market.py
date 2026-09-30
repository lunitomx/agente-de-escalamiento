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
from pathlib import Path

import pytest
from pydantic import ValidationError

from coaching.research.diagnosis import to_diagnostic_inputs
from coaching.research.engine import (
    build_queries,
    check_queries,
    is_own_company,
    normalize,
)
from coaching.research.flow import run
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


# --- the market frame: no size search without segment and geography ----------


def _frame_step(**fields: object) -> dict[str, object]:
    return {
        "action": "frame",
        "frame": _frame(**fields).model_dump(mode="json"),
        "private": PRIVATE.model_dump(),
    }


def test_market_searches_demand_customers_and_size_with_segment_and_zone() -> None:
    queries = build_queries(_frame())

    assert queries == [
        "demanda de tortillas de maíz en Cholula 2026",
        "clientes de tortillas de maíz fondas y restaurantes en Cholula",
        "tamaño del mercado de tortillas de maíz fondas y restaurantes en Cholula 2026",
    ]


@pytest.mark.parametrize(
    ("missing", "question"),
    [
        ({"segment": None}, "¿A qué tipo de cliente le vendes?"),
        ({"geography": None}, "¿En qué ciudad o zona?"),
        (
            {"segment": " ", "geography": None},
            "¿A qué tipo de cliente le vendes y en qué ciudad o zona?",
        ),
    ],
)
def test_without_segment_or_zone_no_size_is_searched_and_the_question_comes_back(
    missing: dict[str, object], question: str
) -> None:
    result = run(_frame_step(**missing))

    assert result.errors == []
    assert result.frame is not None
    assert not any("tamaño" in query for query in result.frame.queries)
    assert result.missing_question == question
    assert "no calculo el tamaño de tu mercado" in result.message
    assert result.message.endswith("¿Va, o cambio algo?")


def test_with_segment_and_zone_there_is_no_missing_question() -> None:
    result = run(_frame_step())

    assert result.missing_question is None
    assert "no calculo" not in result.message


def test_without_search_the_market_frame_also_asks_what_is_missing() -> None:
    result = run(_frame_step(segment=None, search_mode="sin_busqueda"))

    assert result.missing_question == "¿A qué tipo de cliente le vendes?"
    assert "no calculo el tamaño de tu mercado" in result.message


def test_market_searches_stay_private() -> None:
    frame = _frame(segment="clientes de Zorblax", competitors=["Tortillería El Sol"])

    result = check_queries(
        frame.model_copy(update={"queries": build_queries(frame)}), PRIVATE
    )

    for query in result.accepted:
        assert "zorblax" not in normalize(query)
    assert [item.reason for item in result.rejected] == ["empresa", "empresa"]


# --- what the owner sees ------------------------------------------------------

JARGON = ("TAM", "SAM", "SOM", "triangul", "módulo", "estimado", "no_estimable")


def _step(
    action: str, size: dict[str, object] | None, **fields: object
) -> dict[str, object]:
    step: dict[str, object] = {
        "action": action,
        "today": TODAY.isoformat(),
        "frame": _frame(confirmed=True, queries=[], **fields).model_dump(mode="json"),
        "private": PRIVATE.model_dump(),
        "sources": [source.model_dump(mode="json") for source in SOURCES],
        "options": [option.model_dump(mode="json") for option in OPTIONS],
        "recommendation": "A",
        "recommendation_reason": "hay fondas suficientes en Cholula",
    }
    if size is not None:
        step["market_size"] = size
    return step


def _size_input(**fields: object) -> dict[str, object]:
    return _size(**fields).model_dump(mode="json")


def test_the_result_shows_the_range_how_and_what_it_assumes() -> None:
    result = run(_step("report", _size_input()))

    assert result.errors == []
    text = result.message
    assert (
        "Tamaño de tu mercado (fondas y restaurantes en Cholula): entre 120,000 y "
        "180,000 kilos de tortilla al mes." in text
    )
    assert "**Confirmado**" in text
    assert "Cómo lo calculé: fondas de Cholula por kilos que compra cada una." in text
    assert "Lo que supongo: cada fonda compra entre 40 y 60 kilos al mes." in text
    assert text.endswith("¿Cuál tomas?")
    for word in JARGON:
        assert word not in text


def test_a_size_short_of_sources_says_how_many_recent_ones_it_has() -> None:
    result = run(_step("report", _size_input(supporting=["c1", "old"])))

    assert result.report is not None
    assert "**Por confirmar**" in result.message
    assert "1 fuente reciente" in result.message
    assert "hacen falta 3" in result.message


def test_disagreeing_sources_are_shown_side_by_side() -> None:
    figures = [
        {"value": 120000, "source_id": "c1"},
        {"value": 180000, "source_id": "p1"},
    ]
    result = run(_step("report", _size_input(supporting=["r1"], figures=figures)))

    text = result.message
    assert "Lo que dice cada fuente (no coinciden; no las promedio):" in text
    assert (
        "- Cámara de la Tortilla de Puebla, 10 de septiembre de 2026: 120,000" in text
    )
    assert "- Diario de Cholula, 10 de septiembre de 2026: 180,000" in text


def test_not_estimable_says_what_is_missing() -> None:
    result = run(_step("report", None, segment=None))

    assert result.errors == []
    assert (
        "Tamaño de tu mercado: no estimable todavía. Para estimarlo me falta: "
        "tipo de cliente." in result.message
    )


def test_the_flow_refuses_a_size_without_segment_and_a_market_without_size() -> None:
    assert run(_step("report", _size_input(), geography=None)).errors == [
        "size_needs_segment_and_geography"
    ]
    assert run(_step("report", None)).errors == ["mercado_needs_size"]


def test_a_saved_market_report_keeps_the_size(tmp_path: Path) -> None:
    step = _step("save", _size_input()) | {
        "base_path": str(tmp_path),
        "user_confirmed": True,
        "chosen": "A",
    }

    result = run(step)

    assert result.saved_to is not None
    saved = (tmp_path / result.saved_to).read_text(encoding="utf-8")
    assert "entre 120,000 y 180,000 kilos de tortilla al mes" in saved


# --- the next diagnosis: size as an assumption, never cut ---------------------


def _fits(line: str) -> bool:
    return len(line) <= 96 and len(line.split()) <= 12 and "/" not in line


def test_the_size_reaches_the_diagnosis_whole_as_an_assumption() -> None:
    report = _report(_size()).model_copy(update={"chosen": OPTIONS[0]})

    inputs = to_diagnostic_inputs(report, "r.md", TODAY)

    assert inputs.assumptions == [
        "Mercado confirmado, sep 2026: 120,000 a 180,000 kilos de tortilla al mes"
    ]
    assert all(_fits(line) for line in inputs.assumptions + inputs.open_questions)


def test_not_estimable_and_disagreement_are_open_questions() -> None:
    blank = _report(None, _frame(confirmed=True, queries=[], segment=None))
    figures = [
        {"value": 120000, "source_id": "c1"},
        {"value": 180000, "source_id": "p1"},
    ]
    split = _report(_size(figures=figures))

    missing = to_diagnostic_inputs(
        blank.model_copy(update={"chosen": OPTIONS[0]}), "r.md", TODAY
    )
    doubt = to_diagnostic_inputs(
        split.model_copy(update={"chosen": OPTIONS[0]}), "r.md", TODAY
    )

    assert missing.open_questions == [
        "Tamaño no estimable, sep 2026, falta: tipo de cliente"
    ]
    assert "Tamaño en duda, las fuentes no coinciden, sep 2026" in doubt.open_questions


def test_a_size_that_would_not_fit_is_refused_never_cut() -> None:
    long_unit = "kilos de tortilla de maíz nixtamalizado vendidos al mes en total"

    result = run(_step("report", _size_input(unit=long_unit)))

    assert result.errors == ["finding_too_long"]
    assert "conserva la cifra" in result.message
    assert run(_step("report", None, segment=None)).errors == []
