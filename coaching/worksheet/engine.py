"""coaching.worksheet.engine — pure logic for worksheet loading and guidance.

No I/O. Accepts worksheet data and registry, returns structured worksheet dict.
"""

from __future__ import annotations


def find_worksheet(registry: list[dict], worksheet_id: str) -> dict | None:
    for w in registry:
        if w.get("id") == worksheet_id:
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
