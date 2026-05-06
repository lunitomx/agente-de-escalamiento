"""
Tests for welcome module.
"""
import json
import subprocess
import sys
from pathlib import Path


def test_welcome_creates_profile(tmp_path: Path):
    """Run welcome module and verify profile is created."""
    context = {
        "company_name": "TestCorp",
        "industry": "Tech",
        "employees": 15,
        "entry_methodology": "lean-canvas",
        "base_path": str(tmp_path / ".scaleup"),
    }
    input_json = json.dumps(context)

    # Simulate the CLI invocation
    result = subprocess.run(
        [sys.executable, "-c", f"""
import sys, json
sys.path.insert(0, r'{tmp_path.parent.parent.parent.parent}')
sys.path.insert(0, r'{tmp_path.parent.parent.parent}')
from scaleup.coaching.welcome import run
ctx = json.loads('{input_json}')
out = run(ctx)
print(json.dumps(out))
"""],
        capture_output=True, text=True, timeout=10,
    )

    output = json.loads(result.stdout)
    assert len(output["errors"]) == 0, f"Errors: {output['errors']}"
    assert "TestCorp" in output["output"]
    assert output["artifacts"]["profile"]["company"]["name"] == "TestCorp"
    assert output["artifacts"]["profile"]["company"]["growth_stage"] == "growth"


def test_welcome_rejects_missing_name():
    """Welcome should error on missing company_name."""
    from .scaleup.coaching.welcome import run
    result = run({"industry": "Tech", "employees": 5, "base_path": "/tmp"})
    assert any("company_name" in e for e in result["errors"])


def test_stage_detection():
    """Verify stage detection logic."""
    from .scaleup.coaching.core import detect_stage
    assert detect_stage(3) == "startup"
    assert detect_stage(10) == "startup"
    assert detect_stage(15) == "growth"
    assert detect_stage(50) == "growth"
    assert detect_stage(100) == "scaling"
    assert detect_stage(500) == "expansion"
