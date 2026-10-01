"""S67.6 keeps the Agent Plugins package portable and fail-closed."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.agent_plugins.build_plugin import (
    AgentPluginBuildError,
    build_agent_plugin,
)
from validators.door_bundle import door_bundle
from validators.agent_plugin import (
    AGENT_PLUGIN_SCHEMA_URL,
    AgentPluginError,
    discover_public_skills,
    load_agent_plugin,
)


ROOT = Path(__file__).resolve().parents[1]


def _build(tmp_path: Path) -> Path:
    allowed_root = tmp_path / "artifacts"
    allowed_root.mkdir(parents=True)
    output = allowed_root / "escala-agent-plugin"
    return build_agent_plugin(output=output, allowed_root=allowed_root)


def test_builds_the_minimum_self_contained_agent_plugin_v1(tmp_path: Path) -> None:
    package = _build(tmp_path)

    assert {
        path.relative_to(package).as_posix()
        for path in package.rglob("*")
        if path.is_file()
    } == {
        "plugin.json",
        "skills/escala/SKILL.md",
        "skills/escala/references/capability-catalog.json",
        # S86.10: the list and procedures the door follows, still exact.
        *(f"skills/escala/{path}" for path in door_bundle()),
    }
    manifest = json.loads((package / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["$schema"] == AGENT_PLUGIN_SCHEMA_URL
    assert manifest["name"] == "escala"
    assert discover_public_skills(package) == ("escala",)

    fixture = load_agent_plugin(package)
    assert fixture.skill_name == "escala"
    assert fixture.capability_catalog_id == "escala.mvp-capability-map.v1"
    assert "references/capability-catalog.json" in (
        package / "skills" / "escala" / "SKILL.md"
    ).read_text(encoding="utf-8")


def test_rejects_unknown_manifest_fields_without_accepting_a_partial_package(
    tmp_path: Path,
) -> None:
    package = _build(tmp_path)
    manifest_path = package / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["mcp"] = {"server": "not-allowed"}
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(AgentPluginError, match="manifest_invalid"):
        load_agent_plugin(package)


def test_rejects_symlink_and_private_content(tmp_path: Path) -> None:
    package = _build(tmp_path)
    catalog = package / "skills" / "escala" / "references" / "capability-catalog.json"
    catalog.unlink()
    catalog.symlink_to(tmp_path / "outside.json")

    with pytest.raises(AgentPluginError, match="symlink_forbidden"):
        load_agent_plugin(package)

    package = _build(tmp_path / "second")
    skill = package / "skills" / "escala" / "SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8") + "\n.scaleup/company/private.yaml\n",
        encoding="utf-8",
    )

    with pytest.raises(AgentPluginError, match="private_content_forbidden"):
        load_agent_plugin(package)


def test_discovery_is_limited_to_direct_skills_children(tmp_path: Path) -> None:
    root = tmp_path / "fixture"
    (root / "skills" / "escala").mkdir(parents=True)
    (root / "skills" / "escala" / "SKILL.md").write_text(
        "---\nname: escala\n---\n", encoding="utf-8"
    )
    (root / "skills" / "nested" / "hidden").mkdir(parents=True)
    (root / "skills" / "nested" / "hidden" / "SKILL.md").write_text(
        "hidden", encoding="utf-8"
    )

    assert discover_public_skills(root) == ("escala",)


def test_rejects_an_empty_mcp_directory(tmp_path: Path) -> None:
    package = _build(tmp_path)
    (package / "mcp").mkdir()

    with pytest.raises(AgentPluginError, match="package_surface_invalid"):
        load_agent_plugin(package)


def test_builder_rejects_an_output_outside_its_explicit_root(tmp_path: Path) -> None:
    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    output = tmp_path / "outside" / "escala-agent-plugin"
    output.parent.mkdir()

    with pytest.raises(AgentPluginBuildError, match="output_outside_allowed_root"):
        build_agent_plugin(output=output, allowed_root=allowed_root)

    assert not output.exists()
