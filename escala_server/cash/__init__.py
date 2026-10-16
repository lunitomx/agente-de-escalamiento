"""Power of One — motor local de simulación de siete palancas financieras.

Los resultados son escenarios operativos, no asesoría financiera. Las entradas,
fórmulas y supuestos deben validarse con la empresa antes de tomar decisiones.

Las 7 palancas:
  1. PRICE  (precio)          → % mejora = +1% de precio
  2. VOLUME (volumen)         → % mejora = +1% de volumen
  3. COGS   (costo venta)     → % mejora = -1% de COGS
  4. OPEX   (gastos operativos) → % mejora = -1% de OPEX
  5. AR     (cuentas x cobrar) → días mejora = -1 día DSO
  6. INV    (inventario)       → días mejora = -1 día DIO
  7. AP     (cuentas x pagar)  → días mejora = +1 día DPO
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any

DAYS_PER_YEAR = 365


class LeverType(Enum):
    PRICE = "PRICE"
    VOLUME = "VOLUME"
    COGS = "COGS"
    OPEX = "OPEX"
    ACCOUNTS_RECEIVABLE = "A/R"
    INVENTORY = "INVENTORY"
    ACCOUNTS_PAYABLE = "A/P"


LEVER_META: dict[str, dict[str, Any]] = {
    "price": {
        "label": "Precio",
        "type": "pct",
        "improvement_dir": "up",  # +1% = mejora (subir precio)
        "difficulty": 3,
        "time": "2-4 semanas",
    },
    "volume": {
        "label": "Volumen",
        "type": "pct",
        "improvement_dir": "up",  # +1% = mejora (vender más)
        "difficulty": 4,
        "time": "1-3 meses",
    },
    "cogs": {
        "label": "COGS (Costo de Ventas)",
        "type": "pct",
        "improvement_dir": "down",  # -1% = mejora (reducir costo)
        "difficulty": 3,
        "time": "1-2 meses",
    },
    "opex": {
        "label": "Gastos Operativos",
        "type": "pct",
        "improvement_dir": "down",  # -1% = mejora (gastar menos)
        "difficulty": 2,
        "time": "2-6 semanas",
    },
    "ar_days": {
        "label": "Cuentas por Cobrar (DSO)",
        "type": "day",
        "improvement_dir": "down",  # -1 día = mejora (cobrar más rápido)
        "difficulty": 2,
        "time": "2-4 semanas",
    },
    "inv_days": {
        "label": "Inventario (DIO)",
        "type": "day",
        "improvement_dir": "down",  # -1 día = mejora (menos inventario)
        "difficulty": 3,
        "time": "1-3 meses",
    },
    "ap_days": {
        "label": "Cuentas por Pagar (DPO)",
        "type": "day",
        "improvement_dir": "up",  # +1 día = mejora (pagar más tarde)
        "difficulty": 2,
        "time": "2-8 semanas",
    },
}


@dataclass
class FinancialInputs:
    """Datos financieros de entrada para el cálculo de las 7 palancas."""

    net_sales: Decimal  # Ventas netas (anuales)
    cost_of_goods_sold: Decimal  # COGS (anual)
    total_opex: Decimal  # Gastos operativos (anual)
    accounts_receivable: Decimal  # Cuentas por cobrar
    inventory: Decimal  # Inventario
    accounts_payable: Decimal  # Cuentas por pagar
    net_profit: Decimal  # Utilidad neta (anual)

    @classmethod
    def from_dict(cls, data: dict) -> FinancialInputs:
        return cls(
            net_sales=Decimal(str(data.get("net_sales", 0))),
            cost_of_goods_sold=Decimal(str(data.get("cogs", 0))),
            total_opex=Decimal(str(data.get("opex", 0))),
            accounts_receivable=Decimal(str(data.get("accounts_receivable", 0))),
            inventory=Decimal(str(data.get("inventory", 0))),
            accounts_payable=Decimal(str(data.get("accounts_payable", 0))),
            net_profit=Decimal(str(data.get("net_profit", 0))),
        )

    def to_dict(self) -> dict:
        return {
            "net_sales": float(self.net_sales),
            "cogs": float(self.cost_of_goods_sold),
            "opex": float(self.total_opex),
            "accounts_receivable": float(self.accounts_receivable),
            "inventory": float(self.inventory),
            "accounts_payable": float(self.accounts_payable),
            "net_profit": float(self.net_profit),
        }


@dataclass
class LeverImpact:
    lever: str
    label: str
    improvement_pct: float  # ej: 1.0 = 1%
    improvement_days: int  # ej: 1 = 1 día (solo para type=day)
    current_value: float
    improved_value: float
    cash_impact: float  # Impacto en cash flow ($)
    ebit_impact: float  # Impacto en EBIT ($)
    direction: str  # "up" o "down"
    difficulty: int  # 1-5
    time: str
    cash_formula: str = ""  # Fórmula del flujo con los números del dueño
    ebit_formula: str = ""  # Fórmula de la utilidad con los números del dueño


@dataclass
class PowerOfOneResult:
    inputs: FinancialInputs
    impacts: list[LeverImpact]
    combined_cash_impact: float
    combined_ebit_impact: float
    metrics: dict[str, float]  # DSO, DIO, DPO, CCC, margen, etc.
    priorities: list[dict]  # Palancas ordenadas por impacto/dificultad


CENT = Decimal("0.01")


def _cents(value: Decimal) -> float:
    """Redondea a centavos (mitad hacia arriba) solo al final del cálculo."""
    return float(value.quantize(CENT, rounding=ROUND_HALF_UP))


def _money(value: Decimal) -> str:
    return f"{value:,.2f}"


@dataclass(frozen=True)
class LeverParts:
    """Los dos lados del efecto de mover una palanca, antes de ISR, sin redondear.

    Según el curso de cash que vimos (F4.1):

    - ``per_period``: lo que cambia cada periodo (más venta, menos costo o gasto).
      Es la utilidad y se repite cada periodo.
    - ``one_time``: lo que se queda (negativo) o se libera (positivo) una sola vez
      en clientes, inventario o proveedores. Es balance.

    El flujo es la suma de los dos: ``cash``.
    """

    per_period: Decimal
    one_time: Decimal
    per_period_formula: str
    one_time_formula: str
    cash_formula: str

    @property
    def cash(self) -> Decimal:
        return self.per_period + self.one_time


def lever_parts(
    lever_id: str,
    inputs: FinancialInputs,
    units: int,
    days_in_period: int = DAYS_PER_YEAR,
) -> LeverParts:
    """Efecto de mejorar una palanca `units` puntos (% o días), en sus dos lados.

    Es la única definición de las fórmulas: ``_lever_effect`` y el motor salen de aquí.
    Las palancas de días dividen entre los días del periodo de los estados
    (365 en un año; los días reales en un mes o un acumulado). Nunca ×12.
    """
    pct = Decimal(units) / Decimal("100")
    label = f"{units}%"
    days = Decimal(units)
    day_label = f"{units} día" if units == 1 else f"{units} días"
    sales = inputs.net_sales
    cogs = inputs.cost_of_goods_sold
    ar = inputs.accounts_receivable
    inv = inputs.inventory
    ap = inputs.accounts_payable
    no_profit = "0: mover días no cambia la utilidad"

    if lever_id == "price":
        return LeverParts(
            per_period=pct * sales,
            one_time=-(pct * ar),
            per_period_formula=f"{label} × ventas {_money(sales)}",
            one_time_formula=f"−{label} × clientes {_money(ar)}",
            cash_formula=f"{label} × ventas {_money(sales)} − {label} × clientes {_money(ar)}",
        )
    if lever_id == "volume":
        gross = sales - cogs
        working_capital = ar + inv - ap
        detail = (
            f"{_money(working_capital)} (clientes {_money(ar)} + inventario {_money(inv)}"
            f" − proveedores {_money(ap)})"
        )
        return LeverParts(
            per_period=pct * gross,
            one_time=-(pct * working_capital),
            per_period_formula=(
                f"{label} × utilidad bruta {_money(gross)} (ventas − costo de ventas)"
            ),
            one_time_formula=f"−{label} × capital de trabajo {detail}",
            cash_formula=(
                f"{label} × utilidad bruta {_money(gross)} − {label} × capital de trabajo "
                + detail
            ),
        )
    if lever_id == "cogs":
        stock = f"{label} × (inventario {_money(inv)} − proveedores {_money(ap)})"
        return LeverParts(
            per_period=pct * cogs,
            one_time=pct * (inv - ap),
            per_period_formula=f"{label} × costo de ventas {_money(cogs)}",
            one_time_formula=stock,
            cash_formula=f"{label} × costo de ventas {_money(cogs)} + {stock}",
        )
    if lever_id == "opex":
        opex = inputs.total_opex
        formula = f"{label} × gastos de operación {_money(opex)}"
        return LeverParts(
            per_period=pct * opex,
            one_time=Decimal("0"),
            per_period_formula=formula,
            one_time_formula="0: los gastos no se quedan en clientes, inventario ni proveedores",
            cash_formula=formula,
        )
    if lever_id == "ar_days":
        formula = f"{day_label} × ventas {_money(sales)} ÷ {days_in_period}"
        return LeverParts(
            per_period=Decimal("0"),
            one_time=days * sales / days_in_period,
            per_period_formula=no_profit,
            one_time_formula=formula,
            cash_formula=formula,
        )
    if lever_id in ("inv_days", "ap_days"):
        formula = f"{day_label} × costo de ventas {_money(cogs)} ÷ {days_in_period}"
        return LeverParts(
            per_period=Decimal("0"),
            one_time=days * cogs / days_in_period,
            per_period_formula=no_profit,
            one_time_formula=formula,
            cash_formula=formula,
        )
    raise ValueError(f"palanca desconocida: {lever_id}")


def _lever_effect(
    lever_id: str,
    inputs: FinancialInputs,
    units: int,
    days_in_period: int = DAYS_PER_YEAR,
) -> tuple[Decimal, Decimal, str, str]:
    """Efecto de mejorar una palanca `units` puntos (% o días), antes de ISR.

    Según el curso de cash que vimos (F4.1): el flujo de cada palanca es su
    efecto en utilidad menos el capital de trabajo que se lleva. Sale de
    ``lever_parts``: flujo = por periodo + una vez.

    Returns:
        (flujo, utilidad, fórmula del flujo, fórmula de la utilidad), sin redondear.
    """
    parts = lever_parts(lever_id, inputs, units, days_in_period)
    return parts.cash, parts.per_period, parts.cash_formula, parts.per_period_formula


class PowerOfOneEngine:
    """Motor de simulación del Poder del 1%.

    Calcula el impacto de mejorar 1% (o 1 día) en cada una de las 7 palancas
    financieras, tanto individual como combinado.
    """

    def __init__(self, days_in_period: int = DAYS_PER_YEAR) -> None:
        if days_in_period <= 0:
            raise ValueError("days_in_period debe ser mayor que 0")
        self.days_per_year = days_in_period

    def calculate(
        self,
        inputs: FinancialInputs,
        adjustments: dict[str, int] | None = None,
    ) -> PowerOfOneResult:
        """Calcula el impacto de las 7 palancas.

        Args:
            inputs: Datos financieros base.
            adjustments: Ajustes por palanca. Ej: {"price": 2, "cogs": -1}
                        +1 = mejora de 1% (o 1 día). -1 = empeoramiento.
                        Si es None, calcula con +1%/+1d en todas (simulación 1%).

        Returns:
            PowerOfOneResult con impactos y métricas.
        """
        if adjustments is None:
            adjustments = {k: 1 for k in LEVER_META}

        daily_sales = inputs.net_sales / self.days_per_year
        daily_cogs = inputs.cost_of_goods_sold / self.days_per_year

        # Métricas base
        dso = (
            (inputs.accounts_receivable / daily_sales)
            if daily_sales > 0
            else Decimal("0")
        )
        dio = (inputs.inventory / daily_cogs) if daily_cogs > 0 else Decimal("0")
        dpo = (inputs.accounts_payable / daily_cogs) if daily_cogs > 0 else Decimal("0")
        ccc = dso + dio - dpo
        contribution_margin = (
            (inputs.net_sales - inputs.cost_of_goods_sold) / inputs.net_sales
            if inputs.net_sales > 0
            else Decimal("0")
        )
        profit_margin = (
            inputs.net_profit / inputs.net_sales * 100
            if inputs.net_sales > 0
            else Decimal("0")
        )

        impacts: list[LeverImpact] = []
        raw_cash_total = Decimal("0")
        raw_ebit_total = Decimal("0")

        for lever_id, meta in LEVER_META.items():
            adj = adjustments.get(lever_id, 0)
            if adj == 0:
                continue

            sign = Decimal("1") if adj > 0 else Decimal("-1")  # +1 = mejora
            abs_adj = abs(adj)
            cash, ebit, cash_formula, ebit_formula = _lever_effect(
                lever_id, inputs, abs_adj, self.days_per_year
            )
            cash *= sign
            ebit *= sign
            if sign < 0:
                cash_formula = f"−({cash_formula})"
                ebit_formula = f"−({ebit_formula})" if ebit != 0 else ebit_formula
            raw_cash_total += cash
            raw_ebit_total += ebit
            pct_change = Decimal(abs_adj) / Decimal("100")

            impacts.append(
                LeverImpact(
                    lever=lever_id,
                    label=meta["label"],
                    improvement_pct=float(pct_change) if meta["type"] == "pct" else 0.0,
                    improvement_days=abs_adj if meta["type"] == "day" else 0,
                    current_value=0.0,
                    improved_value=0.0,
                    cash_impact=_cents(cash),
                    ebit_impact=_cents(ebit),
                    direction=meta["improvement_dir"],
                    difficulty=meta["difficulty"],
                    time=meta["time"],
                    cash_formula=cash_formula,
                    ebit_formula=ebit_formula,
                )
            )

        # Combinado: se suma sin redondear y se redondea una sola vez.
        total_cf = _cents(raw_cash_total)
        total_ebit = _cents(raw_ebit_total)

        # Priorizar por impacto/dificultad
        scored = sorted(
            impacts,
            key=lambda i: (i.cash_impact + i.ebit_impact) / max(i.difficulty, 1),
            reverse=True,
        )
        priorities = [
            {
                "rank": rank,
                "lever": i.lever,
                "label": i.label,
                "impact": round(i.cash_impact + i.ebit_impact, 2),
                "difficulty": i.difficulty,
                "time": i.time,
                "score": round(
                    (i.cash_impact + i.ebit_impact) / max(i.difficulty, 1), 2
                ),
            }
            for rank, i in enumerate(scored, 1)
        ]

        return PowerOfOneResult(
            inputs=inputs,
            impacts=impacts,
            combined_cash_impact=total_cf,
            combined_ebit_impact=total_ebit,
            metrics={
                "dso_days": round(float(dso), 1),
                "dio_days": round(float(dio), 1),
                "dpo_days": round(float(dpo), 1),
                "ccc_days": round(float(ccc), 1),
                "profit_margin_pct": round(float(profit_margin), 1),
                "contribution_margin_pct": round(float(contribution_margin * 100), 1),
                "daily_sales": round(float(daily_sales), 2),
                "daily_cogs": round(float(daily_cogs), 2),
            },
            priorities=priorities,
        )

    @staticmethod
    def format_currency(value: float) -> str:
        """Formatea un valor monetario."""
        if value >= 0:
            return f"+${value:,.0f}"
        return f"-${abs(value):,.0f}"
