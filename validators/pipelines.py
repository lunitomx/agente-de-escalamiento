"""Validation for declarative ScaleUp pipeline registries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from escala_server.capabilities import (
    CatalogError,
    load_capability_catalog,
    load_legacy_aliases,
)

try:
    import yaml
except ImportError as exc:  # pragma: no cover - project dependency
    raise ImportError("PyYAML required: pip install pyyaml") from exc


_PIPELINE_REQUIRED = {
    "id",
    "entrypoint",
    "intent",
    "inputs",
    "phases",
    "gates",
    "stop_conditions",
    "outputs",
    "evidence",
}
_PHASE_REQUIRED = {
    "id",
    "skill",
    "mode",
    "context",
    "output",
    "evidence",
    "inference_budget",
    "model_hint",
}
_VALID_MODES = {"inline", "subskill", "code_gate", "manual_gate"}
_VALID_GATE_TYPES = {"code", "manual"}
_VALID_BUDGETS = {"low", "medium", "high"}


def validate_pipeline_registry(
    registry_path: Path,
    skills_root: Path = Path(".agents/skills"),
) -> list[str]:
    """Validate a ScaleUp pipeline registry.

    Returns a list of errors. An empty list means the registry is valid.
    """
    errors: list[str] = []

    if not registry_path.exists():
        return [f"Registry not found: {registry_path}"]

    try:
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"Invalid YAML: {exc}"]

    if not isinstance(data, dict):
        return ["Registry root must be a mapping"]

    pipelines = data.get("pipelines")
    if not isinstance(pipelines, list) or not pipelines:
        return ["Registry must contain a non-empty 'pipelines' list"]

    pipeline_ids: set[str] = set()
    for index, pipeline in enumerate(pipelines):
        if not isinstance(pipeline, dict):
            errors.append(f"pipelines[{index}] must be a mapping")
            continue

        pipeline_id = str(pipeline.get("id", f"pipelines[{index}]"))
        missing = _PIPELINE_REQUIRED - pipeline.keys()
        if missing:
            errors.append(
                f"{pipeline_id}: missing required keys: {', '.join(sorted(missing))}"
            )

        if pipeline_id in pipeline_ids:
            errors.append(f"{pipeline_id}: duplicate pipeline id")
        pipeline_ids.add(pipeline_id)

        entrypoint = pipeline.get("entrypoint")
        if isinstance(entrypoint, str):
            _validate_skill_exists(entrypoint, skills_root, errors, pipeline_id)
        else:
            errors.append(f"{pipeline_id}: entrypoint must be a string")

        phase_ids = _validate_phases(pipeline_id, pipeline.get("phases"), skills_root)
        errors.extend(phase_ids["errors"])
        errors.extend(
            _validate_gates(pipeline_id, pipeline.get("gates"), phase_ids["ids"])
        )

        for list_key in ("inputs", "stop_conditions", "outputs", "evidence"):
            value = pipeline.get(list_key)
            if not isinstance(value, list) or not value:
                errors.append(f"{pipeline_id}: {list_key} must be a non-empty list")

    return errors


def _validate_phases(
    pipeline_id: str,
    phases: Any,
    skills_root: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    phase_ids: set[str] = set()

    if not isinstance(phases, list) or not phases:
        return {
            "ids": phase_ids,
            "errors": [f"{pipeline_id}: phases must be non-empty"],
        }

    for index, phase in enumerate(phases):
        if not isinstance(phase, dict):
            errors.append(f"{pipeline_id}: phases[{index}] must be a mapping")
            continue

        phase_id = str(phase.get("id", f"phases[{index}]"))
        prefix = f"{pipeline_id}.{phase_id}"

        missing = _PHASE_REQUIRED - phase.keys()
        if missing:
            errors.append(
                f"{prefix}: missing required keys: {', '.join(sorted(missing))}"
            )

        if phase_id in phase_ids:
            errors.append(f"{pipeline_id}: duplicate phase id: {phase_id}")
        phase_ids.add(phase_id)

        skill = phase.get("skill")
        if isinstance(skill, str):
            _validate_skill_exists(skill, skills_root, errors, prefix)
        else:
            errors.append(f"{prefix}: skill must be a string")

        mode = phase.get("mode")
        if mode not in _VALID_MODES:
            errors.append(f"{prefix}: invalid mode: {mode!r}")

        budget = phase.get("inference_budget")
        if budget not in _VALID_BUDGETS:
            errors.append(f"{prefix}: invalid inference_budget: {budget!r}")

        for text_key in ("context", "output", "evidence", "model_hint"):
            text_value = phase.get(text_key)
            if not isinstance(text_value, str) or not text_value.strip():
                errors.append(f"{prefix}: {text_key} must be a non-empty string")

    return {"ids": phase_ids, "errors": errors}


def _validate_gates(
    pipeline_id: str,
    gates: Any,
    phase_ids: set[str],
) -> list[str]:
    errors: list[str] = []

    if not isinstance(gates, list):
        return [f"{pipeline_id}: gates must be a list"]

    gate_names: set[str] = set()
    for index, gate in enumerate(gates):
        if not isinstance(gate, dict):
            errors.append(f"{pipeline_id}: gates[{index}] must be a mapping")
            continue

        name = gate.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{pipeline_id}: gates[{index}] missing non-empty name")
            name = f"gates[{index}]"

        if name in gate_names:
            errors.append(f"{pipeline_id}: duplicate gate name: {name}")
        gate_names.add(name)

        gate_type = gate.get("type")
        if gate_type not in _VALID_GATE_TYPES:
            errors.append(f"{pipeline_id}.{name}: invalid gate type: {gate_type!r}")

        after_phase = gate.get("after_phase")
        if after_phase is not None and after_phase not in phase_ids:
            errors.append(
                f"{pipeline_id}.{name}: after_phase does not exist: {after_phase!r}"
            )

        if gate_type == "code" and not isinstance(gate.get("validator"), str):
            errors.append(f"{pipeline_id}.{name}: code gate requires validator")

        on_fail = gate.get("on_fail")
        if not isinstance(on_fail, str) or not on_fail.strip():
            errors.append(f"{pipeline_id}.{name}: on_fail must be a non-empty string")

    return errors


def _validate_skill_exists(
    skill_name: str,
    skills_root: Path,
    errors: list[str],
    owner: str,
) -> None:
    if not skill_name.startswith("scaleup-"):
        errors.append(f"{owner}: skill must use scaleup-* prefix: {skill_name}")
        return

    skill_path = skills_root / skill_name / "SKILL.md"
    if skill_path.exists():
        return
    try:
        catalog = load_capability_catalog()
        alias = next(
            (item for item in load_legacy_aliases(catalog) if item.alias == skill_name),
            None,
        )
    except CatalogError:
        alias = None
    if alias is not None:
        canonical_path = (
            Path(__file__).resolve().parents[1]
            / "escala-skills"
            / alias.target
            / "SKILL.md"
        )
        if canonical_path.exists():
            return
    errors.append(f"{owner}: skill not found: {skill_path}")
