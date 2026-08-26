"""Honest, source-aware executive view over one project's local business data."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .project_memory import ProjectMemoryRuntime
from .project_memory_migration import ProjectMemoryMigrator
from .schema import init_db

DECISIONS = {
    "people": {
        "label": "People",
        "question": "¿Tenemos a las personas correctas haciendo lo correcto?",
        "route": "/dashboards/people/team-growth.html",
    },
    "strategy": {
        "label": "Strategy",
        "question": "¿Nuestra estrategia es clara y diferente?",
        "route": "/dashboards/strategy/bmc-board.html",
    },
    "execution": {
        "label": "Execution",
        "question": "¿Convertimos prioridades en resultados?",
        "route": "/dashboards/execution/priorities.html",
    },
    "cash": {
        "label": "Cash",
        "question": "¿El crecimiento genera suficiente efectivo?",
        "route": "/dashboards/cash/cash-board.html",
    },
}

PROFILE_PATH = ".scaleup/agent/memory/company-profile.yaml"
PLAN_PATH = "work/strategy/opsp.md"
PULSE_PATH = ".scaleup/my-company/pulse-history.yaml"


class BusinessPulseHandler:
    """Build a deterministic executive payload without inventing company data."""

    def __init__(self, db_path: str, project_root: str | Path | None = None) -> None:
        self.db_path = db_path
        self.project_root = (
            Path(project_root).expanduser().resolve() if project_root else None
        )
        connection = init_db(db_path)
        connection.close()

    def get(self, demo: str = "false") -> dict[str, Any]:
        if str(demo).casefold() in {"1", "true", "yes", "si", "sí"}:
            return {"status": "ok", "data": self._demo()}
        refresh = self._refresh_sources()
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            payload = self._real_payload(connection)
        if refresh:
            payload["refresh"] = refresh
        return {"status": "ok", "data": payload}

    def _refresh_sources(self) -> dict[str, Any] | None:
        """Re-import changed allowlisted files only when this is their own DB."""
        if self.project_root is None or self.db_path.startswith("file:"):
            return None
        runtime = ProjectMemoryRuntime(self.project_root)
        try:
            if Path(self.db_path).resolve() != runtime.db_path.resolve():
                return None
            result = ProjectMemoryMigrator(self.project_root).migrate()
        except (OSError, ValueError):
            return {"ready": False}
        return {
            "ready": result.ready,
            "changed": sum(result.imported.values()),
            "errors": len(result.errors),
        }

    def _real_payload(self, db: sqlite3.Connection) -> dict[str, Any]:
        profile, profile_source = self._profile(db)
        plan, plan_source = self._worksheet(db, "strategy", "opsp")
        pulse, pulse_source = self._worksheet(db, "diagnosis", "pulse-history")
        power, power_source = self._worksheet(db, "cash", "power-of-one")

        scores = profile.get("scores") if isinstance(profile.get("scores"), dict) else {}
        focus = profile.get("focus") if isinstance(profile.get("focus"), dict) else {}
        latest_pulse = self._latest_pulse(pulse)
        decisions = self._decisions(scores, latest_pulse, profile_source, pulse_source)
        priority = self._priority(focus, decisions, profile_source)
        plan_view = self._plan(plan, plan_source)
        company = self._company(profile, plan, profile_source, plan_source)
        timeline = self._timeline(db, power_source)
        source_dates = [
            source.get("observed_at")
            for source in (profile_source, plan_source, pulse_source, power_source)
            if source and source.get("observed_at")
        ]
        has_data = any(
            [company.get("name"), any(d["score"] is not None for d in decisions), plan, power]
        )
        complete_sections = sum(
            [
                any(d["score"] is not None for d in decisions),
                bool(plan),
                bool(power),
            ]
        )
        return {
            "mode": "company",
            "synthetic": False,
            "state": "empty" if not has_data else "ready" if complete_sections == 3 else "partial",
            "company": company,
            "as_of": max(source_dates) if source_dates else None,
            "decisions": decisions,
            "priority": priority,
            "plan": plan_view,
            "power_of_one": {
                "available": bool(power and isinstance(power.get("variables"), dict)),
                "route": "/dashboards/cash/power-of-one.html",
                "source": power_source,
            },
            "timeline": timeline,
            "actions": self._actions(decisions, plan_view, power),
        }

    @staticmethod
    def _profile(db: sqlite3.Connection) -> tuple[dict[str, Any], dict[str, Any] | None]:
        row = db.execute(
            "SELECT metadata, updated_at FROM companies ORDER BY updated_at DESC, id DESC LIMIT 1"
        ).fetchone()
        source = BusinessPulseHandler._latest_source(db, "company-profile", PROFILE_PATH)
        if row is None:
            return {}, source
        try:
            payload = json.loads(row["metadata"])
        except (TypeError, json.JSONDecodeError):
            return {}, source
        return (payload if isinstance(payload, dict) else {}), source

    @staticmethod
    def _worksheet(
        db: sqlite3.Connection, category: str, tool: str
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        row = db.execute(
            """SELECT data, version, created_at, updated_at FROM worksheets
               WHERE category=? AND tool=? ORDER BY version DESC LIMIT 1""",
            (category, tool),
        ).fetchone()
        if row is None:
            return {}, None
        try:
            raw = json.loads(row["data"])
        except (TypeError, json.JSONDecodeError):
            return {}, None
        if not isinstance(raw, dict):
            return {}, None
        payload = raw
        source = {
            "label": "Dato guardado localmente",
            "path": f"{category}/{tool}",
            "observed_at": row["updated_at"] or row["created_at"],
            "type": "local_worksheet",
        }
        if all(raw.get(key) for key in ("source_kind", "relative_path", "content_sha256")):
            nested = raw.get("payload")
            payload = nested if isinstance(nested, dict) else {}
            source = {
                "label": BusinessPulseHandler._source_label(str(raw["source_kind"])),
                "path": str(raw["relative_path"]),
                "observed_at": row["created_at"],
                "type": str(raw["source_kind"]),
            }
        if category == "strategy" and tool == "opsp":
            frontmatter = payload.get("frontmatter") if isinstance(payload, dict) else None
            if isinstance(frontmatter, dict) and isinstance(frontmatter.get("data"), dict):
                payload = dict(frontmatter["data"])
                payload.setdefault("status", frontmatter.get("status"))
                source["observed_at"] = frontmatter.get("updated_at") or source["observed_at"]
        return payload, source

    @staticmethod
    def _latest_source(
        db: sqlite3.Connection, source_kind: str, path: str
    ) -> dict[str, Any] | None:
        row = db.execute(
            """SELECT relative_path, applied_at FROM migration_applications
               WHERE source_kind=? AND relative_path=? ORDER BY id DESC LIMIT 1""",
            (source_kind, path),
        ).fetchone()
        if row is None:
            return None
        return {
            "label": BusinessPulseHandler._source_label(source_kind),
            "path": row["relative_path"],
            "observed_at": row["applied_at"],
            "type": source_kind,
        }

    @staticmethod
    def _source_label(source_kind: str) -> str:
        return {
            "company-profile": "Diagnóstico confirmado",
            "opsp": "Plan en una hoja",
            "pulse-history": "Revisión de pulso",
            "worksheet": "Herramienta guardada",
            "legacy-plan": "Plan histórico",
        }.get(source_kind, "Fuente local")

    @staticmethod
    def _company(
        profile: dict[str, Any],
        plan: dict[str, Any],
        profile_source: dict[str, Any] | None,
        plan_source: dict[str, Any] | None,
    ) -> dict[str, Any]:
        company = profile.get("company") if isinstance(profile.get("company"), dict) else {}
        name = company.get("name") or plan.get("company_name")
        industry = company.get("industry")
        return {
            "name": str(name).strip() if name else None,
            "industry": str(industry).strip() if industry else None,
            "source": profile_source if company.get("name") else plan_source if name else None,
        }

    @staticmethod
    def _latest_pulse(payload: dict[str, Any]) -> dict[str, Any]:
        pulses = payload.get("pulses") if isinstance(payload, dict) else None
        if not isinstance(pulses, list):
            return {}
        return next((item for item in reversed(pulses) if isinstance(item, dict)), {})

    @staticmethod
    def _decisions(
        scores: dict[str, Any],
        pulse: dict[str, Any],
        profile_source: dict[str, Any] | None,
        pulse_source: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        trends = pulse.get("trends") if isinstance(pulse.get("trends"), dict) else {}
        output = []
        for key, config in DECISIONS.items():
            raw_score = scores.get(key)
            score = raw_score if isinstance(raw_score, (int, float)) and 1 <= raw_score <= 5 else None
            trend = trends.get(key) if trends.get(key) in {"improving", "stalling", "regressing"} else None
            output.append(
                {
                    "id": key,
                    **config,
                    "score": score,
                    "trend": trend,
                    "state": "available" if score is not None else "pending",
                    "source": profile_source if score is not None else None,
                    "trend_source": pulse_source if trend else None,
                    "cta": "Cuéntame cómo funciona hoy esta área" if score is None else "Abrir herramientas",
                }
            )
        return output

    @staticmethod
    def _priority(
        focus: dict[str, Any],
        decisions: list[dict[str, Any]],
        source: dict[str, Any] | None,
    ) -> dict[str, Any]:
        explicit = focus.get("current_decision")
        if explicit in DECISIONS:
            return {
                "decision": explicit,
                "label": DECISIONS[explicit]["label"],
                "reason": "Foco confirmado en el diagnóstico",
                "derived": False,
                "source": source,
            }
        scored = [item for item in decisions if item["score"] is not None]
        if scored:
            lowest = min(scored, key=lambda item: (item["score"], list(DECISIONS).index(item["id"])))
            return {
                "decision": lowest["id"],
                "label": lowest["label"],
                "reason": "Es la calificación más baja del diagnóstico disponible",
                "derived": True,
                "source": source,
            }
        return {"decision": None, "label": None, "reason": "Completa el diagnóstico para definir el foco", "derived": False, "source": None}

    @staticmethod
    def _plan(plan: dict[str, Any], source: dict[str, Any] | None) -> dict[str, Any]:
        fields = {
            "purpose": bool(plan.get("purpose")),
            "bhag": bool(plan.get("bhag")),
            "market": bool((plan.get("sandbox") or {}).get("market")) if isinstance(plan.get("sandbox"), dict) else False,
            "brand_promise": bool((plan.get("brand_promise") or {}).get("promise")) if isinstance(plan.get("brand_promise"), dict) else False,
            "critical_number": bool(plan.get("critical_number")),
            "annual_priorities": bool(plan.get("annual_priorities")),
            "quarterly_priorities": bool(plan.get("quarterly_priorities")),
        }
        complete = sum(fields.values())
        total = len(fields)
        priorities = [
            {key: item.get(key) for key in ("priority", "owner", "kpi", "status")}
            for item in plan.get("quarterly_priorities", [])
            if isinstance(item, dict) and item.get("priority")
        ] if isinstance(plan.get("quarterly_priorities"), list) else []
        return {
            "available": bool(plan),
            "status": plan.get("status") if plan else None,
            "quarter": plan.get("quarter") if plan else None,
            "critical_number": plan.get("critical_number") if plan else None,
            "priorities": priorities,
            "completion": {"complete": complete, "total": total, "percent": round(complete * 100 / total)},
            "missing": [key for key, present in fields.items() if not present],
            "source": source,
            "route": "/dashboards/execution/vision-summary.html",
        }

    @staticmethod
    def _timeline(db: sqlite3.Connection, power_source: dict[str, Any] | None) -> list[dict[str, Any]]:
        rows = db.execute(
            """SELECT source_kind, relative_path, applied_at FROM migration_applications
               ORDER BY id DESC LIMIT 8"""
        ).fetchall()
        items = [
            {
                "label": BusinessPulseHandler._source_label(row["source_kind"]),
                "source": row["relative_path"],
                "observed_at": row["applied_at"],
                "type": row["source_kind"],
            }
            for row in rows
        ]
        if power_source and power_source.get("type") == "local_worksheet":
            items.append(
                {
                    "label": "Escenario Power of One guardado",
                    "source": power_source["path"],
                    "observed_at": power_source["observed_at"],
                    "type": "local_worksheet",
                }
            )
        return sorted(items, key=lambda item: item["observed_at"] or "", reverse=True)[:8]

    @staticmethod
    def _actions(
        decisions: list[dict[str, Any]], plan: dict[str, Any], power: dict[str, Any]
    ) -> list[dict[str, str]]:
        actions = []
        if not any(item["score"] is not None for item in decisions):
            actions.append({"label": "Iniciar diagnóstico", "say": "Quiero entender cómo está mi empresa"})
        if not plan["available"]:
            actions.append({"label": "Crear plan en una hoja", "say": "Ayúdame a crear mi plan en una hoja"})
        if not (power and isinstance(power.get("variables"), dict)):
            actions.append({"label": "Modelar efectivo", "route": "/dashboards/cash/power-of-one.html"})
        actions.append({"label": "Ver Accountability", "route": "/dashboards/execution/accountability.html"})
        return actions

    @staticmethod
    def _demo() -> dict[str, Any]:
        observed = "2026-08-26"
        source = {"label": "Demo sintética", "path": None, "observed_at": observed, "type": "synthetic_demo"}
        scores = {"people": 4, "strategy": 3, "execution": 2, "cash": 3}
        decisions = BusinessPulseHandler._decisions(scores, {"trends": {"people": "improving", "strategy": "stalling", "execution": "regressing", "cash": "improving"}}, source, source)
        return {
            "mode": "synthetic_demo",
            "synthetic": True,
            "state": "ready",
            "company": {"name": "Empresa Ejemplo", "industry": "Demo", "source": source},
            "as_of": observed,
            "decisions": decisions,
            "priority": {"decision": "execution", "label": "Execution", "reason": "Ejemplo: calificación más baja", "derived": True, "source": source},
            "plan": {"available": True, "status": "completed", "quarter": "Trimestre de ejemplo", "critical_number": "Ejemplo: 90% de entregas a tiempo", "priorities": [{"priority": "Reducir retrasos", "owner": "Responsable ejemplo", "kpi": "90% puntual", "status": "En curso"}], "completion": {"complete": 7, "total": 7, "percent": 100}, "missing": [], "source": source, "route": "/dashboards/execution/vision-summary.html"},
            "power_of_one": {"available": True, "route": "/dashboards/cash/power-of-one.html", "source": source},
            "timeline": [{"label": "Diagnóstico de demostración", "source": "Demo sintética", "observed_at": observed, "type": "synthetic_demo"}],
            "actions": [],
        }
