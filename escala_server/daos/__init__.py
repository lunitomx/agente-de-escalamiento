"""Escala DAO layer — SQLite-backed data access objects.

Public exports:
    BaseDAO        — base class with get_connection()
    init_db        — schema initialisation (re-exported from escala_server.schema)
    CompanyDAO     — CRUD for companies
    WorksheetDAO   — versioned CRUD for worksheets
    SessionDAO     — CRUD for coaching sessions
    ChangeDAO      — audit-log for field-level changes
"""

from .base import BaseDAO
from .schema import init_db
from .company_dao import CompanyDAO
from .worksheet_dao import WorksheetDAO
from .session_dao import SessionDAO
from .change_dao import ChangeDAO

__all__ = [
    "BaseDAO",
    "init_db",
    "CompanyDAO",
    "WorksheetDAO",
    "SessionDAO",
    "ChangeDAO",
]
