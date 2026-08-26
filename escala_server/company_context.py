"""Read-only, source-labelled executive context for ScaleUp consumers."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .board.contracts import CompanyFact
from .evidence import DECISIONS, EvidenceStore
from .human_context import HumanContextStore
from .project_memory import ProjectMemoryRuntime


@dataclass(frozen=True)
class ContextItem:
    id: str
    category: str
    text: str
    source: str
    observed_at: str | None
    status: str
    kind: str = "fact"


@dataclass(frozen=True)
class CompanyContext:
    items: tuple[ContextItem, ...]
    gaps: tuple[str, ...]
    human_items: tuple[ContextItem, ...] = ()

    def for_board(self, category: str) -> tuple[CompanyFact, ...]:
        selected = [
            item
            for item in self.items + self.human_items
            if item.category in {category, "all"} and item.status == "confirmed"
        ]
        return tuple(
            CompanyFact(
                item.id,
                f"Dato confirmado ({item.source}, {item.observed_at or 'sin fecha'}): {item.text}",
                category,
            )
            for item in selected[:6]
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [item.__dict__ for item in self.items],
            "gaps": list(self.gaps),
        }


class CompanyContextReader:
    """Compose only confirmed business data; it performs no writes."""

    def __init__(self, project_root: str | Path) -> None:
        self.root = Path(project_root).expanduser().resolve()
        self.runtime = ProjectMemoryRuntime(self.root)

    def read(
        self, *, consumer: str = "pulse", include_board_human: bool = False
    ) -> CompanyContext:
        items: list[ContextItem] = []
        gaps: list[str] = []
        ready = self.runtime.ensure_memory()
        if not ready.ready:
            return CompanyContext((), ("La memoria local no está disponible.",))
        with sqlite3.connect(ready.db_path) as db:
            company = db.execute(
                "SELECT name, industry, updated_at FROM companies ORDER BY updated_at DESC LIMIT 1"
            ).fetchone()
            if company and company[0]:
                items.append(
                    ContextItem(
                        "company:profile",
                        "all",
                        f"Empresa: {company[0]}"
                        + (f"; industria: {company[1]}" if company[1] else ""),
                        "perfil de empresa",
                        company[2],
                        "confirmed",
                    )
                )
            else:
                gaps.append("Falta el perfil confirmado de la empresa.")
            plan = db.execute(
                "SELECT data, updated_at FROM worksheets WHERE category='strategy' AND tool='opsp' ORDER BY version DESC LIMIT 1"
            ).fetchone()
            if plan:
                try:
                    raw = json.loads(plan[0])
                    summary = (
                        raw.get("purpose") or raw.get("bhag") or raw.get("company_name")
                    )
                    if summary:
                        items.append(
                            ContextItem(
                                "strategy:opsp",
                                "strategy",
                                str(summary)[:320],
                                "plan en una hoja",
                                plan[1],
                                "confirmed",
                            )
                        )
                except (TypeError, ValueError):
                    pass
            cadence = db.execute(
                "SELECT COUNT(*) FROM weekly_commitments WHERE status='planned'"
            ).fetchone()
            if cadence and cadence[0]:
                items.append(
                    ContextItem(
                        "execution:cadence",
                        "execution",
                        f"{cadence[0]} compromiso(s) semanales abiertos; el detalle personal no se comparte.",
                        "cadencia semanal",
                        None,
                        "confirmed",
                    )
                )
        for decision in DECISIONS:
            snapshot = EvidenceStore(self.root).snapshot(decision)
            fields = snapshot.get("fields", {}) if isinstance(snapshot, dict) else {}
            confirmed = 0
            for field, detail in fields.items():
                state = detail.get("state")
                if state == "confirmed":
                    confirmed += 1
                    source = (
                        detail.get("source")
                        if isinstance(detail.get("source"), dict)
                        else {}
                    )
                    items.append(
                        ContextItem(
                            f"evidence:{decision}:{field}",
                            decision,
                            f"{detail.get('label')}: {detail.get('value')}",
                            str(source.get("label", "evidencia confirmada")),
                            detail.get("observed_at"),
                            "confirmed",
                        )
                    )
                elif state == "stale":
                    gaps.append(
                        f"{decision}: {detail.get('label')} está desactualizado y no se usa para cálculos."
                    )
            if not confirmed:
                gaps.append(f"Falta evidencia confirmada de {decision}.")
        human: list[ContextItem] = []
        if include_board_human and consumer == "board":
            projection = HumanContextStore(self.root).project("board")
            if projection.ready:
                for entry in projection.entries:
                    human.append(
                        ContextItem(
                            f"human:{entry.id}",
                            "all",
                            f"Preferencia de colaboración ({entry.field}): {entry.value}",
                            "contexto humano autorizado para Board",
                            entry.consented_at,
                            "confirmed",
                            "human",
                        )
                    )
        return CompanyContext(tuple(items), tuple(dict.fromkeys(gaps)), tuple(human))
