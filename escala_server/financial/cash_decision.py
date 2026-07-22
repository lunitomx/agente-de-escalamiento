"""Validated CCC and Power-of-One coaching for E38 S38.3."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from escala_server.cash import FinancialInputs, LEVER_META, PowerOfOneEngine

from .statements import FinancialFigure, FinancialStatements, Provenance


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


DecisionStatus = Literal["ready", "blocked"]


class CashScenarioRequest(_StrictModel):
    scenario_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,48}$")
    adjustments: dict[str, int] = Field(default_factory=dict)


class CashAssumptions(_StrictModel):
    days_per_year: int = Field(default=365, ge=1, le=366)
    annualization_factor: int = Field(default=1, ge=1, le=24)
    period: str = Field(min_length=1, max_length=40)
    currency: str = Field(min_length=1, max_length=12)
    unit: str = Field(min_length=1, max_length=40)
    confidence: Literal["high", "medium", "low"]
    freshness: Literal["fresh", "stale", "unknown"]
    source_ids: tuple[str, ...] = ()
    scenarios_share_baseline: Literal[True] = True


class ValidatedCashInputs(_StrictModel):
    period: str
    currency: str
    unit: str
    net_sales: Decimal
    cost_of_goods_sold: Decimal
    total_opex: Decimal
    accounts_receivable: Decimal
    inventory: Decimal
    accounts_payable: Decimal
    net_profit: Decimal
    provenance: tuple[Provenance, ...] = ()


class CashImpact(_StrictModel):
    lever: str
    cash_impact: float
    ebit_impact: float
    direction: str


class CashScenarioResult(_StrictModel):
    scenario_id: str
    adjustments: dict[str, int]
    metrics: dict[str, float]
    combined_cash_impact: float
    combined_ebit_impact: float
    delta_vs_baseline: dict[str, float]
    impacts: tuple[CashImpact, ...] = ()


class CashDecision(_StrictModel):
    schema_version: Literal[1] = 1
    status: DecisionStatus
    assumptions: CashAssumptions | None = None
    validated_inputs: ValidatedCashInputs | None = None
    baseline: CashScenarioResult | None = None
    scenarios: tuple[CashScenarioResult, ...] = ()
    recommendations: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()
    questions: tuple[object, ...] = ()


_REQUIRED_ACCOUNTS = (
    "revenue",
    "cogs",
    "opex",
    "net_profit",
    "accounts_receivable",
    "inventory",
    "accounts_payable",
)
_PNL_ACCOUNTS = {"revenue", "cogs", "opex", "net_profit"}


def build_cash_decision(
    statements: FinancialStatements,
    *,
    as_of: date | None = None,
    scenarios: tuple[CashScenarioRequest, ...] = (),
) -> CashDecision:
    """Validate statement evidence before invoking the V1 cash engine."""

    findings = set(statements.findings)
    figures = _required_figures(statements)
    if statements.status != "ready":
        findings.add("statements_not_ready")
    for view in (statements.pnl, statements.balance):
        findings.update(view.findings)
    unknown_adjustments = {
        key
        for request in scenarios
        for key in request.adjustments
        if key not in LEVER_META
    }
    if unknown_adjustments:
        findings.add("scenario_adjustment_unknown")
    if not all(account in figures for account in _REQUIRED_ACCOUNTS):
        findings.add("cash_input_missing")
    if any(
        figure.freshness != "fresh" for values in figures.values() for figure in values
    ):
        findings.add("stale_input")
    if any(
        figure.confidence != "high" for values in figures.values() for figure in values
    ):
        findings.add("low_confidence_input")
    common_periods = _common_periods(figures)
    if not common_periods:
        findings.add("period_mismatch")
    period = max(common_periods) if common_periods else "unknown"
    selected = {
        account: next((figure for figure in values if figure.period == period), None)
        for account, values in figures.items()
    }
    if any(figure is None for figure in selected.values()):
        findings.add("cash_input_missing")
    currencies = {figure.currency for figure in selected.values() if figure is not None}
    units = {figure.unit for figure in selected.values() if figure is not None}
    if len(currencies) != 1 or "MIXED" in currencies:
        findings.add("currency_mismatch")
    if len(units) != 1 or "UNKNOWN" in units:
        findings.add("unit_mismatch")
    if any(
        figure is not None
        and account in {"accounts_receivable", "inventory", "accounts_payable"}
        and figure.value < 0
        for account, figure in selected.items()
    ):
        findings.add("invalid_working_capital")
    if any(
        figure is not None
        and account in {"revenue", "cogs", "opex"}
        and figure.value < 0
        for account, figure in selected.items()
    ):
        findings.add("invalid_profit_input")

    if findings:
        return CashDecision(
            status="blocked",
            findings=tuple(sorted(findings)),
            questions=statements.questions,
        )

    assert all(figure is not None for figure in selected.values())
    annualization = _annualization_factor(period)
    input_values = _build_inputs(selected, annualization)
    freshness = "fresh"
    confidence = "high"
    assumptions = CashAssumptions(
        annualization_factor=annualization,
        period=period,
        currency=input_values.currency,
        unit=input_values.unit,
        confidence=confidence,
        freshness=freshness,
        source_ids=tuple(
            sorted({provenance.source_id for provenance in input_values.provenance})
        ),
    )
    engine = PowerOfOneEngine()
    baseline = _scenario_result(
        "baseline",
        {key: 0 for key in LEVER_META},
        engine,
        input_values,
        baseline_metrics=None,
    )
    scenario_results = tuple(
        _scenario_result(
            request.scenario_id,
            request.adjustments,
            engine,
            input_values,
            baseline_metrics=baseline.metrics,
        )
        for request in scenarios
    )
    recommendations = tuple(
        f"{scenario.scenario_id}: escenario comparable con impacto cash positivo"
        for scenario in sorted(
            scenario_results,
            key=lambda scenario: scenario.combined_cash_impact,
            reverse=True,
        )
        if scenario.combined_cash_impact > 0
    )
    return CashDecision(
        status="ready",
        assumptions=assumptions,
        validated_inputs=input_values,
        baseline=baseline,
        scenarios=scenario_results,
        recommendations=recommendations,
    )


def render_cash_decision_receipt_json(decision: CashDecision) -> str:
    """Render safe metadata without values, metrics or machine paths."""

    payload = {
        "schema_version": decision.schema_version,
        "status": decision.status,
        "findings": decision.findings,
        "scenario_ids": tuple(scenario.scenario_id for scenario in decision.scenarios),
        "assumptions": (
            {
                "days_per_year": decision.assumptions.days_per_year,
                "annualization_factor": decision.assumptions.annualization_factor,
                "period": decision.assumptions.period,
                "currency": decision.assumptions.currency,
                "unit": decision.assumptions.unit,
                "confidence": decision.assumptions.confidence,
                "freshness": decision.assumptions.freshness,
            }
            if decision.assumptions is not None
            else None
        ),
        "recommendation_count": len(decision.recommendations),
    }
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def render_cash_decision_receipt_markdown(decision: CashDecision) -> str:
    """Render safe human-readable decision metadata."""

    lines = [
        "# Cash Decision Receipt",
        "",
        f"- status: {decision.status}",
        f"- scenarios: {', '.join(scenario.scenario_id for scenario in decision.scenarios) or 'none'}",
        f"- findings: {', '.join(decision.findings) or 'none'}",
        f"- recommendations: {len(decision.recommendations)}",
    ]
    if decision.assumptions is not None:
        lines.extend(
            [
                f"- period: {decision.assumptions.period}",
                f"- annualization_factor: {decision.assumptions.annualization_factor}",
                f"- confidence: {decision.assumptions.confidence}",
                f"- freshness: {decision.assumptions.freshness}",
            ]
        )
    return "\n".join(lines) + "\n"


def _required_figures(
    statements: FinancialStatements,
) -> dict[str, tuple[FinancialFigure, ...]]:
    result: dict[str, list[FinancialFigure]] = {}
    for figure in (*statements.pnl.figures, *statements.balance.figures):
        if figure.account in _REQUIRED_ACCOUNTS:
            result.setdefault(figure.account, []).append(figure)
    return {account: tuple(values) for account, values in result.items()}


def _common_periods(figures: dict[str, tuple[FinancialFigure, ...]]) -> tuple[str, ...]:
    available = [
        {figure.period for figure in values} for values in figures.values() if values
    ]
    if not available:
        return ()
    return tuple(sorted(set.intersection(*available)))


def _annualization_factor(period: str) -> int:
    return 12 if re.fullmatch(r"20\d{2}-\d{1,2}", period) else 1


def _build_inputs(
    selected: dict[str, FinancialFigure | None],
    annualization_factor: int,
) -> ValidatedCashInputs:
    figures = {
        account: figure for account, figure in selected.items() if figure is not None
    }
    assert len(figures) == len(selected)
    provenance = tuple(figure.provenance for figure in figures.values())
    currency = next(iter({figure.currency for figure in figures.values()}))
    unit = next(iter({figure.unit for figure in figures.values()}))
    return ValidatedCashInputs(
        period=next(iter({figure.period for figure in figures.values()})),
        currency=currency,
        unit=unit,
        net_sales=figures["revenue"].value * annualization_factor,
        cost_of_goods_sold=figures["cogs"].value * annualization_factor,
        total_opex=figures["opex"].value * annualization_factor,
        accounts_receivable=figures["accounts_receivable"].value,
        inventory=figures["inventory"].value,
        accounts_payable=figures["accounts_payable"].value,
        net_profit=figures["net_profit"].value * annualization_factor,
        provenance=provenance,
    )


def _scenario_result(
    scenario_id: str,
    adjustments: dict[str, int],
    engine: PowerOfOneEngine,
    inputs: ValidatedCashInputs,
    baseline_metrics: dict[str, float] | None,
) -> CashScenarioResult:
    financial_inputs = FinancialInputs(
        net_sales=inputs.net_sales,
        cost_of_goods_sold=inputs.cost_of_goods_sold,
        total_opex=inputs.total_opex,
        accounts_receivable=inputs.accounts_receivable,
        inventory=inputs.inventory,
        accounts_payable=inputs.accounts_payable,
        net_profit=inputs.net_profit,
    )
    result = engine.calculate(financial_inputs, adjustments=adjustments)
    impacts = tuple(
        CashImpact(
            lever=impact.lever,
            cash_impact=impact.cash_impact,
            ebit_impact=impact.ebit_impact,
            direction=impact.direction,
        )
        for impact in result.impacts
    )
    baseline = baseline_metrics or result.metrics
    delta = {
        key: result.metrics[key] - baseline.get(key, result.metrics[key])
        for key in result.metrics
    }
    delta["combined_cash_impact"] = result.combined_cash_impact
    delta["combined_ebit_impact"] = result.combined_ebit_impact
    return CashScenarioResult(
        scenario_id=scenario_id,
        adjustments=dict(sorted(adjustments.items())),
        metrics=dict(sorted(result.metrics.items())),
        combined_cash_impact=result.combined_cash_impact,
        combined_ebit_impact=result.combined_ebit_impact,
        delta_vs_baseline=dict(sorted(delta.items())),
        impacts=impacts,
    )
