"""coaching.responder.engine — pure executive-response assembly logic.

No I/O. Accepts a decision, evidence package, selection receipt and review
report, then returns an ExecutiveResponse with the five required blocks.
"""

from __future__ import annotations

from coaching.evidence.models import DecisionRef, EvidencePackage
from coaching.reviewer.models import ReviewReport
from coaching.selector.models import SelectionReceipt

from .models import ExecutiveResponse


def _evidence_lines(package: EvidencePackage, selection: SelectionReceipt) -> list[str]:
    """Return formatted evidence lines for sources used in the selection."""
    used_ids = set(selection.evidence_used)
    lines: list[str] = []
    for source in package.sources:
        if source.source_id in used_ids:
            period = f" ({source.period})" if source.period else ""
            lines.append(f"{source.title}{period}")
    return lines


def build_response(
    decision: DecisionRef,
    package: EvidencePackage,
    selection: SelectionReceipt,
    review_report: ReviewReport,
) -> ExecutiveResponse:
    """Build an executive response from reviewed inputs."""
    if not review_report.can_proceed:
        return ExecutiveResponse(
            decision=decision.decision,
            area=decision.area,
            what_i_see="No tengo elementos suficientes para una recomendación.",
            why_it_matters=f"El objetivo es: {decision.outcome}.",
            evidence=[],
            what_i_dont_know="Ver los hallazgos de revisión antes de continuar.",
            next_step="Resolver las advertencias de revisión y volver a intentar.",
            can_proceed=False,
        )

    evidence = _evidence_lines(package, selection)
    primary_skill = selection.skills[0] if selection.skills else "/escala-diagnose"

    return ExecutiveResponse(
        decision=decision.decision,
        area=decision.area,
        what_i_see=f"Tienes evidencia de {decision.area.title()} disponible para analizar.",
        why_it_matters=f"{decision.outcome}.",
        evidence=evidence,
        what_i_dont_know="No tengo proyecciones ni datos fuera de las fuentes disponibles.",
        next_step=f"Ejecutar `{primary_skill}` para profundizar en el análisis.",
        can_proceed=True,
    )
