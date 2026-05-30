"""Verne Harnish — Board Member Handler.

Provides Verne-style answers to business questions using the Alma
document (S21.1) and the E19 knowledge graph.

Usage::

    from escala_server.verne_handler import VerneHandler

    handler = VerneHandler("~/.escala/escala.db")
    result = handler.ask("¿Cuál es mi CCC?")
    # -> {"answer": "...", "entities_used": [...], "category": "cash", ...}
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from .graph_engine import GraphEngine
from .knowledge_handler import KnowledgeHandler

# ── Category classification keywords ──────────────────────────────────

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "people": [
        "persona", "gente", "equipo", "talento", "contratar", "a-player",
        "fac", "organigrama", "rol", "responsabilidad", "accountability",
        "cultura", "valores", "topgrading", "liderazgo", "entrevista",
        "people", "hiring", "talent", "team", "who",
    ],
    "strategy": [
        "estrategia", "diferenciación", "core customer", "cliente",
        "brand promise", "bhag", "ops", "propósito", "visión", "misión",
        "marca", "posicionamiento", "swot", "7 estratos", "profit per x",
        "strategy", "differentiation", "purpose", "vision",
    ],
    "execution": [
        "ejecución", "daily huddle", "weekly meeting", "prioridad",
        "kpi", "métricas", "ritmo", "hábito", "disciplina",
        "reunión", "tema del trimestre", "critical number",
        "execution", "habit", "rhythm", "priority", "meeting",
        "huddle", "routine",
    ],
    "cash": [
        "cash", "flujo", "efectivo", "power of one", "palanca",
        "ccc", "capital", "trabajo", "gross margin", "margen",
        "ingreso", "gasto", "cuentas por cobrar", "inventario",
        "proveedores", "revenue", "profit", "rentabilidad",
        "liquidez", "cash flow", "financial",
    ],
}

# ── Verne response templates per category ────────────────────────────

_VERNE_TEMPLATES: dict[str, dict[str, Any]] = {
    "people": {
        "diagnosis": "Eso suena a un tema de **People**. Déjame preguntarte algo directo:",
        "questions": [
            "¿Tienes a la persona correcta en cada asiento de tu FACe?",
            "¿Cuándo fue la última vez que hiciste una entrevista Topgrading real?",
            "¿Tu equipo tiene Healthy Conflict o silencio político?",
            "¿Qué estás haciendo para desarrollar a tus A-players?",
        ],
        "principles": ["Delegate and Predict", "Healthy Conflict"],
        "reframe": "Recuerda: las nalgas correctas en los asientos correctos. Sin eso, nada más funciona.",
    },
    "strategy": {
        "diagnosis": "Eso es un tema de **Estrategia**. Antes de profundizar:",
        "questions": [
            "¿Quién es tu Core Customer? Descríbelo en una frase.",
            "¿Cuáles son tus 3 Brand Promises y cómo sabes que las cumples?",
            "¿Cuál es tu BHAG a 10-25 años?",
            "¿Tu OPSP está actualizado y todo el equipo lo conoce?",
        ],
        "principles": ["Same Page", "Keep Things Simple"],
        "reframe": "La estrategia sin ejecución es un sueño. Pero empecemos por tener claro el sueño en una página.",
    },
    "execution": {
        "diagnosis": "Hablas de **Ejecución**. El talón de Aquiles de la mayoría de las empresas. Pregunto:",
        "questions": [
            "¿Tienes un Daily Huddle de 15 minutos todos los días?",
            "¿Cuál es tu Prioridad #1 este trimestre?",
            "¿Tu weekly meeting termina con un WWW claro?",
            "¿Tus KPIs son leading o lagging?",
        ],
        "principles": ["No Surprises", "Priority #1", "Routine Sets You Free"],
        "reframe": "Las metas sin rutinas son deseos. El ritmo constante vence a la intensidad esporádica.",
    },
    "cash": {
        "diagnosis": "**Cash** — mi tema favorito. Sin efectivo no hay empresa. Por eso pregunto:",
        "questions": [
            "¿Cuál es tu Cash Conversion Cycle en días?",
            "¿Qué está pasando con cada palanca del Power of One?",
            "¿Sabes tu Gross Margin sin mirarlo?",
            "¿Tienes suficiente efectivo para 12 meses sin crecimiento?",
        ],
        "principles": ["No Surprises", "Keep Things Simple"],
        "reframe": "El efectivo es el oxígeno. El Power of One no miente — mejora 1% en cada palanca y verás lo que pasa.",
    },
    "general": {
        "diagnosis": "Déjame ponerme mis lentes de Verne y ver esto desde las **4 Decisiones**:",
        "questions": [
            ("People", "¿Quién es responsable de esto?"),
            ("Strategy", "¿Esto está alineado con tu Core Customer y Brand Promise?"),
            ("Execution", "¿Tienes un ritmo para darle seguimiento?"),
            ("Cash", "¿Cómo impacta esto tu flujo de efectivo?"),
        ],
        "principles": ["Keep Things Simple", "No Surprises", "Routine Sets You Free"],
        "reframe": "Mira, todo negocio se reduce a 4 decisiones. Siempre empiezo por ahí.",
    },
}


class VerneHandler:
    """Handle Verne-style answers to business questions."""

    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            db_path = str(Path.home() / ".escala" / "escala.db")
        self.graph = GraphEngine(db_path)
        self.knowledge = KnowledgeHandler(self.graph)
        self._alma: str | None = None

    # ── public API ────────────────────────────────────────────────────

    def ask(self, question: str, context: dict | None = None) -> dict:
        """Answer a business question in Verne Harnish's voice.

        Args:
            question: The question to answer (e.g. "¿Cómo mejoro mi flujo de caja?")
            context:  Optional context dict (company, session_id, etc.)

        Returns:
            dict with answer, category, entities_used, principles_applied, status.
        """
        if not question or not question.strip():
            return {
                "status": "error",
                "message": "No question provided. Verne espera una pregunta.",
            }

        # 1. Classify the question
        category = self._classify_question(question)

        # 2. Get relevant entities from the knowledge graph
        entities = self._get_relevant_entities(question, category)

        # 3. Get template for this category
        template = _VERNE_TEMPLATES.get(category, _VERNE_TEMPLATES["general"])

        # 4. Build the answer
        answer = self._build_answer(question, category, template, entities)

        return {
            "answer": answer,
            "category": category,
            "entities_used": [e["name"] for e in entities],
            "entity_count": len(entities),
            "principles_applied": template.get("principles", []),
            "status": "ok",
        }

    # ── internal methods ──────────────────────────────────────────────

    def _classify_question(self, question: str) -> str:
        """Classify a question into a Verne category using keyword matching."""
        q_lower = question.lower()

        scores: dict[str, int] = {}
        for category, keywords in _CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in q_lower)
            if score > 0:
                scores[category] = score

        if not scores:
            return "general"

        # Return highest-scoring category
        return max(scores, key=scores.get)  # type: ignore[arg-type]

    def _get_relevant_entities(
        self, question: str, category: str
    ) -> list[dict[str, Any]]:
        """Find knowledge graph entities relevant to the question."""
        all_entities: list[dict[str, Any]] = []
        seen: set[str] = set()

        # Search with category context
        ctx = self.knowledge.get_context(category=category)
        for ent in ctx.get("entities", []):
            if ent["name"] not in seen:
                all_entities.append(ent)
                seen.add(ent["name"])

        # Also search by question keywords
        words = [w for w in question.lower().split() if len(w) > 3]
        for word in words[:5]:
            result = self.knowledge.search(query=word)
            for ent in result.get("entities", []):
                if ent["name"] not in seen:
                    all_entities.append(ent)
                    seen.add(ent["name"])

        return all_entities

    def _build_answer(
        self,
        question: str,
        category: str,
        template: dict[str, Any],
        entities: list[dict[str, Any]],
    ) -> str:
        """Build a structured Verne-style answer."""
        lines: list[str] = []

        # Opening — Verne's diagnosis
        lines.append(f"**Verne:** {template['diagnosis']}\n")

        # Entity context (if found)
        if entities:
            entity_names = [e["name"] for e in entities[:3]]
            lines.append(f"Veo que mencionas conceptos como *{', '.join(entity_names)}* — déjame ponerte contexto:\n")

            for ent in entities[:2]:
                desc = ent.get("description", "")
                if desc:
                    lines.append(f"- **{ent['name']}**: {desc}")

            lines.append("")

        # Verne's characteristic questions
        questions = template.get("questions", [])
        if questions:
            lines.append("**Mis preguntas para ti:**")
            for q in questions:
                if isinstance(q, tuple):
                    lines.append(f"  - *[{q[0]}]* {q[1]}")
                else:
                    lines.append(f"  - {q}")

        lines.append("")

        # Principles
        principles = template.get("principles", [])
        if principles:
            principle_bullets = "\n".join(f"  - **{p}**" for p in principles)
            lines.append(f"**Principios que aplicarían aquí:**\n{principle_bullets}")

        lines.append("")

        # Reframe / closing
        reframe = template.get("reframe", "")
        if reframe:
            lines.append(f"*{reframe}*\n")

        # Call to action
        lines.append("**¿Qué vas a hacer al respecto?**")

        return "\n".join(lines)
