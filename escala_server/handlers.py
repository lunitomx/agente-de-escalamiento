"""In-memory data handlers for the Escala server API.

These are temporary implementations backed by Python dicts.
S18.8 will replace them with SQLite persistence.
"""

import uuid
from typing import Any


class DAOBase:
    """Base class for in-memory DAOs."""

    def __init__(self):
        self._data: dict[str, Any] = {}


class CompaniesHandler(DAOBase):
    """Handle CRUD for company profiles."""

    def list_companies(self) -> dict:
        return {"data": list(self._data.values()), "status": "ok"}

    def create_company(self, company_data: dict) -> dict:
        company_id = str(uuid.uuid4())[:8]
        company = {"id": company_id, **company_data}
        self._data[company_id] = company
        return {"data": company, "status": "ok"}

    def get_company(self, company_id: str) -> dict:
        company = self._data.get(company_id)
        if company is None:
            return {"status": "error", "message": f"Company {company_id} not found"}
        return {"data": company, "status": "ok"}

    def update_company(self, company_id: str, updates: dict) -> dict:
        company = self._data.get(company_id)
        if company is None:
            return {"status": "error", "message": f"Company {company_id} not found"}
        company.update(updates)
        return {"data": company, "status": "ok"}


class WorksheetsHandler(DAOBase):
    """Handle CRUD for worksheet data."""

    def get_worksheets(self, category: str, tool: str) -> dict:
        key = f"{category}/{tool}"
        return {"data": self._data.get(key, {}), "status": "ok"}

    def save_worksheet(self, category: str, tool: str, payload: dict) -> dict:
        key = f"{category}/{tool}"
        self._data[key] = payload
        return {"data": payload, "status": "ok"}


class SessionsHandler(DAOBase):
    """Handle session management."""

    def list_sessions(self) -> dict:
        return {"data": list(self._data.values()), "status": "ok"}

    def create_session(self, session_data: dict) -> dict:
        session_id = str(uuid.uuid4())[:8]
        session = {"id": session_id, **session_data}
        self._data[session_id] = session
        return {"data": session, "status": "ok"}

    def get_session(self, session_id: str) -> dict:
        session = self._data.get(session_id)
        if session is None:
            return {"status": "error", "message": f"Session {session_id} not found"}
        return {"data": session, "status": "ok"}
