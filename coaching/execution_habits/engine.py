"""Pure logic for the 10 Execution Habits assessment.

Scores each habit 1-5, computes a total, and identifies the top 3
weakest habits to prioritize for action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

MISSING = "[PENDIENTE]"
MIN_SCORE = 1
MAX_SCORE = 5

HABITS: tuple[dict[str, str], ...] = (
    {
        "id": "executive_team",
        "name": "Equipo ejecutivo sano y alineado",
        "description": "El equipo ejecutivo se reúne regularmente y está alineado en prioridades y valores.",
    },
    {
        "id": "priority_alignment",
        "name": "Todos alineados con la prioridad #1",
        "description": "Cada persona conoce la prioridad número uno del trimestre y cómo su trabajo la impacta.",
    },
    {
        "id": "communication_rhythm",
        "name": "Ritmo de comunicación establecido",
        "description": "Daily huddles, semanales, mensuales y trimestrales funcionan con agenda clara.",
    },
    {
        "id": "department_dashboards",
        "name": "Cada departamento tiene un dashboard",
        "description": "Cada área mide lo que importa y lo visualiza en un dashboard simple.",
    },
    {
        "id": "one_priority",
        "name": "Todos tienen una prioridad clara",
        "description": "Cada empleado tiene una prioridad individual por periodo y la comunica.",
    },
    {
        "id": "strategy_articulation",
        "name": "Todos pueden articular la estrategia",
        "description": "Cualquier empleado puede explicar la estrategia de la empresa en una frase.",
    },
    {
        "id": "growth_execution_review",
        "name": "Crecimiento y ejecución revisados",
        "description": "Se revisan métricas de crecimiento y ejecución en ritmo semanal/mensual.",
    },
    {
        "id": "values_alive",
        "name": "Valores y propósito vivos",
        "description": "Los core values y el propósito se usan en decisiones cotidianas y reconocimientos.",
    },
    {
        "id": "metrics_articulation",
        "name": "Todos conocen los KPIs clave",
        "description": "Cada empleado conoce las métricas que miden el éxito de su área.",
    },
    {
        "id": "employee_feedback",
        "name": "Retroalimentación continua",
        "description": "Existe un mecanismo regular de feedback entre líderes y equipos.",
    },
)


@dataclass
class HabitScore:
    """Score for a single Execution Habit."""

    habit_id: str
    score: int | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "habit_id": self.habit_id,
            "score": self.score,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HabitScore":
        score = data.get("score")
        if score is not None:
            try:
                score = int(score)
            except (TypeError, ValueError):
                score = None
        return cls(
            habit_id=str(data.get("habit_id", "")),
            score=score,
            notes=str(data.get("notes", "")),
        )


@dataclass
class ExecutionAssessment:
    """A complete assessment of the 10 Execution Habits."""

    scores: list[HabitScore] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Ensure all 10 habits are represented, filling defaults as needed."""
        by_id = {s.habit_id: s for s in self.scores if s.habit_id}
        self.scores = [
            by_id.get(h["id"], HabitScore(habit_id=h["id"])) for h in HABITS
        ]

    def to_dict(self) -> dict[str, Any]:
        return {"scores": [s.to_dict() for s in self.scores]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionAssessment":
        raw_scores = data.get("scores", []) if isinstance(data, dict) else []
        by_id = {
            s["habit_id"]: HabitScore.from_dict(s)
            for s in raw_scores
            if isinstance(s, dict) and s.get("habit_id")
        }
        # Ensure all 10 habits are present, using defaults for missing ones.
        scores = [by_id.get(h["id"], HabitScore(habit_id=h["id"])) for h in HABITS]
        return cls(scores=scores)


def validate(assessment: ExecutionAssessment) -> list[str]:
    """Return validation errors; empty means valid enough to score."""
    errors: list[str] = []
    for habit, score in zip(HABITS, assessment.scores):
        if score.score is None:
            errors.append(f"{habit['name']}: sin calificación.")
        elif score.score < MIN_SCORE or score.score > MAX_SCORE:
            errors.append(
                f"{habit['name']}: la calificación debe estar entre {MIN_SCORE} y {MAX_SCORE}."
            )
    return errors


def score(assessment: ExecutionAssessment) -> dict[str, Any]:
    """Compute total score, average, and top 3 weakest habits."""
    rated = [s for s in assessment.scores if s.score is not None]
    if not rated:
        return {
            "total": 0,
            "average": 0.0,
            "max": len(HABITS) * MAX_SCORE,
            "completeness": 0,
            "top_weaknesses": [],
        }

    total = sum(s.score for s in rated if s.score is not None)
    max_possible = len(HABITS) * MAX_SCORE
    completeness = round((len(rated) / len(HABITS)) * 100)
    average = round(total / len(HABITS), 1)

    # Weaknesses: lowest scores first; tie-break by habit order.
    weakness_order = sorted(
        assessment.scores,
        key=lambda s: (s.score if s.score is not None else 99, s.habit_id),
    )[:3]

    habit_by_id = {h["id"]: h for h in HABITS}
    top_weaknesses = [
        {
            "habit_id": s.habit_id,
            "name": habit_by_id[s.habit_id]["name"],
            "score": s.score,
        }
        for s in weakness_order
    ]

    return {
        "total": total,
        "average": average,
        "max": max_possible,
        "completeness": completeness,
        "top_weaknesses": top_weaknesses,
    }
