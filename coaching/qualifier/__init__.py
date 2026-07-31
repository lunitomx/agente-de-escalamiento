"""
Qualifier module — run the reliable coaching loop against positive and negative
cases for all four decisions.
"""

from __future__ import annotations

from typing import Any

from .cases import ALL_CASES
from .runner import run_case


def qualify(context: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Run all qualification cases and report results.

    Context is optional and currently ignored; cases are defined in code.
    """
    results: list[dict[str, Any]] = []
    passed = 0
    failed = 0

    for case in ALL_CASES:
        outcome = run_case(case.decision, case.package)
        responder_action = (
            outcome.get("responder", {}).get("artifacts", {}).get("action")
        )
        success = responder_action == case.expected_action
        if success:
            passed += 1
        else:
            failed += 1

        results.append(
            {
                "case_id": case.case_id,
                "area": case.area,
                "description": case.description,
                "expected_action": case.expected_action,
                "actual_action": responder_action,
                "success": success,
                "selector_action": outcome.get("selector", {})
                .get("artifacts", {})
                .get("action"),
                "reviewer_action": outcome.get("reviewer", {})
                .get("artifacts", {})
                .get("action"),
            }
        )

    return {
        "output": _format_summary(passed, failed, results),
        "artifacts": {
            "action": "qualification_complete",
            "passed": passed,
            "failed": failed,
            "results": results,
        },
        "errors": [],
    }


def _format_summary(passed: int, failed: int, results: list[dict[str, Any]]) -> str:
    lines = [
        "## Calificación del ciclo de coaching confiable",
        "",
        f"**Pasaron:** {passed}  ",
        f"**Fallaron:** {failed}  ",
        "",
        "| Caso | Área | Esperado | Real | Estado |",
        "|------|------|----------|------|--------|",
    ]
    for result in results:
        status = "✅" if result["success"] else "❌"
        lines.append(
            f"| {result['case_id']} | {result['area']} | "
            f"{result['expected_action']} | {result['actual_action']} | {status} |"
        )
    lines.append("")
    if failed:
        lines.append("Revisar los casos marcados con ❌ antes de cerrar E43.")
    else:
        lines.append(
            "Todos los casos pasaron. El ciclo es confiable en las cuatro decisiones."
        )
    lines.append("")
    return "\n".join(lines)


def _main() -> None:
    """Minimal module entry point for ``python -m coaching.qualifier``."""
    import json
    import sys

    result = qualify({})
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["artifacts"]["failed"] == 0 else 1)
