"""Evidence-first dashboard for multi-source onboarding."""

from __future__ import annotations

from typing import Sequence

from pydantic import BaseModel, Field

from .facts import Decision, Fact


class MetricRequirement(BaseModel):
    """A business metric the owner may supply before a diagnosis."""

    metric_definition: str = Field(..., min_length=1)
    decision: Decision | None = None
    question: str = Field(..., min_length=1)


class EvidenceGap(BaseModel):
    """A required metric that has no comparable local fact yet."""

    metric_definition: str
    decision: Decision | None = None
    question: str


class EvidenceDashboard(BaseModel):
    """Pre-diagnostic evidence state; deliberately contains no maturity score."""

    known: list[Fact] = Field(default_factory=list)
    not_comparable: list[Fact] = Field(default_factory=list)
    pending: list[EvidenceGap] = Field(default_factory=list)


def build_evidence_dashboard(
    facts: Sequence[Fact], requirements: Sequence[MetricRequirement] = ()
) -> EvidenceDashboard:
    """Separate known facts from blocked comparisons and genuine information gaps."""
    comparable = [fact for fact in facts if fact.comparable]
    blocked = [fact for fact in facts if not fact.comparable]
    pending: list[EvidenceGap] = []
    for requirement in requirements:
        matching = any(
            fact.metric_definition.casefold()
            == requirement.metric_definition.casefold()
            and (requirement.decision is None or fact.decision == requirement.decision)
            for fact in comparable
        )
        if not matching:
            pending.append(EvidenceGap(**requirement.model_dump()))
    return EvidenceDashboard(
        known=comparable,
        not_comparable=blocked,
        pending=pending,
    )


def format_evidence_dashboard(dashboard: EvidenceDashboard) -> str:
    """Render the dashboard in business language without implying a diagnosis."""
    lines = [
        "## Evidencia disponible antes del diagnóstico",
        "",
        "Esto no es una calificación: muestra qué datos podemos usar, qué no "
        "podemos comparar todavía y qué falta confirmar.",
        "",
    ]
    if dashboard.known:
        lines.extend(["### Datos conocidos", ""])
        for fact in dashboard.known:
            unit = f" {fact.unit}" if fact.unit else ""
            lines.append(
                f"- **{fact.metric_definition}:** {fact.value}{unit} "
                f"({fact.period}; fuente: {fact.source}; confianza: {fact.confidence})."
            )
        lines.append("")
    if dashboard.not_comparable:
        lines.extend(["### Datos no comparables todavía", ""])
        for fact in dashboard.not_comparable:
            lines.append(
                f"- **{fact.metric_definition}** ({fact.period}; fuente: "
                f"{fact.source}) queda fuera de cualquier comparación hasta "
                "aclarar su definición o base temporal."
            )
        lines.append("")
    if dashboard.pending:
        lines.extend(["### Información pendiente", ""])
        for gap in dashboard.pending:
            lines.append(f"- {gap.question}")
        lines.append("")
    if not dashboard.known and not dashboard.not_comparable and not dashboard.pending:
        lines.extend(["Aún no hay hechos autorizados para mostrar.", ""])
    return "\n".join(lines)
