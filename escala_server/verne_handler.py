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

import yaml

from .graph_engine import GraphEngine
from .knowledge_handler import KnowledgeHandler

# ── Category classification keywords ──────────────────────────────────

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "people": [
        "persona", "gente", "equipo", "talento", "contratar", "a-player",
        "fac", "organigrama", "rol", "responsabilidad", "accountability",
        "cultura", "valores", "topgrading", "liderazgo", "entrevista",
        "people", "hiring", "talent", "team", "who",
        # Coloquial SME/Latam
        "prima", "primo", "encargada", "encargado", "rendir", "rinde",
        "maistro", "recomendación", "familia", "familiar", "jefe",
        "contratación", "despedir", "renunció", "renuncia",
    ],
    "strategy": [
        "estrategia", "diferenciación", "core customer", "cliente",
        "brand promise", "bhag", "ops", "propósito", "visión", "misión",
        "marca", "posicionamiento", "swot", "7 estratos", "profit per x",
        "strategy", "differentiation", "purpose", "vision",
        # Coloquial + negocio
        "competencia", "expandir", "crecer", "nuevo mercado",
        "sucursal", "franquicia", "local", "colonia", "zona",
    ],
    "execution": [
        "ejecución", "daily huddle", "weekly meeting", "prioridad",
        "kpi", "métricas", "ritmo", "hábito", "disciplina",
        "reunión", "tema del trimestre", "critical number",
        "execution", "habit", "rhythm", "priority", "meeting",
        "huddle", "routine",
        # Coloquial + SaaS
        "churn", "descompuso", "descompone", "máquina", "taller",
        "producción", "proceso", "seguimiento", "atraso", "retraso",
    ],
    "cash": [
        "cash", "flujo", "efectivo", "power of one", "palanca",
        "ccc", "capital", "gross margin", "margen",
        "ingreso", "gasto", "cuentas por cobrar", "inventario",
        "proveedores", "revenue", "profit", "rentabilidad",
        "liquidez", "cash flow", "financial", "return on cash", "roc",
        # Coloquial SME
        "maíz", "insumos", "materia prima", "quincena",
        "cobrar", "pagar", "cobranza", "corte de caja",
        "precio", "costos",
    ],
}

# ── Verne response templates — loaded from YAML at init ──────────
# See conocimiento/coaching/verne-templates.yaml
# See conocimiento/coaching/daily-checklist.yaml


