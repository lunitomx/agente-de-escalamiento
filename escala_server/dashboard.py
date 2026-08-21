"""Dashboard aggregation handler.

Aggregates worksheet data from SQLite into a summary suitable for the
home dashboard. Keeps the server layer thin: scoring logic lives in the
coaching engines; this module only translates stored worksheet data into
score-friendly shapes.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Ensure project root is available when this module is imported outside __main__
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from coaching.execution_habits.engine import ExecutionAssessment  # noqa: E402
from coaching.people_facchart.engine import FACChart  # noqa: E402
from coaching.strategy_opsp.engine import SECTIONS, missing_fields  # noqa: E402

from .cash import FinancialInputs, PowerOfOneEngine  # noqa: E402
from .handlers import WorksheetsHandler  # noqa: E402


class DashboardHandler:
    """Aggregate decision scores and focus for the home dashboard."""

    def __init__(self, db_path: str = ":memory:"):
        self.worksheets = WorksheetsHandler(db_path)
        self.cash_engine = PowerOfOneEngine()

    def summary(self) -> dict:
        """Return a summary with a score per decision and a focus hint."""
        strategy = self._strategy_score()
        cash = self._cash_score()
        people: dict[str, Any] | None = self._people_score()
        execution: dict[str, Any] | None = self._execution_score()

        decisions = {
            "strategy": strategy,
            "cash": cash,
            "people": people,
            "execution": execution,
        }

        return {
            "status": "ok",
            "data": {
                "decisions": decisions,
                "focus": self._focus(decisions),
                "overall": self._overall(decisions),
            },
        }

    def _strategy_score(self) -> dict:
        """Score based on OPSP worksheet completeness."""
        result = self.worksheets.get_worksheets("strategy", "opsp")
        data = result.get("data") or {}
        # The saved payload may be wrapped in a top-level "data" key by older
        # clients; normalise both shapes.
        state = data.get("data") if isinstance(data.get("data"), dict) else data
        if not state:
            return {"score": None, "status": "missing", "label": "Sin datos"}

        missing = missing_fields(state)
        filled = len(SECTIONS) - len(missing)
        score = round((filled / len(SECTIONS)) * 100)
        status = "good" if score >= 80 else "warning" if score >= 40 else "critical"
        return {
            "score": score,
            "status": status,
            "label": f"{filled}/{len(SECTIONS)} secciones",
            "missing": missing,
        }

    def _cash_score(self) -> dict:
        """Score based on Power of One worksheet completeness + health."""
        result = self.worksheets.get_worksheets("cash", "power-of-one")
        data = result.get("data") or {}
        payload = data.get("data") if isinstance(data.get("data"), dict) else data
        financials = payload.get("financials") if isinstance(payload, dict) else None

        required_fields = [
            "net_sales",
            "cogs",
            "opex",
            "accounts_receivable",
            "inventory",
            "accounts_payable",
            "net_profit",
        ]

        if not financials:
            return {"score": None, "status": "missing", "label": "Sin datos"}

        present = [f for f in required_fields if f in financials]
        completeness = len(present) / len(required_fields)

        # Health bonus: profit margin and CCC from a baseline +1%/+1d simulation
        health = 0.0
        try:
            inputs = FinancialInputs.from_dict(financials)
            if inputs.net_sales > 0:
                result = self.cash_engine.calculate(inputs)
                metrics = result.metrics
                margin = metrics.get("profit_margin_pct", 0)
                ccc = metrics.get("ccc_days", 0)
                margin_score = min(max(margin / 20, 0), 1)  # 20% margin = 1.0
                ccc_score = 1 - min(max(ccc / 90, 0), 1)  # 0 CCC = 1.0, 90 = 0.0
                health = (margin_score + ccc_score) / 2
        except Exception:
            health = 0.0

        score = round((completeness * 0.6 + health * 0.4) * 100)
        status = "good" if score >= 70 else "warning" if score >= 40 else "critical"
        return {
            "score": score,
            "status": status,
            "label": f"{len(present)}/{len(required_fields)} campos",
        }

    def _people_score(self) -> dict | None:
        """Score based on FACChart worksheet completeness and health."""
        from coaching.people_facchart.engine import score as facchart_score, validate

        result = self.worksheets.get_worksheets("people", "facchart")
        data = result.get("data") or {}
        payload = data.get("data") if isinstance(data.get("data"), dict) else data
        chart = FACChart.from_dict(payload if isinstance(payload, dict) else {})
        if not chart.functions:
            return {"score": None, "status": "missing", "label": "Sin datos"}

        score_result = facchart_score(chart)
        overall = score_result["overall"]
        status = "good" if overall >= 70 else "warning" if overall >= 40 else "critical"
        errors = validate(chart)
        return {
            "score": overall,
            "status": status,
            "label": f"{score_result['function_count']} funciones",
            "errors": errors,
        }

    def _execution_score(self) -> dict | None:
        """Score based on Execution Habits worksheet."""
        from coaching.execution_habits.engine import score as execution_habits_score, validate

        result = self.worksheets.get_worksheets("execution", "execution_habits")
        data = result.get("data") or {}
        payload = data.get("data") if isinstance(data.get("data"), dict) else data
        assessment = ExecutionAssessment.from_dict(
            payload if isinstance(payload, dict) else {}
        )
        if not any(s.score is not None for s in assessment.scores):
            return {"score": None, "status": "missing", "label": "Sin datos"}

        score_result = execution_habits_score(assessment)
        overall = round((score_result["total"] / score_result["max"]) * 100)
        status = "good" if overall >= 70 else "warning" if overall >= 40 else "critical"
        errors = validate(assessment)
        return {
            "score": overall,
            "status": status,
            "label": f"{score_result['total']}/{score_result['max']} puntos",
            "errors": errors,
        }

    def _focus(self, decisions: dict) -> dict:
        """Pick the decision that most needs attention."""
        candidates = []
        for key, value in decisions.items():
            if value is None or value.get("score") is None:
                candidates.append((key, -1))
            else:
                candidates.append((key, value["score"]))

        if not candidates:
            return {"decision": None, "message": "No hay áreas configuradas"}

        # Lowest score (or missing) is the focus; missing sorts below zero.
        focus_key, focus_score = min(candidates, key=lambda x: x[1])
        labels = {
            "strategy": "Estrategia",
            "cash": "Cash",
            "people": "People",
            "execution": "Execution",
        }
        if focus_score < 0:
            message = f"{labels.get(focus_key, focus_key)} no tiene datos. Empieza por su worksheet."
        else:
            message = (
                f"{labels.get(focus_key, focus_key)} tiene el score más bajo ({focus_score}). "
                "Revisa sus próximos pasos."
            )
        return {"decision": focus_key, "score": focus_score, "message": message}

    def _overall(self, decisions: dict) -> dict:
        """Overall score only over decisions that have data."""
        scores = [
            v["score"]
            for v in decisions.values()
            if v is not None and v.get("score") is not None
        ]
        if not scores:
            return {"score": None, "status": "missing", "label": "Sin datos"}
        avg = round(sum(scores) / len(scores))
        status = "good" if avg >= 70 else "warning" if avg >= 40 else "critical"
        return {"score": avg, "status": status, "label": f"{avg}/100"}
