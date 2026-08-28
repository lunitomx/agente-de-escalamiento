"""Regression tests for narrative-first progress dashboards."""

from __future__ import annotations

from coaching.core import write_yaml
from coaching.progress import run


def _write_registry(base_path) -> None:
    write_yaml(
        base_path / ".escala" / "knowledge" / "registry" / "worksheets.yaml",
        {
            "worksheets": [
                {
                    "id": "cash-ccc",
                    "name": "Cash Conversion Cycle",
                    "decision": "cash",
                    "difficulty": "M",
                    "time_estimate": "45 min",
                },
                {
                    "id": "people-face",
                    "name": "Function Accountability",
                    "decision": "people",
                },
            ]
        },
    )


def test_progress_uses_confirmed_narrative_focus_without_scores(tmp_path) -> None:
    _write_registry(tmp_path)
    write_yaml(
        tmp_path / ".escala" / "agent" / "memory" / "company-profile.yaml",
        {
            "narrative_assessment": {
                "company_summary": "La empresa cobra tarde después de entregar.",
                "confirmation_status": "confirmed",
                "proposed_focuses": [
                    {
                        "decision": "cash",
                        "rationale": "El ciclo de cobro es el dolor declarado.",
                    }
                ],
            }
        },
    )

    result = run({"base_path": str(tmp_path)})

    assert result["errors"] == []
    assert "Assessment narrativo" in result["output"]
    assert "Cash Conversion Cycle" in result["output"]
    assert result["artifacts"]["focus_source"] == "narrative"


def test_progress_keeps_pending_assessment_visible_without_auto_route(tmp_path) -> None:
    _write_registry(tmp_path)
    write_yaml(
        tmp_path / ".escala" / "agent" / "memory" / "company-profile.yaml",
        {
            "narrative_assessment": {
                "company_summary": "La empresa todavía aclara su problema.",
                "confirmation_status": "pending",
                "proposed_focuses": [{"decision": "cash", "rationale": "Pendiente."}],
            }
        },
    )

    result = run({"base_path": str(tmp_path)})

    assert result["errors"] == []
    assert "Confirma o corrige el assessment" in result["output"]
    assert result["artifacts"]["focus_source"] is None
