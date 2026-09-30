"""Market mode: demand, customers, competitors and a size that is never a lone
number (E83 S83.3).

Synthetic data only. Owner decisions (2026-09-30): one freshness window of 90
days for every mode; the size is "por confirmar" without three independent
recent sources; words naming a type of business ("tortillería", "taller") are
never private company words, so a competitor sharing them can be searched.
"""

from __future__ import annotations

import pytest

from coaching.research.engine import check_queries, is_own_company, normalize
from coaching.research.models import PrivateTerms, ResearchFrame

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
