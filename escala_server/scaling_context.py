"""Coaching Skill Helper — access ESCALA context from coaching sessions.

Provides a simple function that any Escala coaching skill can import
to retrieve relevant context from the ESCALA knowledge graph.

Usage::

    from escala_server.scaling_context import get_scaling_context

    # By category
    ctx = get_scaling_context(category="cash")
    # -> {"principles": [...], "habits": [...], "entities": [...], "status": "ok"}

    # By specific tool
    ctx = get_scaling_context(tool="Power of One")
    # -> {"tool": {...}, "entities": [...], "principles": [...], "status": "ok"}
"""

from __future__ import annotations

from pathlib import Path

from .graph_engine import GraphEngine
from .knowledge_handler import KnowledgeHandler


def _default_db_path() -> str:
    """Return the default Escala database path."""
    return str(Path.home() / ".escala" / "escala.db")


def get_scaling_context(
    category: str | None = None,
    tool: str | None = None,
    db_path: str | None = None,
) -> dict:
    """Get relevant context from the ESCALA knowledge graph.

    Args:
        category: Filter by category (cash, strategy, people, execution).
        tool:     Specific tool name (e.g. "Power of One").
        db_path:  Optional custom database path. Defaults to ~/.escala/escala.db.

    Returns:
        A dict with ``principles``, ``habits``, ``entities`` (and optionally
        ``tool`` and ``category`` keys) plus a ``status`` field.

    Examples::

        >>> ctx = get_scaling_context(category="execution")
        >>> ctx["status"]
        'ok'
        >>> len(ctx["principles"])
        3
    """
    if not category and not tool:
        return {"status": "error", "message": "requires 'category' or 'tool' parameter"}

    path = db_path or _default_db_path()
    graph = GraphEngine(path)
    handler = KnowledgeHandler(graph)
    return handler.get_context(category=category, tool=tool)
