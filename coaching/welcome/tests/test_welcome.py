"""
Tests for welcome module.
"""

import sys
from pathlib import Path


def test_welcome_creates_profile(tmp_path):
    """Run welcome module and verify profile is created."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from coaching.welcome import run

    context = {
        "company_name": "TestCorp",
        "industry": "Tech",
        "employees": 15,
        "entry_methodology": "lean-canvas",
        "base_path": str(tmp_path),
    }
    result = run(context)
    assert len(result["errors"]) == 0, f"Errors: {result['errors']}"
    assert "TestCorp" in result["output"]
    assert result["artifacts"]["profile"]["company"]["name"] == "TestCorp"
    assert result["artifacts"]["profile"]["company"]["growth_stage"] == "growth"


def test_welcome_rejects_missing_name(tmp_path):
    """Welcome should error on missing company_name."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from coaching.welcome import run

    result = run(
        {
            "company_name": "",
            "industry": "Tech",
            "employees": 5,
            "base_path": str(tmp_path),
        }
    )
    assert any("company_name" in e for e in result["errors"])


def test_stage_detection():
    """Verify stage detection logic."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from coaching.core import detect_stage

    assert detect_stage(3) == "startup"
    assert detect_stage(10) == "startup"
    assert detect_stage(15) == "growth"
    assert detect_stage(50) == "growth"
    assert detect_stage(100) == "scaling"
    assert detect_stage(500) == "expansion"
