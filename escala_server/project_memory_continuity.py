"""Natural-language adapter for explicit project-local memory continuity."""

from __future__ import annotations

import re
import unicodedata
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .project_memory_context import ProjectMemorySessionContext
from .project_memory_session_close import (
    CandidateSource,
    MemoryCandidate,
    ProjectMemorySessionClose,
)

Stage = Literal["normal", "capture", "confirm"]
_FORBIDDEN = frozenset(
    {
        "sqlite",
        "database",
        "db",
        "skill",
        "command",
        "log",
        "token",
        "password",
        "secret",
        "apikey",
    }
)
_PATH = re.compile(r"(?:^|[\s\"'`=:(\[])(?:/|\\|[A-Za-z]:[\\/])")


@dataclass(frozen=True)
class NaturalTurn:
    """A safe, user-facing turn plus opaque state for the router only."""

    prefix: str | None = None
    next_question: str | None = None
    stage: Stage = "normal"
    session_id: str | None = None
    proposal_id: str | None = None


class ProjectMemoryContinuity:
    """Translate verified S22.4/S22.5 results without exposing internals."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.context = ProjectMemorySessionContext(self.project_root)
        self.close = ProjectMemorySessionClose(self.project_root)

    def resume(self) -> NaturalTurn:
        result = self.context.load()
        if not result.ready:
            return NaturalTurn()
        for item in result.items:
            value = self._public_text(item.value)
            if value is not None:
                return NaturalTurn(prefix=f"La última vez dejamos como foco: {value}.")
        return NaturalTurn()

    def begin_pause(self) -> NaturalTurn:
        session_id = f"s-{uuid.uuid4()}"
        opened = self.close.open_session(session_id)
        if not opened.ready:
            return NaturalTurn()
        return NaturalTurn(
            next_question=(
                "Antes de pausar, ¿qué decisión o dato concreto quieres que recuerde "
                "para la próxima vez?"
            ),
            stage="capture",
            session_id=session_id,
        )

    def capture_statement(self, session_id: str, text: str) -> NaturalTurn:
        statement = self._public_text(text)
        if statement is None:
            return NaturalTurn(
                next_question="No voy a guardar nada. Podemos seguir cuando quieras."
            )
        kind = (
            "decision"
            if re.search(r"\b(decid|contrat|abrir|cerrar|priori)", statement.casefold())
            else "fact"
        )
        proposed = self.close.propose(
            session_id,
            MemoryCandidate(
                kind,
                statement,
                CandidateSource(
                    session_id, (f"o-{uuid.uuid4()}",), "explicit_user_statement"
                ),
            ),
        )
        if not proposed.ready or proposed.status != "proposed" or not proposed.id:
            return NaturalTurn(
                next_question="No voy a guardar nada. Podemos seguir cuando quieras."
            )
        return NaturalTurn(
            next_question=f"Entendí: {statement}. ¿Quieres que lo recuerde para la próxima sesión? (sí/no)",
            stage="confirm",
            session_id=session_id,
            proposal_id=proposed.id,
        )

    def answer_confirmation(
        self, session_id: str, proposal_id: str, answer: str
    ) -> NaturalTurn:
        result = self.close.confirm(proposal_id, answer)
        if not result.ready:
            return NaturalTurn(next_question="Podemos seguir cuando quieras.")
        if result.status == "confirmed":
            self.close.close(session_id)
            return NaturalTurn(
                next_question="Listo. La próxima vez podremos retomar esa decisión."
            )
        if result.status == "rejected":
            self.close.close(session_id)
            return NaturalTurn(
                next_question="De acuerdo, no lo voy a guardar. Podemos seguir cuando quieras."
            )
        if result.status == "proposed":
            return NaturalTurn(
                next_question=(
                    "De acuerdo, no lo voy a dar por hecho. ¿Quieres aclararlo ahora "
                    "o seguimos con lo que estabas trabajando?"
                ),
                stage="confirm",
                session_id=session_id,
                proposal_id=proposal_id,
            )
        return NaturalTurn(next_question="Podemos seguir cuando quieras.")

    @staticmethod
    def _public_text(value: object) -> str | None:
        if not isinstance(value, str):
            return None
        text = " ".join(value.strip().split())
        normalized = unicodedata.normalize("NFKD", text).casefold()
        tokens = set(re.split(r"[^a-z0-9]+", normalized))
        if not text or len(text) > 240 or tokens & _FORBIDDEN or _PATH.search(text):
            return None
        return text
