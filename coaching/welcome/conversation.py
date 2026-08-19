"""Pure conversational welcome state machine for E49."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from coaching.decision.engine import classify_area


class MaturityProfile(StrEnum):
    """Conversation profile used to choose the next useful question."""

    EXPLORER = "explorer"
    SPECIFIC = "specific"
    DIRECTED = "directed"
    RETURNING = "returning"


Phase = Literal["concern", "narrow", "source", "continuity"]
NextAction = Literal["narrow", "evidence", "direct", "continue"]


class WelcomeState(BaseModel):
    """Serializable state for one welcome conversation."""

    phase: Phase
    profile: MaturityProfile | None = None
    returning: bool = False
    previous_focus: str | None = None
    concern: str | None = None
    area: str | None = None
    next_action: NextAction | None = None


class WelcomeTurn(BaseModel):
    """One user-facing question plus the next internal state."""

    question: str = Field(..., min_length=1)
    state: WelcomeState


def begin_welcome(
    *, returning: bool = False, previous_focus: str | None = None
) -> WelcomeTurn:
    """Start a welcome turn without exposing implementation commands."""
    if returning and previous_focus:
        state = WelcomeState(
            phase="continuity",
            profile=MaturityProfile.RETURNING,
            returning=True,
            previous_focus=previous_focus,
            next_action="continue",
        )
        return WelcomeTurn(
            question=(
                f"La última vez trabajamos en {previous_focus}. "
                "¿Quieres continuar con eso o hay algo nuevo que te preocupe?"
            ),
            state=state,
        )

    return WelcomeTurn(
        question="¿Cómo está tu empresa hoy? Cuéntame en una frase lo que más te preocupa.",
        state=WelcomeState(phase="concern"),
    )


def _is_directed(text: str) -> bool:
    normalized = text.lower()
    directed_markers = (
        "quiero hacer",
        "necesito calcular",
        "necesito definir",
        "quiero calcular",
        "ccc",
        "opsp",
        "power of one",
    )
    return any(marker in normalized for marker in directed_markers)


def _source_question(area: str | None) -> str:
    if area:
        return (
            f"Para trabajar en {area}, ¿dónde están tus datos: en un archivo, "
            "un sistema o en tu cabeza?"
        )
    return "¿Dónde están tus datos: en un archivo, un sistema o en tu cabeza?"


def _area_for_concern(text: str) -> str | None:
    """Reuse decision keywords and cover diagnostic terms such as CCC."""
    normalized = text.lower()
    if any(
        term in normalized for term in ("ccc", "cash", "efectivo", "cobrar", "cobro")
    ):
        return "cash"
    if "ventas" in normalized or "vender" in normalized:
        return (
            "cash"
            if any(term in normalized for term in ("bajaron", "bajó", "cash", "cobro"))
            else "strategy"
        )
    return classify_area(text)


def respond_to_welcome(state: WelcomeState, message: str) -> WelcomeTurn:
    """Advance one turn based on the user's latest answer."""
    concern = message.strip()
    if not concern:
        return WelcomeTurn(
            question="¿Qué te preocupa más hoy: tu equipo, tus números, tu estrategia o tu operación diaria?",
            state=WelcomeState(phase="narrow", profile=MaturityProfile.EXPLORER),
        )

    if state.phase == "continuity":
        if any(word in concern.lower() for word in ("nuevo", "otra", "diferente")):
            return begin_welcome()
        area = _area_for_concern(concern) or state.previous_focus
        return WelcomeTurn(
            question=_source_question(area),
            state=WelcomeState(
                phase="source",
                profile=MaturityProfile.RETURNING,
                returning=True,
                previous_focus=state.previous_focus,
                concern=concern,
                area=area,
                next_action="continue",
            ),
        )

    area = _area_for_concern(concern)
    if _is_directed(concern):
        return WelcomeTurn(
            question=_source_question(area),
            state=WelcomeState(
                phase="source",
                profile=MaturityProfile.DIRECTED,
                concern=concern,
                area=area,
                next_action="direct",
            ),
        )

    if area is None:
        return WelcomeTurn(
            question="¿Qué te preocupa más hoy: tu equipo, tus números, tu estrategia o tu operación diaria?",
            state=WelcomeState(
                phase="narrow",
                profile=MaturityProfile.EXPLORER,
                concern=concern,
                next_action="narrow",
            ),
        )

    return WelcomeTurn(
        question=_source_question(area),
        state=WelcomeState(
            phase="source",
            profile=MaturityProfile.SPECIFIC,
            concern=concern,
            area=area,
            next_action="evidence",
        ),
    )
