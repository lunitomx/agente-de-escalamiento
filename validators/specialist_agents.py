"""Compile and verify private agents derived from the E45 specialist contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from escala_server.specialist_team import DecisionArea, SPECIALIST_CONTRACTS
from validators.capability_map import load_capability_map, validate_capability_map


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SPECIALIST_CONTRACT_PATH = (
    REPOSITORY_ROOT / "adapters" / "specialists" / "contract.json"
)
CODEX_AGENT_DIRECTORY = REPOSITORY_ROOT / "adapters" / "codex" / "agents"
CLAUDE_AGENT_DIRECTORY = REPOSITORY_ROOT / "adapters" / "claude" / "agents"
SPECIALIST_AREAS = ("cash", "execution", "people", "strategy")
_PUBLIC_ENTRYPOINT = "escala"
_SCHEMA_VERSION = 1


class SpecialistAgentError(ValueError):
    """Raised when a generated specialist projection is unavailable or unsafe."""


def _area(value: str) -> DecisionArea:
    if value not in SPECIALIST_AREAS:
        raise SpecialistAgentError(f"unknown_specialist_area:{value}")
    return cast(DecisionArea, value)


def _capability_ids_by_profile() -> dict[str, list[str]]:
    capability_map = load_capability_map()
    errors = validate_capability_map(capability_map)
    if errors:
        raise SpecialistAgentError("capability_map_drift:" + ",".join(errors))
    return {
        profile.id: [
            binding.id
            for binding in capability_map.capabilities
            if profile.id in binding.specialist_profiles
        ]
        for profile in capability_map.specialist_profiles
    }


def build_specialist_contract() -> dict[str, Any]:
    """Build the only accepted, source-safe specialist manifest."""
    capability_ids = _capability_ids_by_profile()
    specialists: list[dict[str, Any]] = []
    for raw_area in SPECIALIST_AREAS:
        area = _area(raw_area)
        profile_id = f"specialist.{area}.v1"
        contract = SPECIALIST_CONTRACTS[area]
        specialists.append(
            {
                "agent_name": f"escala-{area}",
                "capability_ids": capability_ids[profile_id],
                "contract_ref": f"e45.specialist.{area}.v1",
                "decision_area": area,
                "id": profile_id,
                "limits": list(contract.limits),
                "minimum_context": list(contract.minimum_context),
                "non_trigger": contract.non_trigger,
                "output": contract.output,
                "permissions": list(contract.permissions),
                "role": contract.role,
                "trigger": contract.trigger,
            }
        )
    return {
        "contract_id": "escala.private-specialists.v1",
        "public_entrypoint": _PUBLIC_ENTRYPOINT,
        "schema_version": _SCHEMA_VERSION,
        "specialists": specialists,
    }


def _instructions(specialist: dict[str, Any]) -> str:
    minimum_context = "; ".join(specialist["minimum_context"])
    permissions = "; ".join(specialist["permissions"])
    limits = "; ".join(specialist["limits"])
    return "\n".join(
        (
            f"You are ESCALA's private specialist for {specialist['decision_area']}.",
            "You are not a public command or a separate product entrypoint.",
            "Work only when the ESCALA orchestrator delegates an authorized case.",
            f"Activate for: {specialist['trigger']}.",
            f"Do not activate for: {specialist['non_trigger']}.",
            f"Minimum authorized context: {minimum_context}.",
            f"You may: {permissions}.",
            f"Return to ESCALA: {specialist['output']}.",
            f"Limits: {limits}.",
            "Do not invent evidence, persist state, create public commands, or use remote configuration.",
        )
    )


def _toml_multiline(value: str) -> str:
    if '"""' in value:
        raise SpecialistAgentError("unsafe_toml_multiline_value")
    return f'"""{value}"""'


def render_codex_agent(specialist: dict[str, Any]) -> str:
    """Render a Codex custom-agent definition from the common contract."""
    description = (
        f"ESCALA private specialist for {specialist['decision_area']}; "
        "delegate only through the ESCALA orchestrator."
    )
    return "\n".join(
        (
            f'name = "{specialist["agent_name"]}"',
            f"description = {_toml_multiline(description)}",
            f"developer_instructions = {_toml_multiline(_instructions(specialist))}",
            "",
        )
    )


def render_claude_agent(specialist: dict[str, Any]) -> str:
    """Render the platform-local Claude agent document from the common contract."""
    description = (
        f"ESCALA private specialist for {specialist['decision_area']}; "
        "delegate only through the ESCALA orchestrator."
    )
    return "\n".join(
        (
            "---",
            f"name: {specialist['agent_name']}",
            f"description: {description}",
            "---",
            "",
            _instructions(specialist),
            "",
        )
    )


def expected_artifacts() -> dict[Path, str]:
    """Return every generated file and its exact deterministic content."""
    contract = build_specialist_contract()
    files: dict[Path, str] = {
        SPECIALIST_CONTRACT_PATH: json.dumps(
            contract, ensure_ascii=False, indent=2, sort_keys=True
        )
        + "\n"
    }
    for specialist in contract["specialists"]:
        agent_name = specialist["agent_name"]
        files[CODEX_AGENT_DIRECTORY / f"{agent_name}.toml"] = render_codex_agent(
            specialist
        )
        files[CLAUDE_AGENT_DIRECTORY / f"{agent_name}.md"] = render_claude_agent(
            specialist
        )
    return files


def write_specialist_artifacts() -> tuple[Path, ...]:
    """Write source-controlled generated artifacts, never user configuration."""
    files = expected_artifacts()
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return tuple(sorted(files))


def _actual_files(directory: Path, suffix: str) -> set[Path]:
    if not directory.exists():
        return set()
    return {
        path for path in directory.iterdir() if path.is_file() and path.suffix == suffix
    }


def validate_specialist_artifacts() -> tuple[str, ...]:
    """Fail closed when checked-in agents diverge from E45 contracts."""
    try:
        expected = expected_artifacts()
    except (OSError, SpecialistAgentError, ValueError) as exc:
        return (f"specialist_contract_unavailable:{exc}",)
    errors: list[str] = []
    for path, content in expected.items():
        try:
            if path.read_text(encoding="utf-8") != content:
                errors.append(
                    f"specialist_artifact_drift:{path.relative_to(REPOSITORY_ROOT)}"
                )
        except OSError:
            errors.append(
                f"specialist_artifact_missing:{path.relative_to(REPOSITORY_ROOT)}"
            )
    expected_codex = {path for path in expected if path.parent == CODEX_AGENT_DIRECTORY}
    expected_claude = {
        path for path in expected if path.parent == CLAUDE_AGENT_DIRECTORY
    }
    if _actual_files(CODEX_AGENT_DIRECTORY, ".toml") != expected_codex:
        errors.append("codex_specialist_surface_drift")
    if _actual_files(CLAUDE_AGENT_DIRECTORY, ".md") != expected_claude:
        errors.append("claude_specialist_surface_drift")
    return tuple(sorted(errors))
