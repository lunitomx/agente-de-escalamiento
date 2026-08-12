"""Render OPSP state into the templates/opsp.md structure.

Every field is either the value the user gave or the explicit MISSING
marker — never a guess, matching escala-strategy-opsp/SKILL.md Step 9
("no afirmar que el OPSP se guardó" / never invent a value).
"""

from __future__ import annotations

from typing import Any

from .engine import MISSING


def _val(value: Any) -> str:
    if value is None or value == "":
        return MISSING
    return str(value)


def _core_values_rows(core_values: list[str] | None) -> str:
    values = core_values or []
    rows = []
    for i in range(1, 6):
        value = values[i - 1] if i <= len(values) else None
        rows.append(f"| {i} | {_val(value)} | |")
    return "\n".join(rows)


def _priority_rows(priorities: list[dict[str, Any]] | None, with_status: bool) -> str:
    priorities = priorities or []
    rows = []
    for i in range(1, 6):
        p = priorities[i - 1] if i <= len(priorities) else {}
        if with_status:
            rows.append(
                f"| {i} | {_val(p.get('priority'))} | {_val(p.get('owner'))} | "
                f"{_val(p.get('kpi'))} | {_val(p.get('status'))} |"
            )
        else:
            rows.append(
                f"| {i} | {_val(p.get('priority'))} | {_val(p.get('owner'))} | "
                f"{_val(p.get('kpi'))} |"
            )
    return "\n".join(rows)


def render_markdown(
    state: dict[str, Any], company_name: str = "", date: str = ""
) -> str:
    """Render `state` using the same structure as templates/opsp.md."""
    bhag = state.get("bhag") or {}
    sandbox = state.get("sandbox") or {}
    brand_promise = state.get("brand_promise") or {}
    profit_per_x = state.get("profit_per_x") or {}
    annual_goals = state.get("annual_goals") or {}
    quarterly_plan = state.get("quarterly_plan") or {}
    theme = quarterly_plan.get("theme") or {}

    return f"""# One-Page Strategic Plan (OPSP)

> Empresa: {_val(company_name)} | Fecha: {_val(date)}

---

## CORE VALUES / Valores Fundamentales

| # | Core Value | Descripción |
|---|-----------|-------------|
{_core_values_rows(state.get("core_values"))}

## PURPOSE / Propósito

> {_val(state.get("purpose"))}

## BHAG (Big Hairy Audacious Goal) — Meta 10-25 años

> {_val(bhag.get("statement"))}

**Fecha objetivo:** {_val(bhag.get("target_date"))}
**Progreso actual:** {_val(bhag.get("progress"))}

---

## SANDBOX / Arena Competitiva (3-5 años)

| Elemento | Definición |
|----------|-----------|
| Revenue target | {_val(sandbox.get("revenue_target"))} |
| Profit target | {_val(sandbox.get("profit_target"))} |
| Market/Geography | {_val(sandbox.get("market_geography"))} |
| Customer segment | {_val(sandbox.get("customer_segment"))} |
| Product/Service focus | {_val(sandbox.get("product_focus"))} |

## BRAND PROMISE / Promesa de Marca

| Elemento | Definición |
|----------|-----------|
| Brand Promise | {_val(brand_promise.get("promise"))} |
| KPI que la mide | {_val(brand_promise.get("kpi"))} |
| Guarantee (si aplica) | {_val(brand_promise.get("guarantee"))} |
| Catalytic Mechanism | {_val(brand_promise.get("catalytic_mechanism"))} |

## PROFIT PER X / Motor Económico

> Profit per {_val(profit_per_x.get("x"))} = ${_val(profit_per_x.get("amount"))}

---

## QUARTERLY PLAN / Plan Trimestral

**Trimestre:** {_val(quarterly_plan.get("quarter"))}
**Critical Number:** {_val(quarterly_plan.get("critical_number"))}

### Prioridades de la Empresa (Top 5)

| # | Prioridad | Owner | KPI | Status |
|---|----------|-------|-----|--------|
{_priority_rows(quarterly_plan.get("priorities"), with_status=True)}

### Theme / Tema del Trimestre

| Elemento | Definición |
|----------|-----------|
| Theme name | {_val(theme.get("name"))} |
| Celebration/Reward | {_val(theme.get("celebration"))} |
| Deadline | {_val(theme.get("deadline"))} |
| Scoreboard | {_val(theme.get("scoreboard"))} |

---

## ANNUAL GOALS / Metas Anuales

**Año:** {_val(annual_goals.get("year"))}
**Revenue target:** {_val(annual_goals.get("revenue_target"))}
**Profit target:** {_val(annual_goals.get("profit_target"))}

### Prioridades Anuales (Top 5)

| # | Prioridad | Owner | KPI |
|---|----------|-------|-----|
{_priority_rows(annual_goals.get("priorities"), with_status=False)}
"""
