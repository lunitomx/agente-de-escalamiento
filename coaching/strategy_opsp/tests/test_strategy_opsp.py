"""Tests for the OPSP persist/resume/export module (S47.4)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from coaching.strategy_opsp import run  # noqa: E402
from coaching.strategy_opsp.engine import (  # noqa: E402
    MISSING,
    merge_section,
    missing_fields,
)
from coaching.strategy_opsp.formatter import render_markdown  # noqa: E402


def test_load_on_fresh_company_has_no_saved_plan(tmp_path):
    """First load, no prior state: nothing to resume, no state claimed."""
    result = run({"action": "load", "base_path": str(tmp_path)})
    assert result["errors"] == []
    assert result["artifacts"]["state"] == {}
    assert result["artifacts"]["resuming"] is False


def test_save_core_values_then_load_resumes_them(tmp_path):
    base = str(tmp_path)
    save_result = run(
        {
            "action": "save",
            "base_path": base,
            "section": "core_values",
            "data": ["Honestidad", "Excelencia", "Servicio"],
        }
    )
    assert save_result["errors"] == []

    load_result = run({"action": "load", "base_path": base})
    assert load_result["artifacts"]["resuming"] is True
    assert load_result["artifacts"]["state"]["core_values"] == [
        "Honestidad",
        "Excelencia",
        "Servicio",
    ]


def test_save_persists_across_separate_run_calls(tmp_path):
    """Persistence must survive independent process-like calls, not just
    live in memory within one run()."""
    base = str(tmp_path)
    run(
        {
            "action": "save",
            "base_path": base,
            "section": "purpose",
            "data": "Ayudar a que las empresas escalen con integridad.",
        }
    )
    run(
        {
            "action": "save",
            "base_path": base,
            "section": "bhag",
            "data": {"statement": "10x en 10 años", "target_date": "2036"},
        }
    )
    state = run({"action": "load", "base_path": base})["artifacts"]["state"]
    assert state["purpose"] == "Ayudar a que las empresas escalen con integridad."
    assert state["bhag"]["statement"] == "10x en 10 años"


def test_export_never_invents_missing_data(tmp_path):
    """A field never saved must render as an explicit pending marker,
    never a fabricated value — this is the bug the coach originally hit."""
    base = str(tmp_path)
    run(
        {
            "action": "save",
            "base_path": base,
            "section": "purpose",
            "data": "Servir con excelencia.",
        }
    )
    result = run({"action": "export", "base_path": base})
    markdown = result["artifacts"]["markdown"]
    assert "Servir con excelencia." in markdown
    assert "[PENDIENTE]" in markdown
    assert result["artifacts"]["missing"] != []


def test_export_writes_opsp_md_to_disk(tmp_path):
    base = str(tmp_path)
    run(
        {
            "action": "save",
            "base_path": base,
            "section": "purpose",
            "data": "Servir con excelencia.",
        }
    )
    result = run({"action": "export", "base_path": base})
    opsp_path = Path(result["artifacts"]["export_path"])
    assert opsp_path.exists()
    assert "Servir con excelencia." in opsp_path.read_text(encoding="utf-8")


def test_unknown_section_is_rejected(tmp_path):
    result = run(
        {
            "action": "save",
            "base_path": str(tmp_path),
            "section": "not_a_real_section",
            "data": "x",
        }
    )
    assert result["errors"] != []


def test_unknown_action_is_rejected(tmp_path):
    result = run({"action": "teleport", "base_path": str(tmp_path)})
    assert result["errors"] != []


# ---------------------------------------------------------------------------
# engine.py unit tests
# ---------------------------------------------------------------------------


def test_merge_section_sets_a_field():
    state = merge_section({}, "purpose", "x")
    assert state["purpose"] == "x"


def test_merge_section_rejects_unknown_section():
    import pytest

    with pytest.raises(ValueError):
        merge_section({}, "nope", "x")


def test_missing_fields_flags_everything_on_empty_state():
    missing = missing_fields({})
    assert "core_values" in missing
    assert "quarterly_plan" in missing


def test_missing_fields_excludes_saved_sections():
    state = {"purpose": "x"}
    missing = missing_fields(state)
    assert "purpose" not in missing
    assert "core_values" in missing


def test_render_markdown_uses_pending_marker_constant():
    markdown = render_markdown({})
    assert MISSING in markdown
