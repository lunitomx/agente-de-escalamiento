from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / ".raise/pipelines/scaleup.yaml"
SKILLS_ROOT = ROOT / ".agents/skills"
SPEC = importlib.util.spec_from_file_location(
    "pipeline_registry_validator",
    ROOT / "validators/pipelines.py",
)
assert SPEC is not None
assert SPEC.loader is not None
PIPELINE_VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PIPELINE_VALIDATOR)
validate_pipeline_registry = PIPELINE_VALIDATOR.validate_pipeline_registry


def test_scaleup_pipeline_registry_is_valid() -> None:
    assert validate_pipeline_registry(REGISTRY, SKILLS_ROOT) == []


def test_missing_skill_is_reported(tmp_path: Path) -> None:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    data["pipelines"][0]["phases"][0]["skill"] = "scaleup-missing-skill"
    registry = tmp_path / "scaleup.yaml"
    registry.write_text(yaml.safe_dump(data), encoding="utf-8")

    errors = validate_pipeline_registry(registry, SKILLS_ROOT)

    assert any("skill not found" in error for error in errors)


def test_duplicate_phase_id_is_reported(tmp_path: Path) -> None:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    phase = deepcopy(data["pipelines"][0]["phases"][0])
    data["pipelines"][0]["phases"].append(phase)
    registry = tmp_path / "scaleup.yaml"
    registry.write_text(yaml.safe_dump(data), encoding="utf-8")

    errors = validate_pipeline_registry(registry, SKILLS_ROOT)

    assert any("duplicate phase id" in error for error in errors)


def test_gate_without_name_is_reported(tmp_path: Path) -> None:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    del data["pipelines"][0]["gates"][0]["name"]
    registry = tmp_path / "scaleup.yaml"
    registry.write_text(yaml.safe_dump(data), encoding="utf-8")

    errors = validate_pipeline_registry(registry, SKILLS_ROOT)

    assert any("missing non-empty name" in error for error in errors)


def test_entrypoint_skills_reference_canonical_pipeline_ids() -> None:
    expected = {
        "scaleup-start": "scaleup-session-start",
        "scaleup-close": "scaleup-session-close",
        "scaleup-cash": "scaleup-cash-acceleration-system",
        "scaleup-strategy": "scaleup-strategy-development",
        "scaleup-people": "scaleup-people-development",
        "scaleup-execution": "scaleup-execution-system",
    }

    for skill, pipeline_id in expected.items():
        text = (ROOT / ".claude/skills" / skill / "SKILL.md").read_text(
            encoding="utf-8"
        )
        assert pipeline_id in text
        assert ".raise/pipelines/scaleup.yaml" in text
