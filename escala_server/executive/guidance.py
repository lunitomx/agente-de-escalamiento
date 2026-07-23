"""Honest guidance projection for material uncertainty."""

from __future__ import annotations

from .models import GuidanceRequest, HonestGuidance


def build_honest_guidance(request: GuidanceRequest) -> HonestGuidance:
    """Return explicit context buckets and questions for unknown material data."""

    unknowns = tuple(dict.fromkeys(request.unknowns))
    if not unknowns and not request.facts and not request.inferences:
        unknowns = (request.topic,)
    questions = ()
    if unknowns:
        questions = (
            (request.question,)
            if request.question
            else tuple(
                f"¿Qué evidencia local confirma {unknown}?" for unknown in unknowns
            )
        )
    next_action = (
        f"Resolver primero: {', '.join(unknowns)}."
        if unknowns
        else f"Convertir la evidencia de {request.topic} en una acción con dueño y fecha."
    )
    return HonestGuidance(
        status="evidence_limited" if unknowns else "supported",
        facts=request.facts,
        inferences=request.inferences,
        unknowns=unknowns,
        questions=questions,
        next_action=next_action,
    )
