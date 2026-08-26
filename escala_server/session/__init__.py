"""Escala Session package.

Provides orchestrators for the session lifecycle:
  - SessionStartOrchestrator — initializes coaching sessions with full
    context (company profile, recent sessions, memory facts, worksheet
    changes, and server health).
  - SessionCloseOrchestrator — closes sessions, captures learnings/
    decisions, detects worksheet changes, extracts facts, updates the
    knowledge graph, persists status, and writes a markdown log.
"""

from .session_close import SessionCloseOrchestrator, SessionCloseResult
from .session_start import SessionContext, SessionStartOrchestrator

__all__ = [
    "SessionCloseOrchestrator",
    "SessionCloseResult",
    "SessionContext",
    "SessionStartOrchestrator",
]
