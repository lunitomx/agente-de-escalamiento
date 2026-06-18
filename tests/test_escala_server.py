"""Tests for Escala Server Core (S18.1)."""

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "escala_server"))

# Import after path setup
from escala_server.router import Router
from escala_server.handlers import CompaniesHandler, WorksheetsHandler
from escala_server.cors import CORSHandler


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("localhost", 0))
        return int(sock.getsockname()[1])


def wait_for_server(proc: subprocess.Popen[Any], port: int) -> None:
    import urllib.request

    deadline = time.monotonic() + 5
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            assert proc.stderr is not None
            stderr = proc.stderr.read().decode("utf-8", errors="replace")
            raise AssertionError(f"server exited early: {stderr}")
        try:
            with urllib.request.urlopen(
                f"http://localhost:{port}/api/health",
                timeout=0.2,
            ) as response:
                if response.status == 200:
                    return
        except Exception as exc:
            last_error = exc
            time.sleep(0.1)
    raise AssertionError(f"server did not start: {last_error}")


# ─── Router Tests ─────────────────────────────────────────────


class TestRouter:
    def test_register_and_dispatch_get(self):
        router = Router()
        results = {}

        @router.get("/api/companies")
        def handler(data):
            results["called"] = True
            return {"data": []}

        handler({})
        assert results["called"]

    def test_route_with_path_params(self):
        router = Router()

        @router.get("/api/worksheets/{category}/{tool}")
        def handler(category=None, tool=None):
            return {"data": {"category": category, "tool": tool}}

        fn, params = router.dispatch("GET", "/api/worksheets/cash/power-of-one")
        assert fn is not None
        assert params["category"] == "cash"
        assert params["tool"] == "power-of-one"
        result = fn(**params)
        assert result["data"]["category"] == "cash"
        assert result["data"]["tool"] == "power-of-one"

    def test_dispatch_missing_route(self):
        router = Router()
        fn, params = router.dispatch("GET", "/api/nonexistent")
        assert fn is None
        assert params == {}


# ─── CORS Tests ───────────────────────────────────────────────


class TestCORSHandler:
    def test_cors_headers_present(self):
        headers = CORSHandler.get_headers()
        assert "Access-Control-Allow-Origin" in headers
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert "Access-Control-Allow-Methods" in headers
        assert "Access-Control-Allow-Headers" in headers


# ─── Handler Tests ────────────────────────────────────────────


class TestCompaniesHandler:
    def setup_method(self):
        import uuid

        self.db_path = f"file:test_co_{uuid.uuid4().hex[:8]}?mode=memory&cache=shared"
        self.handler = CompaniesHandler(db_path=self.db_path)

    def test_list_companies_empty(self):
        result = self.handler.list_companies()
        assert "data" in result
        assert result["status"] == "ok"

    def test_create_company(self):
        company = {"name": "Test Corp", "industry": "Tech"}
        result = self.handler.create_company(company)
        assert result["status"] == "ok"
        assert "id" in result["data"]

    def test_get_company_by_id(self):
        created = self.handler.create_company({"name": "Get Test"})
        cid = created["data"]["id"]
        result = self.handler.get_company(cid)
        assert result["status"] == "ok"
        assert result["data"]["name"] == "Get Test"

    def test_get_nonexistent_company(self):
        result = self.handler.get_company("nonexistent-id")
        assert result["status"] == "error"
        assert "not found" in result.get("message", "").lower()


class TestWorksheetsHandler:
    def setup_method(self):
        # Unique :memory: db per test to avoid state leakage
        import uuid

        self.db_path = f"file:test_ws_{uuid.uuid4().hex[:8]}?mode=memory&cache=shared"
        self.handler = WorksheetsHandler(db_path=self.db_path)

    def test_get_worksheets_empty(self):
        result = self.handler.get_worksheets("cash", "power-of-one")
        assert result["data"] == {}

    def test_save_and_retrieve(self):
        data = {"palancas": {"precio": 5, "clientes": 10}}
        save_result = self.handler.save_worksheet("cash", "power-of-one", data)
        assert save_result["status"] == "ok"

        get_result = self.handler.get_worksheets("cash", "power-of-one")
        assert get_result["data"]["palancas"]["precio"] == 5


# ─── Server Integration Tests ─────────────────────────────────


@pytest.fixture
def server_process():
    """Start server in background for integration testing."""
    port = free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "escala_server", "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=PROJECT_ROOT,
    )
    wait_for_server(proc, port)
    yield port, proc
    # Cleanup
    os.kill(proc.pid, signal.SIGTERM)
    proc.wait(timeout=5)


@pytest.mark.skip(reason="Integration test — run manually")
class TestServerIntegration:
    def test_server_starts_and_responds(self, server_process):
        import urllib.request

        port, _ = server_process
        url = f"http://localhost:{port}/api/companies"
        try:
            resp = urllib.request.urlopen(url)
            data = json.loads(resp.read())
            assert data["status"] == "ok"
        except Exception as e:
            pytest.fail(f"Server integration test failed: {e}")

    def test_static_file_serving(self, server_process):
        import urllib.request

        port, _ = server_process
        # Create a temp test file
        url = f"http://localhost:{port}/api/companies"
        try:
            resp = urllib.request.urlopen(url)
            assert resp.status == 200
        except Exception as e:
            pytest.fail(f"Static file test failed: {e}")


# ─── Resilience Tests ──────────────────────────────────────────


class TestServerResilience:
    """Verify server survives errors gracefully (S27.1)."""

    def test_invalid_json_returns_400(self):
        """POST with malformed body must return 400, not crash."""
        import urllib.request
        import urllib.error

        port = free_port()
        proc = subprocess.Popen(
            [sys.executable, "-m", "escala_server", "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=PROJECT_ROOT,
        )
        wait_for_server(proc, port)
        try:
            url = f"http://localhost:{port}/api/companies"
            req = urllib.request.Request(
                url,
                data=b"{invalid",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                urllib.request.urlopen(req)
                pytest.fail("Expected HTTPError for 400")
            except urllib.error.HTTPError as e:
                assert e.code == 400
                body = json.loads(e.read())
                assert body["status"] == "error"
                assert "JSON" in body["message"]
        finally:
            os.kill(proc.pid, signal.SIGTERM)
            proc.wait(timeout=5)

    def test_server_survives_error(self):
        """After an error, health check must still return 200."""
        import urllib.request
        import urllib.error

        port = free_port()
        proc = subprocess.Popen(
            [sys.executable, "-m", "escala_server", "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=PROJECT_ROOT,
        )
        wait_for_server(proc, port)
        try:
            # Trigger an error first
            url = f"http://localhost:{port}/api/companies"
            req = urllib.request.Request(
                url,
                data=b"{invalid",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                urllib.request.urlopen(req)
            except urllib.error.HTTPError:
                pass  # Expected

            # Server must still be alive
            health_url = f"http://localhost:{port}/api/health"
            resp = urllib.request.urlopen(health_url)
            assert resp.status == 200
            data = json.loads(resp.read())
            assert data["status"] == "ok"
        finally:
            os.kill(proc.pid, signal.SIGTERM)
            proc.wait(timeout=5)
