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


# Security review (S83.1): the check must run on exactly what is sent.


@pytest.mark.parametrize(
    ("query", "reason"),
    [
        ("precios Zor​blax Puebla", "empresa"),  # zero-width space
        ("precios Zor⁠blax Puebla", "empresa"),  # word joiner
        ("precios Zor­blax Puebla", "empresa"),  # soft hyphen
        ("precios Ｚｏｒｂｌａｘ Puebla", "empresa"),  # fullwidth
        ("precios Z.o.r.b.l.a.x Puebla", "empresa"),
        ("precios Z o r b l a x Puebla", "empresa"),
        ("Xi‍mena tortillas Puebla", "persona"),  # zero-width joiner
        ("Ｘｉｍｅｎａ tortillas", "persona"),  # fullwidth
        ("Okonkwo tortillas", "persona"),  # NBSP
        ("precios Zоrblax Puebla", "caracteres"),  # Cyrillic o
    ],
)
def test_hidden_or_disguised_names_are_rejected(query: str, reason: str) -> None:
    result = _check([query])

    assert result.accepted == []
    assert [item.reason for item in result.rejected] == [reason]


@pytest.mark.parametrize(
    "query",
    [
        "tortillerías con 4 321 clientes",
        "tortillerías con 4.321 clientes",
        "tortillerías con 4'321 clientes",
        "tortillerías con 4 321 clientes",
        "tortillerías con 4 321 clientes",
        "ventas de 987 654 al mes",
        "tortillas 2026 4321",
        "ventas de ９８７６５４",  # fullwidth digits
        "ventas de 98​7654",
    ],
)
def test_figures_with_any_digit_grouping_are_rejected(query: str) -> None:
    result = _check([query])

    assert result.accepted == []
    assert [item.reason for item in result.rejected] == ["cifra"]


@pytest.mark.parametrize(
    ("figure", "query"),
    [
        ("1,200,000", "ventas de 1.2 millones"),
        ("1,200,000", "ventas de 1,2 millones de pesos"),
        ("1,234,567", "ventas de 1.2 millones"),
        ("1,200,000", "ventas de 1.2M"),
        ("987,654", "ventas de 987 mil"),
        ("987,654", "ventas de 988k"),
        ("1'200,000", "ventas de 1 200 000"),
        ("1.2 millones", "ventas de 1,200,000"),
    ],
)
def test_scaled_figures_are_rejected(figure: str, query: str) -> None:
    frame = _frame("benchmark").model_copy(update={"queries": [query]})

    result = check_queries(frame, PrivateTerms(figures=[figure]))

    assert result.accepted == []
    assert [item.reason for item in result.rejected] == ["cifra"]


def test_accepted_queries_are_the_sanitized_form_that_was_checked() -> None:
    raw = "precios de tortillas​ de maíz  en Puebla ¿2026?"

    result = _check([raw])

    assert result.accepted == ["precios de tortillas de maíz en Puebla ¿2026?"]


def test_ordinary_spanish_punctuation_and_accents_pass() -> None:
    query = "¿cuánto cuesta el kilo de tortilla en Puebla? ñandú $ 2026"

    assert _check([query]).accepted == [query]


def test_hidden_characters_in_the_private_terms_do_not_weaken_the_check() -> None:
    private = PrivateTerms(
        company_names=["Zor​blax"],
        people=["Ｘimena Vrkalova"],
        figures=["98​7,654"],
    )
    frame = _frame("benchmark").model_copy(
        update={"queries": ["precios Zorblax", "Ximena tortillas", "ventas 987654"]}
    )

    result = check_queries(frame, private)

    assert result.accepted == []
    assert [item.reason for item in result.rejected] == ["empresa", "persona", "cifra"]


def test_small_or_unrelated_numbers_still_pass() -> None:
    frame = _frame("benchmark").model_copy(
        update={
            "queries": ["precios de tortillas 2026", "tortillerías con 987 sucursales"]
        }
    )

    result = check_queries(frame, PrivateTerms(figures=["$987,654"]))

    assert result.rejected == []
