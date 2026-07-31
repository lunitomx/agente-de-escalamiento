"""
Responder module — generate the five-block executive response for a reviewed
decision.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from coaching.core import read_yaml
from coaching.evidence.models import DecisionRef, EvidencePackage
from coaching.reviewer.models import ReviewReport
from coaching.selector.models import SelectionReceipt

from .engine import build_response
from .formatter import format_response

PROFILE_REL_PATH = Path(".escala") / "agent" / "memory" / "company-profile.yaml"


def _profile_path(base: Path) -> Path:
    return base / PROFILE_REL_PATH


def _load_decision(base: Path) -> DecisionRef | None:
    """Load the confirmed decision from the company profile."""
    profile = read_yaml(_profile_path(base))
    focus = profile.get("focus") or {}
    current = focus.get("current_decision")
    if not isinstance(current, dict) or not current.get("decision"):
        return None
    try:
        return DecisionRef(
            decision=current["decision"],
            area=current["area"],
            horizon=current["horizon"],
            outcome=current["outcome"],
        )
    except Exception:
        return None


def _decision_from_context(context: dict[str, Any]) -> DecisionRef | None:
    """Build a DecisionRef from an explicit decision dict in context."""
    decision = context.get("decision")
    if not isinstance(decision, dict):
        return None
    try:
        return DecisionRef(
            decision=decision["decision"],
            area=decision["area"],
            horizon=decision["horizon"],
            outcome=decision["outcome"],
        )
    except Exception:
        return None


def _package_from_context(context: dict[str, Any]) -> EvidencePackage | None:
    """Build an EvidencePackage from a package dict in context."""
    package = context.get("package")
    if not isinstance(package, dict):
        return None
    try:
        return EvidencePackage(**package)
    except Exception:
        return None


def _selection_from_context(context: dict[str, Any]) -> SelectionReceipt | None:
    """Build a SelectionReceipt from a selection dict in context."""
    selection = context.get("selection")
    if not isinstance(selection, dict):
        return None
    receipt = selection.get("receipt") or selection
    try:
        return SelectionReceipt(**receipt)
    except Exception:
        return None


def _review_from_context(context: dict[str, Any]) -> ReviewReport | None:
    """Build a ReviewReport from a review dict in context."""
    review = context.get("review")
    if not isinstance(review, dict):
        return None
    report = review.get("report") or review
    try:
        return ReviewReport(**report)
    except Exception:
        return None


def run(context: dict[str, Any]) -> dict[str, Any]:
    """
    Generate the five-block executive response.

    Context keys:
        - base_path: str (default: '.')
        - decision: dict (optional, overrides profile)
        - package: dict (EvidencePackage from S43.2)
        - selection: dict (SelectionResult from S43.3)
        - review: dict (ReviewResult from S43.4)

    Returns:
        dict with output, artifacts, errors
    """
    base = Path(context.get("base_path", "."))

    decision = _decision_from_context(context) or _load_decision(base)
    if decision is None:
        return {
            "output": "",
            "artifacts": {},
            "errors": [
                "No hay una decisión confirmada. "
                "Ejecuta /escala-decision primero para aclarar la decisión."
            ],
        }

    package = _package_from_context(context)
    if package is None:
        return {
            "output": "",
            "artifacts": {},
            "errors": [
                "No se recibió un paquete de evidencia. Ejecuta /escala-evidence primero."
            ],
        }

    selection = _selection_from_context(context)
    if selection is None:
        return {
            "output": "",
            "artifacts": {},
            "errors": [
                "No se recibió un recibo de selección. Ejecuta /escala-selector primero."
            ],
        }

    review_report = _review_from_context(context)
    if review_report is None:
        return {
            "output": "",
            "artifacts": {},
            "errors": [
                "No se recibió un informe de revisión. Ejecuta /escala-reviewer primero."
            ],
        }

    if _decision_from_context(context) is not None:
        package = package.model_copy(update={"decision_ref": decision})

    response = build_response(decision, package, selection, review_report)

    return {
        "output": format_response(response),
        "artifacts": {
            "action": "responded" if response.can_proceed else "blocked",
            "response": response.model_dump(),
        },
        "errors": [],
    }


def _main() -> None:
    """Minimal module entry point for ``python -m coaching.responder``."""
    import json
    import sys

    from coaching.core import load_context

    context = load_context()
    result = run(context)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(1 if result.get("errors") else 0)
