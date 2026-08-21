"""Pure conversational welcome state machine for E49."""

from __future__ import annotations

import datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from coaching.core import ensure_dir, read_yaml, write_yaml
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


def _state_path(base_path: Path) -> Path:
    """Return the filesystem location for the persisted welcome state."""
    return base_path / ".escala" / "agent" / "memory" / "welcome-state.yaml"


def save_welcome_state(
    base_path: Path,
    state: WelcomeState,
    *,
    authorized: bool,
) -> Path | None:
    """
    Persist a WelcomeState to disk.

    State is only written when ``authorized`` is True. The caller must obtain
    explicit user consent before setting this flag.
    """
    if not authorized:
        return None

    payload = {
        "schema_version": 1,
        "authorized_at": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
        "updated_at": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
        **state.model_dump(mode="json"),
    }

    path = _state_path(base_path)
    ensure_dir(path.parent)
    write_yaml(path, payload)
    return path


def load_welcome_state(base_path: Path) -> WelcomeState | None:
    """Load a previously persisted WelcomeState, or None if absent."""
    path = _state_path(base_path)
    data = read_yaml(path)
    if not data:
        return None

    # Drop metadata fields that are not part of WelcomeState.
    state_data = {
        k: v
        for k, v in data.items()
        if k not in {"schema_version", "authorized_at", "updated_at"}
    }
    return WelcomeState.model_validate(state_data)


def is_state_fresh(base_path: Path, max_age_days: int = 7) -> bool:
    """
    Return False if the persisted state is older than ``max_age_days``.

    Freshness is checked against the ``updated_at`` metadata stored alongside
    the state. If no timestamp is available, the state is treated as stale.
    """
    data = read_yaml(_state_path(base_path))
    if not data:
        return False

    updated_at = data.get("updated_at")
    if not updated_at:
        return False

    try:
        updated = datetime.datetime.fromisoformat(updated_at)
    except ValueError:
        return False

    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=datetime.timezone.utc)

    return (
        datetime.datetime.now(tz=datetime.timezone.utc) - updated
    ).days < max_age_days
