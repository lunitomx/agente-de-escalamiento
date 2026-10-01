"""Tests for the coaching.decision module."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent.parent))

from coaching.decision.engine import (
    apply_correction,
    build_clarification,
    build_draft,
    classify_area,
    detect_horizon,
    generate_outcome,
    needs_clarification,
    normalize_decision_text,
    validate_draft,
)
from coaching.decision.formatter import (
    format_clarification,
    format_confirmed,
    format_draft,
)


class TestClassifyArea:
    def test_people_from_contratar(self):
        assert classify_area("¿Debería contratar a María para ventas?") == "people"

    def test_cash_from_cash(self):
        assert classify_area("Necesito mejorar el cash") == "cash"

    def test_strategy_keyword(self):
        assert (
            classify_area("¿Cómo diferenciamos nuestra estrategia de marca?")
            == "strategy"
        )

    def test_execution_keyword(self):
        assert classify_area("Necesito mejorar el proceso de KPIs") == "execution"

    def test_unknown_returns_none(self):
        assert classify_area("¿Cuál es el próximo paso?") is None


class TestDetectHorizon:
    def test_inmediato(self):
        assert detect_horizon("¿Debería contratar a María para ventas?") == "inmediato"

    def test_corto(self):
        assert detect_horizon("Plan para el próximo trimestre") == "corto"

    def test_medio(self):
        assert detect_horizon("Meta para este año") == "medio"

    def test_largo(self):
        assert detect_horizon("Visión a 5 años") == "largo"

    def test_unknown(self):
        assert detect_horizon("Necesito mejorar el cash") is None


class TestNormalizeDecisionText:
    def test_removes_question_marks_and_prefix(self):
        assert (
            normalize_decision_text("¿Debería contratar a María para ventas?")
            == "contratar a María en ventas"
        )


class TestGenerateOutcome:
    def test_people_contratar(self):
        assert (
            generate_outcome("contratar a María en ventas", "people")
            == "cubrir la vacante y mejorar cobertura comercial"
        )

    def test_generic_cash(self):
        assert (
            generate_outcome("reducir días de cobro", "cash")
            == "mejorar la salud de cash flow"
        )

    def test_generic_strategy(self):
        assert (
            generate_outcome("definir OPSP", "strategy")
            == "alinear la estrategia de la empresa"
        )

    def test_generic_execution(self):
        assert (
            generate_outcome("implementar KPIs", "execution")
            == "mejorar la disciplina de ejecución"
        )

    def test_missing_area(self):
        assert generate_outcome("algo", None) is None


class TestBuildDraft:
    def test_clear_question(self):
        draft = build_draft("¿Debería contratar a María para ventas?")
        assert draft == {
            "decision": "contratar a María en ventas",
            "area": "people",
            "horizon": "inmediato",
            "outcome": "cubrir la vacante y mejorar cobertura comercial",
        }

    def test_ambiguous_area_known(self):
        draft = build_draft("Necesito mejorar el cash")
        assert draft["area"] == "cash"
        assert draft["decision"] is None
        assert draft["horizon"] is None
        assert draft["outcome"] is None

    def test_totally_ambiguous(self):
        draft = build_draft("¿Cuál es el próximo paso?")
        assert all(
            draft[field] is None for field in ["decision", "area", "horizon", "outcome"]
        )


class TestNeedsClarification:
    def test_complete_draft_false(self):
        assert not needs_clarification(
            {
                "decision": "x",
                "area": "people",
                "horizon": "inmediato",
                "outcome": "y",
            }
        )

    def test_incomplete_draft_true(self):
        assert needs_clarification(
            {"decision": None, "area": "cash", "horizon": None, "outcome": None}
        )


class TestBuildClarification:
    def test_asks_decision_first(self):
        question = build_clarification(
            {"decision": None, "area": "cash", "horizon": None, "outcome": None}
        )
        assert "cash" in question.lower()
        assert "decidir" in question.lower()

    def test_asks_area_when_decision_present(self):
        question = build_clarification(
            {
                "decision": "contratar a María",
                "area": None,
                "horizon": None,
                "outcome": None,
            }
        )
        assert "área" in question.lower() or "decisión" in question.lower()

    def test_asks_horizon_when_decision_and_area_present(self):
        question = build_clarification(
            {
                "decision": "reducir días de cobro",
                "area": "cash",
                "horizon": None,
                "outcome": "mejorar cash flow",
            }
        )
        assert "horizonte" in question.lower() or "plazo" in question.lower()


class TestApplyCorrection:
    def test_correct_area(self):
        draft = {
            "decision": "contratar a María en ventas",
            "area": "people",
            "horizon": "inmediato",
            "outcome": "cubrir la vacante y mejorar cobertura comercial",
        }
        corrected = apply_correction(draft, {"area": "execution"})
        assert corrected["area"] == "execution"
        assert corrected["decision"] == draft["decision"]


class TestValidateDraft:
    def test_valid(self):
        assert (
            validate_draft(
                {
                    "decision": "x",
                    "area": "people",
                    "horizon": "inmediato",
                    "outcome": "y",
                }
            )
            == []
        )

    def test_invalid_area(self):
        errors = validate_draft(
            {"decision": "x", "area": "moon", "horizon": "inmediato", "outcome": "y"}
        )
        assert any("area" in err.lower() for err in errors)

    def test_missing_field(self):
        errors = validate_draft(
            {"decision": None, "area": "people", "horizon": "inmediato", "outcome": "y"}
        )
        assert any("decision" in err.lower() for err in errors)


class TestFormatter:
    def test_format_draft_contains_fields(self):
        draft = {
            "decision": "contratar a María en ventas",
            "area": "people",
            "horizon": "inmediato",
            "outcome": "cubrir la vacante",
        }
        text = format_draft(draft)
        assert "contratar a María en ventas" in text
        assert "Tu equipo" in text  # S86.2: área en español
        assert "inmediato" in text

    def test_format_clarification(self):
        text = format_clarification("¿Qué quieres decidir?")
        assert "¿Qué quieres decidir?" in text

    def test_format_confirmed(self):
        text = format_confirmed(
            {"decision": "x", "area": "cash", "horizon": "inmediato", "outcome": "y"}
        )
        assert "confirmada" in text.lower()


class TestRun:
    def test_clear_question_returns_proposed_draft(self):
        from coaching.decision import run

        result = run(
            {
                "action": "question",
                "question": "¿Debería contratar a María para ventas?",
            }
        )
        assert result["errors"] == []
        assert "Ficha de decisión propuesta" in result["output"]
        assert result["artifacts"]["action"] == "propose"
        assert result["artifacts"]["draft"]["area"] == "people"

    def test_ambiguous_question_returns_clarification(self):
        from coaching.decision import run

        result = run({"action": "question", "question": "Necesito mejorar el cash"})
        assert result["errors"] == []
        assert "Antes de continuar" in result["output"]
        assert result["artifacts"]["action"] == "clarify"
        assert result["artifacts"]["draft"]["area"] == "cash"

    def test_confirm_persists_draft(self, tmp_path):
        from coaching.decision import run

        base = tmp_path
        draft = {
            "decision": "contratar a María en ventas",
            "area": "people",
            "horizon": "inmediato",
            "outcome": "cubrir la vacante y mejorar cobertura comercial",
        }
        result = run({"action": "confirm", "draft": draft, "base_path": str(base)})
        assert result["errors"] == []
        assert "confirmada" in result["output"].lower()

        profile = (
            base / ".escala" / "agent" / "memory" / "company-profile.yaml"
        ).read_text()
        assert "contratar a María en ventas" in profile
        assert "current_decision" in profile

    def test_correct_updates_draft(self):
        from coaching.decision import run

        draft = {
            "decision": "contratar a María en ventas",
            "area": "people",
            "horizon": "inmediato",
            "outcome": "cubrir la vacante y mejorar cobertura comercial",
        }
        result = run(
            {"action": "correct", "draft": draft, "corrections": {"area": "execution"}}
        )
        assert result["errors"] == []
        assert result["artifacts"]["draft"]["area"] == "execution"
        assert "Ficha de decisión propuesta" in result["output"]

    def test_missing_question_returns_error(self):
        from coaching.decision import run

        result = run({"action": "question"})
        assert result["errors"]
        assert "question" in result["errors"][0].lower()

    def test_invalid_action_returns_error(self):
        from coaching.decision import run

        result = run({"action": "unknown"})
        assert result["errors"]
        assert "action" in result["errors"][0].lower()

    def test_confirm_validates_incomplete_draft(self):
        from coaching.decision import run

        result = run(
            {
                "action": "confirm",
                "draft": {
                    "decision": "x",
                    "area": "people",
                    "horizon": None,
                    "outcome": "y",
                },
            }
        )
        assert result["errors"]
        assert any("horizon" in err.lower() for err in result["errors"])


class TestSkillAdapterSmoke:
    def test_skill_context_returns_expected_contract(self):
        """Simulate the JSON context the escala-decision skill sends."""
        from coaching.decision import run

        context = {
            "action": "question",
            "question": "¿Debería contratar a María para ventas?",
            "base_path": ".",
        }
        result = run(context)
        assert "output" in result
        assert "artifacts" in result
        assert "errors" in result
        assert result["errors"] == []
        assert result["artifacts"]["draft"]["area"] == "people"

    def test_skill_confirm_context_persists(self, tmp_path):
        from coaching.decision import run

        context = {
            "action": "confirm",
            "draft": {
                "decision": "reducir días de cobro",
                "area": "cash",
                "horizon": "corto",
                "outcome": "mejorar cash flow",
            },
            "base_path": str(tmp_path),
        }
        result = run(context)
        assert result["errors"] == []
        assert result["artifacts"]["action"] == "confirmed"
        assert (
            tmp_path / ".escala" / "agent" / "memory" / "company-profile.yaml"
        ).exists()
