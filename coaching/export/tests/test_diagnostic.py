"""Tests for local E49 diagnostic artifacts."""

from __future__ import annotations

from pathlib import Path

from coaching.diagnose import DiagnosticEvidence, DiagnosticIntake
from coaching.export.diagnostic import render_diagnostic_result
from coaching.export import run_diagnostic


def _intake() -> DiagnosticIntake:
    return DiagnosticIntake(
        company={"name": "Demo"},
        evidence=[
            DiagnosticEvidence(
                evidence_id="execution_q1",
                question_id="execution_q1",
                decision="execution",
                value=2,
                source_kind="conversation",
                source_ref="conversation:welcome",
                freshness="current",
                confidence="high",
                rationale="No hay ritmo semanal.",
            )
        ],
    )


def test_run_diagnostic_writes_markdown_and_json(tmp_path: Path) -> None:
    result = run_diagnostic(
        {"base_path": str(tmp_path), "intake": _intake().model_dump(mode="json")}
    )

    assert result["errors"] == []
    markdown_path = Path(result["artifacts"]["diagnostic_path"])
    json_path = Path(result["artifacts"]["diagnostic_json_path"])
    assert markdown_path.exists()
    assert json_path.exists()
    content = markdown_path.read_text(encoding="utf-8")
    assert "## Evidencia del foco" in content
    assert "execution_q1" in content
    assert "## Ruta de 90 días" in content


def test_renderer_has_score_coverage_and_confidence() -> None:
    from coaching.diagnose import score_diagnostic
    from coaching.diagnose.result import build_diagnostic_result

    result = build_diagnostic_result(_intake(), score_diagnostic(_intake()))
    markdown = render_diagnostic_result(result)

    assert "Cobertura" in markdown
    assert "Confianza" in markdown
    assert "execution_q1" in markdown
