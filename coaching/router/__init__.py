"""
Router module — deterministic routing to decision sub-agents.
"""

from ..core import read_yaml
from pathlib import Path

PRIORITY_ORDER = ["people", "strategy", "execution", "cash"]

SUB_AGENT_COMMANDS = {
    "people": "/escala-people",
    "strategy": "/escala-strategy",
    "execution": "/escala-execution",
    "cash": "/escala-cash",
}

SUB_AGENT_LABELS = {
    "people": "People — Personas",
    "strategy": "Strategy — Estrategia",
    "execution": "Execution — Ejecución",
    "cash": "Cash — Efectivo",
}

_CONFIRMED_ASSESSMENTS = {"confirmed", "corrected"}


def _confirmed_narrative_focus(profile: dict) -> str | None:
    assessment = profile.get("narrative_assessment")
    if not isinstance(assessment, dict):
        return None
    if assessment.get("confirmation_status") not in _CONFIRMED_ASSESSMENTS:
        return None
    focuses = assessment.get("proposed_focuses")
    if not isinstance(focuses, list):
        return None
    for focus in focuses:
        if isinstance(focus, dict) and focus.get("decision") in PRIORITY_ORDER:
            return focus["decision"]
    return None


def detect_priority(scores: dict[str, int]) -> str:
    """Find lowest-scored decision. Tiebreaker: PRIORITY_ORDER."""
    valid = {k: v for k, v in scores.items() if isinstance(v, int) and v >= 1}
    if not valid:
        return "people"
    min_score = min(valid.values())
    candidates = [k for k in PRIORITY_ORDER if k in valid and valid[k] == min_score]
    return candidates[0]


def run(context: dict) -> dict:
    """
    Route to the right sub-agent based on context.

    Context keys:
        - action: 'route' | 'list' | 'status'
        - scores: dict (for route)
        - explicit_request: str (optional, overrides score-based routing)
        - base_path: str

    Returns:
        dict with output, artifacts, errors
    """
    base = Path(context.get("base_path", "."))
    action = context.get("action", "route")

    profile_path = base / ".escala" / "agent" / "memory" / "company-profile.yaml"
    profile = read_yaml(profile_path)
    scores = context.get("scores", profile.get("scores", {}))

    if action == "list":
        lines = [
            "## Sub-agentes Disponibles",
            "",
            "| Ruta interna | Comando | Señal opcional |",
            "|---------------|---------|----------------|",
        ]
        for dec_key in PRIORITY_ORDER:
            score = scores.get(dec_key, "—")
            lines.append(
                f"| {SUB_AGENT_LABELS[dec_key]} | `{SUB_AGENT_COMMANDS[dec_key]}` | {score} |"
            )
        lines.extend(
            [
                "",
                "Para ir a un sub-agente específico, usa su comando directamente.",
                "O construye un assessment con `/escala-diagnose` y confirma el foco.",
            ]
        )
        return {
            "output": "\n".join(lines),
            "artifacts": {"sub_agents": list(SUB_AGENT_COMMANDS.keys())},
            "errors": [],
        }

    elif action == "route":
        narrative_focus = _confirmed_narrative_focus(profile)
        if not scores and narrative_focus is None:
            return {
                "output": "",
                "artifacts": {},
                "errors": [
                    "Aún no hay un foco confirmado. Construye o corrige el assessment "
                    "narrativo antes de enrutar."
                ],
            }

        raw_explicit = context.get("explicit_request", "")
        explicit = raw_explicit.lower() if isinstance(raw_explicit, str) else ""
        if explicit and explicit in SUB_AGENT_COMMANDS:
            target = explicit
            reason = "Solicitud explícita del usuario"
        elif scores:
            target = detect_priority(scores)
            reason = f"Calificación opcional más baja ({scores.get(target, '?')}/5)"
        else:
            target = narrative_focus
            reason = "Foco confirmado en el assessment narrativo"

        if target not in SUB_AGENT_COMMANDS:
            return {
                "output": "",
                "artifacts": {},
                "errors": [
                    "El foco confirmado no corresponde a una decisión disponible."
                ],
            }

        lines = [
            f"## Routing: {SUB_AGENT_LABELS[target]}",
            "",
            f"**Razón:** {reason}",
            "",
            f"Usa `{SUB_AGENT_COMMANDS[target]}` para empezar.",
            "",
        ]
        if scores:
            lines.extend(
                [
                    "### Calificación cuantitativa opcional",
                    "| Decisión | Score |",
                    "|----------|-------|",
                ]
            )
            for dec_key in PRIORITY_ORDER:
                score = scores.get(dec_key, "—")
                lines.append(
                    f"| {SUB_AGENT_LABELS[dec_key]} | {score}{' ⬅' if dec_key == target else ''} |"
                )
        else:
            lines.extend(
                [
                    "La ruta se basa en un assessment confirmado, no en un promedio numérico.",
                    "Confirma que quieres profundizar antes de solicitar datos detallados.",
                ]
            )

        return {
            "output": "\n".join(lines),
            "artifacts": {
                "target_decision": target,
                "target_command": SUB_AGENT_COMMANDS[target],
                "reason": reason,
                "scores": scores,
            },
            "errors": [],
        }

    elif action == "status":
        current = profile.get("focus", {}).get("current_decision")
        lines = [
            "## Estado de Sub-agentes",
            "",
            "Última decisión trabajada: " + (current or "Ninguna"),
            "",
        ]
        return {
            "output": "\n".join(lines),
            "artifacts": {"current_decision": current},
            "errors": [],
        }

    return {"output": "", "artifacts": {}, "errors": [f"Unknown action: {action}"]}


def _main() -> None:
    """Minimal module entry point for ``python -m coaching.router``."""
    result = run({})
    if result.get("output"):
        print(result["output"])
    for error in result.get("errors", []):
        print(error)
