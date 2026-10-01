# pyright: strict
"""Board proposals: the decision they serve and each metric's source and period.

``BoardMetric`` extends the idea of ``coaching.evidence.MetricRequirement``
(which has no source or period) without changing it: the recommender derives
a ``MetricRequirement`` from each metric to get its state from
``build_evidence_dashboard``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Area = Literal["ventas", "caja", "equipo", "ejecucion", "progreso", "mercado"]
MetricStatus = Literal["conocido", "no_comparable", "falta"]
Feasibility = Literal["se_puede_hoy", "necesita_datos", "no_ahora"]
OptionCode = Literal["construir", "esperar", "no"]
Outcome = Literal[
    "propuestas", "existe", "pregunta_decision", "sin_patron", "pospuesto"
]

MAX_PROPOSALS = 2


class BoardMetric(BaseModel):
    """One metric: definition, where it comes from, its period and state."""

    model_config = ConfigDict(extra="forbid")

    metric_definition: str = Field(min_length=1)
    source: str = Field(min_length=1)
    period: str = Field(min_length=1)
    status: MetricStatus = "falta"
    how_to_get: str = ""


class BoardProposal(BaseModel):
    """One board: which decision it serves, who looks, how often, 3-5 metrics."""

    model_config = ConfigDict(extra="forbid")

    board_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    decision: str = Field(min_length=1)
    audience: str = Field(min_length=1)
    cadence: str = Field(min_length=1)
    metrics: list[BoardMetric] = Field(min_length=3, max_length=5)
    feasibility: Feasibility
    missing: list[str] = Field(default_factory=list[str])


class DecisionOption(BaseModel):
    """What the owner can decide about the proposals."""

    model_config = ConfigDict(extra="forbid")

    code: OptionCode
    label: str


class Recommendation(BaseModel):
    """What the recommender hands back; always ends in a decision or a pointer."""

    model_config = ConfigDict(extra="forbid")

    outcome: Outcome
    area: Area | None = None
    proposals: list[BoardProposal] = Field(
        default_factory=list[BoardProposal], max_length=MAX_PROPOSALS
    )
    points_to_existing: str | None = None
    needs_journey_stages: bool = False
    options: list[DecisionOption] = Field(default_factory=list[DecisionOption])
    recommended: OptionCode | None = None
    message: str = ""
