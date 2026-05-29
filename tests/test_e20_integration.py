"""Integration tests for E20 — Contextual Skills pipeline.

Verifies that all E20 components work together:
- S20.1: Knowledge Context API (tested in test_knowledge_api.py)
- S20.2: Dashboard Context Panel (HTML includes)
- S20.3: Coaching Skill Helper (scaling_context module)
"""

from pathlib import Path

import pytest

DASHBOARDS_DIR = (
    Path(__file__).resolve().parent.parent
    / "escala_server" / "static" / "dashboards"
)


# ── S20.3: Coaching Skill Helper ──────────────────────────────────


class TestScalingContextModule:
    """Smoke tests for the scaling_context helper module."""

    def test_module_importable(self):
        """scaling_context module should be importable."""
        import escala_server.scaling_context  # noqa: F811
        assert True

    def test_get_scaling_context_no_args_returns_error(self):
        """Calling get_scaling_context() without args should return error."""
        from escala_server.scaling_context import get_scaling_context
        result = get_scaling_context()
        assert result["status"] == "error"

    def test_get_scaling_context_invalid_category(self):
        """Calling with invalid category should return error dict (not crash)."""
        from escala_server.scaling_context import get_scaling_context
        result = get_scaling_context(category="nonexistent")
        assert "status" in result


# ── S20.2: Dashboard Context Panel ─────────────────────────────────


class TestDashboardContextPanelIncludes:
    """Verify all dashboard HTML files include the context panel."""

    DASHBOARD_FILES = sorted(DASHBOARDS_DIR.rglob("*.html"))

    def test_all_dashboards_have_context_panel_css(self):
        """Every dashboard HTML should link context-panel.css."""
        missing = []
        for f in self.DASHBOARD_FILES:
            content = f.read_text(encoding="utf-8")
            if "context-panel.css" not in content:
                missing.append(f.name)
        assert not missing, f"Missing context-panel.css in: {missing}"

    def test_all_dashboards_have_context_panel_js(self):
        """Every dashboard HTML should include context-panel.js."""
        missing = []
        for f in self.DASHBOARD_FILES:
            content = f.read_text(encoding="utf-8")
            if "context-panel.js" not in content:
                missing.append(f.name)
        assert not missing, f"Missing context-panel.js in: {missing}"

    def test_dashboard_count(self):
        """Should have 22+ dashboard HTML files."""
        assert len(self.DASHBOARD_FILES) >= 22
