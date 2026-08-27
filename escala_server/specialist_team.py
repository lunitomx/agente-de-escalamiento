"""Evidence-bounded, local coordination for E45's private specialists.

The coordinator is deliberately deterministic: it decides whether a problem is
simple or transversal, gives each role only evidence tagged for that decision,
then makes evidence gaps and disagreements visible to the business owner.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Any, Literal


DecisionArea = Literal["people", "strategy", "execution", "cash"]
_AREAS = {"people", "strategy", "execution", "cash"}


@dataclass(frozen=True)
class SpecialistContract:
    role: str
    trigger: str
    non_trigger: str
    minimum_context: tuple[str, ...]
    permissions: tuple[str, ...]
    output: str
    limits: tuple[str, ...]


SPECIALIST_CONTRACTS: dict[DecisionArea, SpecialistContract] = {
    "cash": SpecialistContract(
        role="cash-analyst",
        trigger="cash, margins, forecasts, CCC, reconciliation, or financial risk",
        non_trigger="people evaluation or legal/tax advice",
        minimum_context=("financial evidence", "period", "currency or unit"),
        permissions=("identify missing financial comparability",),
        output="cash risk, assumptions, and the next verifiable question",
        limits=("never persist unconfirmed figures", "never give tax or legal advice"),
    ),
    "execution": SpecialistContract(
        role="execution-operator",
        trigger="priorities, commitments, meetings, KPIs, or operating rhythm",
        non_trigger="person scoring or strategy rewrite",
        minimum_context=("commitments", "cadence", "operational evidence"),
        permissions=("identify blocked execution dependencies",),
        output="operational constraint and accountable next action",
        limits=("never infer individual performance",),
    ),
    "people": SpecialistContract(
        role="people-coach",
        trigger="accountability, roles, capacity, development, or team tension",
        non_trigger="hiring, firing, compensation, or personality diagnosis",
        minimum_context=("owner-provided role evidence", "consent state"),
        permissions=("ask for explicit accountability and consent",),
        output="role/accountability question and people risk",
        limits=("never make employment decisions", "never infer personal traits"),
    ),
    "strategy": SpecialistContract(
        role="strategy-analyst",
        trigger="customer, market, competition, differentiation, vision, or journey",
        non_trigger="unverified market declaration or operational task assignment",
        minimum_context=("company evidence", "dated market evidence when supplied"),
        permissions=("mark external claims as unverified",),
        output="strategic trade-off and evidence gap",
        limits=("never present market claims without source and date",),
    ),
}


class TeamReviewError(ValueError):
    """Raised for an incomplete or unsafe team-review request."""


def choose_team(request: dict[str, Any]) -> dict[str, Any]:
    """Choose a minimal team; simple cases deliberately keep one specialist."""
    areas = _areas(request.get("areas", []))
    if not areas:
        raise TeamReviewError("at least one decision area is required")
    complex_case = bool(
        request.get("owner_requests_cross_review")
        or request.get("material_risk")
        or request.get("contradictory_evidence")
        or len(areas) >= 2
        or request.get("single_coach_blocked")
    )
    roles = [SPECIALIST_CONTRACTS[area].role for area in areas]
    if complex_case:
        roles.extend(["independent-critic", "evidence-verifier"])
    return {
        "mode": "team" if complex_case else "single_specialist",
        "areas": areas,
        "roles": tuple(roles),
        "reason": _route_reason(request, areas, complex_case),
    }


def minimum_context(
    request: dict[str, Any], area: DecisionArea
) -> tuple[dict[str, Any], ...]:
    """Return only evidence explicitly tagged for a role or all selected areas."""
    evidence = request.get("evidence", [])
    if not isinstance(evidence, list):
        raise TeamReviewError("evidence must be a list")
    selected: list[dict[str, Any]] = []
    for item in evidence:
        if not isinstance(item, dict):
            raise TeamReviewError("evidence item must be an object")
        tags = set(item.get("areas", []))
        _validate_evidence_privacy(item, tags)
        if area in tags or "shared" in tags:
            selected.append(item)
    return tuple(selected)


def review(request: dict[str, Any]) -> dict[str, Any]:
    """Run one local review and return a single executive-facing synthesis."""
    started = monotonic()
    limits = _review_limits(request)
    team = choose_team(request)
    context = {area: minimum_context(request, area) for area in team["areas"]}
    verification = _verify(context)
    agreements, disagreements = _resolve_claims(request.get("claims", []))
    critical = _critic(request, context, verification, disagreements)
    needs_question = verification["blocked"] or bool(disagreements)
    question = _next_question(verification, disagreements)
    evidence_ids = tuple(
        dict.fromkeys(
            str(item["source_id"])
            for items in context.values()
            for item in items
            if item.get("source_id")
        )
    )
    primary_constraint = (
        verification["gaps"][0]
        if verification["gaps"]
        else disagreements[0]["topic"]
        if disagreements
        else None
    )
    synthesis = {
        "status": "blocked"
        if verification["blocked"]
        else "needs_evidence"
        if disagreements
        else "ready",
        "primary_constraint": primary_constraint,
        "decision_suggested": (
            "Pausa la decisión hasta confirmar la evidencia faltante."
            if needs_question
            else "Avanza con una acción reversible y revísala en la cadencia acordada."
        ),
        "alternatives": (
            "Confirmar el dato faltante antes de actuar.",
            "Tomar una acción reversible y medir su resultado.",
        ),
        "evidence_ids": evidence_ids,
        "assumptions": (),
        "risk": critical,
        "next_question": question,
        "next_action": "Registrar la decisión humana y su seguimiento en ESCALA.",
        "owner_suggestion": None,
        "review_cadence": None,
    }
    elapsed_ms = int((monotonic() - started) * 1000)
    if elapsed_ms > limits["time_limit_ms"]:
        raise TeamReviewError("team review exceeded its declared time limit")
    return {
        "route": team,
        "context_receipts": {area: len(items) for area, items in context.items()},
        "verification": verification,
        "agreements": agreements,
        "disagreements": disagreements,
        "synthesis": synthesis,
        "coordination_limits": {
            **limits,
            "elapsed_ms": elapsed_ms,
            "privacy_boundary": "tagged-minimum-context-only",
        },
    }


def _areas(raw: Any) -> tuple[DecisionArea, ...]:
    if not isinstance(raw, list) or not raw:
        return ()
    if any(area not in _AREAS for area in raw):
        raise TeamReviewError("unknown decision area")
    return tuple(dict.fromkeys(raw))


def _review_limits(request: dict[str, Any]) -> dict[str, int]:
    rounds_used = request.get("rounds_used", 0)
    time_limit_ms = request.get("time_limit_ms", 1_000)
    if (
        isinstance(rounds_used, bool)
        or not isinstance(rounds_used, int)
        or rounds_used < 0
        or rounds_used > 1
    ):
        raise TeamReviewError("team review allows at most one clarification round")
    if (
        isinstance(time_limit_ms, bool)
        or not isinstance(time_limit_ms, int)
        or not 25 <= time_limit_ms <= 60_000
    ):
        raise TeamReviewError("team review time limit must be 25 to 60000 ms")
    return {
        "rounds_allowed": 1,
        "rounds_used": rounds_used,
        "time_limit_ms": time_limit_ms,
    }


def _validate_evidence_privacy(item: dict[str, Any], tags: set[Any]) -> None:
    sensitivity = item.get("sensitivity", "business")
    if sensitivity not in {"business", "financial", "personal"}:
        raise TeamReviewError("evidence sensitivity is not supported")
    if sensitivity == "personal":
        if tags != {"people"}:
            raise TeamReviewError("personal evidence must stay within People context")
        if item.get("people_consent") is not True:
            raise TeamReviewError("personal evidence requires explicit People consent")
    if sensitivity == "financial" and tags - {"cash"}:
        raise TeamReviewError("financial evidence must stay within Cash context")


def _route_reason(
    request: dict[str, Any], areas: tuple[DecisionArea, ...], complex_case: bool
) -> str:
    if not complex_case:
        return "Una sola decisión con evidencia suficiente no justifica una revisión transversal."
    if len(areas) >= 2:
        return "Más de una decisión aporta evidencia relevante al problema."
    if request.get("contradictory_evidence"):
        return "Hay evidencia contradictoria que requiere crítica y verificación."
    return "El riesgo material o la solicitud del dueño justifica revisión transversal."


def _verify(context: dict[DecisionArea, tuple[dict[str, Any], ...]]) -> dict[str, Any]:
    gaps: list[str] = []
    for area, items in context.items():
        if not items:
            gaps.append(f"Falta evidencia para {area}.")
        for item in items:
            if not item.get("source_id"):
                gaps.append(f"Una evidencia de {area} no tiene fuente.")
            if area == "cash" and (not item.get("period") or not item.get("unit")):
                gaps.append("Una cifra de Cash no declara periodo y unidad.")
    return {"blocked": bool(gaps), "gaps": tuple(dict.fromkeys(gaps))}


def _resolve_claims(raw: Any) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    if not isinstance(raw, list):
        raise TeamReviewError("claims must be a list")
    topics: dict[str, set[str]] = {}
    for claim in raw:
        if (
            not isinstance(claim, dict)
            or not claim.get("topic")
            or not claim.get("position")
        ):
            raise TeamReviewError("claim needs topic and position")
        topics.setdefault(str(claim["topic"]), set()).add(str(claim["position"]))
    agreements = tuple(
        topic for topic, positions in topics.items() if len(positions) == 1
    )
    disagreements = tuple(
        {
            "topic": topic,
            "positions": " / ".join(sorted(positions)),
            "question": f"¿Qué dato verificable resolvería la diferencia sobre {topic}?",
        }
        for topic, positions in topics.items()
        if len(positions) > 1
    )
    return agreements, disagreements


def _critic(
    request: dict[str, Any],
    context: dict[DecisionArea, tuple[dict[str, Any], ...]],
    verification: dict[str, Any],
    disagreements: tuple[dict[str, str], ...],
) -> str:
    if verification["blocked"]:
        return "No es seguro recomendar: faltan fuentes, periodo o unidad verificable."
    if disagreements:
        return "Hay un desacuerdo material; no se debe elegir por mayoría."
    if request.get("material_risk"):
        return "Existe riesgo material; limita la primera acción a una decisión reversible."
    if any(not items for items in context.values()):
        return "Una decisión relevante no tiene contexto suficiente."
    return "No se detectó un supuesto crítico adicional con la evidencia disponible."


def _next_question(
    verification: dict[str, Any], disagreements: tuple[dict[str, str], ...]
) -> str:
    if verification["gaps"]:
        return verification["gaps"][0]
    if disagreements:
        return disagreements[0]["question"]
    return "¿Qué resultado medible confirmarás en la siguiente revisión?"
