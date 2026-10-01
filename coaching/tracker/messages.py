# pyright: strict
"""What ESCALA says to the owner while finding their tab (plain Spanish).

Before the user's "sí" these messages only ever mention tab names, which the
user already sees in Drive. Cells are quoted only from the confirmed tab.
"""

from __future__ import annotations

from coaching.core import owner_area_choice
from coaching.tracker.identity import SheetCandidate, is_placeholder_name
from coaching.tracker.maintenance import (
    DateOrder,
    MeetingPrep,
    ReviewedItem,
    RocksPrep,
)
from coaching.tracker.parser import CommitmentsLayout, Column, cell_ref
from coaching.tracker.proposal import (
    ProposedRow,
    QuarterCheck,
    RockProposal,
    RowProposal,
    quarter_key,
    render_table,
)

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
REVIEW_BEFORE_PASTING = (
    "Revísalas; si quieres cambiar algo, dímelo antes de pegar. "
    "Para pasarlas a tu hoja:"
)
PASTE_ONLY_THERE = (
    "Pega sólo ahí, sobre celdas vacías. No pegues arriba, donde está tu "
    "nombre: viene de START HERE."
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


# S86.2 (A5): the sheet's own names stay, after a Spanish explanation, so the
# owner can find the cell; later mentions in the same message use the name.
_DONE = "terminados (Done)"
_ROCKS = "metas del trimestre (Rocks)"
_CRITICAL_NUMBER = "tu número clave (Critical Number)"
_BELOW_COMMITMENTS = "tus compromisos del mes (Monthly Commitments)"
_BELOW_DONE = f"lo que ya tienes en {_DONE}"


def _where(
    layout: CommitmentsLayout | None,
    tab_name: str,
    count: int,
    below: str = _BELOW_COMMITMENTS,
) -> list[str]:
    focus = _focus_label(layout)
    if layout is None:
        return [
            f"En tu pestaña **{tab_name}**, haz clic en la primera celda vacía de "
            f"la columna {focus}, debajo de la última fila de {below}."
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
        f"primera fila vacía debajo de {below}, en la columna {focus}."
    )
    return steps


def _critical_number(proposal: RowProposal) -> str:
    if proposal.critical_number == "different":
        return (
            f"Ojo: tu hoja dice que {_CRITICAL_NUMBER} es "
            f"**{proposal.sheet_critical_number}**, y en lo que trabajamos quedó "
            f"**{proposal.plan_critical_number}**. ¿Cuál es el bueno? No lo toco "
            "hasta que me digas."
        )
    if proposal.critical_number == "add":
        return (
            f"Tu hoja todavía no tiene {_CRITICAL_NUMBER}. Si quieres, escribe "
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
        notes.append(missing_area_note(proposal.missing_area))
    return "\n\n".join(
        [
            intro,
            render_table(proposal.rows, _table_headers(layout)),
            *notes,
            REVIEW_BEFORE_PASTING,
            _paste_steps(layout, tab_name, count, paste_block, _BELOW_COMMITMENTS),
            UNDO,
        ]
    )


def missing_area_note(items: list[str]) -> str:
    """Ask the area of rows that have none, in the owner's words (S86.2)."""
    return (
        f"No sé de qué parte de tu negocio es: {_join(items)}. ¿Es de "
        f"{owner_area_choice()}? Si no sabes, la dejo vacía."
    )


def _paste_steps(
    layout: CommitmentsLayout | None,
    tab_name: str,
    count: int,
    paste_block: str,
    below: str,
    *extra: str,
) -> str:
    steps = _where(layout, tab_name, count, below)
    steps.append(
        f"Copia este bloque y pégalo ahí (Ctrl+V; Cmd+V en Mac):\n\n```\n"
        f"{paste_block}\n```"
    )
    steps += [PASTE_ONLY_THERE, *extra]
    return "\n".join(f"{i}. {step}" for i, step in enumerate(steps, 1))


# --- S82.7: Rocks rows for the quarter the sheet declares ---------------------

ASK_TABLE = f"¿Las filas son para tus compromisos del mes o para tus {_ROCKS}?"
NO_ROCKS_TABLE = (
    f"No encuentro la tabla de tus {_ROCKS} en tu pestaña (se llama Quarterly "
    "Goals), así que no sé dónde irían. ¿Tu hoja tiene esa sección con otro "
    "nombre?"
)
_BELOW_ROCKS = f"tus {_ROCKS}, en Quarterly Goals"
_ROCK_FIELDS: tuple[Column, ...] = ("focus", "text", "kpi", "due")


def _plan_quarter(check: QuarterCheck) -> str | None:
    planned = check.plan_quarter
    return planned.strip() if planned is not None and quarter_key(planned) else None


def ask_quarter_message(check: QuarterCheck) -> str:
    """The sheet does not say which quarter its Rocks are for: ask, never guess."""
    if check.sheet_quarter is None or not check.sheet_quarter.strip():
        said = f"Tu tabla de {_ROCKS} no dice de qué trimestre es."
    else:
        said = (
            f"Tu tabla de {_ROCKS} dice «{check.sheet_quarter.strip()}» y no sé a qué "
            "trimestre se refiere."
        )
    planned = _plan_quarter(check)
    ask = (
        f"¿Son del **{planned}**?"
        if planned
        else "¿De qué trimestre son? (por ejemplo, Q4-2026)"
    )
    return f"{said} {ask}"


def quarter_mismatch_message(check: QuarterCheck) -> str:
    planned = _plan_quarter(check) or check.plan_quarter or ""
    return (
        f"Tu tabla de {_ROCKS} es del **{check.quarter}** y tus prioridades son del "
        f"**{planned}**. Para no mezclar trimestres no te propongo filas ahí "
        "todavía. Si esa tabla ya es para el trimestre nuevo, cambia su título a "
        f"«Quarterly Goals (Rocks) - {planned}» y te las propongo. ¿Cómo lo "
        "quieres hacer?"
    )


def _rock_columns(layout: CommitmentsLayout) -> tuple[list[str], list[Column]]:
    headers: list[str] = []
    fields: list[Column] = []
    for header, field in zip(layout.headers, layout.fields):
        if field in _ROCK_FIELDS:
            headers.append(header)
            fields.append(field)
    return headers, fields


def _left_out(rows: list[ProposedRow], fields: list[Column]) -> str:
    missing: list[str] = []
    if "kpi" not in fields and any(row.kpi for row in rows):
        missing.append("KPI")
    if "due" not in fields and any(row.due for row in rows):
        missing.append("fecha")
    if not missing:
        return ""
    return (
        f"Tu tabla de Rocks no tiene columna de {' ni de '.join(missing)}: "
        "sólo van el área y el Rock."
    )


def rocks_proposal_message(
    proposal: RockProposal,
    layout: CommitmentsLayout,
    tab_name: str,
    paste_block: str,
) -> str:
    """Rocks rows to review, the block, exactly where to paste and how to undo."""
    quarter = f"**{proposal.quarter}**"
    notes: list[str] = []
    if proposal.skipped:
        notes.append(f"Ya tenías escritos: {_join(proposal.skipped)}; no los repito.")
    if not proposal.rows:
        return "\n\n".join(
            [
                f"Tus {_ROCKS} del {quarter} ya tienen tus prioridades: "
                "no hay nada nuevo que pegar.",
                *notes,
            ]
        )
    count = len(proposal.rows)
    headers, fields = _rock_columns(layout)
    if left_out := _left_out(proposal.rows, fields):
        notes.append(left_out)
    if proposal.missing_area:
        notes.append(missing_area_note(proposal.missing_area))
    intro = (
        f"Te propongo {'esta fila' if count == 1 else f'estas {count} filas'} para "
        f"tus {_ROCKS} del {quarter}:"
    )
    return "\n\n".join(
        [
            intro,
            render_table(proposal.rows, headers, fields),
            *notes,
            REVIEW_BEFORE_PASTING,
            _paste_steps(layout, tab_name, count, paste_block, _BELOW_ROCKS),
            UNDO,
        ]
    )


# --- S82.5: before the group meeting (suggestions only) -----------------------

PREP_NEEDS_CONFIRMED_TAB = (
    "Antes de revisar tu hoja necesito saber cuál es tu pestaña. "
    "¿Me confirmas cuál es la tuya?"
)
PREP_LINK_MISMATCH = (
    "Este archivo no es el que usamos la otra vez. Antes de revisarlo, "
    "¿me confirmas cuál es tu pestaña aquí?"
)
# Clear the cells only: deleting the whole row could break the tab's layout.
CLEAR_MOVED = (
    "Después, si quieres, borra esos compromisos de tu lista del mes: selecciona "
    "sus celdas y presiona Supr (Delete en Mac). No elimines la fila completa."
)
ASK_TODAY = "¿Qué fecha es hoy? Con eso veo qué está vencido."
NOTHING_MOVED = "No moví nada en tu hoja."
PREP_EMPTY = (
    "Tu pestaña todavía no tiene compromisos del mes que revisar. ¿Quieres que "
    "te proponga filas con tus prioridades del trimestre?"
)
PREP_UP_TO_DATE = (
    "Antes de tu reunión: tus compromisos del mes están al día. No veo nada "
    f"vencido, nada cumplido por pasar a {_DONE} ni datos faltantes. ¿Quieres "
    "revisar algo más antes de la reunión?"
)
PREP_ALL_UP_TO_DATE = (
    f"Antes de tu reunión: tus compromisos del mes y tus {_ROCKS} están al "
    f"día. No veo nada vencido, nada cumplido por pasar a {_DONE} ni datos "
    "faltantes. ¿Quieres revisar algo más antes de la reunión?"
)
PREP_ROCKS_ONLY_UP_TO_DATE = (
    "Antes de tu reunión: todavía no tienes compromisos del mes, y tus "
    f"{_ROCKS} están al día. ¿Quieres que te proponga filas con tus prioridades "
    "del trimestre?"
)
_COMMITMENTS_FINE = "Antes de tu reunión: tus compromisos del mes están al día."
_NO_COMMITMENTS = "Antes de tu reunión: todavía no tienes compromisos del mes."


_ORDER_NAMES: dict[DateOrder, str] = {"dd/mm": "día/mes", "mm/dd": "mes/día"}


def _count(items: list[ReviewedItem], one: str, many: str) -> str | None:
    if not items:
        return None
    return f"1 {one}" if len(items) == 1 else f"{len(items)} {many}"


def _headline(prep: MeetingPrep) -> str:
    parts = [
        _count(prep.overdue, "compromiso vencido", "compromisos vencidos"),
        _count(
            prep.finished,
            f"cumplido que puedes pasar a {_DONE}",
            f"cumplidos que puedes pasar a {_DONE}",
        ),
        _count(prep.already_in_done, "que ya está en Done", "que ya están en Done"),
        _count(prep.missing_kpi, "sin KPI", "sin KPI"),
        _count(prep.missing_due, "sin fecha", "sin fecha"),
        _count(prep.unclear_due, "con fecha por confirmar", "con fecha por confirmar"),
    ]
    return f"Antes de tu reunión: {_join([p for p in parts if p])}."


def _section(title: str, items: list[ReviewedItem], detail: str = "") -> str:
    lines = [f"- {item.text}{detail.format(due=item.due)}" for item in items]
    return "\n".join([title, *lines])


def _sections(prep: MeetingPrep) -> list[str]:
    sections: list[str] = []
    if prep.overdue:
        sections.append(_section("**Vencidos:**", prep.overdue, " (era para el {due})"))
    if prep.finished:
        sections.append(_section("**Para pasar a Done:**", prep.finished))
    if prep.already_in_done:
        sections.append(
            _section(
                "**Ya están en Done** (si quieres, bórralos de tus compromisos "
                "del mes):",
                prep.already_in_done,
            )
        )
    if prep.missing_kpi:
        sections.append(_section("**Sin KPI:**", prep.missing_kpi))
    if prep.missing_due:
        sections.append(_section("**Sin fecha:**", prep.missing_due))
    if prep.unclear_due:
        sections.append(
            _section(
                "**Fecha por confirmar** (no la pude leer sin adivinar):",
                prep.unclear_due,
                " («{due}»)",
            )
        )
    return sections


def _done_steps(
    prep: MeetingPrep, layout: CommitmentsLayout | None, tab_name: str, block: str
) -> str:
    count = len(prep.finished)
    numbered = _paste_steps(layout, tab_name, count, block, _BELOW_DONE, CLEAR_MOVED)
    them = "pasarlo" if len(prep.finished) == 1 else "pasarlos"
    return f"Si decides {them} a Done:\n\n{numbered}"


def _missing_ask(kpi: bool, dates: bool, where: str = "") -> str | None:
    if kpi and dates:
        return f"¿Me dices los KPI y las fechas que faltan{where}?"
    if kpi:
        return f"¿Me dices los KPI que faltan{where}?"
    if dates:
        return f"¿Me dices las fechas que faltan{where}?"
    return None


def _decisions(prep: MeetingPrep) -> list[str]:
    if not prep.has_commitment_findings:
        return []
    asks: list[str] = []
    if len(prep.finished) == 1:
        asks.append(f"¿Pasas «{prep.finished[0].text}» a Done?")
    elif prep.finished:
        asks.append("¿Pasas los terminados a Done?")
    if len(prep.overdue) == 1:
        asks.append(
            f"¿Qué hacemos con «{prep.overdue[0].text}»: nueva fecha o ya no va?"
        )
    elif prep.overdue:
        asks.append("¿Qué hacemos con los vencidos: nueva fecha o ya no van?")
    missing = _missing_ask(
        bool(prep.missing_kpi), bool(prep.missing_due or prep.unclear_due)
    )
    asks += [missing] if missing else []
    if not asks:
        asks.append("¿Borras de tus compromisos del mes lo que ya está en Done?")
    return asks


def _rocks_title(rocks: RocksPrep) -> str:
    return f"del {rocks.quarter}" if rocks.quarter else "del trimestre"


def _rocks_block(rocks: RocksPrep) -> str:
    """The Rocks findings, apart from the commitments (S82.7)."""
    parts = [
        _count(rocks.overdue, "vencido", "vencidos"),
        _count(rocks.missing_kpi, "sin KPI", "sin KPI"),
        _count(rocks.missing_due, "sin fecha", "sin fecha"),
        _count(rocks.unclear_due, "con fecha por confirmar", "con fecha por confirmar"),
    ]
    lines = [
        f"**Tus {_ROCKS} {_rocks_title(rocks)}:** {_join([p for p in parts if p])}.",
        *(f"- Vencido: {i.text} (era para el {i.due})" for i in rocks.overdue),
        *(f"- Sin KPI: {i.text}" for i in rocks.missing_kpi),
        *(f"- Sin fecha: {i.text}" for i in rocks.missing_due),
        *(f"- Fecha por confirmar: {i.text} («{i.due}»)" for i in rocks.unclear_due),
    ]
    return "\n".join(lines)


def _rock_decisions(rocks: RocksPrep) -> list[str]:
    asks: list[str] = []
    if len(rocks.overdue) == 1:
        asks.append(
            f"¿Qué hacemos con el Rock «{rocks.overdue[0].text}»: nueva fecha o "
            "ya no va este trimestre?"
        )
    elif rocks.overdue:
        asks.append(
            "¿Qué hacemos con los Rocks vencidos: nueva fecha o ya no van este "
            "trimestre?"
        )
    missing = _missing_ask(
        bool(rocks.missing_kpi),
        bool(rocks.missing_due or rocks.unclear_due),
        " en tus Rocks",
    )
    return [*asks, missing] if missing else asks


def _up_to_date(prep: MeetingPrep) -> str:
    if prep.rocks.reviewed == 0:
        return PREP_UP_TO_DATE
    return PREP_ALL_UP_TO_DATE if prep.reviewed else PREP_ROCKS_ONLY_UP_TO_DATE


def prep_message(
    prep: MeetingPrep,
    done_layout: CommitmentsLayout | None,
    tab_name: str,
    done_block: str,
) -> str:
    """Short summary for the meeting; says nothing was moved; ends with a decision.

    Commitments come first; the Rocks follow in their own block (S82.7).
    """
    if prep.reviewed == 0 and prep.rocks.reviewed == 0:
        return PREP_EMPTY
    if not prep.has_findings:
        return _up_to_date(prep)
    if prep.has_commitment_findings:
        parts = [_headline(prep), *_sections(prep)]
    else:
        parts = [_COMMITMENTS_FINE if prep.reviewed else _NO_COMMITMENTS]
    if prep.finished:
        parts += [_done_steps(prep, done_layout, tab_name, done_block), UNDO]
    if prep.rocks.has_findings:
        parts.append(_rocks_block(prep.rocks))
    if prep.ordered_dates and prep.date_order is not None:
        dates = _join([f"«{due}»" for due in prep.ordered_dates])
        parts.append(
            f"Leí {dates} como {_ORDER_NAMES[prep.date_order]}, igual que las "
            "demás fechas de tu hoja."
        )
    decisions = [*_decisions(prep), *_rock_decisions(prep.rocks)]
    parts += [NOTHING_MOVED, " ".join(decisions)]
    return "\n\n".join(parts)
