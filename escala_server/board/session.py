"""Optional session hook; failure or disabled mode never blocks a session."""

from __future__ import annotations

from dataclasses import dataclass

from .context import BoardContextBuilder, PortableKnowledgeHandler
from .verne import VerneLensAdvisor


@dataclass(frozen=True)
class BoardHookResult:
    enabled: bool
    output: str | None = None
    warning: str | None = None
    schema_version: str = "board-response-v1"
    profile_version: str = "verne-lens-v1"


def optional_board_review(text: str, *, enabled: bool, mode: str = "daily_review") -> BoardHookResult:
    if not enabled:
        return BoardHookResult(enabled=False)
    try:
        packet = BoardContextBuilder(PortableKnowledgeHandler()).build(text)
        advisor = VerneLensAdvisor()
        response = advisor.daily_review(packet) if mode == "daily_review" else advisor.decision_consult(packet)
        return BoardHookResult(enabled=True, output=advisor.render_markdown(response))
    except (OSError, ValueError, RuntimeError) as error:
        return BoardHookResult(enabled=True, warning=f"El board no estuvo disponible: {error}")
