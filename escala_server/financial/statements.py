"""Traceable statement reconstruction for E38 S38.2."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .profiling import (
    FinancialWorkbookProfile,
    MappingQuestion,
    MappingCandidate,
    MappingTarget,
    RawCell,
)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


Freshness = Literal["fresh", "stale", "unknown"]
Confidence = Literal["high", "medium", "low"]
StatementStatus = Literal["ready", "partial", "not_derivable"]
StatementsStatus = Literal["ready", "partial", "blocked"]


class Provenance(_StrictModel):
    source_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    relative_path: str = Field(min_length=1, max_length=512)
    sheet: str = Field(min_length=1, max_length=120)
    cell_range: str = Field(min_length=1, max_length=240)
    period: str = Field(min_length=1, max_length=40)
    currency: str = Field(min_length=1, max_length=12)
    unit: str = Field(min_length=1, max_length=40)
    transformation: str = Field(min_length=1, max_length=240)


class FinancialFigure(_StrictModel):
    account: str = Field(min_length=1, max_length=80)
    period: str = Field(min_length=1, max_length=40)
    value: Decimal
    currency: str = Field(min_length=1, max_length=12)
    unit: str = Field(min_length=1, max_length=40)
    confidence: Confidence
    freshness: Freshness
    provenance: Provenance


class StatementView(_StrictModel):
    name: Literal["pnl", "balance", "cash_flow"]
    status: StatementStatus
    figures: tuple[FinancialFigure, ...] = ()
    missing: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()


class FinancialStatements(_StrictModel):
    schema_version: Literal[1] = 1
    status: StatementsStatus
    pnl: StatementView
    balance: StatementView
    cash_flow: StatementView
    questions: tuple[MappingQuestion, ...] = ()
    findings: tuple[str, ...] = ()


_PNL_TARGETS: tuple[MappingTarget, ...] = ("revenue", "cogs", "opex", "net_profit")
_BALANCE_TARGETS: tuple[MappingTarget, ...] = (
    "cash",
    "accounts_receivable",
    "inventory",
    "accounts_payable",
)


def reconstruct_statements(
    profile: FinancialWorkbookProfile,
    *,
    as_of: date | None = None,
) -> FinancialStatements:
    """Build bounded statements, blocking unresolved or unsafe inputs."""

    effective_date = as_of or date.today()
    empty_pnl = StatementView(name="pnl", status="not_derivable", missing=_PNL_TARGETS)
    empty_balance = StatementView(
        name="balance", status="not_derivable", missing=_BALANCE_TARGETS
    )
    empty_cash = StatementView(
        name="cash_flow", status="not_derivable", missing=("net_cash_change",)
    )
    if profile.mapping_status == "unresolved":
        return FinancialStatements(
            status="blocked",
            pnl=empty_pnl,
            balance=empty_balance,
            cash_flow=empty_cash,
            questions=profile.questions,
            findings=("mapping_unresolved",),
        )

    selected = _select_candidates(profile)
    figures: dict[MappingTarget, tuple[FinancialFigure, ...]] = {
        target: _figures_for_candidate(profile, selected[target], effective_date)
        for target in selected
        if selected[target] is not None
    }
    findings = set(profile.findings)
    currencies = {
        figure.currency
        for target_figures in figures.values()
        for figure in target_figures
        if figure.currency not in {"UNKNOWN", "MIXED"}
    }
    if len(currencies) > 1 or any(
        figure.currency == "MIXED"
        for target_figures in figures.values()
        for figure in target_figures
    ):
        findings.add("currency_mismatch")
    period_sets = {
        tuple(figure.period for figure in target_figures)
        for target_figures in figures.values()
        if target_figures
    }
    if len(period_sets) > 1:
        findings.add("period_mismatch")

    pnl = _build_pnl(figures, profile, effective_date)
    balance = _build_balance(figures, profile, effective_date)
    cash_flow = _build_cash_flow(figures, profile, effective_date)
    all_views = (pnl, balance, cash_flow)
    if "currency_mismatch" in findings:
        status: StatementsStatus = "blocked"
    elif any(view.status != "ready" for view in all_views):
        status = "partial"
    else:
        status = "ready"
    return FinancialStatements(
        status=status,
        pnl=pnl,
        balance=balance,
        cash_flow=cash_flow,
        findings=tuple(sorted(findings)),
    )


def _select_candidates(
    profile: FinancialWorkbookProfile,
) -> dict[MappingTarget, MappingCandidate | None]:
    confirmed = {
        answer.target: answer.candidate_id for answer in profile.confirmed_mappings
    }
    grouped: dict[MappingTarget, list[MappingCandidate]] = {}
    for candidate in profile.mapping_candidates:
        grouped.setdefault(candidate.target, []).append(candidate)
    selected: dict[MappingTarget, MappingCandidate | None] = {}
    for target, candidates in grouped.items():
        owner_id = confirmed.get(target)
        if owner_id is not None:
            selected[target] = next(
                (
                    candidate
                    for candidate in candidates
                    if candidate.candidate_id == owner_id
                ),
                None,
            )
        else:
            selected[target] = sorted(
                candidates,
                key=lambda candidate: (-candidate.score, candidate.candidate_id),
            )[0]
    return selected


def _figures_for_candidate(
    profile: FinancialWorkbookProfile,
    candidate: MappingCandidate | None,
    as_of: date,
) -> tuple[FinancialFigure, ...]:
    if candidate is None:
        return ()
    raw_sheet = next(
        (sheet for sheet in profile.raw_sheets if sheet.name == candidate.sheet), None
    )
    sheet_profile = next(
        (sheet for sheet in profile.sheets if sheet.name == candidate.sheet), None
    )
    if (
        raw_sheet is None
        or sheet_profile is None
        or candidate.row_index >= len(raw_sheet.rows)
    ):
        return ()
    row = raw_sheet.rows[candidate.row_index]
    period_columns = {
        period: index
        for index, cell in enumerate(raw_sheet.rows[sheet_profile.header_row])
        if (period := _period_token(cell.value)) is not None
    }
    if not period_columns:
        period_columns = {"undated": index for index in candidate.value_columns[:1]}
    result: list[FinancialFigure] = []
    for period, column_index in period_columns.items():
        if column_index >= len(row):
            continue
        cell = row[column_index]
        if cell.formula and cell.cached_value is None:
            continue
        value = _decimal(cell.value or cell.cached_value or "")
        if value is None:
            continue
        currency = _row_currency(row, sheet_profile.currencies)
        unit = _row_unit(row, sheet_profile.units)
        freshness = _freshness(period, as_of)
        result.append(
            FinancialFigure(
                account=candidate.target,
                period=period,
                value=value,
                currency=currency,
                unit=unit,
                confidence=candidate.confidence,
                freshness=freshness,
                provenance=Provenance(
                    source_id=profile.identity.source_id,
                    relative_path=profile.identity.relative_path,
                    sheet=candidate.sheet,
                    cell_range=f"{candidate.sheet}!{cell.address}",
                    period=period,
                    currency=currency,
                    unit=unit,
                    transformation="source value",
                ),
            )
        )
    return tuple(result)


def _build_pnl(
    figures: dict[MappingTarget, tuple[FinancialFigure, ...]],
    profile: FinancialWorkbookProfile,
    as_of: date,
) -> StatementView:
    required = _figures_for_targets(figures, _PNL_TARGETS)
    missing = tuple(target for target in _PNL_TARGETS if not figures.get(target))
    periods = _common_periods(figures, _PNL_TARGETS)
    output = [
        figure
        for target in _PNL_TARGETS
        for figure in figures.get(target, ())
        if figure.period in periods
    ]
    for period in periods:
        revenue = _one(figures.get("revenue", ()), period)
        cogs = _one(figures.get("cogs", ()), period)
        opex = _one(figures.get("opex", ()), period)
        if revenue is not None and cogs is not None:
            output.append(
                _derived(
                    revenue,
                    cogs,
                    "gross_profit",
                    revenue.value - cogs.value,
                    "revenue - cogs",
                )
            )
            if opex is not None:
                output.append(
                    _derived(
                        revenue,
                        cogs,
                        "ebit",
                        revenue.value - cogs.value - opex.value,
                        "revenue - cogs - opex",
                    )
                )
    del required
    return _view("pnl", output, missing, profile, as_of)


def _build_balance(
    figures: dict[MappingTarget, tuple[FinancialFigure, ...]],
    profile: FinancialWorkbookProfile,
    as_of: date,
) -> StatementView:
    required = _figures_for_targets(figures, _BALANCE_TARGETS)
    missing = tuple(target for target in _BALANCE_TARGETS if not figures.get(target))
    periods = _common_periods(figures, _BALANCE_TARGETS)
    output = [
        figure
        for target in _BALANCE_TARGETS
        for figure in figures.get(target, ())
        if figure.period in periods
    ]
    del required
    return _view("balance", output, missing, profile, as_of)


def _build_cash_flow(
    figures: dict[MappingTarget, tuple[FinancialFigure, ...]],
    profile: FinancialWorkbookProfile,
    as_of: date,
) -> StatementView:
    components: tuple[MappingTarget, ...] = (
        "operating_cash_flow",
        "investing_cash_flow",
        "financing_cash_flow",
    )
    periods = _common_periods(figures, components)
    output = [
        figure
        for target in components
        for figure in figures.get(target, ())
        if figure.period in periods
    ]
    missing: tuple[str, ...] = ()
    for period in periods:
        operands = [_one(figures.get(target, ()), period) for target in components]
        usable = [operand for operand in operands if operand is not None]
        if len(usable) == len(components):
            derived = _derived(
                usable[0],
                usable[1],
                "net_cash_change",
                sum((operand.value for operand in usable), Decimal("0")),
                "operating + investing + financing",
            )
            output.append(
                derived.model_copy(
                    update={
                        "currency": (
                            usable[0].currency
                            if len({operand.currency for operand in usable}) == 1
                            else "MIXED"
                        ),
                        "provenance": derived.provenance.model_copy(
                            update={
                                "cell_range": " + ".join(
                                    operand.provenance.cell_range for operand in usable
                                )
                            }
                        ),
                    }
                )
            )
    if not periods:
        opening = figures.get("opening_cash", ())
        closing = figures.get("closing_cash", ())
        periods = _common_periods(figures, ("opening_cash", "closing_cash"))
        if periods:
            for period in periods:
                opening_figure = _one(opening, period)
                closing_figure = _one(closing, period)
                if opening_figure is not None and closing_figure is not None:
                    output.append(
                        _derived(
                            closing_figure,
                            opening_figure,
                            "net_cash_change",
                            closing_figure.value - opening_figure.value,
                            "closing cash - opening cash",
                        )
                    )
    if not output:
        missing = ("net_cash_change",)
    return _view("cash_flow", output, missing, profile, as_of)


def _view(
    name: Literal["pnl", "balance", "cash_flow"],
    output: list[FinancialFigure],
    missing: tuple[str, ...],
    profile: FinancialWorkbookProfile,
    as_of: date,
) -> StatementView:
    findings: set[str] = set()
    if any(figure.freshness == "stale" for figure in output):
        findings.add("stale_input")
    if any(figure.confidence == "low" for figure in output):
        findings.add("low_confidence_input")
    del profile, as_of
    if not output:
        status: StatementStatus = "not_derivable"
    elif missing:
        status = "partial"
    else:
        status = "ready"
    return StatementView(
        name=name,
        status=status,
        figures=tuple(
            sorted(output, key=lambda figure: (figure.period, figure.account))
        ),
        missing=tuple(sorted(set(missing))),
        findings=tuple(sorted(findings)),
    )


def _figures_for_targets(
    figures: dict[MappingTarget, tuple[FinancialFigure, ...]],
    targets: tuple[MappingTarget, ...],
) -> tuple[FinancialFigure, ...]:
    return tuple(figure for target in targets for figure in figures.get(target, ()))


def _common_periods(
    figures: dict[MappingTarget, tuple[FinancialFigure, ...]],
    targets: tuple[MappingTarget, ...],
) -> tuple[str, ...]:
    available = [
        {figure.period for figure in figures.get(target, ())}
        for target in targets
        if figures.get(target)
    ]
    if not available:
        return ()
    return tuple(sorted(set.intersection(*available)))


def _one(figures: tuple[FinancialFigure, ...], period: str) -> FinancialFigure | None:
    return next((figure for figure in figures if figure.period == period), None)


def _derived(
    first: FinancialFigure,
    second: FinancialFigure,
    account: str,
    value: Decimal,
    transformation: str,
) -> FinancialFigure:
    currency = first.currency if first.currency == second.currency else "MIXED"
    cell_range = f"{first.provenance.cell_range} - {second.provenance.cell_range}"
    return first.model_copy(
        update={
            "account": account,
            "value": value,
            "confidence": "low"
            if "low" in {first.confidence, second.confidence}
            else "medium"
            if "medium" in {first.confidence, second.confidence}
            else "high",
            "freshness": "stale"
            if "stale" in {first.freshness, second.freshness}
            else "unknown"
            if "unknown" in {first.freshness, second.freshness}
            else "fresh",
            "currency": currency,
            "provenance": first.provenance.model_copy(
                update={"cell_range": cell_range, "transformation": transformation}
            ),
        }
    )


def _decimal(value: str) -> Decimal | None:
    normalized = value.strip().replace(",", "").replace("$", "")
    if not normalized:
        return None
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def _row_currency(row: tuple[RawCell, ...], sheet_currencies: tuple[str, ...]) -> str:
    aliases = {"MXN", "USD", "EUR", "GBP", "CAD", "$", "€", "£"}
    row_values = [cell.value.strip().upper() for cell in row]
    matches = tuple(value for value in row_values if value in aliases)
    if len(set(matches)) > 1:
        return "MIXED"
    if matches:
        return matches[0]
    return sheet_currencies[0] if len(sheet_currencies) == 1 else "UNKNOWN"


def _row_unit(row: tuple[RawCell, ...], sheet_units: tuple[str, ...]) -> str:
    aliases = {"PESOS", "PESO", "MILES", "MILLONES", "%", "PORCENTAJE"}
    matches = tuple(
        cell.value.casefold()
        for cell in row
        if cell.value.casefold() in {alias.casefold() for alias in aliases}
    )
    if matches:
        return matches[0]
    return sheet_units[0] if len(sheet_units) == 1 else "UNKNOWN"


def _period_token(value: str) -> str | None:
    token = value.strip()
    if re.fullmatch(r"20\d{2}[-/]\d{1,2}(?:[-/]\d{1,2})?", token):
        return token.replace("/", "-")
    return None


def _freshness(period: str, as_of: date) -> Freshness:
    if not re.fullmatch(r"20\d{2}-\d{1,2}(?:-\d{1,2})?", period):
        return "unknown"
    parts = [int(part) for part in period.split("-")]
    try:
        observed = date(parts[0], parts[1], parts[2] if len(parts) == 3 else 28)
    except ValueError:
        return "unknown"
    return "stale" if (as_of - observed).days > 90 else "fresh"
