"""
Welcome module — company intake, stage detection, profile creation.
"""

from pathlib import Path
from ..core import detect_stage, write_yaml


def run(context: dict) -> dict:
    """
    Execute the welcome/intake flow.

    Context keys:
        - company_name: str
        - industry: str
        - employees: int
        - entry_methodology: str (lean-canvas | bmc | skip)
        - base_path: str (path to project root)

    Returns:
        dict with output, artifacts, errors
    """
    base = Path(context.get("base_path", "."))
    profile_path = base / ".scaleup" / "agent" / "memory" / "company-profile.yaml"

    name = context.get("company_name", "").strip()
    industry = context.get("industry", "").strip()
    employees = context.get("employees", 0)
    methodology = context.get("entry_methodology", "lean-canvas")

    errors = []
    if not name:
        errors.append("company_name es requerido")
    if not industry:
        errors.append("industry es requerida")
    if not isinstance(employees, int) or employees < 1:
        errors.append("employees debe ser un entero positivo")

    if errors:
        return {"output": "", "artifacts": {}, "errors": errors}

    stage = detect_stage(employees)

    profile = {
        "company": {
            "name": name,
            "industry": industry,
            "employees": employees,
            "growth_stage": stage,
            "entry_methodology": methodology,
        },
        "scores": {},
        "focus": {"current_decision": None, "last_session": None},
        "coaching": {"level": "shu", "level_source": "auto"},
        "created": str(__import__("datetime").datetime.now().date()),
    }

    write_yaml(profile_path, profile)

    output_lines = [
        f"## Bienvenido, {name}!",
        "",
        "He creado tu perfil de empresa:",
        "",
        "| Campo | Valor |",
        "|-------|-------|",
        f"| Industria | {industry} |",
        f"| Empleados | {employees} |",
        f"| Etapa | {stage} |",
        "",
    ]

    if methodology == "lean-canvas":
        output_lines.append(
            "Como startup en etapa temprana, te recomiendo empezar con un **Lean Canvas** "
            "para clarificar tu modelo de negocio antes de sumergirte en Scaling Up."
        )
    elif methodology == "bmc":
        output_lines.append(
            "Tienes un modelo de negocio establecido. Pasemos directo al diagnóstico "
            "de las 4 decisiones con `/scaleup-diagnose`."
        )
    else:
        output_lines.append(
            "Tu perfil está listo. Siguiente paso: `/scaleup-diagnose` para evaluar "
            "tu situación actual en las 4 decisiones."
        )

    return {
        "output": "\n".join(output_lines),
        "artifacts": {"profile": profile, "profile_path": str(profile_path)},
        "errors": [],
    }


def _main() -> None:
    """Minimal module entry point for ``python -m coaching.welcome``."""
    result = run({})
    if result.get("output"):
        print(result["output"])
    for error in result.get("errors", []):
        print(error)
