"""Escala HTTP Server — serves static files and API endpoints."""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, parse_qs

from .cors import CORSHandler
from .dashboard import DashboardHandler
from .handlers import (
    CompaniesHandler,
    WorksheetsHandler,
    SessionsHandler,
    MemoryHandler,
)
from .router import Router


class EscalaRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler that routes to static files or API endpoints."""

    # Class-level state (set by make_server)
    static_root: str = ""
    router: Router = Router()
    companies: CompaniesHandler = None  # type: ignore
    worksheets: WorksheetsHandler = None  # type: ignore
    sessions: SessionsHandler = None  # type: ignore
    memory: MemoryHandler = None  # type: ignore
    dashboard: DashboardHandler = None  # type: ignore
    knowledge: Any = None  # type: ignore[annotation-unchecked]
    advisor: Any = None  # type: ignore[annotation-unchecked]
    outcomes: Any = None  # type: ignore[annotation-unchecked]
    specialist_team: Any = None  # type: ignore[annotation-unchecked]

    def do_GET(self):
        path = self.path
        # Parse query string before dispatch
        parsed = urlparse(path)
        clean_path = parsed.path
        query_params: dict[str, str] = {}
        for k, v in parse_qs(parsed.query).items():
            query_params[k] = v[0]

        # Try API route first (with clean path, no query string)
        handler, params = self.router.dispatch("GET", clean_path)
        if handler:
            # Merge query params into path params (path params take precedence)
            for key, value in query_params.items():
                if key not in params:
                    params[key] = value
            self._send_json_response(handler(**params))
            return
        # Fall back to static file
        self._serve_static(path)

    def _handle_api_request(self, method: str):
        """Handle API POST/PATCH requests with error handling.

        Wraps JSON parsing and handler execution in try/except so that
        malformed payloads or unexpected handler exceptions don't crash
        the worker thread.
        """
        handler, params = self.router.dispatch(method, self.path)
        if not handler:
            return self._send_json_error(404, "Not found")

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            return self._send_json_error(400, "Invalid JSON")

        try:
            self._send_json_response(handler(payload=payload, **params))
        except Exception:
            self._send_json_error(500, "Internal server error")

    def do_POST(self):
        self._handle_api_request("POST")

    def do_PATCH(self):
        self._handle_api_request("PATCH")

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

    from .graph_engine import GraphEngine
    from .handlers import (
        OutcomeLearningHandler,
        SpecialistTeamHandler,
        WorksheetsHandler,
        SessionsHandler,
    )
    from .knowledge_handler import KnowledgeHandler
    from .business_advisor import BusinessAdvisorHandler

    EscalaRequestHandler.static_root = str(Path(static_root).resolve())
    EscalaRequestHandler.router = _build_router()
    EscalaRequestHandler.companies = CompaniesHandler(db_path)
    EscalaRequestHandler.worksheets = WorksheetsHandler(db_path)
    EscalaRequestHandler.sessions = SessionsHandler(db_path)
    EscalaRequestHandler.memory = MemoryHandler(db_path)
    EscalaRequestHandler.dashboard = DashboardHandler(db_path)
    EscalaRequestHandler.knowledge = KnowledgeHandler(GraphEngine(db_path))
    EscalaRequestHandler.advisor = BusinessAdvisorHandler(db_path)
    EscalaRequestHandler.outcomes = OutcomeLearningHandler(
        Path(db_path).expanduser().resolve(strict=False).parent / "outcome-learning"
    )
    EscalaRequestHandler.specialist_team = SpecialistTeamHandler()

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
        assert company_id is not None
        return EscalaRequestHandler.companies.get_company(company_id)

    @router.patch("/api/companies/{company_id}")
    def update_company(company_id=None, payload=None):
        assert company_id is not None
        return EscalaRequestHandler.companies.update_company(company_id, payload or {})

    @router.get("/api/dashboard/summary")
    def dashboard_summary():
        return EscalaRequestHandler.dashboard.summary()

    @router.get("/api/worksheets/{category}/{tool}")
    def get_worksheet(category=None, tool=None):
        assert category is not None
        assert tool is not None
        return EscalaRequestHandler.worksheets.get_worksheets(category, tool)

    @router.post("/api/worksheets/{category}/{tool}")
    def save_worksheet(category=None, tool=None, payload=None):
        assert category is not None
        assert tool is not None
        return EscalaRequestHandler.worksheets.save_worksheet(
            category, tool, payload or {}
        )

    @router.get("/api/worksheets/{category}/{tool}/changes")
    def get_worksheet_changes(category=None, tool=None):
        assert category is not None
        assert tool is not None
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
        assert session_id is not None
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
        assert entity_id is not None
        return EscalaRequestHandler.memory.get_entity(int(entity_id))

    @router.post("/api/memory/entities")
    def memory_create_entity(payload=None):
        return EscalaRequestHandler.memory.create_entity(payload or {})

    @router.post("/api/memory/relationships")
    def memory_create_relationship(payload=None):
        return EscalaRequestHandler.memory.create_relationship(payload or {})

    # ── Knowledge API routes (S19.4) ────────────────────────────

    @router.get("/api/knowledge/search")
    def knowledge_search(q: str = "", type: str | None = None):
        return EscalaRequestHandler.knowledge.search(query=q, type_filter=type)

    @router.get("/api/knowledge/entity/{entity_name}")
    def knowledge_get_entity(entity_name=None):
        return EscalaRequestHandler.knowledge.get_entity(entity_name)

    @router.get("/api/knowledge/context")
    def knowledge_context(tool: str | None = None, category: str | None = None):
        return EscalaRequestHandler.knowledge.get_context(tool=tool, category=category)

    # ── Local business-advisor routes ─────────────────────────────

    @router.post("/api/advisor/ask")
    def advisor_ask(payload=None):
        question = (payload or {}).get("question", "")
        context = (payload or {}).get("context")
        return EscalaRequestHandler.advisor.ask(question=question, context=context)

    @router.get("/api/advisor/ask")
    def advisor_ask_get(q: str = ""):
        return EscalaRequestHandler.advisor.ask(question=q)

    @router.post("/api/advisor/review-daily")
    def advisor_review_daily(payload=None):
        daily_text = (payload or {}).get("daily_text", "")
        return EscalaRequestHandler.advisor.review_daily(daily_text=daily_text)

    @router.post("/api/advisor/debate")
    def advisor_debate(payload=None):
        decision = (payload or {}).get("decision", "")
        context = (payload or {}).get("context")
        history = (payload or {}).get("history")
        return EscalaRequestHandler.advisor.board_debate(
            decision=decision, context=context, history=history
        )

    # ── Outcome learning API (E44) ───────────────────────────────

    @router.get("/api/companies/{company_id}/outcomes")
    def outcome_cockpit(company_id=None, on: str | None = None):
        assert company_id is not None
        return EscalaRequestHandler.outcomes.cockpit(company_id, on=on)

    @router.post("/api/companies/{company_id}/outcomes/decisions")
    def outcome_create_decision(company_id=None, payload=None):
        assert company_id is not None
        return EscalaRequestHandler.outcomes.create_decision(company_id, payload or {})

    @router.post("/api/companies/{company_id}/outcomes/{cycle_id}/actions")
    def outcome_create_action(company_id=None, cycle_id=None, payload=None):
        assert company_id is not None and cycle_id is not None
        return EscalaRequestHandler.outcomes.create_action(
            company_id, cycle_id, payload or {}
        )

    @router.post(
        "/api/companies/{company_id}/outcomes/{cycle_id}/actions/{action_id}/update"
    )
    def outcome_update_action(
        company_id=None, cycle_id=None, action_id=None, payload=None
    ):
        assert company_id is not None and cycle_id is not None and action_id is not None
        return EscalaRequestHandler.outcomes.update_action(
            company_id, cycle_id, action_id, payload or {}
        )

    @router.post(
        "/api/companies/{company_id}/outcomes/{cycle_id}/actions/{action_id}/cancel"
    )
    def outcome_cancel_action(
        company_id=None, cycle_id=None, action_id=None, payload=None
    ):
        assert company_id is not None and cycle_id is not None and action_id is not None
        return EscalaRequestHandler.outcomes.cancel_action(
            company_id, cycle_id, action_id, payload or {}
        )

    @router.post("/api/companies/{company_id}/outcomes/{cycle_id}/results/{action_id}")
    def outcome_create_result(
        company_id=None, cycle_id=None, action_id=None, payload=None
    ):
        assert company_id is not None and cycle_id is not None and action_id is not None
        return EscalaRequestHandler.outcomes.create_result(
            company_id, cycle_id, action_id, payload or {}
        )

    @router.post(
        "/api/companies/{company_id}/outcomes/{cycle_id}/learnings/{result_id}"
    )
    def outcome_confirm_learning(
        company_id=None, cycle_id=None, result_id=None, payload=None
    ):
        assert company_id is not None and cycle_id is not None and result_id is not None
        return EscalaRequestHandler.outcomes.confirm_learning(
            company_id, cycle_id, result_id, payload or {}
        )

    @router.post("/api/advisor/team-review")
    def advisor_team_review(payload=None):
        return EscalaRequestHandler.specialist_team.review(payload or {})

    # ── Cash / Power of One routes ────────────────────────────────

    @router.post("/api/cash/power-of-one")
    def cash_power_of_one(payload=None):
        from .cash import PowerOfOneEngine, FinancialInputs

        data = payload or {}
        inputs = FinancialInputs.from_dict(data.get("financials", {}))
        adjustments = data.get("adjustments")
        engine = PowerOfOneEngine()
        result = engine.calculate(inputs, adjustments=adjustments)

        return {
            "status": "ok",
            "data": {
                "combined_cash_impact": result.combined_cash_impact,
                "combined_ebit_impact": result.combined_ebit_impact,
                "metrics": result.metrics,
                "impacts": [
                    {
                        "lever": i.lever,
                        "label": i.label,
                        "cash_impact": i.cash_impact,
                        "ebit_impact": i.ebit_impact,
                        "difficulty": i.difficulty,
                        "time": i.time,
                        "improvement_pct": i.improvement_pct,
                        "improvement_days": i.improvement_days,
                    }
                    for i in result.impacts
                ],
                "priorities": result.priorities,
            },
        }

    return router
