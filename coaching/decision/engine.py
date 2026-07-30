"""coaching.decision.engine — pure decision-clarification logic.

No I/O. Accepts a user question or correction, returns a structured decision
sheet (draft) or a clarification request.
"""

from __future__ import annotations

from typing import Any

VALID_AREAS = ["people", "strategy", "execution", "cash"]
VALID_HORIZONS = ["inmediato", "corto", "medio", "largo"]

AREA_KEYWORDS: dict[str, list[str]] = {
    "people": [
        "contratar",
        "equipo",
        "empleado",
        "gerente",
        "liderazgo",
        "gente",
        "personas",
        "talento",
        "rh",
        "recursos humanos",
        "cultura",
        "valores",
        "capacitar",
        "despedir",
        "equipo de ventas",
    ],
    "strategy": [
        "estrategia",
        "opsp",
        "bhag",
        "marca",
        "diferenciación",
        "diferenciacion",
        "competencia",
        "mercado",
        "crecimiento",
        "posicionamiento",
        "propuesta de valor",
    ],
    "execution": [
        "ejecución",
        "ejecucion",
        "proceso",
        "kpi",
        "prioridades",
        "reunión",
        "reunion",
        "huddle",
        "operación",
        "operacion",
        "proyecto",
        "ritmo",
        "disciplina",
    ],
    "cash": [
        "cash",
        "efectivo",
        "dinero",
        "cobro",
        "margen",
        "proveedores",
        "finanzas",
        "precio",
        "costo",
        "costos",
        "facturación",
        "facturacion",
        "ingresos",
    ],
}

HORIZON_KEYWORDS: dict[str, list[str]] = {
    "inmediato": [
        "ahora",
        "ya",
        "este mes",
        "inmediato",
        "próximo paso",
        "proximo paso",
        "debería",
        "deberia",
        "debo",
    ],
    "corto": [
        "trimestre",
        "próximo trimestre",
        "proximo trimestre",
        "este trimestre",
        "3 meses",
        "tres meses",
    ],
    "medio": [
        "este año",
        "este ano",
        "12 meses",
        "doce meses",
        "anual",
    ],
    "largo": [
        "años",
        "anos",
        "5 años",
        "5 anos",
        "largo plazo",
        "próximos años",
        "proximos anos",
    ],
}

# Verbs that signal a concrete decision (subject + action) rather than a vague need.
DECISION_VERBS = [
    "contratar",
    "reducir",
    "implementar",
    "definir",
    "lanzar",
    "renegociar",
    "cubrir",
    "establecer",
    "diseñar",
    "disenar",
    "crear",
    "adquirir",
    "vender",
    "expandir",
    "ajustar",
    "negociar",
    "renovar",
    "invertir",
]

GENERIC_OUTCOMES: dict[str, str] = {
    "people": "fortalecer el equipo y la cultura organizacional",
    "strategy": "alinear la estrategia de la empresa",
    "execution": "mejorar la disciplina de ejecución",
    "cash": "mejorar la salud de cash flow",
}


def _clean_text(text: str) -> str:
    """Lowercase and strip common punctuation/markers."""
    text = text.lower()
    for char in "¿?!.,;:":
        text = text.replace(char, " ")
    return " ".join(text.split())


def _normalize_text(text: str) -> str:
    """Strip punctuation and collapse whitespace while preserving casing."""
    for char in "¿?!.,;:":
        text = text.replace(char, " ")
    return " ".join(text.split())


def classify_area(text: str) -> str | None:
    """Return the first matching decision area or None."""
    cleaned = _clean_text(text)
    for area in VALID_AREAS:
        for keyword in AREA_KEYWORDS[area]:
            if keyword in cleaned:
                return area
    return None


def detect_horizon(text: str) -> str | None:
    """Return the first matching horizon or None."""
    cleaned = _clean_text(text)
    for horizon in VALID_HORIZONS:
        for keyword in HORIZON_KEYWORDS[horizon]:
            if keyword in cleaned:
                return horizon
    return None


