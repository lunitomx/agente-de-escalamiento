"""Combined private-source integrity receipt without corpus disclosure."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from validators.public_boundary import (
    PublicPathDisposition,
    classify_public_path,
    load_public_boundary_policy,
    public_boundary_policy_hash,
)
from validators.source_authority import build_source_authority_receipt
from validators.source_manifest import build_source_manifest_receipt


_SHA256_PATTERN = r"^[0-9a-f]{64}$"


class SourceIntegrityError(ValueError):
    """Raised without exposing source paths, locators, or text."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceIntegrityReceipt(_StrictModel):
    schema_version: Literal[1]
    status: Literal["pass"]
    registry_sha256: str = Field(pattern=_SHA256_PATTERN)
    manifest_sha256: str = Field(pattern=_SHA256_PATTERN)
    public_boundary_sha256: str = Field(pattern=_SHA256_PATTERN)
    source_count: int = Field(ge=1)
    artifact_count: int = Field(ge=1)
    unit_count: int = Field(ge=1)
    excluded_line_count: int = Field(ge=0)
    source_artifacts_explicitly_denied: Literal[True]
    private_only: Literal[True]
    rights_unresolved: Literal[True]


def build_source_integrity_receipt(
    repository: Path,
    registry_path: Path,
    manifest_path: Path,
    policy_path: Path,
) -> SourceIntegrityReceipt:
    """Prove custody, structural coverage, and explicit export denial together."""
    try:
        authority = build_source_authority_receipt(repository, registry_path)
        manifest = build_source_manifest_receipt(
            repository, registry_path, manifest_path
        )
        policy = load_public_boundary_policy(policy_path)
        dispositions = {
            classify_public_path(policy, "sources/source-registry.yaml"),
            classify_public_path(policy, "sources/source-manifest.jsonl"),
        }
    except Exception as exc:
        raise SourceIntegrityError("source integrity validation failed") from exc
    if dispositions != {PublicPathDisposition.DENIED}:
        raise SourceIntegrityError("private source surfaces are not explicitly denied")
    return SourceIntegrityReceipt(
        schema_version=1,
        status="pass",
        registry_sha256=authority.registry_sha256,
        manifest_sha256=manifest.manifest_sha256,
        public_boundary_sha256=public_boundary_policy_hash(policy),
        source_count=authority.source_count,
        artifact_count=authority.artifact_count,
        unit_count=manifest.unit_count,
        excluded_line_count=manifest.excluded_line_count,
        source_artifacts_explicitly_denied=True,
        private_only=True,
        rights_unresolved=True,
    )


def render_source_integrity_json(receipt: SourceIntegrityReceipt) -> str:
    return (
        json.dumps(
            receipt.model_dump(mode="json"), ensure_ascii=True, indent=2, sort_keys=True
        )
        + "\n"
    )


def render_source_integrity_markdown(receipt: SourceIntegrityReceipt) -> str:
    return "\n".join(
        [
            "# ESCALA Private Source Integrity Receipt",
            "",
            "- Status: `pass`",
            f"- Source records verified: {receipt.source_count}",
            f"- Private artifacts verified: {receipt.artifact_count}",
            f"- Structural units verified: {receipt.unit_count}",
            "- Explicitly denied source surfaces: `true`",
            "- Distribution: private only",
            "- Rights posture: unresolved; distribution remains blocked",
            "",
        ]
    )
