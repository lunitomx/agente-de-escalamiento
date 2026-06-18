"""Tests para el motor Power of One (basado en Humberto Martínez Barón / Alan Miltz)."""

from __future__ import annotations

from decimal import Decimal
from escala_server.cash import (
    PowerOfOneEngine,
    FinancialInputs,
)


class TestPowerOfOneEngine:
    """Pruebas del motor de 7 palancas financieras."""

    def setup_method(self):
        self.engine = PowerOfOneEngine()
        # Datos típicos de una PyME mexicana (~$1M/mes ventas)
        self.inputs = FinancialInputs(
            net_sales=Decimal("12000000"),  # 12M anual
            cost_of_goods_sold=Decimal("7200000"),  # 60% COGS
            total_opex=Decimal("3600000"),  # 30% OPEX
            accounts_receivable=Decimal("1500000"),  # $1.5M en cuentas x cobrar
            inventory=Decimal("600000"),  # $600K inventario
            accounts_payable=Decimal("800000"),  # $800K cuentas x pagar
            net_profit=Decimal("1200000"),  # 10% margen
        )

    def test_calculate_default_1pct(self):
        """Con ajustes default (1% mejora en todo), calcula impactos."""
        result = self.engine.calculate(self.inputs)

        assert len(result.impacts) == 7, "Deben ser 7 palancas"
        assert result.combined_cash_impact > 0, "Impacto combinado debe ser positivo"

        # Price debe tener impacto positivo
        price = [i for i in result.impacts if i.lever == "price"][0]
        assert price.cash_impact > 0, "+1% precio debe aumentar cash flow"

        # COGS debe tener impacto positivo (reducir COGS = mejorar)
        cogs = [i for i in result.impacts if i.lever == "cogs"][0]
        assert cogs.cash_impact > 0, "-1% COGS debe aumentar cash flow"

    def test_metrics_calculated(self):
        """Métricas clave (DSO, DIO, DPO, CCC) se calculan correctamente."""
        result = self.engine.calculate(self.inputs)

        # DSO = AR / (ventas/365)
        expected_dso = 1500000 / (12000000 / 365)
        assert abs(result.metrics["dso_days"] - expected_dso) < 1

        # DIO = Inventory / (COGS/365)
        expected_dio = 600000 / (7200000 / 365)
        assert abs(result.metrics["dio_days"] - expected_dio) < 1

        # DPO = AP / (COGS/365)
        expected_dpo = 800000 / (7200000 / 365)
        assert abs(result.metrics["dpo_days"] - expected_dpo) < 1

        # CCC = DSO + DIO - DPO
        assert (
            abs(
                result.metrics["ccc_days"]
                - (expected_dso + expected_dio - expected_dpo)
            )
            < 1
        )

    def test_negative_adjustment(self):
        """Ajustes negativos (empeorar) deben dar impacto negativo."""
        adjustments = {"price": -1}  # Bajar precio 1%
        result = self.engine.calculate(self.inputs, adjustments=adjustments)

        price = [i for i in result.impacts if i.lever == "price"][0]
        assert price.cash_impact < 0, "Bajar precio debe reducir cash flow"

    def test_custom_adjustments(self):
        """Ajustes personalizados funcionan (ej: 2% mejora en precio)."""
        adjustments = {"price": 2, "cogs": 1}
        result = self.engine.calculate(self.inputs, adjustments=adjustments)

        price = [i for i in result.impacts if i.lever == "price"][0]
        # 2% de 12M = 240K
        assert abs(price.cash_impact - 240000) < 1000

    def test_priorities_ordered(self):
        """Las prioridades se ordenan por impacto/dificultad."""
        result = self.engine.calculate(self.inputs)

        scores = [p["score"] for p in result.priorities]
        assert scores == sorted(scores, reverse=True), (
            "Prioridades deben ir de mayor a menor score"
        )

    def test_format_currency(self):
        """Formato de moneda funciona."""
        assert "+" in PowerOfOneEngine.format_currency(1000)
        assert "-" in PowerOfOneEngine.format_currency(-500)

    def test_benchmark_retail(self):
        """Benchmarks de retail existen y tienen las claves correctas."""
        bench = PowerOfOneEngine.benchmark_by_industry("retail")
        assert "profit_margin_pct" in bench
        assert "ccc_days" in bench
        assert "dso_days" in bench

    def test_benchmark_unknown_defaults_to_services(self):
        """Industria desconocida usa services como default."""
        bench = PowerOfOneEngine.benchmark_by_industry("unknown")
        assert bench["profit_margin_pct"]["target"] == 15.0

    def test_saas_ccc_negative(self):
        """SaaS típicamente tiene CCC negativo (cobran antes de pagar)."""
        inputs = FinancialInputs(
            net_sales=Decimal("42000000"),
            cost_of_goods_sold=Decimal("8400000"),
            total_opex=Decimal("25000000"),
            accounts_receivable=Decimal("2000000"),
            inventory=Decimal("0"),
            accounts_payable=Decimal("3000000"),
            net_profit=Decimal("5000000"),
        )
        result = self.engine.calculate(inputs)
        assert result.metrics["ccc_days"] < 0, "SaaS debe tener CCC negativo"
