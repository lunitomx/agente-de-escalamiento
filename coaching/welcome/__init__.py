"""
Welcome module — company intake, stage detection, profile creation.
"""

from pathlib import Path
from ..core import detect_stage, read_yaml, write_yaml
from .conversation import (
    MaturityProfile,
    WelcomeState,
    WelcomeTurn,
    begin_welcome,
    default_onboarding_requirements,
    is_state_fresh,
    load_welcome_state,
    respond_to_welcome,
    respond_to_welcome_with_evidence,
    respond_to_welcome_from_local_evidence,
    save_welcome_state,
)

__all__ = [
    "MaturityProfile",
    "WelcomeState",
    "WelcomeTurn",
    "begin_welcome",
    "default_onboarding_requirements",
    "is_state_fresh",
    "load_welcome_state",
    "respond_to_welcome",
    "respond_to_welcome_with_evidence",
    "respond_to_welcome_from_local_evidence",
    "run",
    "save_welcome_state",
]


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
    if context.get("action") == "adaptive_conversation":
        return _run_adaptive_conversation(context, base)

    profile_path = base / ".escala" / "agent" / "memory" / "company-profile.yaml"

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

    existing = read_yaml(profile_path)

    new_company = {
        "name": name,
        "industry": industry,
        "employees": employees,
        "growth_stage": stage,
        "entry_methodology": methodology,
    }

    # Preserve the whole existing profile and overwrite only the explicitly
    # provided company fields. This prevents silent data loss for users who
    # already have scores, focus, coaching level, or diagnosis history.
    profile = dict(existing) if existing else {}
    profile["company"] = {**(existing.get("company") or {}), **new_company}
    profile.setdefault("scores", {})
    profile.setdefault("focus", {"current_decision": None, "last_session": None})
    profile.setdefault("coaching", {"level": "shu", "level_source": "auto"})
    profile.setdefault("created", str(__import__("datetime").datetime.now().date()))

    write_yaml(profile_path, profile)

    is_update = bool(existing)
    greeting = "Bienvenido de vuelta" if is_update else "Bienvenido"
    action = "actualicé" if is_update else "creado"

    output_lines = [
        f"## {greeting}, {name}!",
        "",
        f"He {action} tu perfil de empresa:",
        "",
        "| Campo | Valor |",
        "|-------|-------|",
        f"| Industria | {industry} |",
        f"| Empleados | {employees} |",
        f"| Etapa | {stage} |",
        "",
    ]

    if is_update and existing.get("scores"):
        output_lines.append(
            "Tus scores y foco de diagnóstico anteriores se conservaron."
        )
        output_lines.append("")

    if methodology == "lean-canvas":
        output_lines.append(
            "Como startup en etapa temprana, te recomiendo empezar con un **Lean Canvas** "
            "para clarificar tu modelo de negocio antes de sumergirte en ESCALA."
        )
    elif methodology == "bmc":
        output_lines.append(
            "Tienes un modelo de negocio establecido. Pasemos directo al diagnóstico "
            "de las 4 decisiones con `/escala-diagnose`."
        )
    else:
        output_lines.append(
            "Tu perfil está listo. Siguiente paso: `/escala-diagnose` para evaluar "
            "tu situación actual en las 4 decisiones."
        )

    return {
        "output": "\n".join(output_lines),
        "artifacts": {"profile": profile, "profile_path": str(profile_path)},
        "errors": [],
    }


def _run_adaptive_conversation(context: dict, base: Path) -> dict:
    """Run one evidence-aware Welcome turn without exposing implementation details."""
    from pydantic import ValidationError

    from coaching.evidence.dashboard import MetricRequirement, build_evidence_dashboard
    from coaching.evidence.facts import Fact, load_facts, save_fact

    state_payload = context.get("conversation_state")
    try:
        state = (
            WelcomeState.model_validate(state_payload)
            if state_payload is not None
            else None
        )
        requirements_payload = context.get("requested_metrics")
        requirements = (
            [MetricRequirement.model_validate(item) for item in requirements_payload]
            if requirements_payload is not None
            else default_onboarding_requirements()
        )
        confirmed_facts = [
            Fact.model_validate(item) for item in context.get("confirmed_facts", [])
        ]
    except (TypeError, ValidationError, ValueError) as exc:
        return {
            "output": "",
            "artifacts": {},
            "errors": [f"contexto inválido: {exc}"],
        }

    if confirmed_facts and not context.get("persist_authorized", False):
        return {
            "output": "",
            "artifacts": {},
            "errors": [
                "Las respuestas confirmadas requieren persist_authorized=True "
                "antes de guardarse localmente."
            ],
        }
    for fact in confirmed_facts:
        save_fact(base, fact)

    facts = load_facts(base)
    dashboard = build_evidence_dashboard(facts, requirements)
    message = context.get("message")
    if not isinstance(message, str) or not message.strip():
        turn = begin_welcome(
            returning=bool(context.get("returning", False)),
            previous_focus=context.get("previous_focus"),
        )
    else:
        turn = respond_to_welcome_with_evidence(
            state or begin_welcome().state,
            message,
            facts=facts,
            requirements=requirements,
        )

    state_path = save_welcome_state(
        base, turn.state, authorized=bool(context.get("persist_authorized", False))
    )
    return {
        "output": turn.question,
        "artifacts": {
            "action": "adaptive_conversation",
            "welcome_state": turn.state.model_dump(mode="json"),
            "evidence_dashboard": dashboard.model_dump(mode="json"),
            "persisted_state_path": str(state_path) if state_path else None,
            "persisted_fact_count": len(confirmed_facts),
        },
        "errors": [],
    }


def _main() -> None:
    """Minimal module entry point for ``python -m coaching.welcome``."""
    result = run({})
    if result.get("output"):
        print(result["output"])
    for error in result.get("errors", []):
        print(error)
