"""
Router module — deterministic routing to decision sub-agents.
"""
from ..core import read_yaml
from pathlib import Path
import re

PRIORITY_ORDER = ["people", "strategy", "execution", "cash"]

SUB_AGENT_COMMANDS = {
    "people": "/scaleup-people",
    "strategy": "/scaleup-strategy",
    "execution": "/scaleup-execution",
    "cash": "/scaleup-cash",
}

SUB_AGENT_LABELS = {
    "people": "People — Personas",
    "strategy": "Strategy — Estrategia",
    "execution": "Execution — Ejecución",
    "cash": "Cash — Efectivo",
}


# Public routes use product language; internal skill names stay in adapters.
PUBLIC_HANDOFFS = {
    "onboarding": "coaching.welcome",
    "diagnosis": "coaching.diagnose",
    "opsp": "coaching.opsp",
    "progress": "coaching.progress",
}


def _normalise(text: str) -> str:
    import unicodedata
    return "".join(char for char in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(char) != "Mn")


def detect_public_intent(message: str, profile: dict | None = None) -> str:
    """Route a natural-language request to a beginner-friendly ScaleUp journey."""
    text = _normalise(message or "")
    has_profile = bool((profile or {}).get("company", {}).get("name"))
    if re.search(r"\b(opsp|one[ -]?page|una pagina|plan en una hoja|plan.*hoja|plan estrategico)\b", text):
        return "opsp"
    if re.search(r"\b(diagnostico|diagnosticar|evaluar|cuatro decisiones|4 decisiones|por donde empiezo|no se por donde)\b", text):
        return "diagnosis" if has_profile else "onboarding"
    if re.search(r"\b(progreso|avance|tareas|pendiente|continuar|retomar|como vamos)\b", text):
        return "progress" if has_profile else "onboarding"
    if re.search(r"\b(organizar|ordena|escalar|empresa|negocio|ayuda|empezar)\b", text):
        return "diagnosis" if has_profile else "onboarding"
    return "progress" if has_profile else "onboarding"


def route_public_intent(message: str, profile: dict | None = None) -> dict:
    """Return a product handoff and a plain-Spanish next question."""
    intent = detect_public_intent(message, profile)
    messages = {
        "onboarding": "Para orientarte bien, empecemos por tu empresa. ¿Cómo se llama y a qué se dedica?",
        "diagnosis": "Vamos a encontrar el mejor punto de partida. Te haré una pregunta a la vez sobre tu empresa.",
        "opsp": "Vamos a construir tu plan estratégico en una hoja. ¿Qué tres a cinco valores definen cómo trabaja tu empresa?",
        "progress": "Revisemos dónde vas y el siguiente paso más útil para tu empresa.",
    }
    return {"intent": intent, "handoff": PUBLIC_HANDOFFS[intent], "message": messages[intent], "requires_command": False}


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

    if action in {"frontdoor", "intent"} or "message" in context:
        public_route = route_public_intent(str(context.get("message", "")), profile)
        return {"output": public_route["message"], "artifacts": public_route, "errors": []}

    if action == "list":
        lines = ["## Sub-agentes Disponibles", "", "| Sub-agente | Comando | Score |", "|------------|---------|-------|"]
        for dec_key in PRIORITY_ORDER:
            score = scores.get(dec_key, "—")
            lines.append(f"| {SUB_AGENT_LABELS[dec_key]} | `{SUB_AGENT_COMMANDS[dec_key]}` | {score} |")
        lines.extend(["", "Para ir a un sub-agente específico, usa su comando directamente.", "O corre `/scaleup-diagnose` para que el router decida por ti."])
        return {"output": "\n".join(lines), "artifacts": {"sub_agents": list(SUB_AGENT_COMMANDS.keys())}, "errors": []}

    elif action == "route":
        if not scores:
            return {"output": "", "artifacts": {}, "errors": ["No hay scores de diagnóstico. Corre `/scaleup-diagnose` primero."]}

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
