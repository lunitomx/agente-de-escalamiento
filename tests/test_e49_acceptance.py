"""Synthetic E49 acceptance path; never uses network or real company data."""

from __future__ import annotations

from pathlib import Path

from coaching.diagnose import DiagnosticEvidence, build_diagnostic_intake
from coaching.export import run_diagnostic
from coaching.welcome import WelcomeState, begin_welcome, respond_to_welcome


def test_e49_synthetic_path_reaches_local_explainable_result(tmp_path: Path) -> None:
    first = begin_welcome()
    routed = respond_to_welcome(
        first.state, "Mis ventas bajaron y necesito entender mi cash este mes."
    )
    assert routed.state.area == "cash"
    assert routed.state.next_action == "evidence"

    intake = build_diagnostic_intake(
        company={"name": "Synthetic Demo", "employees": 6},
        evidence=[
            DiagnosticEvidence(
                evidence_id="cash_q1",
                question_id="cash_q1",
                decision="cash",
                value=2,
                source_kind="conversation",
                source_ref="conversation:welcome",
                freshness="current",
                confidence="high",
                rationale="El ciclo de cobro no está medido.",
            ),
            DiagnosticEvidence(
                evidence_id="cash_q2",
                question_id="cash_q2",
                decision="cash",
                value=3,
                source_kind="estimate",
                source_ref="estimate:user",
                answer_status="estimate",
                freshness="unknown",
                confidence="medium",
                rationale="Estimación del usuario.",
            ),
        ],
        funnel={"prospects": 20, "conversations": 8, "proposals": 4, "wins": 2},
        open_context={"obstacle": "No hay una cadencia de caja"},
    )
    result = run_diagnostic(
        {
            "base_path": str(tmp_path),
            "intake": intake.model_dump(mode="json"),
            "generated_at": "2026-08-19",
        }
    )

    assert result["errors"] == []
    markdown = Path(result["artifacts"]["diagnostic_path"])
    payload = Path(result["artifacts"]["diagnostic_json_path"])
    assert markdown.exists()
    assert payload.exists()
    text = markdown.read_text(encoding="utf-8")
    assert "cash_q1" in text
    assert "Ruta de 90 días" in text
    assert "http://" not in text
    assert "https://" not in text


def test_e49_welcome_state_is_serializable() -> None:
    state = WelcomeState(phase="concern")

    assert state.model_dump(mode="json")["phase"] == "concern"


def test_e49_skill_guidance_names_the_contract() -> None:
    root = Path(__file__).resolve().parents[1]
    welcome = (root / "escala-skills/escala-welcome/SKILL.md").read_text(
        encoding="utf-8"
    )
    diagnose = (root / "escala-skills/escala-diagnose/SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "dos velocidades" in welcome
    assert "not_applicable" in diagnose
    assert "Markdown + JSON" in diagnose
