# pyright: strict
"""What ESCALA says to the owner while finding their tab (plain Spanish).

Before the user's "sí" these messages only ever mention tab names, which the
user already sees in Drive. Cells are quoted only from the confirmed tab.
"""

from __future__ import annotations

from coaching.tracker.identity import SheetCandidate, is_placeholder_name
from coaching.tracker.parser import CommitmentsLayout, cell_ref
from coaching.tracker.proposal import RowProposal, render_table

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


# --- S82.4: proposed rows, where to paste and how to undo ---------------------

NEEDS_CONFIRMED_TAB = (
    "Antes de proponerte filas necesito saber cuál es tu pestaña. "
    "¿Me confirmas cuál es la tuya?"
)
NO_PLAN = (
    "Todavía no tenemos tus prioridades del trimestre. ¿Las definimos primero? "
    "Con eso te propongo las filas para tu hoja."
)
ASK_MONTH = "¿Para qué mes son estos compromisos?"
LINK_MISMATCH = (
    "Este archivo no es el que usamos la otra vez. Antes de proponerte filas, "
    "¿me confirmas cuál es tu pestaña aquí?"
)
# S82.6: "restore this version" rolls back everyone's edits in the shared file.
UNDO = (
    "Si algo quedó mal, deshazlo con Ctrl+Z (Cmd+Z en Mac) justo después de "
    "pegar, o con clic derecho en la celda → «Mostrar historial de ediciones». "
    "No uses «Restaurar esta versión»: borraría lo que los demás escribieron en "
    "el archivo del grupo."
)


def _focus_label(layout: CommitmentsLayout | None) -> str:
    if layout is not None and "focus" in layout.fields:
        return layout.headers[layout.fields.index("focus")]
    return "Focus Area"


def _table_headers(layout: CommitmentsLayout | None) -> list[str] | None:
    if layout is None:
        return None
    by_field = dict(zip(layout.fields, layout.headers))
    wanted = ("focus", "text", "kpi", "due")
    if not all(field in by_field for field in wanted):
        return None
    return [by_field[field] for field in wanted]


def _fits(free: int) -> str:
    if free == 0:
        return "no cabe ninguna fila"
    return "sólo cabe 1 fila" if free == 1 else f"sólo caben {free} filas"


def _where(layout: CommitmentsLayout | None, tab_name: str, count: int) -> list[str]:
    focus = _focus_label(layout)
    if layout is None:
        return [
            f"En tu pestaña **{tab_name}**, haz clic en la primera celda vacía de "
            f"la columna {focus}, debajo de la última fila de tus compromisos del "
            "mes (Monthly Commitments)."
        ]
    steps: list[str] = []
    if layout.free_rows is not None and layout.free_rows < count:
        missing = count - layout.free_rows
        next_row = layout.first_free_row + layout.free_rows + 1
        times = "1 vez" if missing == 1 else f"{missing} veces"
        steps.append(
            f"Primero haz espacio: ahí {_fits(layout.free_rows)} antes de la "
            f"siguiente sección. Haz clic derecho en el número de la fila "
            f"{next_row} y elige «Insertar 1 fila arriba», {times}."
        )
    cell = cell_ref(layout.first_free_row, layout.focus_col)
    steps.append(
        f"En tu pestaña **{tab_name}**, haz clic en la celda **{cell}**: es la "
        "primera fila vacía debajo de tus compromisos del mes (Monthly "
        f"Commitments), en la columna {focus}."
    )
    return steps


def _critical_number(proposal: RowProposal) -> str:
    if proposal.critical_number == "different":
        return (
            f"Ojo: tu hoja dice que tu Critical Number es "
            f"**{proposal.sheet_critical_number}**, y en lo que trabajamos quedó "
            f"**{proposal.plan_critical_number}**. ¿Cuál es el bueno? No lo toco "
            "hasta que me digas."
        )
    if proposal.critical_number == "add":
        return (
            "Tu hoja todavía no tiene Critical Number. Si quieres, escribe "
            f"**{proposal.plan_critical_number}** en la celda junto a "
            "«Critical Number»."
        )
    return ""


def proposal_message(
    proposal: RowProposal,
    layout: CommitmentsLayout | None,
    tab_name: str,
    paste_block: str,
) -> str:
    """Rows to review, the block to copy, exactly where to paste and how to undo."""
    notes = [note for note in [_critical_number(proposal)] if note]
    if proposal.skipped:
        notes.append(f"Ya tenías escritas: {_join(proposal.skipped)}; no las repito.")
    if not proposal.rows:
        return "\n\n".join(
            [
                "Tu hoja ya tiene tus prioridades del trimestre: no hay nada nuevo "
                "que pegar.",
                *notes,
            ]
        )
    count = len(proposal.rows)
    intro = (
        f"Te propongo {'esta fila' if count == 1 else f'estas {count} filas'} para "
        f"tus compromisos de {proposal.month_name}:"
    )
    if proposal.missing_area:
        notes.append(
            f"No sé el área de: {_join(proposal.missing_area)}. Dime cuál es "
            "(Cash, Strategy, Execution o People) o déjala vacía."
        )
    steps = _where(layout, tab_name, count)
    steps.append(
        f"Copia este bloque y pégalo ahí (Ctrl+V; Cmd+V en Mac):\n\n```\n"
        f"{paste_block}\n```"
    )
    steps.append(
        "Pega sólo ahí, sobre celdas vacías. No pegues arriba, donde está tu "
        "nombre: viene de START HERE."
    )
    numbered = "\n".join(f"{i}. {step}" for i, step in enumerate(steps, 1))
    return "\n\n".join(
        [
            intro,
            render_table(proposal.rows, _table_headers(layout)),
            *notes,
            "Revísalas; si quieres cambiar algo, dímelo antes de pegar. "
            "Para pasarlas a tu hoja:",
            numbered,
            UNDO,
        ]
    )
