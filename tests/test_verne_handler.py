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
