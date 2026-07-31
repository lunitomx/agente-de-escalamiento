"""
Selector module — choose the best Scaling Up analysis tool for a confirmed
decision and its evidence package.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from coaching.core import read_yaml
from coaching.evidence.models import DecisionRef, EvidencePackage

from .engine import select_tool

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


def run(context: dict[str, Any]) -> dict[str, Any]:
    """
    Select the best analysis tool for the current decision and evidence.

    Context keys:
        - base_path: str (default: '.')
        - decision: dict (optional, overrides profile)
        - package: dict (EvidencePackage produced by S43.2)
        - package_summary: dict (optional, ignored for selection logic)

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
                "No se recibió un paquete de evidencia. "
                "Ejecuta /escala-evidence primero para armar el paquete de evidencia."
            ],
        }

    # Ensure the package decision_ref matches the active decision loaded from
    # context or profile; otherwise trust the package.
    if decision is not None:
        package = package.model_copy(update={"decision_ref": decision})

    result = select_tool(package)

    return {
        "output": result.output,
        "artifacts": {
            "action": result.action,
            "receipt": result.receipt.model_dump(),
            "questions": result.questions,
        },
        "errors": [],
    }


def _main() -> None:
    """Minimal module entry point for ``python -m coaching.selector``."""
    import json
    import sys

    from coaching.core import load_context

    context = load_context()
    result = run(context)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(1 if result.get("errors") else 0)
