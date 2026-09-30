# pyright: strict
"""What ESCALA tells the owner during a research (plain Spanish, E83 S83.1).

Never the words "módulo", "triangulación", "TAM" or a procedure name. Every
research result ends in a question about the decision.
"""

from __future__ import annotations

from datetime import date

_MONTHS = (
    "enero febrero marzo abril mayo junio julio agosto septiembre octubre "
    "noviembre diciembre"
).split()

# Owner decision (2026-09-30): web search is assumed; without it, one line
# saying it is off and how to turn it on, then offer the owner's own sources.
SEARCH_OFF = (
    "Aquí la búsqueda en internet está apagada: puedes prenderla en el menú de "
    "herramientas o en la configuración de este asistente, o pégame dos o tres "
    "fuentes (el link de un competidor, una cotización que te llegó, lo que te "
    "dicen tus clientes) y sigo con eso, diciéndote hasta dónde llega."
)
LINK_IN_REPORT = "(enlace en el reporte)"
STALE_MARK = "[vencida] "
DETAIL_UNREADABLE = "no pude leer el detalle"
NEEDS_OFFER = (
    "¿Qué vendes exactamente y en qué ciudad o zona? Con eso armo las búsquedas."
)
NO_SAFE_QUERY = (
    "No armé búsquedas que no lleven datos de tu empresa. ¿Me dices con otras "
    "palabras qué vendes y dónde?"
)
NEEDS_CHOICE = "Antes de guardar necesito que me digas cuál opción tomas."
NOTHING_CONTRARY = "No encontré fuentes que digan lo contrario."
NOTHING_MISSING = "Encontré algo para cada punto que buscamos."
NOT_COUNTED = "No los cuento hasta que me digas que se parecen al tuyo."
NO_COUNTED_COMPARABLES = (
    "Todavía no hay negocios parecidos al tuyo que me hayas confirmado."
)
WHICH_LOOK_ALIKE = "¿Cuáles se parecen al tuyo? Sólo cuento los que me digas que sí."
NOT_FOUND_CELL = "no encontrado"
ONLY_THE_TABLE = "Lo que encontré: lo que está en la tabla, con su fuente."
TABLE_GAPS = "Lo que en la tabla dice «no encontrado»: no hallé una fuente que lo diga."


def comparing_with(names: list[str]) -> str:
    return f"Voy a comparar con: {_join(names)}."


def table_title(offer: str, geography: str) -> str:
    return f"Cómo lo hacen negocios parecidos ({offer} en {geography}):"


def candidates_intro(offer: str, geography: str) -> str:
    return (
        f"Encontré estos negocios que venden {offer} en {geography} y podrían "
        "parecerse al tuyo:"
    )


def spanish_date(value: date) -> str:
    return f"{value.day} de {_MONTHS[value.month - 1]} de {value.year}"


def no_search_limit(source_count: int) -> str:
    fuentes = "fuente" if source_count == 1 else "fuentes"
    return (
        "En este asistente no hubo búsqueda en internet; usé "
        f"{source_count} {fuentes} que tú diste."
    )


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " y " + items[-1]


def join_names(names: list[str]) -> str:
    return _join(names)


def frame_message(decision_informed: str, queries: list[str]) -> str:
    """One message: the decision it informs, the searches, and the permission."""
    searches = _join([f"*{query}*" for query in queries])
    return (
        f"Quieres decidir: {decision_informed}. Voy a buscar: {searches}. "
        "No llevo tu nombre ni tus cifras. ¿Va, o cambio algo?"
    )


def saved_message(review_by: date) -> str:
    return (
        "Listo, quedó guardado en tu carpeta con tu decisión. La próxima vez "
        "que veamos tu empresa, parto de esta decisión. Conviene revisarlo "
        f"antes del {spanish_date(review_by)}."
    )


def stale_offer(question: str, researched_on: date, review_by: date) -> str:
    """A research past its review date is offered for refresh before use."""
    return (
        f"Tu investigación «{question}» es del {spanish_date(researched_on)} y ya "
        f"pasó su fecha de revisión ({spanish_date(review_by)}). ¿La actualizamos "
        "antes de usarla para ver tu empresa?"
    )


def sources_to_open(count: int) -> str:
    return (
        f"Elegí {count} fuentes del reporte. Abre cada enlace y dame el texto "
        "de la página; reviso si la cita está ahí."
    )


def sources_checked(found: int, missing: int, unchecked: int) -> str:
    text = f"Revisé las fuentes: {found} con la cita en la página, {missing} sin ella"
    if unchecked:
        text += f" y {unchecked} sin revisar"
    if missing:
        text += ". Las que no la tienen no cuentan hasta volver a confirmarlas"
    return text + "."