def normalize_decision_text(text: str) -> str:
    """Convert a question into a concise decision statement."""
    cleaned = _normalize_text(text)

    # Drop leading intent words that do not add decision content (case-insensitive).
    prefixes = [
        "debería ",
        "debo ",
        "quiero ",
        "necesito ",
        "cómo ",
        "cuál es ",
        "cuál ",
    ]
    lower = cleaned.lower()
    for prefix in prefixes:
        if lower.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
            lower = cleaned.lower()
            break

    # Specific normalizations derived from examples.
    cleaned = cleaned.replace("para ventas", "en ventas")

    return cleaned.strip()


def _looks_like_decision(text: str) -> bool:
    """True if the text contains a concrete decision verb."""
    cleaned = _clean_text(text)
    return any(verb in cleaned for verb in DECISION_VERBS)


def generate_outcome(decision: str | None, area: str | None) -> str | None:
    """Generate an expected outcome from a decision and its area."""
    if not area:
        return None

    decision_clean = _clean_text(decision or "")
    if area == "people" and "contratar" in decision_clean:
        return "cubrir la vacante y mejorar cobertura comercial"

    return GENERIC_OUTCOMES.get(area)


def build_draft(question: str) -> dict[str, Any]:
    """Build a decision sheet from a free-form question."""
    decision = None
    if _looks_like_decision(question):
        decision = normalize_decision_text(question) or None

    area = classify_area(question)
    # Only infer horizon/outcome once we have a concrete decision to anchor them.
    horizon = detect_horizon(question) if decision else None
    outcome = generate_outcome(decision, area) if decision else None

    return {
        "decision": decision,
        "area": area,
        "horizon": horizon,
        "outcome": outcome,
    }


def needs_clarification(draft: dict[str, Any]) -> bool:
    """True if any critical field is missing."""
    return any(
        draft.get(field) is None for field in ["decision", "area", "horizon", "outcome"]
    )


def build_clarification(draft: dict[str, Any]) -> str:
    """Ask a single clarification question for the first missing field."""
    if draft.get("decision") is None:
        area = draft.get("area")
        if area:
            return (
                f"¿Qué quieres decidir sobre {area}? "
                "Descríbelo en una frase (por ejemplo: 'contratar a alguien', 'reducir días de cobro')."
            )
        return "¿Sobre qué área o decisión quieres que trabajemos?"

    if draft.get("area") is None:
        return (
            "¿A cuál área pertenece esta decisión: People, Strategy, Execution o Cash?"
        )

    if draft.get("horizon") is None:
        return (
            "¿En qué horizonte quieres tomar esta decisión: "
            "inmediato, corto, medio o largo?"
        )

    if draft.get("outcome") is None:
        return "¿Qué resultado esperas lograr con esta decisión?"

    return "¿Puedes aclarar un poco más sobre esta decisión?"


def apply_correction(
    draft: dict[str, Any], corrections: dict[str, Any]
) -> dict[str, Any]:
    """Return a new draft with corrections applied."""
    updated = dict(draft)
    for key, value in corrections.items():
        if key in updated:
            updated[key] = value
    return updated


def validate_draft(draft: dict[str, Any]) -> list[str]:
    """Validate a confirmed draft and return human-readable errors."""
    errors = []
    for field in ["decision", "area", "horizon", "outcome"]:
        if not draft.get(field):
            errors.append(f"Missing required field: {field}")

    area = draft.get("area")
    if area and area not in VALID_AREAS:
        errors.append(f"Invalid area: {area}. Must be one of {VALID_AREAS}")

    horizon = draft.get("horizon")
    if horizon and horizon not in VALID_HORIZONS:
        errors.append(f"Invalid horizon: {horizon}. Must be one of {VALID_HORIZONS}")

    return errors
