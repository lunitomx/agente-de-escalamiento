"""coaching.selector.engine — pure tool-selection logic.

No I/O. Accepts an EvidencePackage and returns a SelectionResult with a
traceable receipt.
"""

from __future__ import annotations

from coaching.evidence.models import EvidencePackage, EvidenceSource

from .formatter import format_clarify, format_selection
from .models import SelectionReceipt, SelectionResult, ToolSelection

TOOL_CATALOG: dict[str, ToolSelection] = {
    "cash": ToolSelection(
        tool="cash_analysis",
        label="Cash Analysis",
        skills=["/escala-cash", "/escala-cash-ccc", "/escala-cash-power1"],
    ),
    "execution": ToolSelection(
        tool="execution_rhythms",
        label="Execution Rhythms",
        skills=[
            "/escala-execution",
            "/escala-execution-rhythms",
            "/escala-execution-priorities",
        ],
    ),
    "people": ToolSelection(
        tool="people_analysis",
        label="People Analysis",
        skills=[
            "/escala-people",
            "/escala-people-fac",
            "/escala-people-values",
        ],
    ),
    "strategy": ToolSelection(
        tool="strategy_analysis",
        label="Strategy Analysis",
        skills=[
            "/escala-strategy",
            "/escala-strategy-opsp",
            "/escala-strategy-7strata",
        ],
    ),
}

# Source-type and title-keyword patterns that count as minimum evidence for each
# area. Keeping the mapping explicit makes the heuristic deterministic and easy
# to extend for People and Strategy without changing select_tool's signature.
EVIDENCE_PATTERNS: dict[str, dict[str, list[str]]] = {
    "cash": {
        "source_types": ["worksheet", "metric"],
        "title_keywords": [
            "cash",
            "cobro",
            "finanzas",
            "ccc",
            "power of one",
            "aceleración",
            "aceleracion",
        ],
    },
    "execution": {
        "source_types": ["session_log", "task"],
        "title_keywords": [
            "sesión",
            "sesion",
            "reunión",
            "reunion",
            "huddle",
            "prioridad",
            "ritmo",
            "kpi",
        ],
    },
    "people": {
        "source_types": ["worksheet"],
        "title_keywords": [
            "face",
            "topgrading",
            "values",
            "facchart",
            "people",
        ],
    },
    "strategy": {
        "source_types": ["worksheet"],
        "title_keywords": [
            "opsp",
            "7 strata",
            "strata",
            "swot",
            "strategy",
            "estrategia",
        ],
    },
}

_AREA_EVIDENCE_LABEL: dict[str, str] = {
    "cash": "workbook financiero",
    "execution": "registros de reuniones/prioridades",
    "people": "worksheets de People",
    "strategy": "worksheets de Strategy",
}


def _normalize(text: str) -> str:
    """Lowercase and remove accents for simple matching."""
    return (
        text.lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )


def _source_matches_area_evidence(source: EvidenceSource, area: str) -> bool:
    """Return True when an available source matches the area evidence pattern."""
    if source.status != "available":
        return False

    patterns = EVIDENCE_PATTERNS.get(area)
    if not patterns:
        return False

    if source.source_type in patterns["source_types"]:
        return True

    normalized_title = _normalize(source.title)
    return any(
        _normalize(keyword) in normalized_title
        for keyword in patterns["title_keywords"]
    )


def _selection_reason(area: str) -> str:
    label = _AREA_EVIDENCE_LABEL.get(area, f"evidencia para {area}")
    return f"Área {area.title()} con {label} disponible."


def _clarify_reason(area: str) -> str:
    return f"No hay evidencia mínima disponible para el área {area.title()}."


def select_tool(package: EvidencePackage) -> SelectionResult:
    """Select the best analysis tool for a decision given its evidence package."""
    area = package.decision_ref.area
    decision = package.decision_ref.decision
    tool = TOOL_CATALOG.get(area)

    matching_sources = [
        source
        for source in package.sources
        if _source_matches_area_evidence(source, area)
    ]

    if matching_sources and tool is not None:
        evidence_used = [source.source_id for source in matching_sources]
        reason = _selection_reason(area)
        receipt = SelectionReceipt(
            area=area,
            decision=decision,
            tool=tool.tool,
            label=tool.label,
            skills=tool.skills,
            evidence_used=evidence_used,
            reason=reason,
            missing_minimum=False,
        )
        return SelectionResult(
            action="tool_selected",
            receipt=receipt,
            output=format_selection(receipt, package),
        )

    questions = list(package.questions)
    if not questions:
        questions.append(
            f"¿Tienes disponible la evidencia mínima para analizar una decisión de {area.title()}?"
        )

    receipt = SelectionReceipt(
        area=area,
        decision=decision,
        tool=None,
        label=None,
        skills=[],
        evidence_used=[],
        reason=_clarify_reason(area),
        missing_minimum=True,
    )
    return SelectionResult(
        action="clarify",
        receipt=receipt,
        output=format_clarify(receipt, questions, package),
        questions=questions,
    )
