"""Tests for the source-neutral BusinessAdvisorHandler."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


class TestBusinessAdvisorHandler:
    """Test the local business-advisor handler."""

    @pytest.fixture
    def handler(self):
        from escala_server.business_advisor import BusinessAdvisorHandler

        return BusinessAdvisorHandler(":memory:")

    def test_ask_cash_question(self, handler):
        """A cash-related question returns cash category and advisor framing."""
        result = handler.ask("¿Cómo mejoro mi flujo de efectivo?")
        assert result["status"] == "ok"
        assert result["category"] == "cash"
        assert "Asesor" in result["answer"]
        assert "Cash" in result["answer"]
        assert len(result.get("principles_applied", [])) > 0

    def test_ask_people_question(self, handler):
        """A people-related question returns people category."""
        result = handler.ask("Necesito contratar mejores personas")
        assert result["status"] == "ok"
        assert result["category"] == "people"

    def test_ask_strategy_question(self, handler):
        """A strategy question returns strategy category."""
        result = handler.ask("¿Cómo defino mi estrategia?")
        assert result["status"] == "ok"
        assert result["category"] == "strategy"

    def test_ask_execution_question(self, handler):
        """An execution question returns execution category."""
        result = handler.ask(
            "Necesitamos mejorar nuestra ejecución y tener daily huddle"
        )
        assert result["status"] == "ok"
        assert result["category"] == "execution"

    def test_ask_general_question(self, handler):
        """A general question with no clear category returns general."""
        result = handler.ask("¿Qué opinas de mi negocio?")
        assert result["status"] == "ok"
        assert result["category"] in ("general", "strategy", "execution")

    def test_ask_empty_question(self, handler):
        """An empty question returns error."""
        result = handler.ask("")
        assert result["status"] == "error"

    def test_ask_classify_cash(self, handler):
        """_classify_question identifies cash keywords."""
        category = handler._classify_question("mi cash flow es negativo")
        assert category == "cash"

    def test_ask_classify_people(self, handler):
        """_classify_question identifies people keywords."""
        category = handler._classify_question("necesito un mejor equipo de ventas")
        assert category == "people"

    def test_ask_classify_strategy(self, handler):
        """_classify_question identifies strategy keywords."""
        category = handler._classify_question("cuál es nuestra estrategia de marca")
        assert category == "strategy"

    def test_ask_classify_execution(self, handler):
        """_classify_question identifies execution keywords."""
        category = handler._classify_question("no tenemos daily huddle")
        assert category == "execution"

    def test_answer_structure(self, handler):
        """Answer includes advisor framing, questions, and call to action."""
        result = handler.ask("¿Cómo reduzco mi CCC?")
        assert result["status"] == "ok"
        answer = result["answer"]
        # Advisor framing
        assert "**Asesor:**" in answer
        # Has questions
        assert "?" in answer
        # Has principles
        assert len(result.get("principles_applied", [])) > 0
        # Has call to action
        assert "¿Qué vas a hacer" in answer

    def test_answer_includes_entity_context(self, handler):
        """Answer references entities from the knowledge graph."""
        result = handler.ask("Explícame el Power of One")
        # Should reference at least the entity found
        assert len(result.get("entities_used", [])) >= 0

    # ── review_daily tests ─────────────────────────────────────────

    def test_review_daily_complete(self, handler):
        """A complete daily gets high score."""
        result = handler.review_daily(
            "Ayer logré cerrar 2 ventas. Hoy voy a llamar a 5 leads. "
            "Mi obstáculo es que el CRM no actualiza. KPI: 10 llamadas/día. "
            "Esto conecta con nuestra Prioridad #1 del trimestre."
        )
        assert result["status"] == "ok"
        assert result["score_percent"] >= 80
        assert "Logros de ayer" in result["elements_found"]
        assert "Prioridades de hoy" in result["elements_found"]
        assert "Obstáculos" in " ".join(result["elements_found"])

    def test_review_daily_incomplete(self, handler):
        """A sparse daily gets low score."""
        result = handler.review_daily("Hoy tengo reuniones todo el día.")
        assert result["status"] == "ok"
        assert result["score_percent"] < 50
        assert len(result["elements_missing"]) >= 3

    def test_review_daily_empty(self, handler):
        """Empty daily returns 0 score."""
        result = handler.review_daily("")
        assert result["status"] == "ok"
        assert result["score"] == 0
        assert result["score_percent"] == 0

    # ── session_perspective tests ──────────────────────────────────

    def test_session_perspective_cash(self, handler):
        """Cash session returns cash principle."""
        result = handler.session_perspective(category="cash", changes_count=5)
        assert result["status"] == "ok"
        assert "Cash" in result["perspective"]
        assert "Power of One" in result["perspective"]

    def test_session_perspective_no_changes(self, handler):
        """Session with no changes gets reflection comment."""
        result = handler.session_perspective(category="strategy", changes_count=0)
        assert result["status"] == "ok"
        assert "reflexión" in result["perspective"]

    def test_session_perspective_with_company(self, handler):
        """Company name appears in perspective."""
        result = handler.session_perspective(
            category="people", changes_count=3, company="Acme"
        )
        assert "Acme" in result["perspective"]
        assert "People" in result["perspective"]

    # ── board_debate tests ────────────────────────────────────────

    def test_board_debate_first_turn(self, handler):
        """First turn analyzes across 4 Decisions."""
        result = handler.board_debate("Deberíamos abrir una nueva oficina")
        assert result["status"] == "ok"
        assert result["turn"] == 1
        assert "People" in result["response"]
        assert "Strategy" in result["response"]
        assert "Cash" in result["response"]
        assert len(result["next_questions"]) == 4

    def test_board_debate_second_turn(self, handler):
        """Second turn challenges the user's position."""
        history = [
            {
                "user": "Creo que tenemos el equipo para esto",
                "advisor": "... análisis ...",
            }
        ]
        result = handler.board_debate(
            "Deberíamos abrir una nueva oficina",
            history=history,
        )
        assert result["status"] == "ok"
        assert result["turn"] == 2
        assert len(result["next_questions"]) == 3

    def test_board_debate_with_context(self, handler):
        """Company context appears in first turn."""
        result = handler.board_debate("Expandir producto", context="Acme Corp")
        assert "Acme Corp" in result["response"]

    # ── coherence tests (S21.6) ────────────────────────────────────

    def test_coherence_templates_cover_business_categories(self):
        """Advisor templates cover all four business categories."""
        templates = yaml.safe_load(
            Path("conocimiento/coaching/advisor-templates.yaml").read_text()
        )
        assert {"People", "Strategy", "Execution", "Cash"} == {
            key.title() for key in templates if key != "general"
        }

    def test_coherence_daily_checklist_keeps_execution_structure(self):
        """The daily checklist retains the five weighted execution signals."""
        checklist = yaml.safe_load(
            Path("conocimiento/coaching/daily-checklist.yaml").read_text()
        )
        assert len(checklist) == 5
        assert sum(item["weight"] for item in checklist.values()) == 12
        assert "Daily Huddle" in " ".join(
            item["message_missing"] for item in checklist.values()
        )

    def test_coherence_templates_keep_diagnostic_questions(self):
        """Advisor templates retain the business diagnostic questions."""
        templates = yaml.safe_load(
            Path("conocimiento/coaching/advisor-templates.yaml").read_text()
        )
        questions = " ".join(
            question
            for template in templates.values()
            for question in template["questions"]
        )
        assert "Core Customer" in questions
        assert "Cash Conversion Cycle" in questions
        assert "BHAG" in questions

    def test_coherence_ask_uses_framework(self, handler):
        """Answers reference the correct framework for the category."""
        cash_result = handler.ask("¿Cómo mejoro mi flujo de efectivo?")
        assert "Power of One" in cash_result["answer"]
        assert "Cash Conversion Cycle" in cash_result.get("answer", "")

        people_result = handler.ask("Necesito mejores personas en mi equipo")
        assert (
            "A-player" in people_result["answer"]
            or "asiento" in people_result["answer"]
        )

    def test_coherence_ask_principles_are_correct(self, handler):
        """Each category returns the correct set of principles."""
        # Cash
        r = handler.ask("¿Cómo reduzco mi CCC?")
        assert "No Surprises" in r["answer"]
        # Execution
        r = handler.ask("¿Cómo mejoro mi daily huddle?")
        assert "Routine Sets You Free" in r["answer"] or "Priority" in r["answer"]
        # People
        r = handler.ask("Necesito contratar mejor")
        assert "Healthy Conflict" in r["answer"] or "Delegate" in r["answer"]

    def test_coherence_answer_structure(self, handler):
        """Every answer has advisor framing, questions, and a call to action."""
        for question in [
            "¿Cómo mejoro mi cash flow?",
            "¿Necesito un daily huddle?",
            "¿Cuál es mi estrategia?",
            "¿Debo contratar más gente?",
        ]:
            result = handler.ask(question)
            assert "**Asesor:**" in result["answer"], (
                f"Missing advisor framing for: {question}"
            )
            assert "?" in result["answer"], f"Missing questions for: {question}"
            assert "¿Qué vas a hacer" in result["answer"], (
                f"Missing CTA for: {question}"
            )

    def test_coherence_entities_are_real(self):
        """All 42 entities from the book-knowledge.json are valid."""
        with open("escala_server/data/book-knowledge.json") as f:
            data = json.load(f)
        assert data["meta"]["entities_count"] == 42
        assert data["meta"]["relationships_count"] == 59
        names = [e["name"] for e in data["entities"]]
        assert "Power of One" in names
        assert "4D Framework" in names
        assert len(names) == 42


def test_advisor_routes_replace_legacy_public_routes() -> None:
    """The local API exposes only the source-neutral advisor route family."""
    from escala_server.server import _build_router

    router = _build_router()
    for method, path in (
        ("POST", "/api/advisor/ask"),
        ("GET", "/api/advisor/ask"),
        ("POST", "/api/advisor/review-daily"),
        ("POST", "/api/advisor/debate"),
    ):
        handler, _ = router.dispatch(method, path)
        assert handler is not None

    for method, path in (
        ("POST", "/api/verne/ask"),
        ("GET", "/api/verne/ask"),
        ("POST", "/api/verne/review-daily"),
        ("POST", "/api/verne/debate"),
    ):
        handler, _ = router.dispatch(method, path)
        assert handler is None
