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
from .change_dao import ChangeDAO
from .company_dao import CompanyDAO
from .schema import init_db
from .session_dao import SessionDAO
from .worksheet_dao import WorksheetDAO

__all__ = [
    "BaseDAO",
    "ChangeDAO",
    "CompanyDAO",
    "SessionDAO",
    "WorksheetDAO",
    "init_db",
]
