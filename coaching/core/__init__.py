"""
Core shared utilities for ESCALA coaching modules.
"""

import json
import sys
from pathlib import Path


def load_context() -> dict:
    """Load context from stdin (JSON). Returns empty dict if no input."""
    if not sys.stdin.isatty():
        try:
            return json.loads(sys.stdin.read())
        except (json.JSONDecodeError, EOFError):
            return {}
    return {}


def run_and_print(module_name: str, context: dict) -> None:
    """Dynamically import a coaching module and run it, printing JSON result."""
    import importlib

    mod = importlib.import_module(f"coaching.{module_name}")
    result = mod.run(context)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def require_local_ref(value: str, field_name: str) -> str:
    """Reject URLs, absolute paths, and parent traversal in evidence refs."""
    if value.startswith(("http://", "https://", "file://")):
        raise ValueError(f"{field_name} must not be a URL")
    if value.startswith(("/", "\\\\")) or ":\\" in value[:10]:
        raise ValueError(f"{field_name} must not be an absolute path")
    if ".." in value:
        raise ValueError(f"{field_name} must not contain parent traversal")
    return value


def read_yaml(path: Path) -> dict:
    """Read a YAML file, returning empty dict on failure."""
    try:
        import yaml

        if path.exists():
            return yaml.safe_load(path.read_text()) or {}
    except Exception:
        pass
    return {}


def write_yaml(path: Path, data: dict) -> None:
    """Write a dict to a YAML file."""
    import yaml

    ensure_dir(path.parent)
    path.write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    )


# ---------------------------------------------------------------------------
# Decision constants (shared across pulse, diagnose, export)
# ---------------------------------------------------------------------------

PRIORITY_ORDER = ["people", "strategy", "execution", "cash"]

DECISION_LABELS = {
    "people": "People",
    "strategy": "Strategy",
    "execution": "Execution",
    "cash": "Cash",
    "overall": "Overall",
}

# S86.2: the only names the owner reads for the four areas. Ids, routing keys
# and catalog values stay in English; every Spanish text uses these.
OWNER_AREA_NAMES: dict[str, str] = {
    "people": "tu equipo",
    "strategy": "tus clientes y tu estrategia",
    "execution": "tu día a día",
    "cash": "tu dinero",
}
_OWNER_WHOLE_BUSINESS = "tu negocio"


def owner_area_name(area: str | None, capital: bool = False) -> str:
    """Spanish name of an area for the owner; unknown or overall → 'tu negocio'."""
    name = OWNER_AREA_NAMES.get(area or "", _OWNER_WHOLE_BUSINESS)
    return name[0].upper() + name[1:] if capital else name


def owner_area_choice() -> str:
    """The four areas as one Spanish choice: 'tu equipo, …, tu día a día o tu dinero'."""
    names = [OWNER_AREA_NAMES[area] for area in PRIORITY_ORDER]
    return ", ".join(names[:-1]) + " o " + names[-1]


ROUTING_RULES = {
    "people": "/escala-people",
    "strategy": "/escala-strategy",
    "execution": "/escala-execution",
    "cash": "/escala-cash",
    "overall": "/escala-diagnose",
}


GROWTH_STAGES = {
    "startup": {
        "label": "Startup",
        "employees_max": 10,
        "description": "Buscando product-market fit",
    },
    "growth": {
        "label": "Growth",
        "employees_max": 50,
        "description": "Escalando el negocio",
    },
    "scaling": {
        "label": "Scaling",
        "employees_max": 200,
        "description": "Sistematizando operaciones",
    },
    "expansion": {
        "label": "Expansion",
        "employees_max": 99999,
        "description": "Múltiples mercados o líneas",
    },
}


def detect_stage(employees: int) -> str:
    """Detect growth stage based on employee count."""
    for stage_key, info in GROWTH_STAGES.items():
        if employees <= info["employees_max"]:
            return stage_key
    return "expansion"


def format_profile_markdown(profile: dict) -> str:
    """Format company profile dict as user-facing markdown."""
    company = profile.get("company", {})
    lines = [
        f"## {company.get('name', 'Sin nombre')}",
        "",
        "| Campo | Valor |",
        "|-------|-------|",
        f"| Industria | {company.get('industry', '—')} |",
        f"| Empleados | {company.get('employees', '—')} |",
        f"| Etapa | {company.get('growth_stage', '—')} |",
        f"| Metodología de entrada | {company.get('entry_methodology', '—')} |",
        "",
    ]
    scores = profile.get("scores", {})
    if scores:
        lines.append("### Scores de Diagnóstico")
        lines.append("")
        lines.append("| Decisión | Score |")
        lines.append("|----------|-------|")
        for decision in ["people", "strategy", "execution", "cash"]:
            score = scores.get(decision, "—")
            lines.append(f"| {decision.title()} | {score} |")
    return "\n".join(lines)