class VerneHandler:
    """Handle Verne-style answers to business questions."""

    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            db_path = str(Path.home() / ".escala" / "escala.db")
        self.graph = GraphEngine(db_path)
        self.knowledge = KnowledgeHandler(self.graph)
        self._alma: str | None = None

        # Load Verne templates from YAML
        _coaching_dir = Path(__file__).resolve().parent.parent / "conocimiento" / "coaching"
        self._templates = yaml.safe_load(
            (_coaching_dir / "verne-templates.yaml").read_text(encoding="utf-8")
        )
        self._checklist = yaml.safe_load(
            (_coaching_dir / "daily-checklist.yaml").read_text(encoding="utf-8")
        )
        self._max_score = sum(item["weight"] for item in self._checklist.values())

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

        # 0. Check for identity questions (C6)
        q_lower = question.lower().strip("¿?¡!")
        if q_lower in ("quién eres", "quien eres", "who are you", "quién eres verne", "quien es verne"):
            return {
                "answer": (
                    "**Verne:** Soy Verne Harnish, fundador de Gazelles y autor de *Scaling Up*.\n\n"
                    "Llevo 30 años ayudando a empresas a escalar. Mi framework son las **4 Decisiones**:\n"
                    "  - **People:** La gente correcta en los asientos correctos\n"
                    "  - **Strategy:** Diferenciación real que importa al cliente\n"
                    "  - **Execution:** Ritmo imparable con Rockefeller Habits\n"
                    "  - **Cash:** Flujo de efectivo para crecer sin morir\n\n"
                    "Puedes preguntarme:\n"
                    "  • `ask` — \"¿cómo mejoro mi flujo de caja?\"\n"
                    "  • `review-daily` — pásame tu daily y lo califico\n"
                    "  • `debate` — \"¿deberíamos expandirnos?\"\n\n"
                    "¿Por dónde quieres empezar?"
                ),
                "category": "general",
                "entities_used": [],
                "entity_count": 0,
                "principles_applied": [],
                "status": "ok",
            }

        # 1. Classify the question
        category = self._classify_question(question)

        # 2. Get relevant entities from the knowledge graph
        entities = self._get_relevant_entities(question, category)

        # 3. Get template for this category
        template = self._templates.get(category, self._templates["general"])

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

    # ── daily review ───────────────────────────────────────────────────

    def review_daily(self, daily_text: str) -> dict:
        """Review a daily huddle summary against Rockefeller Habits.

        Args:
            daily_text: The daily huddle summary text (free form or JSON).

        Returns:
            dict with score, score_percent, elements_found, elements_missing,
            observations, and status.
        """
        text_lower = daily_text.lower()
        found: list[str] = []
        missing: list[str] = []
        score = 0

        for item_id, item in self._checklist.items():
            if any(kw in text_lower for kw in item["keywords"]):
                found.append(item["label"])
                score += item["weight"]
            else:
                missing.append(item["label"])

        score_percent = round((score / self._max_score) * 100)

        # Build observations
        observations: list[str] = []
        observations.append(f"**Puntuación Rockefeller:** {score}/{self._max_score} ({score_percent}%)")

        if score_percent >= 80:
            observations.append("✅ Buen daily. Tienes los elementos clave. Sigue así.")
        elif score_percent >= 50:
            observations.append("⚠️ Daily incompleto. Tienes lo básico pero faltan elementos clave.")
        else:
            observations.append("❌ Esto no es un Daily Huddle. Es una lista de tareas.")

        if found:
            observations.append(f"\n**Presente:** {', '.join(f'✅ {f}' for f in found)}")
        if missing:
            observations.append(f"\n**Ausente:**")
            for item_id in [k for k in self._checklist if self._checklist[k]["label"] in missing]:
                observations.append(f"  - ❌ {self._checklist[item_id]['message_missing']}")

        # Verne's closing
        if missing:
            observations.append(
                "\n*Un daily sin estructura no es un huddle — es ruido. "
                "15 minutos. De pie. Logros de ayer, prioridades de hoy, obstáculos. "
                "Eso es todo.*"
            )
        else:
            observations.append(
                "\n*Eso es un Daily Huddle de verdad. 15 minutos bien invertidos. "
                "Ahora: ¿qué vas a hacer con esto?*"
            )

        return {
            "score": score,
            "score_max": self._max_score,
            "score_percent": score_percent,
            "elements_found": found,
            "elements_missing": missing,
            "observations": "\n".join(observations),
            "status": "ok",
        }

    # ── session perspective ────────────────────────────────────────────

    _SESSION_PRINCIPLES = {
        "people": (
            "Trabajaste **People**. Recuerda: *Delegate and Predict*. "
            "El trabajo de un líder es desarrollar a otros para que puedan predecir resultados. "
            "Pregunta para la próxima: ¿tus A-players están en los asientos correctos?"
        ),
        "strategy": (
            "Trabajaste **Strategy**. Recuerda: *Same Page*. "
            "La estrategia más brillante no vale nada si no está en una página que todos entiendan. "
            "Pregunta para la próxima: ¿tu OPSP refleja lo que acabas de decidir?"
        ),
        "execution": (
            "Trabajaste **Execution**. Recuerda: *Routine Sets You Free*. "
            "No se trata de trabajar más duro — se trata de tener el ritmo correcto. "
            "Pregunta para la próxima: ¿tu Daily Huddle refleja estas prioridades?"
        ),
        "cash": (
            "Trabajaste **Cash**. Recuerda: *No Surprises*. "
            "El efectivo es el oxígeno del negocio. Lo que no se mide no se gestiona. "
            "Pregunta para la próxima: ¿qué palanca del Power of One vas a mover esta semana?"
        ),
    }

    _SESSION_CLOSINGS = [
        "Buen trabajo. La ejecución no es un evento — es un hábito diario.",
        "Sigue así. Recuerda: las empresas no crecen por casualidad, crecen por disciplina.",
        "El camino es simple, no fácil. Pero tienes las herramientas. Úsalas.",
        "Una sesión productiva. Ahora: ¿qué vas a hacer DIFERENTE mañana?",
        "La estrategia sin ejecución es un sueño. Tú ya tienes el sueño — ahora ejecuta.",
        "No se trata de trabajar más duro, sino de tener el ritmo correcto. ¿Tienes tu daily huddle?",
        "Lo que no se mide no se gestiona. Esta sesión te dio claridad — no la desperdicies.",
        "El crecimiento sostenible se construye con hábitos, no con genialidad. Sigue construyendo.",
        "El Power of One no miente. Mejora 1% en cada palanca y verás.",
        "No surprises. Las malas noticias temprano son buenas noticias. Vuelve cuando tengas dudas.",
    ]

    def session_perspective(
        self,
        category: str | None = None,
        changes_count: int = 0,
        company: str | None = None,
    ) -> dict:
        """Provide Verne's board member perspective at session close.

        Args:
            category:      The category worked on (cash/strategy/people/execution).
            changes_count: How many changes were made in the session.
            company:       Optional company name.

        Returns:
            dict with perspective (text), principle_applied, and status.
        """
        import random

        parts: list[str] = []
        company_line = f"de **{company}**" if company else ""
        parts.append(
            f"**Verne** (perspectiva de board {company_line}):\n"
        )

        # Opening
        if changes_count > 0:
            parts.append(
                f"Veo que hiciste {changes_count} cambio(s) en esta sesión. "
                "El movimiento es bueno — pero asegúrate de que sea movimiento hacia adelante.\n"
            )
        else:
            parts.append(
                "Esta sesión fue más de reflexión que de acción. "
                "Nada de malo con eso — siempre y cuando la próxima sea de ejecución.\n"
            )

        # Category-specific principle
        if category and category in self._SESSION_PRINCIPLES:
            parts.append(self._SESSION_PRINCIPLES[category])

        parts.append("")

        # Closing
        closing = random.choice(self._SESSION_CLOSINGS)
        parts.append(f"*{closing}*")

        return {
            "perspective": "\n".join(parts),
            "category": category or "general",
            "principle_applied": self._SESSION_PRINCIPLES.get(category or "", ""),
            "status": "ok",
        }

    # ── board debate ───────────────────────────────────────────────────

    def board_debate(
        self,
        decision: str,
        context: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> dict:
        """Board-level debate on a strategic decision.

        First turn (no history): analyze the decision across all 4 Decisions.
        Subsequent turns (with history): challenge the user's position.

        Args:
            decision: Strategic decision to debate.
            context:  Optional company context.
            history:  Prior turns [{user: ..., verne: ...}, ...].

        Returns:
            dict with response, turn_number, next_questions, and status.
        """
        if not decision or not decision.strip():
            return {
                "status": "error",
                "message": ("No decision provided. Verne necesita una decisión para debatir.\n"
                            "Ej: escala verne debate \"deberíamos abrir un nuevo local\""),
            }

        turn = len(history) if history else 0
        lines: list[str] = []
        decision_category = self._classify_question(decision)

        if turn == 0:
            # First turn: full board analysis
            company_line = f" de **{context}**" if context else ""
            lines.append(
                f"**Verne** (modo board{company_line}):\n"
                f"Analicemos esta decisión con las **4 Decisiones**:\n"
            )

            # People check
            lines.append(
                "**People:** ¿Quién liderará esto? ¿Tienes a la persona correcta "
                "en el asiento? Sin un A-player responsable, el mejor plan fracasa."
            )
            # Strategy check
            lines.append(
                "**Strategy:** ¿Esta decisión está alineada con tu Core Customer "
                "y Brand Promise? ¿O te estás desviando de tu diferenciación?"
            )
            # Execution check  
            lines.append(
                "**Execution:** ¿Tienes el ritmo para darle seguimiento? Una decisión "
                "sin WWW (*Who does What by When*) es solo una intención."
            )
            # Cash check
            lines.append(
                "**Cash:** ¿Cómo impacta esto tu flujo de efectivo? ¿Cuánto oxígeno "
                "tienes para esto? *No Surprises.*"
            )

            lines.append("")
            lines.append("Ahora respóndeme esta: ¿cuál de estas 4 áreas te preocupa más?")
            lines.append("")

            next_questions = [
                "¿Quién liderará esto y qué experiencia tiene?",
                "¿Cómo se alinea con tu Core Customer?",
                "¿Qué métricas usarás para medir éxito?",
                "¿Cuánto efectivo requiere y de dónde sale?",
            ]
        else:
            # Subsequent turn: respond to the user's last point
            last_user = history[-1].get("user", "") if history else ""

            # Build a reference to what the user said (M3)
            last_user_short = (last_user[:80] + "...") if len(last_user) > 80 else last_user
            lines.append(f"**Verne:**\n")
            lines.append(f"Sobre lo que dices: *\"{last_user_short}\"* — déjame darte mi perspectiva.\n")

            user_category = self._classify_question(last_user) if last_user else "general"

            # Acknowledge
            lines.append(
                f"Entiendo tu punto. Analicémoslo desde **{decision_category.title()}**:\n"
            )

            # Challenge based on category
            challenges = {
                "people": (
                    "Has hablado de personas. Pero recuerda: *Healthy Conflict* es necesario. "
                    "¿Estás dispuesto a tener la conversación incómoda que esto requiere?"
                ),
                "strategy": (
                    "Hablas de estrategia. Pero la estrategia sin Core Customer definido "
                    "es dirección sin mapa. ¿Tu Core Customer sigue siendo el mismo?"
                ),
                "execution": (
                    "Te enfocas en ejecución. *Routine Sets You Free* — ¿qué ritmo "
                    "vas a poner en marcha para que esto no quede en el aire?"
                ),
                "cash": (
                    "Cash es lo que siempre pongo primero. *Power of One* — ¿cuál "
                    "de las 7 palancas te va a dar el mayor impacto aquí?"
                ),
                "general": (
                    "Mire, todo se reduce a una cosa: ¿esto acerca o aleja a tu empresa "
                    "de tu BHAG? Si no sabes cuál es tu BHAG, esa es la conversación "
                    "que deberíamos tener."
                ),
            }

            lines.append(challenges.get(user_category, challenges["general"]))
            lines.append("")

            next_questions = [
                "¿Qué evidencia tienes de que esto funcionará?",
                "¿Qué pasaría si no haces nada?",
                "¿Quién más en tu equipo debería estar en esta conversación?",
            ]

        lines.append("")
        lines.append("*¿Qué opinas de mi análisis? Sigue debatiendo.*")

        return {
            "response": "\n".join(lines),
            "turn": turn + 1,
            "category": decision_category,
            "next_questions": next_questions,
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

        # Verne's characteristic questions (C5: shuffled for variety)
        questions = list(template.get("questions", []))
        if questions:
            import random
            random.shuffle(questions)
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
