"""
Router module — deterministic routing to decision sub-agents.
"""
from ..core import read_yaml
from pathlib import Path

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

SUB_AGENT_FILES = {
    "people": ".scaleup/agent/sub-agents/people.md",
    "strategy": ".scaleup/agent/sub-agents/strategy.md",
    "execution": ".scaleup/agent/sub-agents/execution.md",
    "cash": ".scaleup/agent/sub-agents/cash.md",
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

    # Default: read scores from profile
    profile_path = base / ".scaleup" / "agent" / "memory" / "company-profile.yaml"
    profile = read_yaml(profile_path)
    scores = context.get("scores", profile.get("scores", {}))

    if action == "list":
        lines = [
            "## Sub-agentes Disponibles",
            "",
            "| Sub-agente | Comando | Cuándo usarlo |",
            "|------------|---------|---------------|",
        ]

        for dec_key in PRIORITY_ORDER:
            fpath = Path(SUB_AGENT_FILES[dec_key])
            summary = "—"
            if fpath.exists():
                content = fpath.read_text()
                for line in content.split("\n"):
                    if line.strip().startswith("## Dominio"):
                        continue

            score = scores.get(dec_key, "—")
            lines.append(f"| {SUB_AGENT_LABELS[dec_key]} | `{SUB_AGENT_COMMANDS[dec_key]}` | Score: {score} |")

        lines.extend([
            "",
            "Para ir a un sub-agente específico, usa su comando directamente.",
            "O corre `/scaleup-diagnose` para que el router decida por ti.",
        ])

        return {
            "output": "\n".join(lines),
            "artifacts": {"sub_agents": list(SUB_AGENT_COMMANDS.keys())},
            "errors": [],
        }

    elif action == "route":
        if not scores:
            return {
                "output": "",
                "artifacts": {},
                "errors": ["No hay scores de diagnóstico. Corre `/scaleup-diagnose` primero."],
            }

        # Explicit request overrides score-based routing
        explicit = context.get("explicit_request", "").lower()
        if explicit and explicit in SUB_AGENT_COMMANDS:
            target = explicit
            reason = f"Solicitud explícita del usuario"
        else:
            target = detect_priority(scores)
            reason = f"Score más bajo ({scores.get(target, '?')}/5)"

        lines = [
            f"## Routing: {SUB_AGENT_LABELS[target]}",
            "",
            f"**Razón:** {reason}",
            "",
            f"Usa `{SUB_AGENT_COMMANDS[target]}` para empezar a trabajar en esta decisión.",
            "",
            "### Resumen de Scores",
            "| Decisión | Score |",
            "|----------|-------|",
        ]
        for dec_key in PRIORITY_ORDER:
            score = scores.get(dec_key, "—")
            marker = " ⬅" if dec_key == target else ""
            lines.append(f"| {SUB_AGENT_LABELS[dec_key]} | {score}{marker} |")

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
        # Check which sub-agent files exist
        available = []
        for dec_key, fpath in SUB_AGENT_FILES.items():
            if Path(fpath).exists():
                available.append(dec_key)

        current = profile.get("focus", {}).get("current_decision")
        lines = [
            "## Estado de Sub-agentes",
            "",
            f"Sub-agentes disponibles: {len(available)}/4",
            f"Última decisión trabajada: {current or 'Ninguna'}",
            "",
        ]

        return {
            "output": "\n".join(lines),
            "artifacts": {"available": available, "current_decision": current},
            "errors": [],
        }

    return {"output": "", "artifacts": {}, "errors": [f"Unknown action: {action}"]}
