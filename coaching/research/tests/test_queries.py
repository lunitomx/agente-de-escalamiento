"""Searches carry no private company data (E83 S83.1 privacy test).

A synthetic company has unique markers in its name, its people and its
figures. The owner's concern mentions all of them; no search that the module
builds or accepts may contain any of them.
"""

from __future__ import annotations

import pytest

from coaching.research.engine import QueryCheck, build_queries, check_queries, normalize
from coaching.research.models import PrivateTerms, ResearchFrame

COMPANY = "Tortillería Zorblax"
OWNER = "Ximena Vrkalova"
STAFF = "Brunhilda Okonkwo"
FIGURES = ["$987,654", "4321"]
PRIVATE = PrivateTerms(company_names=[COMPANY], people=[OWNER, STAFF], figures=FIGURES)
MARKERS = [
    "zorblax",
    "ximena",
    "vrkalova",
    "brunhilda",
    "okonkwo",
    "987654",
    "987,654",
    "4321",
]

CONCERN = (
    f"En {COMPANY} vendemos $987,654 al mes con 4321 clientes; {OWNER} y "
    f"{STAFF} creen que cobramos poco."
)


def _frame(mode: str, **fields: str | None) -> ResearchFrame:
    return ResearchFrame.model_validate(
        {
            "concern": CONCERN,
            "question": f"¿{COMPANY} cobra menos que negocios parecidos?",
            "decision_informed": "Subir o no el precio del kilo en enero",
            "mode": mode,
            "offer_category": "tortillas de maíz",
            "geography": "Puebla",
            "horizon": "2026",
            **fields,
        }
    )


def _check(queries: list[str], frame: ResearchFrame | None = None) -> QueryCheck:
    base = frame or _frame("benchmark")
    return check_queries(base.model_copy(update={"queries": queries}), PRIVATE)


def _assert_clean(queries: list[str]) -> None:
    for query in queries:
        flat = normalize(query).replace(" ", "")
        for marker in MARKERS:
            assert normalize(marker).replace(" ", "") not in flat, (marker, query)


@pytest.mark.parametrize("mode", ["benchmark", "mercado", "fortalezas-tendencias"])
def test_built_queries_use_only_frame_fields_and_carry_no_private_marker(
    mode: str,
) -> None:
    queries = build_queries(_frame(mode))

    assert 2 <= len(queries) <= 3
    assert all("tortillas de maíz" in query for query in queries)
    _assert_clean(queries)
    assert _check(queries).rejected == []


def test_built_queries_skip_empty_fields() -> None:
    queries = build_queries(_frame("benchmark", geography=None, horizon=None))

    assert queries
    assert all("None" not in query and "  " not in query for query in queries)


def test_no_offer_category_means_no_queries_yet() -> None:
    assert build_queries(_frame("mercado", offer_category=None)) == []


@pytest.mark.parametrize(
    ("query", "reason"),
    [
        ("precios zorblax puebla", "empresa"),
        ("TORTILLERÍA ZORBLAX opiniones", "empresa"),
        ("ximena tortillas puebla", "persona"),
        ("Okonkwo tortillas de maíz", "persona"),
        ("tortillerías que venden 987654 al mes", "cifra"),
        ("tortillerías con 4,321 clientes", "cifra"),
        ("ventas de $987.654 en tortillas", "cifra"),
    ],
)
def test_proposed_queries_with_private_data_are_rejected(
    query: str, reason: str
) -> None:
    result = _check([query, "precios de tortillas en Puebla 2026"])

    assert result.accepted == ["precios de tortillas en Puebla 2026"]
    assert [(item.query, item.reason) for item in result.rejected] == [(query, reason)]


def test_private_data_smuggled_into_a_frame_field_is_rejected() -> None:
    frame = _frame("benchmark", segment="clientes de Zorblax")

    result = _check(build_queries(frame), frame)

    _assert_clean(result.accepted)
    assert result.rejected


def test_public_words_inside_a_company_name_are_allowed_by_the_confirmed_frame() -> (
    None
):
    frame = _frame("benchmark", offer_category="tortillería")

    assert _check(["precios de tortillería en Puebla"], frame).accepted == [
        "precios de tortillería en Puebla"
    ]
    assert _check(["precios de tortillería en Puebla"]).accepted == []


def test_years_are_allowed_unless_they_are_private_figures() -> None:
    assert _check(["tendencias tortillas 2026"]).accepted
    frame = _frame("benchmark").model_copy(
        update={"queries": ["tendencias tortillas 2026"]}
    )
    assert check_queries(frame, PrivateTerms(figures=["2026"])).accepted == []
