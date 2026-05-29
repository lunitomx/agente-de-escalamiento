"""Escala HTTP Server — serves static files and API endpoints."""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

from .cors import CORSHandler
from .handlers import CompaniesHandler, WorksheetsHandler, SessionsHandler, MemoryHandler
from .router import Router


class EscalaRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler that routes to static files or API handlers."""

    # Class-level state (set by make_server)
    static_root: str = ""
    router: Router = Router()
    companies: CompaniesHandler = None  # type: ignore
    worksheets: WorksheetsHandler = None  # type: ignore
    sessions: SessionsHandler = None  # type: ignore
    memory: MemoryHandler = None  # type: ignore

    def do_GET(self):
        path = self.path
        # Try API route first
        handler, params = self.router.dispatch("GET", path)
        if handler:
            self._send_json_response(handler(**params))
            return
        # Fall back to static file
        self._serve_static(path)

    def do_POST(self):
        handler, params = self.router.dispatch("POST", self.path)
        if not handler:
            self._send_json_error(404, "Not found")
            return
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        payload = json.loads(body) if body else {}
        self._send_json_response(handler(payload=payload, **params))

    def do_PATCH(self):
        handler, params = self.router.dispatch("PATCH", self.path)
        if not handler:
            self._send_json_error(404, "Not found")
            return
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        payload = json.loads(body) if body else {}
        self._send_json_response(handler(payload=payload, **params))

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self._add_cors_headers()
        self.end_headers()

    def _serve_static(self, path: str):
        """Serve a static file from the configured root."""
        # Remove query strings
        path = path.split("?")[0]

        # Default to index.html for root
        if path == "/" or path == "":
            path = "/index.html"

        # Resolve path safely (prevent directory traversal)
        requested = Path(self.static_root + path).resolve()
        static_root_resolved = Path(self.static_root).resolve()

        if not str(requested).startswith(str(static_root_resolved)):
            self._send_json_error(403, "Forbidden")
            return

        if not requested.exists() or not requested.is_file():
            self._send_json_error(404, "Not found")
            return

        # Determine content type
        ext = requested.suffix.lower()
        content_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".woff": "font/woff",
            ".woff2": "font/woff2",
        }
        content_type = content_types.get(ext, "application/octet-stream")

        try:
            with open(requested, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self._add_cors_headers()
            self.end_headers()
            self.wfile.write(content)
        except OSError:
            self._send_json_error(500, "Internal server error")

    def _send_json_response(self, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._add_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_json_error(self, status_code: int, message: str):
        body = json.dumps({"status": "error", "message": message}).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._add_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _add_cors_headers(self):
        for key, value in CORSHandler.get_headers().items():
            self.send_header(key, value)

    def log_message(self, format, *args):
        """Override to add timestamp prefix."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {args[0]} {args[1]} {args[2]}")


def make_server(
    host: str = "localhost",
    port: int = 8080,
    static_root: str = ".",
    db_path: str | None = None,
) -> HTTPServer:
    """Create and configure an Escala server instance.

    Args:
        host: Host to bind to
        port: Port to bind to
        static_root: Root directory for static files
        db_path: Path to SQLite database (default: ~/.escala/escala.db)
    """
    if db_path is None:
        db_path = str(Path.home() / ".escala" / "escala.db")

    from .daos import CompanyDAO
    from .handlers import WorksheetsHandler, SessionsHandler

    EscalaRequestHandler.static_root = str(Path(static_root).resolve())
    EscalaRequestHandler.router = _build_router()
    EscalaRequestHandler.companies = CompaniesHandler(db_path)
    EscalaRequestHandler.worksheets = WorksheetsHandler(db_path)
    EscalaRequestHandler.sessions = SessionsHandler(db_path)
    EscalaRequestHandler.memory = MemoryHandler(db_path)

    server = HTTPServer((host, port), EscalaRequestHandler)
    return server


def _build_router() -> Router:
    """Build and return the API route table."""
    router = Router()

    @router.get("/api/health")
    def health_check():
        return {"status": "ok", "service": "escala-server", "version": "0.1.0"}

    @router.get("/api/companies")
    def list_companies():
        return EscalaRequestHandler.companies.list_companies()

    @router.post("/api/companies")
    def create_company(payload=None):
        return EscalaRequestHandler.companies.create_company(payload or {})

    @router.get("/api/companies/{company_id}")
    def get_company(company_id=None):
        return EscalaRequestHandler.companies.get_company(company_id)

    @router.patch("/api/companies/{company_id}")
    def update_company(company_id=None, payload=None):
        return EscalaRequestHandler.companies.update_company(company_id, payload or {})

    @router.get("/api/worksheets/{category}/{tool}")
    def get_worksheet(category=None, tool=None):
        return EscalaRequestHandler.worksheets.get_worksheets(category, tool)

    @router.post("/api/worksheets/{category}/{tool}")
    def save_worksheet(category=None, tool=None, payload=None):
        return EscalaRequestHandler.worksheets.save_worksheet(
            category, tool, payload or {}
        )

    @router.get("/api/worksheets/{category}/{tool}/changes")
    def get_worksheet_changes(category=None, tool=None):
        changes = EscalaRequestHandler.worksheets.get_changes(category, tool)
        return {"data": changes, "status": "ok"}

    @router.get("/api/sessions")
    def list_sessions():
        return EscalaRequestHandler.sessions.list_sessions()

    @router.post("/api/sessions")
    def create_session(payload=None):
        return EscalaRequestHandler.sessions.create_session(payload or {})

    @router.get("/api/sessions/{session_id}")
    def get_session(session_id=None):
        return EscalaRequestHandler.sessions.get_session(session_id)

    # ── Memory & Knowledge Graph routes ──────────────────────────

    @router.get("/api/memory/context")
    def memory_context():
        return EscalaRequestHandler.memory.context()

    @router.get("/api/memory/facts")
    def memory_list_facts(
        query: str = "",
        category: str | None = None,
        tags: str | None = None,
        min_trust: float = 0.0,
    ):
        return EscalaRequestHandler.memory.list_facts(
            query=query, category=category, tags=tags, min_trust=min_trust
        )

    @router.post("/api/memory/facts")
    def memory_create_fact(payload=None):
        return EscalaRequestHandler.memory.create_fact(payload or {})

    @router.get("/api/memory/graph/{entity_id}")
    def memory_get_entity(entity_id=None):
        return EscalaRequestHandler.memory.get_entity(int(entity_id))

    @router.post("/api/memory/entities")
    def memory_create_entity(payload=None):
        return EscalaRequestHandler.memory.create_entity(payload or {})

    @router.post("/api/memory/relationships")
    def memory_create_relationship(payload=None):
        return EscalaRequestHandler.memory.create_relationship(payload or {})

    return router
