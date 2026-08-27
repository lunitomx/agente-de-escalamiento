"""Turn evidence gaps into locally persisted, reviewable decision work."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from coaching.core import ensure_dir, write_yaml

from .dashboard import EvidenceDashboard

Priority = Literal["high", "medium", "low"]


class DecisionMapItem(BaseModel):
    item_id: str = Field(..., min_length=1)
    decision: str = Field(..., min_length=1)
    priority: Priority
    title: str = Field(..., min_length=1)
    evidence_required: list[str] = Field(default_factory=list)
    source_fact_ids: list[str] = Field(default_factory=list)
    status: Literal["open", "resolved"] = "open"


class DecisionMap(BaseModel):
    decision: str
    items: list[DecisionMapItem] = Field(default_factory=list)


def build_decision_map(dashboard: EvidenceDashboard, *, decision: str) -> DecisionMap:
    """Create only evidence-gathering work; this function never creates a decision."""
    items: list[DecisionMapItem] = []
    for index, gap in enumerate(dashboard.pending, start=1):
        items.append(
            DecisionMapItem(
                item_id=f"{decision}-missing-{index}",
                decision=decision,
                priority="high",
                title=f"Completar: {gap.metric_definition}",
                evidence_required=[gap.metric_definition, gap.question],
            )
        )
    for index, fact in enumerate(dashboard.not_comparable, start=1):
        items.append(
            DecisionMapItem(
                item_id=f"{decision}-clarify-{index}",
                decision=decision,
                priority="high",
                title=f"Aclarar comparabilidad: {fact.metric_definition}",
                evidence_required=[
                    "definición de métrica",
                    "periodo",
                    "fecha base",
                    "moneda o unidad",
                ],
                source_fact_ids=[fact.fact_id],
            )
        )
    return DecisionMap(decision=decision, items=items)


def save_decision_map(base_path: Path, decision_map: DecisionMap) -> Path:
    """Persist the user-visible parking lot inside the local company boundary."""
    path = base_path / ".escala" / "agent" / "memory" / "decision-map.yaml"
    ensure_dir(path.parent)
    write_yaml(path, decision_map.model_dump(mode="json"))
    return path
