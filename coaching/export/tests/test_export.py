"""
Tests for export module — Action Plan Export.
"""
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# ---------------------------------------------------------------------------
# T1: Module skeleton
# ---------------------------------------------------------------------------

def test_run_importable():
    """run() should be importable from coaching.export."""
    from coaching.export import run
    assert callable(run)


def test_run_returns_dict(tmp_path):
    """run() should return a dict with output, artifacts, errors."""
    from coaching.export import run
    result = run({"base_path": str(tmp_path)})
    assert isinstance(result, dict)
    assert "output" in result
    assert "artifacts" in result
    assert "errors" in result


def test_run_errors_is_list(tmp_path):
    """run() result['errors'] must be a list."""
    from coaching.export import run
    result = run({"base_path": str(tmp_path)})
    assert isinstance(result["errors"], list)


def test_output_file_path_format(tmp_path):
    """run() should produce an export file with date-stamped name."""
    import re
    from coaching.export import run
    result = run({"base_path": str(tmp_path)})
    export_path = result.get("artifacts", {}).get("export_path", "")
    assert re.search(r"\d{4}-\d{2}-\d{2}-action-plan\.md$", export_path), (
        f"export_path did not match expected pattern: {export_path}"
    )


# ---------------------------------------------------------------------------
# T2: Data reading logic
# ---------------------------------------------------------------------------

def test_reads_annual_goal(tmp_path):
    """run() should read annual-goal.md content."""
    from coaching.export import run
    goal_dir = tmp_path / ".scaleup" / "my-company"
    goal_dir.mkdir(parents=True)
    (goal_dir / "annual-goal.md").write_text("## Meta del Año\n\nDuplicar revenue.")
    result = run({"base_path": str(tmp_path)})
    assert result["errors"] == []
    assert "missing_optional" in result["artifacts"]


def test_reads_quarterly_focus(tmp_path):
    """run() should read quarterly-focus.md content."""
    from coaching.export import run
    qf_dir = tmp_path / ".scaleup" / "my-company"
    qf_dir.mkdir(parents=True)
    (qf_dir / "quarterly-focus.md").write_text("## Q2 2026\n\nRock 1: Deploy product.")
    result = run({"base_path": str(tmp_path)})
    assert result["errors"] == []


def test_reads_tasks(tmp_path):
    """run() should read tasks.md content."""
    from coaching.export import run
    task_dir = tmp_path / ".scaleup" / "my-company"
    task_dir.mkdir(parents=True)
    (task_dir / "tasks.md").write_text("## In Progress\n\n- Task A")
    result = run({"base_path": str(tmp_path)})
    assert result["errors"] == []


def test_reads_profile(tmp_path):
    """run() should read profile.md for company name context."""
    from coaching.export import run
    prof_dir = tmp_path / ".scaleup" / "my-company"
    prof_dir.mkdir(parents=True)
    (prof_dir / "profile.md").write_text("# Mi Empresa\n\n- **Nombre:** Acme Corp")
    result = run({"base_path": str(tmp_path)})
    assert result["errors"] == []


def test_reads_yaml_scores(tmp_path):
    """run() should read diagnosis scores from company-profile.yaml."""
    import yaml
    from coaching.export import run
    mem_dir = tmp_path / ".scaleup" / "agent" / "memory"
    mem_dir.mkdir(parents=True)
    (mem_dir / "company-profile.yaml").write_text(
        yaml.dump({"scores": {"people": 3, "strategy": 2, "execution": 4, "cash": 1}})
    )
    result = run({"base_path": str(tmp_path)})
    assert result["errors"] == []
    # Scores should appear in the output file
    export_path = Path(result["artifacts"]["export_path"])
    content = export_path.read_text()
    assert "People" in content or "people" in content.lower()


def test_missing_optional_files_graceful(tmp_path):
    """run() should not error when optional files are missing."""
    from coaching.export import run
    # No .scaleup dir at all — all files missing
    result = run({"base_path": str(tmp_path)})
    assert result["errors"] == []
    assert isinstance(result["artifacts"].get("missing_optional"), list)


def test_missing_yaml_graceful(tmp_path):
    """run() should return empty scores when YAML is missing."""
    from coaching.export import run
    result = run({"base_path": str(tmp_path)})
    assert result["errors"] == []


# ---------------------------------------------------------------------------
# T3: Markdown generation + file output
# ---------------------------------------------------------------------------

REQUIRED_SECTION_HEADERS = [
    "## 1. Diagnosis Scores",
    "## 2. Annual Goal",
    "## 3. Active Priorities",
    "## 4. Open Tasks",
    "## 5. Next Steps",
]


def test_output_file_created(tmp_path):
    """run() should create the export file on disk."""
    from coaching.export import run
    result = run({"base_path": str(tmp_path)})
    export_path = Path(result["artifacts"]["export_path"])
    assert export_path.exists(), f"Export file not found at {export_path}"


def test_all_five_sections_present(tmp_path):
    """The generated file must contain all 5 required ## sections."""
    from coaching.export import run
    result = run({"base_path": str(tmp_path)})
    export_path = Path(result["artifacts"]["export_path"])
    content = export_path.read_text()
    for header in REQUIRED_SECTION_HEADERS:
        assert header in content, f"Missing section: {header!r}"


def test_file_has_timestamp(tmp_path):
    """The generated file should include a date/timestamp."""
    import re
    from coaching.export import run
    result = run({"base_path": str(tmp_path)})
    export_path = Path(result["artifacts"]["export_path"])
    content = export_path.read_text()
    assert re.search(r"\d{4}-\d{2}-\d{2}", content), "No date found in export file"


def test_sections_included_in_artifacts(tmp_path):
    """artifacts['sections_included'] should list the 5 section keys."""
    from coaching.export import run
    result = run({"base_path": str(tmp_path)})
    sections = result["artifacts"].get("sections_included", [])
    for expected in ["scores", "goal", "priorities", "tasks", "next_steps"]:
        assert expected in sections, f"Section {expected!r} missing from artifacts"


def test_return_dict_structure(tmp_path):
    """run() return dict matches the module contract exactly."""
    from coaching.export import run
    result = run({"base_path": str(tmp_path)})
    assert "export_path" in result["artifacts"]
    assert "sections_included" in result["artifacts"]
    assert "missing_optional" in result["artifacts"]
    assert result["errors"] == []
    assert result["output"].startswith("Export generated:")


def test_scores_table_in_output(tmp_path):
    """When scores are present, the export file should contain a markdown table."""
    import yaml
    from coaching.export import run
    mem_dir = tmp_path / ".scaleup" / "agent" / "memory"
    mem_dir.mkdir(parents=True)
    (mem_dir / "company-profile.yaml").write_text(
        yaml.dump({"scores": {"people": 3, "strategy": 2, "execution": 4, "cash": 1}})
    )
    result = run({"base_path": str(tmp_path)})
    export_path = Path(result["artifacts"]["export_path"])
    content = export_path.read_text()
    assert "|" in content, "Expected markdown table in export file"
