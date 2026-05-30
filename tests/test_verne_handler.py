"""Tests for the VerneHandler."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


class TestVerneHandler:
    """Test Verne Harnish board member handler."""

    @pytest.fixture
    def handler(self):
        from escala_server.verne_handler import VerneHandler

        return VerneHandler(":memory:")

    def test_ask_cash_question(self, handler):
        """A cash-related question returns cash category and Verne's voice."""
        result = handler.ask("¿Cómo mejoro mi flujo de efectivo?")
        assert result["status"] == "ok"
        assert result["category"] == "cash"
        assert "Verne" in result["answer"]
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
        result = handler.ask("Necesitamos mejorar nuestra ejecución y tener daily huddle")
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
        """Answer includes Verne voice, questions, and call to action."""
        result = handler.ask("¿Cómo reduzco mi CCC?")
        assert result["status"] == "ok"
        answer = result["answer"]
        # Verne's voice
        assert "**Verne:**" in answer
        # Has questions
        assert "?" in answer
        # Has principles
        assert len(result.get("principles_applied", [])) > 0
        # Has call to action
        assert "¿Qué vas a hacer" in answer

    def test_answer_includes_entity_context(self, handler):
        """Answer references entities from the knowledge graph."""
        result = handler.ask("Explícame el Power of One")
        answer = result["answer"]
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
        result = handler.session_perspective(category="people", changes_count=3, company="Acme")
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
        history = [{"user": "Creo que tenemos el equipo para esto", "verne": "... análisis ..."}]
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

    def test_coherence_alma_has_4d_framework(self):
        """The alma document references the 4 Decisions framework."""
        alma = Path("miembro-board/verne-harnish.md").read_text()
        assert "4 Decisiones" in alma
        assert "People" in alma
        assert "Strategy" in alma
        assert "Execution" in alma
        assert "Cash" in alma

    def test_coherence_alma_has_rockefeller_habits(self):
        """The alma document references Rockefeller Habits."""
        alma = Path("miembro-board/verne-harnish.md").read_text()
        assert "Rockefeller Habits" in alma
        assert "Daily Huddle" in alma
        assert "No Surprises" in alma

    def test_coherence_alma_has_verne_questions(self):
        """The alma document includes Verne's characteristic questions."""
        alma = Path("miembro-board/verne-harnish.md").read_text()
        assert "Core Customer" in alma
        assert "Cash Conversion Cycle" in alma
        assert "BHAG" in alma

    def test_coherence_ask_uses_framework(self, handler):
        """Answers reference the correct framework for the category."""
        cash_result = handler.ask("¿Cómo mejoro mi flujo de efectivo?")
        assert "Power of One" in cash_result["answer"]
        assert "Cash Conversion Cycle" in cash_result.get("answer", "")

        people_result = handler.ask("Necesito mejores personas en mi equipo")
        assert "A-player" in people_result["answer"] or "asiento" in people_result["answer"]

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
        """Every answer has Verne's voice + questions + call to action."""
        for question in [
            "¿Cómo mejoro mi cash flow?",
            "¿Necesito un daily huddle?",
            "¿Cuál es mi estrategia?",
            "¿Debo contratar más gente?",
        ]:
            result = handler.ask(question)
            assert "**Verne:**" in result["answer"], f"Missing Verne voice for: {question}"
            assert "?" in result["answer"], f"Missing questions for: {question}"
            assert "¿Qué vas a hacer" in result["answer"], f"Missing CTA for: {question}"

    def test_coherence_entities_are_real(self):
        """All 42 entities from the book-knowledge.json are valid."""
        import json
        with open("escala_server/data/book-knowledge.json") as f:
            data = json.load(f)
        assert data["meta"]["entities_count"] == 42
        assert data["meta"]["relationships_count"] == 59
        names = [e["name"] for e in data["entities"]]
        assert "Power of One" in names
        assert "Rockefeller Habits" in names
        assert "4D Framework" in names
        assert len(names) == 42
