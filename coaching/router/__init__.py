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

    profile_path = base / ".scaleup" / "agent" / "memory" / "company-profile.yaml"
    profile = read_yaml(profile_path)
    scores = context.get("scores", profile.get("scores", {}))

    if action == "list":
        lines = ["## Sub-agentes Disponibles", "", "| Sub-agente | Comando | Score |", "|------------|---------|-------|"]
        for dec_key in PRIORITY_ORDER:
            score = scores.get(dec_key, "—")
            lines.append(f"| {SUB_AGENT_LABELS[dec_key]} | `{SUB_AGENT_COMMANDS[dec_key]}` | {score} |")
        lines.extend(["", "Para ir a un sub-agente específico, usa su comando directamente.", "O corre `/escala-diagnose` para que el router decida por ti."])
        return {"output": "\n".join(lines), "artifacts": {"sub_agents": list(SUB_AGENT_COMMANDS.keys())}, "errors": []}

    elif action == "route":
        if not scores:
            return {"output": "", "artifacts": {}, "errors": ["No hay scores de diagnóstico. Corre `/escala-diagnose` primero."]}

        explicit = context.get("explicit_request", "").lower()
        if explicit and explicit in SUB_AGENT_COMMANDS:
            target = explicit
            reason = "Solicitud explícita del usuario"
        else:
            target = detect_priority(scores)
            reason = f"Score más bajo ({scores.get(target, '?')}/5)"

        lines = [f"## Routing: {SUB_AGENT_LABELS[target]}", "", f"**Razón:** {reason}", "", f"Usa `{SUB_AGENT_COMMANDS[target]}` para empezar.", "", "### Resumen de Scores", "| Decisión | Score |", "|----------|-------|"]
        for dec_key in PRIORITY_ORDER:
            score = scores.get(dec_key, "—")
            lines.append(f"| {SUB_AGENT_LABELS[dec_key]} | {score}{' ⬅' if dec_key == target else ''} |")

        return {"output": "\n".join(lines), "artifacts": {"target_decision": target, "target_command": SUB_AGENT_COMMANDS[target], "reason": reason, "scores": scores}, "errors": []}

    elif action == "status":
        current = profile.get("focus", {}).get("current_decision")
        lines = ["## Estado de Sub-agentes", "", "Última decisión trabajada: " + (current or "Ninguna"), ""]
        return {"output": "\n".join(lines), "artifacts": {"current_decision": current}, "errors": []}

    return {"output": "", "artifacts": {}, "errors": [f"Unknown action: {action}"]}
