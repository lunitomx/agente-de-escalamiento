"""SessionCloseOrchestrator — escala-cierra (Session Close with Learning).

Orchestrates the session closing flow for the Escala coaching server:
captures learnings/decisions, detects worksheet changes, extracts facts,
updates the knowledge graph, persists session update, and writes a
markdown session log.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ..daos.change_dao import ChangeDAO
from ..daos.company_dao import CompanyDAO
from ..daos.session_dao import SessionDAO
from ..daos.worksheet_dao import WorksheetDAO
from ..diff import dict_diff
from ..graph_engine import GraphEngine
from ..memory_engine import MemoryEngine


@dataclass
class SessionCloseResult:
    """Result returned when a session is closed.

    Attributes:
        session_id: The session identifier.
        duration: Human-readable duration string (e.g. "45m 12s").
        changes_count: Number of field-level changes detected.
        new_facts_count: Number of new memory facts created.
        summary: Human-readable summary of the closing operation.
    """

    session_id: str = ""
    duration: str = ""
    changes_count: int = 0
    new_facts_count: int = 0
    summary: str = ""


class SessionCloseOrchestrator:
    """Orchestrates the session-close flow for Escala.

    Captures learnings (¿Qué aprendiste? ¿Qué decidiste?), detects
    worksheet changes via dict_diff, extracts memory facts from
    changes, updates the knowledge graph, persists session status,
    and writes a markdown session log.

    Usage::

        orch = SessionCloseOrchestrator("data/escala.db")
        result = orch.close_session(
            session_id="abc123",
            learnings="Necesitamos más capital de trabajo.",
            decisions="Aumentar presupuesto de marketing 20 %.",
        )
        print(result.summary)
        # Sesión abc123 cerrada. Duración: 45m 12s. 3 cambios detectados.
        # 5 datos aprendidos.
    """

    def __init__(self, db_path: str) -> None:
        """Initialise all DAOs, MemoryEngine, and GraphEngine.

        Args:
            db_path: Path to the SQLite database (or ``:memory:`` /
                     ``file:…?mode=memory&cache=shared`` URI).
        """
        self._db_path = db_path
        self._session_dao = SessionDAO(db_path)
        self._worksheet_dao = WorksheetDAO(db_path)
        self._company_dao = CompanyDAO(db_path)
        self._change_dao = ChangeDAO(db_path)
        self._memory = MemoryEngine(db_path)
        self._graph = GraphEngine(db_path)

    # ── main entry point ─────────────────────────────────────────

    def close_session(
        self,
        session_id: str,
        learnings: str | None = None,
        decisions: str | None = None,
    ) -> SessionCloseResult:
        """Close a coaching session, capturing learnings and changes.

        Steps performed:

        1. Look up the session, resolve company, compute duration.
        2. Capture *learnings* and *decisions* as memory facts.
        3. Detect worksheet changes (version diffs via
           WorksheetDAO + ``dict_diff``).
        4. Extract a memory fact from every detected change.
        5. Update the knowledge graph with entities/relationships.
        6. Persist session status → ``'closed'`` in SessionDAO.
        7. Write a markdown log to
           ``~/.escala/{company}/sessions/session_{id}.md``.

        Args:
            session_id: The session to close.
            learnings: Free-text description of what was learned
                       (¿Qué aprendiste?).  Stored as a fact.
            decisions: Free-text description of what was decided
                       (¿Qué decidiste?).  Stored as a fact.

        Returns:
            SessionCloseResult with counts, duration, and a summary.
        """
        # 1. Look up session
        session = self._session_dao.get(session_id)
        if session is None:
            return SessionCloseResult(
                session_id=session_id,
                summary=f"Session {session_id} not found.",
            )

        company_id = session.get("company_id", "")
        company_name = "my-company"
        if company_id:
            company = self._company_dao.get(company_id)
            if company:
                company_name = company.get("name", "my-company")

        # Compute duration
        created_at = session.get("created_at", "")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        duration = _compute_duration(created_at)

        facts_created = 0

        # 2. Capture learnings & decisions as memory facts
        if learnings:
            self._memory.add_fact(
                content=f"Aprendizaje: {learnings}",
                category="learning",
                tags=["session", "aprendizaje"],
                source=session_id,
            )
            facts_created += 1

        if decisions:
            self._memory.add_fact(
                content=f"Decisión: {decisions}",
                category="decision",
                tags=["session", "decisión"],
                source=session_id,
            )
            facts_created += 1

        # 3. Detect worksheet changes and 4. extract facts from them
        changes = self._detect_and_log_changes(session_id, company_id)

        for change in changes:
            content = _change_to_fact_text(change)
            self._memory.add_fact(
                content=content,
                category="change",
                tags=["session", "worksheet", "cambio"],
                source=session_id,
            )
            facts_created += 1

        # 5. Update knowledge graph
        if changes:
            self._update_graph_for_changes(changes, session_id)

        # 6. Persist session update
        metadata = {
            "summary": (
                f"Sesión cerrada con {facts_created} datos aprendidos"
                f" y {len(changes)} cambios."
            ),
            "learnings": learnings or "",
            "decisions": decisions or "",
            "changes_count": len(changes),
            "facts_count": facts_created,
        }
        self._session_dao.update(session_id, {"status": "closed", "metadata": metadata})

        # 7. Write markdown log
        self._write_markdown_log(
            session_id=session_id,
            company_id=company_id,
            company_name=company_name,
            created_at=created_at,
            closed_at=now_str,
            duration=duration,
            learnings=learnings,
            decisions=decisions,
            changes=changes,
            facts_count=facts_created,
        )

        summary_parts = [
            f"Sesión {session_id} cerrada.",
            f"Duración: {duration}.",
        ]
        if len(changes) == 1:
            summary_parts.append("1 cambio detectado.")
        else:
            summary_parts.append(f"{len(changes)} cambios detectados.")
        if facts_created == 1:
            summary_parts.append("1 dato aprendido.")
        else:
            summary_parts.append(f"{facts_created} datos aprendidos.")

        return SessionCloseResult(
            session_id=session_id,
            duration=duration,
            changes_count=len(changes),
            new_facts_count=facts_created,
            summary=" ".join(summary_parts),
        )

    # ── change detection ─────────────────────────────────────────

    def _detect_and_log_changes(
        self, session_id: str, company_id: str
    ) -> list[dict[str, Any]]:
        """Find worksheet versions saved during *session_id* and diff them.

        For each worksheet row tagged with *session_id*, the method
        loads the preceding version (version – 1, same category +
        tool) and runs ``dict_diff``.  Every field-level difference is
        also recorded in ``changes_log`` via ChangeDAO.

        Returns a list of change-entry dicts with keys:
        ``session_id``, ``category``, ``tool``, ``field``,
        ``old_value``, ``new_value``, ``diff_type``.
        """
        all_changes: list[dict[str, Any]] = []
        conn = self._session_dao.get_connection()

        rows = conn.execute(
            """SELECT * FROM worksheets
               WHERE session_id = ?
               ORDER BY category, tool, version""",
            (session_id,),
        ).fetchall()

        for row in rows:
            row_dict = dict(row)
            category = str(row_dict["category"])
            tool = str(row_dict["tool"])
            version = int(row_dict["version"])

            current_data = _decode_json(row_dict.get("data", "{}"))

            # Load previous version (or empty dict for v1)
            if version > 1:
                prev = conn.execute(
                    """SELECT data FROM worksheets
                       WHERE category = ? AND tool = ? AND version = ?""",
                    (category, tool, version - 1),
                ).fetchone()
                prev_data = _decode_json(prev["data"]) if prev else {}
            else:
                prev_data = {}

            diffs = dict_diff(prev_data, current_data)

            for diff in diffs:
                old_val = diff.get("old_value")
                new_val = diff.get("new_value")

                if old_val is not None and new_val is not None:
                    dtype = "update"
                elif old_val is None:
                    dtype = "create"
                else:
                    dtype = "delete"

                change_entry = {
                    "session_id": session_id,
                    "category": category,
                    "tool": tool,
                    "field": diff["field"],
                    "old_value": old_val,
                    "new_value": new_val,
                    "diff_type": dtype,
                }
                all_changes.append(change_entry)

                # Persist to changes_log
                self._change_dao.log(
                    company_id=company_id,
                    session_id=session_id,
                    category=category,
                    tool=tool,
                    field=diff["field"],
                    old_value=_safe_str(old_val),
                    new_value=_safe_str(new_val),
                    diff_type=dtype,
                )

        return all_changes

    # ── graph updates ────────────────────────────────────────────

    def _update_graph_for_changes(
        self, changes: list[dict[str, Any]], session_id: str
    ) -> None:
        """Create entities and relationships for detected changes.

        Builds a session entity, per-tool entities, per-field entities,
        and wires them together with ``modified_tool``, ``has_field``,
        and ``changed_field`` relationships.
        """
        session_entity_id = self._graph.add_entity(
            name=f"session:{session_id}",
            entity_type="session",
            properties={"id": session_id},
        )

        tool_cache: dict[str, int] = {}
        field_cache: dict[str, int] = {}

        for change in changes:
            category = change.get("category", "")
            tool = change.get("tool", "")
            field = change.get("field", "")

            # Tool entity (once per unique tool)
            tool_key = f"{category}/{tool}"
            if tool_key not in tool_cache:
                tool_cache[tool_key] = self._graph.add_entity(
                    name=f"tool:{tool}",
                    entity_type="tool",
                    properties={"category": category},
                )
                self._graph.add_relationship(
                    session_entity_id,
                    tool_cache[tool_key],
                    "modified_tool",
                    weight=1.0,
                )

            # Field entity (once per unique field)
            field_key = f"{category}/{tool}/{field}"
            if field_key not in field_cache:
                field_cache[field_key] = self._graph.add_entity(
                    name=f"field:{category}.{tool}.{field}",
                    entity_type="field",
                    properties={"category": category, "tool": tool},
                )
                self._graph.add_relationship(
                    tool_cache[tool_key],
                    field_cache[field_key],
                    "has_field",
                    weight=1.0,
                )

            # Link session → field
            self._graph.add_relationship(
                session_entity_id,
                field_cache[field_key],
                "changed_field",
                weight=1.0,
            )

    # ── markdown log ─────────────────────────────────────────────

    def _write_markdown_log(
        self,
        session_id: str,
        company_id: str,
        company_name: str,
        created_at: str,
        closed_at: str,
        duration: str,
        learnings: str | None,
        decisions: str | None,
        changes: list[dict[str, Any]],
        facts_count: int,
    ) -> str:
        """Write a markdown session summary.

        Path: ``~/.escala/{sanitised-company}/sessions/session_{id}.md``
        """
        safe_name = company_name.lower().replace(" ", "-")
        log_dir = Path.home() / ".escala" / safe_name / "sessions"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"session_{session_id}.md"

        lines: list[str] = [
            f"# Sesión: {session_id}",
            "",
            f"- **Empresa:** {company_name} ({company_id or 'N/A'})",
            f"- **Inicio:** {created_at}",
            f"- **Cierre:** {closed_at}",
            f"- **Duración:** {duration}",
            "- **Estado:** closed",
            "",
            "## Aprendizajes",
            "",
            learnings if learnings else "*Sin aprendizajes registrados.*",
            "",
            "## Decisiones",
            "",
            decisions if decisions else "*Sin decisiones registradas.*",
            "",
            "## Cambios detectados",
            "",
            f"- **Total de cambios:** {len(changes)}",
            f"- **Total de datos aprendidos:** {facts_count}",
            "",
        ]

        if changes:
            lines.extend(
                [
                    "| Categoría | Herramienta | Campo | Anterior | Nuevo | Tipo |",
                    "|-----------|-------------|-------|----------|-------|------|",
                ]
            )
            for c in changes:
                old = str(c.get("old_value", "-") or "-")
                new = str(c.get("new_value", "-") or "-")
                lines.append(
                    f"| {c['category']} | {c['tool']} | {c['field']} "
                    f"| {old} | {new} | {c.get('diff_type', 'update')} |"
                )
        else:
            lines.append("*No se detectaron cambios.*")

        lines.append("")
        log_path.write_text("\n".join(lines), encoding="utf-8")
        return str(log_path)


# ── module-level helpers ─────────────────────────────────────────────


def _compute_duration(created_at: str) -> str:
    """Return a human-readable duration from *created_at* to now."""
    if not created_at:
        return "desconocida"
    try:
        start = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return "desconocida"
    delta = datetime.now() - start
    secs = int(delta.total_seconds())
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def _decode_json(raw: str | dict[str, Any]) -> dict[str, Any]:
    """Decode a JSON string to dict, or return the dict as-is."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def _safe_str(value: Any) -> str | None:
    """Stringify *value* for storage, or return None if None."""
    if value is None:
        return None
    return str(value)


def _change_to_fact_text(change: dict[str, Any]) -> str:
    """Turn a change entry into a human-readable fact sentence."""
    cat = change.get("category", "")
    tool = change.get("tool", "")
    field = change.get("field", "")
    old_val = change.get("old_value")
    new_val = change.get("new_value")

    if old_val is not None and new_val is not None:
        return f"Cambio en {cat}/{tool}: '{field}' pasó de '{old_val}' a '{new_val}'"
    if old_val is None:
        return f"Nuevo campo en {cat}/{tool}: '{field}' = '{new_val}'"
    return f"Campo eliminado en {cat}/{tool}: '{field}' (era '{old_val}')"
