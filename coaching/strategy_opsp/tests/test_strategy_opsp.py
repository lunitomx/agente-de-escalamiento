"""Tests for the OPSP persist/resume/export module (S47.4)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from coaching.strategy_opsp import run  # noqa: E402
from coaching.strategy_opsp.engine import (  # noqa: E402
    MISSING,
    SECTIONS,
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


# ---------------------------------------------------------------------------
# S50.4.1 — OPSP guided engine tests
# ---------------------------------------------------------------------------

from coaching.strategy_opsp.engine import SECTION_SCHEMAS  # noqa: E402


def _dummy_data_for_section(section: str, priorities_as_annual: bool = False) -> object:
    """Build a syntactically valid dummy payload for a given OPSP section."""
    schema = SECTION_SCHEMAS.get(section, {})
    if not schema:
        return "ok"
    data: dict[str, object] = {}
    for key, expected_type in schema.items():
        if expected_type is list:
            if priorities_as_annual:
                data[key] = [{"priority": "x", "owner": "y", "kpi": "z"}]
            elif key == "values":
                data[key] = ["item"]
            else:
                data[key] = [{"priority": "x", "owner": "y", "kpi": "z"}]
        elif expected_type is dict:
            data[key] = {"name": "theme", "celebration": "party"}
        elif expected_type is str:
            data[key] = "x"
        elif expected_type is int:
            data[key] = 2026
        elif isinstance(expected_type, tuple):
            if str in expected_type:
                data[key] = "x"
            elif int in expected_type:
                data[key] = 100
            else:
                data[key] = "x"
    return data


def test_completeness_score_is_zero_for_empty_state():
    from coaching.strategy_opsp.engine import completeness_score

    comp = completeness_score({})
    assert comp["overall"] == 0.0
    assert comp["percent"] == 0
    assert comp["complete_sections"] == []
    assert set(comp["incomplete_sections"]) == set(SECTIONS)


def test_completeness_score_increases_when_section_saved():
    import pytest
    from coaching.strategy_opsp.engine import completeness_score

    state = {"purpose": "Servir con excelencia."}
    comp = completeness_score(state)
    assert comp["sections"]["purpose"]["complete"] is True
    assert comp["sections"]["purpose"]["score"] == 1.0
    assert "purpose" in comp["complete_sections"]
    assert comp["overall"] == pytest.approx(1 / len(SECTIONS), abs=0.01)


def test_next_missing_section_follows_canonical_order():
    from coaching.strategy_opsp.engine import next_missing_section

    assert next_missing_section({}) == "core_values"
    assert next_missing_section({"core_values": {"values": ["x"]}}) == "purpose"
    assert next_missing_section({"purpose": "x"}) == "core_values"


def test_next_missing_section_returns_none_when_complete():
    from coaching.strategy_opsp.engine import next_missing_section

    complete_state = {section: _dummy_data_for_section(section) for section in SECTIONS}

    assert next_missing_section(complete_state) is None


def test_save_returns_completeness_and_next_section(tmp_path):
    base = str(tmp_path)
    result = run(
        {
            "action": "save",
            "base_path": base,
            "section": "purpose",
            "data": "Servir con excelencia.",
        }
    )
    assert result["errors"] == []
    assert "completeness" in result["artifacts"]
    assert result["artifacts"]["next_section"] == "core_values"
    assert result["artifacts"]["completeness"]["percent"] == int(100 / len(SECTIONS))


def test_load_returns_completeness_and_next_section(tmp_path):
    base = str(tmp_path)
    run(
        {
            "action": "save",
            "base_path": base,
            "section": "purpose",
            "data": "Servir con excelencia.",
        }
    )
    load_result = run({"action": "load", "base_path": base})
    assert load_result["artifacts"]["completeness"]["percent"] == int(
        100 / len(SECTIONS)
    )
    assert load_result["artifacts"]["next_section"] == "core_values"


def test_opsp_full_plan_marks_complete(tmp_path):
    base = str(tmp_path)
    for section in SECTIONS:
        data = _dummy_data_for_section(section, priorities_as_annual=True)
        run({"action": "save", "base_path": base, "section": section, "data": data})

    load_result = run({"action": "load", "base_path": base})
    comp = load_result["artifacts"]["completeness"]
    assert comp["percent"] == 100
    assert load_result["artifacts"]["next_section"] is None
