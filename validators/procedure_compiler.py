"""Fail-closed compiler for the six internal E65 MVP procedure contracts.

Only the canonical E64 release and the checked-in, authored MVP template
projection are accepted.  This module deliberately has no parameters for a
release, source corpus, candidate queue, or output path.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from validators.ontology_v2 import CanonicalRelease, load_canonical_release
from validators.procedure_contract import (
    ProcedureContract,
    _id,
    _trusted_workspace_root,
    validate_procedure_against_release,
)


MVP_PROCEDURE_IDS = (
    "procedure.diagnose-primary-constraint",
    "procedure.build-leader-oppp",
    "procedure.build-vision-summary",
    "procedure.set-quarterly-priority",
    "procedure.install-meeting-rhythm",
    "procedure.scaleup-quarterly-review",
)
_DENIED_CANDIDATE_IDS = {
    "candidate.cash.metric.working-capital-days",
    "candidate.cash.procedure.cash-tool",
    "candidate.cash.rule.cash-initiative",
}


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MvpTemplate(_StrictModel):
    id: Literal[
        "procedure.diagnose-primary-constraint",
        "procedure.build-leader-oppp",
        "procedure.build-vision-summary",
        "procedure.set-quarterly-priority",
        "procedure.install-meeting-rhythm",
        "procedure.scaleup-quarterly-review",
    ]
    node_ids: list[str] = Field(min_length=1, max_length=32)
    input_node_refs: dict[str, list[str]] = Field(min_length=1, max_length=32)
    contract: dict[str, Any]

    @field_validator("node_ids")
    @classmethod
    def validate_node_ids(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate template node ID")
        return sorted(_id(value, "template node ID") for value in values)

    @field_validator("input_node_refs")
    @classmethod
    def validate_input_node_refs(
        cls, values: dict[str, list[str]]
    ) -> dict[str, list[str]]:
        if not values:
            raise ValueError("template has no input-node mapping")
        validated: dict[str, list[str]] = {}
        for input_id, node_ids in values.items():
            safe_input_id = _id(input_id, "template input ID")
            if not node_ids or len(node_ids) != len(set(node_ids)):
                raise ValueError("invalid template input-node mapping")
            validated[safe_input_id] = sorted(
                _id(node_id, "template input node ID") for node_id in node_ids
            )
        return dict(sorted(validated.items()))

    @field_validator("contract")
    @classmethod
    def validate_contract_shape(cls, value: dict[str, Any]) -> dict[str, Any]:
        if "evidence_refs" in value or "node_ids" in value or "candidate_id" in value:
            raise ValueError("template cannot inject evidence or source mappings")
        return value

    @model_validator(mode="after")
    def validate_input_mapping(self) -> "MvpTemplate":
        inputs = self.contract.get("required_inputs", []) + self.contract.get(
            "optional_inputs", []
        )
        if not isinstance(inputs, list):
            raise ValueError("template inputs are invalid")
        input_ids = {input_.get("id") for input_ in inputs if isinstance(input_, dict)}
        if input_ids != set(self.input_node_refs):
            raise ValueError("template inputs must have approved node mappings")
        if not all(
            set(node_ids).issubset(set(self.node_ids))
            for node_ids in self.input_node_refs.values()
        ):
            raise ValueError("template input mapping escapes procedure nodes")
        return self


class MvpTemplateProjection(_StrictModel):
    schema_version: Literal[1]
    templates: list[MvpTemplate] = Field(min_length=6, max_length=6)

    @model_validator(mode="after")
    def validate_complete_mvp(self) -> "MvpTemplateProjection":
        ids = [template.id for template in self.templates]
        if len(ids) != len(set(ids)) or set(ids) != set(MVP_PROCEDURE_IDS):
            raise ValueError("MVP template set is incomplete")
        return self


class ProcedureTrace(_StrictModel):
    procedure_id: str
    node_ids: list[str]
    evidence_refs: list[str]
    input_node_refs: dict[str, list[str]]


class MvpProcedureRelease(_StrictModel):
    schema_version: Literal[1]
    release_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    procedures: list[ProcedureTrace] = Field(min_length=6, max_length=6)
    node_to_procedures: dict[str, list[str]]


@dataclass(frozen=True)
class CompiledMvpProcedures:
    contracts: tuple[ProcedureContract, ...]
    release: MvpProcedureRelease


def _template_path(root: Path) -> Path:
    return root / "procedures" / "mvp" / "templates.json"


def _release_path(root: Path) -> Path:
    return root / "ontology" / "v2" / "releases" / "s64.1.json"


def _load_projection(root: Path) -> MvpTemplateProjection:
    try:
        return MvpTemplateProjection.model_validate_json(
            _template_path(root).read_text(encoding="utf-8")
        )
    except Exception as exc:
        raise ValueError("MVP procedure template projection invalid") from exc


def _load_release(root: Path) -> CanonicalRelease:
    try:
        return load_canonical_release(_release_path(root))
    except Exception as exc:
        raise ValueError("canonical E64 release unavailable") from exc


def _compile(root: Path) -> CompiledMvpProcedures:
    projection = _load_projection(root)
    canonical = _load_release(root)
    released_nodes = {node.canonical_id: node for node in canonical.nodes}
    excluded_candidates = {item.candidate_id for item in canonical.exclusions}
    if not _DENIED_CANDIDATE_IDS.issubset(excluded_candidates):
        raise ValueError("canonical E64 cash exclusions are incomplete")

    contracts: list[ProcedureContract] = []
    traces: list[ProcedureTrace] = []
    node_to_procedures: dict[str, list[str]] = {}
    for template in sorted(projection.templates, key=lambda item: item.id):
        if any(node_id.startswith("candidate.") for node_id in template.node_ids):
            raise ValueError("candidate IDs cannot compile procedures")
        unknown_node_ids = set(template.node_ids) - set(released_nodes)
        if unknown_node_ids:
            raise ValueError(
                "procedure mapping references nodes outside canonical release"
            )
        evidence_refs = sorted(
            {
                evidence_ref
                for node_id in template.node_ids
                for evidence_ref in released_nodes[node_id].evidence_refs
            }
        )
        payload = dict(template.contract)
        payload["evidence_refs"] = evidence_refs
        try:
            contract = ProcedureContract.model_validate(payload)
        except Exception as exc:
            raise ValueError("MVP procedure contract template invalid") from exc
        if contract.id != template.id:
            raise ValueError("template procedure ID does not match its contract")
        validate_procedure_against_release(contract)
        trace = ProcedureTrace(
            procedure_id=template.id,
            node_ids=template.node_ids,
            evidence_refs=evidence_refs,
            input_node_refs=template.input_node_refs,
        )
        contracts.append(contract)
        traces.append(trace)
        for node_id in template.node_ids:
            node_to_procedures.setdefault(node_id, []).append(template.id)
    rendered_release = _render_json(
        {
            "schema_version": 1,
            "release_sha256": hashlib.sha256(
                _release_path(root).read_bytes()
            ).hexdigest(),
            "procedures": [trace.model_dump(mode="json") for trace in traces],
            "node_to_procedures": {
                node_id: sorted(procedure_ids)
                for node_id, procedure_ids in sorted(node_to_procedures.items())
            },
        }
    )
    return CompiledMvpProcedures(
        contracts=tuple(contracts),
        release=MvpProcedureRelease.model_validate_json(rendered_release),
    )


def compile_mvp_procedures() -> CompiledMvpProcedures:
    """Compile exactly six procedure contracts from the trusted project state."""
    return _compile(_trusted_workspace_root())


def _render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_mvp_procedure_files(compiled: CompiledMvpProcedures) -> dict[str, str]:
    """Render deterministic internal artifacts, without writing them."""
    rendered = {
        "release.json": _render_json(compiled.release.model_dump(mode="json")),
    }
    for contract in compiled.contracts:
        rendered[f"contracts/{contract.id}.yaml"] = yaml.safe_dump(
            contract.model_dump(mode="json"),
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
    return rendered


def build_mvp_procedure_files(check: bool = False) -> bool:
    """Build or exactly verify the canonical internal procedure artifacts."""
    root = _trusted_workspace_root()
    output_root = root / "procedures" / "mvp"
    rendered = render_mvp_procedure_files(compile_mvp_procedures())
    if check:
        return all(
            (output_root / relative_path).is_file()
            and (output_root / relative_path).read_text(encoding="utf-8") == contents
            for relative_path, contents in rendered.items()
        )
    for relative_path, contents in rendered.items():
        target = output_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contents, encoding="utf-8")
    return True
