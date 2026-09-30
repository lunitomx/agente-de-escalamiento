# pyright: strict
"""What ESCALA says to the owner while finding their tab (plain Spanish).

Before the user's "sí" these messages only ever mention tab names, which the
user already sees in Drive. Cells are quoted only from the confirmed tab.
"""

from __future__ import annotations

from coaching.tracker.identity import SheetCandidate, is_placeholder_name

ASK_NAME = "¿Cómo te llamas? Con tu nombre busco tu pestaña en la hoja del grupo."

# Owner decision (AR-E82): mandatory one-line notice when connecting Drive.
DRIVE_NOTICE = (
    "Ojo: al conectarlo, el asistente puede ver todo el archivo compartido del "
    "grupo; ESCALA sólo usa tu pestaña."
)

NEEDS_YES = "Antes de leer tu pestaña necesito que me confirmes que es la tuya."
START_HERE_IS_NOT_YOURS = (
    "**START HERE** es la pestaña de instrucciones del grupo, no la de una "
    "persona. ¿Cuál es la tuya?"
)
NO_TABS = "No encontré pestañas en el archivo. ¿Me pegas aquí tu pestaña?"
ASK_TAB_NAME = "¿Cómo se llama tu pestaña en la hoja? Casi siempre es tu nombre."
_FIX_START_HERE = (
    "puedo trabajar igual, y conviene avisar al grupo para que llene START HERE."
)


def connect_message() -> str:
    return (
        "Para leer tu hoja, conecta Google Drive en tu Claude (Configuración → "
        f"Conectores). {DRIVE_NOTICE} Si prefieres no conectarlo, abre tu "
        "pestaña, selecciónala toda, cópiala y pégala aquí."
    )


def _join(labels: list[str]) -> str:
    return (
        labels[0] if len(labels) == 1 else ", ".join(labels[:-1]) + " y " + labels[-1]
    )


def _bold(tab_name: str) -> str:
    return f"**{tab_name}**"


def _label(candidate: SheetCandidate) -> str:
    suffix = " (todavía sin nombre)" if candidate.placeholder else ""
    return _bold(candidate.tab_name) + suffix


def candidates_message(candidates: list[SheetCandidate], business: str | None) -> str:
    """Propose the best tab by name, or list the tab names if none matches."""
    if not candidates:
        return NO_TABS
    best = candidates[0]
    if best.score == 0:
        labels = _join([_label(c) for c in candidates])
        return (
            "No encontré una pestaña con tu nombre. Estas son las pestañas del "
            f"archivo: {labels}. ¿Cuál es la tuya?"
        )
    tied = [
        _bold(c.tab_name)
        for c in candidates
        if (c.score, c.business_match) == (best.score, best.business_match)
    ]
    if len(tied) == 1:
        return f"Veo una pestaña que se llama **{best.tab_name}**. ¿Es la tuya?"
    ask = (
        "¿Cómo se llama tu negocio? Así sé cuál es."
        if business is None
        else "¿Cuál es la tuya?"
    )
    return f"Veo {len(tied)} pestañas que podrían ser tuyas: {_join(tied)}. {ask}"


def confirmed_message(tab_name: str, participant: str | None) -> str:
    """Close the choice; warn about a placeholder name only after the yes."""
    message = f"Listo: tu pestaña es **{tab_name}**. La próxima vez voy directo a ella."
    if participant is None or not participant.strip():
        return f"{message} Tu pestaña no tiene tu nombre escrito; {_FIX_START_HERE}"
    if is_placeholder_name(participant):
        return (
            f"{message} Tu pestaña dice '{participant}' en vez de tu nombre; "
            f"{_FIX_START_HERE}"
        )
    return message


def remembered_message(tab_name: str) -> str:
    return f"Uso tu pestaña **{tab_name}**, como la otra vez."


def tab_not_found_message(tab_name: str) -> str:
    return f"No encuentro la pestaña **{tab_name}** en el archivo. ¿Me dices cuál es la tuya?"
