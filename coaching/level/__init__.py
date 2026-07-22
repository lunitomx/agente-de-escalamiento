"""
Level module — detect Shu/Ha/Ri coaching level and adapt tone/depth.
"""

from ..core import read_yaml, write_yaml
from pathlib import Path

LEVEL_THRESHOLDS = {
    "shu": {
        "max": 2.4,
        "label": "Shu (Principiante)",
        "description": "Sigue las reglas. Paso a paso.",
    },
    "ha": {
        "max": 3.5,
        "label": "Ha (Intermedio)",
        "description": "Entiende los patrones. Aplica con autonomía.",
    },
    "ri": {
        "max": 5.0,
        "label": "Ri (Avanzado)",
        "description": "Crea nuevos caminos. Desafía los límites.",
    },
}

LEVEL_INSTRUCTIONS = {
    "shu": {
        "tone": "Paciente, didáctico, alentador.",
        "depth": "Instrucciones detalladas paso a paso. Ejemplos concretos.",
        "challenge": "Bajo. Preguntas de verificación.",
        "pacing": "Lento. Una idea a la vez.",
    },
    "ha": {
        "tone": "Confianza, reto moderado.",
        "depth": "Frameworks completos. Usuario aplica con supervisión.",
        "challenge": "Medio. Preguntas de aplicación.",
        "pacing": "Moderado. Varias ideas conectadas.",
    },
    "ri": {
        "tone": "Colega estratégico. Cuestiona.",
        "depth": "Conceptos avanzados, edge cases. Usuario enseña.",
        "challenge": "Alto. Dilemas estratégicos.",
        "pacing": "Rápido. Ir directo a aplicación.",
    },
}


def detect_level(scores: dict[str, int]) -> str:
    """Detect coaching level from average diagnosis score."""
    valid = [v for v in scores.values() if isinstance(v, int) and 1 <= v <= 5]
    if not valid:
        return "shu"
    avg = sum(valid) / len(valid)
    for level, thresholds in LEVEL_THRESHOLDS.items():
        if avg <= thresholds["max"]:
            return level
    return "ri"


def run(context: dict) -> dict:
    """
    Detect or set coaching level.

    Context keys:
        - action: 'detect' | 'set' | 'get'
        - level: str (for 'set' action)
        - scores: dict (for 'detect')
        - base_path: str

    Returns:
        dict with output, artifacts, errors
    """
    base = Path(context.get("base_path", "."))
    action = context.get("action", "detect")

    profile_path = base / ".escala" / "agent" / "memory" / "company-profile.yaml"

    if action == "detect":
        scores = context.get("scores", read_yaml(profile_path).get("scores", {}))
        level = detect_level(scores)
        level_info = LEVEL_THRESHOLDS[level]
        instructions = LEVEL_INSTRUCTIONS[level]
        lines = [
            f"## Nivel de Coaching: {level_info['label']}",
            "",
            f"{level_info['description']}",
            "",
            "### Adaptación",
            "",
            "| Dimensión | Estilo |",
            "|-----------|-------|",
            f"| Tono | {instructions['tone']} |",
            f"| Profundidad | {instructions['depth']} |",
            f"| Reto | {instructions['challenge']} |",
            f"| Ritmo | {instructions['pacing']} |",
            "",
        ]
        if scores:
            avg = round(
                sum(v for v in scores.values() if isinstance(v, int))
                / len([v for v in scores.values() if isinstance(v, int)]),
                1,
            )
            lines.append(f"Basado en score promedio: {avg}/5")
        lines.append("")
        lines.append("Para cambiar manualmente: `/escala-level --set shu|ha|ri`")
        return {
            "output": "\n".join(lines),
            "artifacts": {
                "level": level,
                "level_info": level_info,
                "instructions": instructions,
            },
            "errors": [],
        }

    elif action == "set":
        level = context.get("level", "").lower()
        if level not in LEVEL_THRESHOLDS:
            return {
                "output": "",
                "artifacts": {},
                "errors": [f"Nivel inválido: '{level}'. Usa: shu, ha, o ri."],
            }
        profile = read_yaml(profile_path)
        if "coaching" not in profile:
            profile["coaching"] = {}
        profile["coaching"]["level"] = level
        profile["coaching"]["level_source"] = "manual"
        write_yaml(profile_path, profile)
        return {
            "output": f"Nivel de coaching cambiado a **{LEVEL_THRESHOLDS[level]['label']}**.",
            "artifacts": {"level": level, "level_info": LEVEL_THRESHOLDS[level]},
            "errors": [],
        }

    elif action == "get":
        profile = read_yaml(profile_path)
        coaching = profile.get("coaching", {})
        level = coaching.get("level", "shu")
        source = coaching.get("level_source", "auto")
        return {
            "output": f"Nivel actual: **{LEVEL_THRESHOLDS[level]['label']}** ({source})",
            "artifacts": {
                "level": level,
                "source": source,
                "level_info": LEVEL_THRESHOLDS[level],
            },
            "errors": [],
        }

    return {"output": "", "artifacts": {}, "errors": [f"Unknown action: {action}"]}


def _main() -> None:
    """Minimal module entry point for ``python -m coaching.level``."""
    result = run({})
    if result.get("output"):
        print(result["output"])
    for error in result.get("errors", []):
        print(error)
