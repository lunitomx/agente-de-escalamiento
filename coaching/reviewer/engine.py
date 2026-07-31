"""coaching.reviewer.engine — pure pre-response review logic.

No I/O. Accepts a decision, evidence package and selection receipt, then returns
a ReviewResult with findings and a safe/unsafe action.
"""

from __future__ import annotations

from coaching.evidence.models import DecisionRef, EvidencePackage
from coaching.selector.models import SelectionReceipt

from .models import ReviewAction, ReviewFinding, ReviewReport, ReviewResult


def _has_contradiction(package: EvidencePackage) -> bool:
    """Detect contradiction: two available low-confidence sources same period."""
    low_confidence = [
        source
        for source in package.sources
        if source.status == "available" and source.confidence == "low" and source.period
    ]
    periods = [source.period for source in low_confidence]
    return len(low_confidence) >= 2 and len(set(periods)) < len(periods)


def _has_no_available(package: EvidencePackage) -> bool:
    return not package.sources


def _alignment_finding(
    decision: DecisionRef, selection: SelectionReceipt
) -> ReviewFinding | None:
    if selection.area != decision.area:
        return ReviewFinding(
            kind="alignment",
            severity="critical",
            message=(
                f"El área de la herramienta seleccionada ({selection.area}) "
                f"no coincide con el área de la decisión ({decision.area})."
            ),
            recommendation="Revisar la selección de herramienta antes de responder.",
        )
    return None


def _basic_output(action: ReviewAction, report: ReviewReport) -> str:
    if action == "reviewed":
        tool_label = report.tool or "ninguna herramienta"
        return (
            f"## Revisión de calidad\n\n"
            f"La recomendación puede avanzar para **{report.area.title()}** "
            f"usando **{tool_label}**."
        )
    if action == "clarify":
        return (
            "## Revisión de calidad: falta información\n\n"
            "Se encontraron advertencias que deben resolverse antes de responder."
        )
    return (
        "## Revisión de calidad: bloqueada\n\n"
        "Se detectó un problema crítico que impide generar una recomendación segura."
    )


def review(
    decision: DecisionRef,
    package: EvidencePackage,
    selection: SelectionReceipt,
) -> ReviewResult:
    """Review the evidence and selection before generating a response."""
    findings: list[ReviewFinding] = []
    action: ReviewAction = "reviewed"
    questions = list(package.questions)

    # Critical contradictions between available sources.
    if _has_contradiction(package):
        findings.append(
            ReviewFinding(
                kind="contradiction",
                severity="critical",
                source_ids=[source.source_id for source in package.sources],
                message=(
                    "Se detectan fuentes disponibles con baja confianza en el mismo "
                    "periodo; pueden contradecirse."
                ),
                recommendation="Resolver la contradicción antes de generar una recomendación.",
            )
        )
        action = "blocked"

    # Sources that are not trustworthy yet.
    for source in package.not_trustworthy:
        findings.append(
            ReviewFinding(
                kind="unknown",
                severity="warning",
                source_ids=[source.source_id],
                message=f"'{source.title}' no es confiable todavía: {source.reason}",
                recommendation="Solicitar una versión actualizada o completar la fuente.",
            )
        )
        if action == "reviewed":
            action = "clarify"

    # No available evidence at all.
    if _has_no_available(package):
        findings.append(
            ReviewFinding(
                kind="missing",
                severity="warning",
                message="No hay evidencia disponible para respaldar la recomendación.",
                recommendation="Solicitar la evidencia mínima antes de responder.",
            )
        )
        if action in {"reviewed", "clarify"}:
            action = "clarify"

    # Missing expected sources.
    for source in package.missing:
        findings.append(
            ReviewFinding(
                kind="missing",
                severity="warning",
                source_ids=[source.source_id],
                message=f"Falta la fuente '{source.title}'.",
                recommendation=f"Preguntar si tiene disponible '{source.title}'.",
            )
        )
        if action == "reviewed":
            action = "clarify"

    # Alignment between decision and selection.
    alignment = _alignment_finding(decision, selection)
    if alignment:
        findings.append(alignment)
        action = "blocked"

    # Tool selected without evidence.
    if selection.tool and not selection.evidence_used:
        findings.append(
            ReviewFinding(
                kind="alignment",
                severity="critical",
                message="Se seleccionó una herramienta sin evidencia usada.",
                recommendation="Revisar el recibo de selección.",
            )
        )
        action = "blocked"

    # Period mismatch across available sources.
    periods = {source.period for source in package.sources if source.period}
    if len(periods) > 1:
        findings.append(
            ReviewFinding(
                kind="fact",
                severity="warning",
                source_ids=[source.source_id for source in package.sources],
                message=(
                    "Las fuentes disponibles corresponden a periodos diferentes: "
                    f"{', '.join(sorted(periods))}."
                ),
                recommendation="Verificar que los números sean del periodo correcto.",
            )
        )
        if action == "reviewed":
            action = "clarify"

    can_proceed = action == "reviewed"
    action_aligned = not any(finding.kind == "alignment" for finding in findings)

    report = ReviewReport(
        decision=decision.decision,
        area=decision.area,
        tool=selection.tool,
        findings=findings,
        critical_questions=questions,
        action_aligned=action_aligned,
        can_proceed=can_proceed,
    )

    return ReviewResult(
        action=action,
        report=report,
        output=_basic_output(action, report),
        questions=questions if action != "reviewed" else [],
    )
