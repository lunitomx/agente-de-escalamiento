"""coaching.worksheet.engine — pure logic for worksheet loading and guidance.

No I/O. Accepts worksheet data and registry, returns structured worksheet dict.
"""

from __future__ import annotations

import unicodedata


def plain(text: str) -> str:
    """Lowercase ``text`` without accents, so "Página" matches "pagina"."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def find_worksheet(registry: list[dict], query: str) -> dict | None:
    """The one lookup rule (S87.7 D8).

    An exact id wins over every entry. Then the id without case, then
    ``query`` inside ``name`` or ``name_es``, both without case or accents.
    """
    for w in registry:
        if w.get("id") == query:
            return w
    wanted = plain(query.strip())
    if not wanted:
        return None
    for w in registry:
        if plain(str(w.get("id", ""))) == wanted:
            return w
    for w in registry:
        names = (str(w.get("name") or ""), str(w.get("name_es") or ""))
        if any(wanted in plain(name) for name in names):
            return w
    return None


def list_worksheets(registry: list[dict], decision: str | None = None) -> list[dict]:
    if decision:
        return [w for w in registry if w.get("decision") == decision]
    return list(registry)


def check_prerequisites(
    registry: list[dict], worksheet_id: str, completed: set[str]
) -> list[str]:
    ws = find_worksheet(registry, worksheet_id)
    if not ws:
        return [f"Worksheet not found: {worksheet_id}"]
    missing = []
    for prereq in ws.get("prerequisites", []):
        if prereq not in completed:
            missing.append(prereq)
    return missing


def build_worksheet_session(worksheet_meta: dict, worksheet_content: dict) -> dict:
    fields = worksheet_content.get("fields", [])
    sections = worksheet_content.get("sections", [])

    return {
        "id": worksheet_meta.get("id", ""),
        "name": worksheet_meta.get("name", ""),
        "decision": worksheet_meta.get("decision", ""),
        "difficulty": worksheet_meta.get("difficulty", ""),
        "time_estimate": worksheet_meta.get("time_estimate", ""),
        "fields": fields,
        "sections": sections,
        "total_fields": len(fields),
        "outputs": worksheet_meta.get("outputs", []),
    }
