"""S86.13 — El poder del uno da el efectivo correcto.

Pruebas de oro con «Mi Empresa, S.A. de C.V.» (empresa sintética,
`tests/fixtures/cash/mi_empresa.yaml`). Según el curso de cash que vimos (F4.1):
el flujo de cada palanca descuenta el capital de trabajo que se lleva.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import yaml

from escala_server.cash import FinancialInputs, LeverImpact, PowerOfOneEngine

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "cash" / "mi_empresa.yaml"
DASHBOARD = ROOT / "escala_server" / "static" / "dashboards" / "cash" / "power-of-one.html"


def _mi_empresa() -> dict[str, Any]:
    data: dict[str, Any] = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    return data


def _d(value: Any) -> Decimal:
    return Decimal(str(value))


def _inputs(year: str = "actual", **override: Decimal) -> FinancialInputs:
    data = _mi_empresa()[year]
    balance = data["balance"]
    er = data["estado_resultados"]
    values: dict[str, Decimal] = {
        "net_sales": _d(er["ventas"]),
        "cost_of_goods_sold": _d(er["costo_de_ventas"]),
        "total_opex": _d(er["gastos_de_operacion"]),
        "accounts_receivable": _d(balance["clientes"]),
        "inventory": _d(balance["inventario"]),
        "accounts_payable": _d(balance["proveedores"]),
        "net_profit": _d(er["utilidad_neta"]),
    }
    values.update(override)
    return FinancialInputs(**values)


def _by_lever(inputs: FinancialInputs) -> dict[str, LeverImpact]:
    result = PowerOfOneEngine().calculate(inputs)
    return {impact.lever: impact for impact in result.impacts}


def test_fixture_has_two_years_of_mi_empresa() -> None:
    data = _mi_empresa()
    assert data["empresa"] == "Mi Empresa, S.A. de C.V."
    for year in ("anterior", "actual"):
        assert {"balance", "estado_resultados"} <= set(data[year])
    assert data["actual"]["estado_resultados"]["ventas"] == 43826513.09
    assert data["anterior"]["estado_resultados"]["ventas"] == 35681743.00


# Valores del curso (F4.1, lámina 70). Errata L38: la lámina 38 dice 381,689.12
# para el flujo de precio; el valor correcto (y el que usa la lámina 70) es 381,869.12.
# Errata L37: la utilidad bruta correcta es 20,860,049.09, por eso volumen da 208,600.49.
GOLDEN = {
    "price": (381869.12, 438265.13),
    "volume": (146818.75, 208600.49),
    "cogs": (235050.36, 229664.64),
    "opex": (134210.40, 134210.40),
    "ar_days": (120072.64, 0.0),
    "inv_days": (62921.82, 0.0),
    "ap_days": (62921.82, 0.0),
}


@pytest.mark.parametrize("lever", sorted(GOLDEN))
def test_each_lever_matches_the_course_to_the_cent(lever: str) -> None:
    impact = _by_lever(_inputs())[lever]
    cash, ebit = GOLDEN[lever]
    assert impact.cash_impact == cash
    assert impact.ebit_impact == ebit


def test_totals_match_the_course_to_the_cent() -> None:
    result = PowerOfOneEngine().calculate(_inputs())
    assert result.combined_cash_impact == 1143864.91
    assert result.combined_ebit_impact == 1010740.66


def test_more_customers_balance_lowers_price_and_volume_cash() -> None:
    base = _by_lever(_inputs())
    more_ar = _by_lever(_inputs(accounts_receivable=Decimal("6639601.55")))
    # +1,000,000 en clientes → 1% = 10,000 menos de flujo en precio y en volumen.
    assert more_ar["price"].cash_impact == pytest.approx(base["price"].cash_impact - 10000, abs=0.01)
    assert more_ar["volume"].cash_impact == pytest.approx(base["volume"].cash_impact - 10000, abs=0.01)
    # La utilidad no cambia: clientes es balance, no resultados.
    assert more_ar["price"].ebit_impact == base["price"].ebit_impact


def test_inventory_and_suppliers_move_cost_cash() -> None:
    base = _by_lever(_inputs())
    more_inv = _by_lever(_inputs(inventory=Decimal("2771040.54")))
    assert more_inv["cogs"].cash_impact == pytest.approx(base["cogs"].cash_impact + 10000, abs=0.01)
    more_ap = _by_lever(_inputs(accounts_payable=Decimal("2232468.24")))
    assert more_ap["cogs"].cash_impact == pytest.approx(base["cogs"].cash_impact - 10000, abs=0.01)


def test_worsening_a_lever_flips_the_sign() -> None:
    result = PowerOfOneEngine().calculate(_inputs(), adjustments={"price": -1})
    (price,) = result.impacts
    assert price.cash_impact == -381869.12
    assert price.ebit_impact == -438265.13


def test_each_lever_shows_its_formula_with_the_owner_numbers() -> None:
    impacts = _by_lever(_inputs())
    price = impacts["price"]
    assert "ventas" in price.cash_formula and "clientes" in price.cash_formula
    assert "43,826,513.09" in price.cash_formula
    assert "5,639,601.55" in price.cash_formula
    assert "ventas" in price.ebit_formula
    assert "capital de trabajo" in impacts["volume"].cash_formula
    assert "inventario" in impacts["cogs"].cash_formula
    assert "proveedores" in impacts["cogs"].cash_formula
    assert "365" in impacts["ar_days"].cash_formula


def test_power_of_one_route_returns_corrected_cash_and_formulas() -> None:
    from escala_server.server import _build_router  # pyright: ignore[reportPrivateUsage]

    router = _build_router()
    fn, params = router.dispatch("POST", "/api/cash/power-of-one")
    assert fn is not None
    inputs = _inputs()
    payload = {"financials": inputs.to_dict()}
    response = fn(payload=payload, **params)
    data = response["data"]
    assert data["combined_cash_impact"] == 1143864.91
    price = next(i for i in data["impacts"] if i["lever"] == "price")
    assert price["cash_impact"] == 381869.12
    assert "clientes" in price["cash_formula"]
    assert data["cash_basis"] == "antes de ISR"


def test_dashboard_labels_cash_before_income_tax() -> None:
    html = DASHBOARD.read_text(encoding="utf-8")
    assert "antes de ISR" in html
