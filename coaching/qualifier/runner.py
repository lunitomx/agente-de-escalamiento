"""coaching.qualifier.runner — execute the full coaching loop for a case.

No I/O. Orchestrates selector, reviewer and responder using the existing
production modules.
"""

from __future__ import annotations

from typing import Any

from coaching.evidence.models import DecisionRef, EvidencePackage
from coaching.responder import run as responder_run
from coaching.reviewer import run as reviewer_run
from coaching.selector import run as selector_run


def _selector_context(
    decision: DecisionRef, package: EvidencePackage
) -> dict[str, Any]:
    return {
        "base_path": ".",
        "decision": decision.model_dump(),
        "package": package.model_dump(),
    }


def _reviewer_context(
    decision: DecisionRef,
    package: EvidencePackage,
    selection: dict[str, Any],
) -> dict[str, Any]:
    return {
        "base_path": ".",
        "decision": decision.model_dump(),
        "package": package.model_dump(),
        "selection": selection,
    }


def _responder_context(
    decision: DecisionRef,
    package: EvidencePackage,
    selection: dict[str, Any],
    review: dict[str, Any],
) -> dict[str, Any]:
    return {
        "base_path": ".",
        "decision": decision.model_dump(),
        "package": package.model_dump(),
        "selection": selection,
        "review": review,
    }


def run_case(decision: DecisionRef, package: EvidencePackage) -> dict[str, Any]:
    """Run the full coaching loop for a single decision and package."""
    selector_result = selector_run(_selector_context(decision, package))
    if selector_result.get("errors"):
        return {"selector": selector_result, "reviewer": {}, "responder": {}}

    reviewer_result = reviewer_run(
        _reviewer_context(decision, package, selector_result["artifacts"])
    )
    if reviewer_result.get("errors"):
        return {
            "selector": selector_result,
            "reviewer": reviewer_result,
            "responder": {},
        }

    responder_result = responder_run(
        _responder_context(
            decision,
            package,
            selector_result["artifacts"],
            reviewer_result["artifacts"],
        )
    )

    return {
        "selector": selector_result,
        "reviewer": reviewer_result,
        "responder": responder_result,
    }
