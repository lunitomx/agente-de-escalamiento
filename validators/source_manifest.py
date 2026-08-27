"""Deterministic, private structural manifests without source-text output."""

from __future__ import annotations

from enum import Enum
import hashlib
import json
from pathlib import Path
import re
from typing import Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from validators.source_authority import (
    SourceAuthorityError,
    SourceEntry,
    SourceRegistry,
    load_source_registry,
    validate_source_authority,
)


_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


class SourceManifestError(ValueError):
    """Raised without returning private source text or locators."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ContentType(str, Enum):
    SECTION = "section"
    DEFINITION = "definition"
    DIAGNOSTIC_QUESTION = "diagnostic_question"
    ACTION = "action"
    WARNING = "warning"
    FORMULA = "formula"
    TOOL_OR_FORM = "tool_or_form"
    HISTORICAL_EXAMPLE = "historical_example"
    EXTERNAL_REFERENCE = "external_reference"
    EXCLUSION = "exclusion"


class ManifestUnit(_StrictModel):
    source_id: str = Field(min_length=3, max_length=128)
    unit_id: str = Field(min_length=3, max_length=192)
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    content_type: ContentType
    sha256: str = Field(pattern=_SHA256_PATTERN.pattern)
    exclusion_reason: str | None = None

    @field_validator("source_id", "unit_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        if _ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe manifest identifier")
        return value

    @model_validator(mode="after")
    def validate_range_and_exclusion(self) -> ManifestUnit:
        if self.line_end < self.line_start:
            raise ValueError("invalid manifest range")
        if self.content_type is ContentType.EXCLUSION:
            if not self.exclusion_reason:
                raise ValueError("exclusion requires a reason")
        elif self.exclusion_reason is not None:
            raise ValueError("only exclusions may carry a reason")
        return self


class SourceManifest(_StrictModel):
    schema_version: Literal[1]
    source_id: str = Field(min_length=3, max_length=128)
    source_sha256: str = Field(pattern=_SHA256_PATTERN.pattern)
    source_line_count: int = Field(ge=1)
    units: list[ManifestUnit] = Field(min_length=1)

    @field_validator("source_id")
    @classmethod
    def validate_source_id(cls, value: str) -> str:
        if _ID_PATTERN.fullmatch(value) is None:
            raise ValueError("unsafe manifest source ID")
        return value

    @field_validator("units")
    @classmethod
    def validate_units(cls, values: list[ManifestUnit]) -> list[ManifestUnit]:
        ids = [item.unit_id for item in values]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate manifest unit ID")
        if {item.source_id for item in values} and {
            item.source_id for item in values
        } != {values[0].source_id}:
            raise ValueError("manifest has mixed source IDs")
        return sorted(values, key=lambda item: (item.line_start, item.line_end))

    @model_validator(mode="after")
    def validate_coverage(self) -> SourceManifest:
        if any(unit.source_id != self.source_id for unit in self.units):
            raise ValueError("manifest unit source ID mismatch")
        expected_start = 1
        for unit in self.units:
            if unit.line_start != expected_start:
                raise ValueError("manifest coverage gap or overlap")
            expected_start = unit.line_end + 1
        if expected_start - 1 != self.source_line_count:
            raise ValueError("manifest does not cover source lines")
        return self


class SourceManifestReceipt(_StrictModel):
    schema_version: Literal[1]
    status: Literal["pass"]
    source_id: str
    unit_count: int = Field(ge=1)
    excluded_line_count: int = Field(ge=0)
    source_sha256: str = Field(pattern=_SHA256_PATTERN.pattern)
    manifest_sha256: str = Field(pattern=_SHA256_PATTERN.pattern)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _primary_artifact(source: SourceEntry):
    return next(item for item in source.artifacts if item.role.value == "primary")


def _read_primary_source(repository: Path, source: SourceEntry) -> list[bytes]:
    artifact = _primary_artifact(source)
    path = (repository.resolve() / artifact.path).resolve()
    try:
        path.relative_to(repository.resolve())
        raw = path.read_bytes()
    except (OSError, ValueError) as exc:
        raise SourceManifestError("primary source unreadable") from exc
    return raw.splitlines(keepends=True)


def _classify_heading(heading: str) -> ContentType:
    normalized = heading.casefold()
    if "warning" in normalized:
        return ContentType.WARNING
    if "key question" in normalized or "question" in normalized:
        return ContentType.DIAGNOSTIC_QUESTION
    if "action" in normalized or normalized.startswith("step"):
        return ContentType.ACTION
    if "formula" in normalized or "equation" in normalized:
        return ContentType.FORMULA
    if any(token in normalized for token in ("worksheet", "chart", "tool", "plan")):
        return ContentType.TOOL_OR_FORM
    if any(token in normalized for token in ("example", "case", "experience")):
        return ContentType.HISTORICAL_EXAMPLE
    if any(token in normalized for token in ("reference", "resource", "bibliography")):
        return ContentType.EXTERNAL_REFERENCE
    if any(token in normalized for token in ("definition", "what is", "meaning")):
        return ContentType.DEFINITION
    return ContentType.SECTION


def _heading_starts(lines: list[bytes]) -> list[tuple[int, ContentType]]:
    starts: list[tuple[int, ContentType]] = []
    for line_number, raw_line in enumerate(lines, start=1):
        match = _HEADING_PATTERN.match(raw_line.decode("utf-8", errors="replace"))
        if match:
            starts.append((line_number, _classify_heading(match.group(2))))
    return starts


def build_source_manifest(
    repository: Path, registry: SourceRegistry, source_id: str
) -> SourceManifest:
    repository = repository.resolve()
    try:
        validate_source_authority(repository, registry)
    except SourceAuthorityError as exc:
        raise SourceManifestError("source authority verification failed") from exc
    source = next(
        (item for item in registry.sources if item.source_id == source_id), None
    )
    if source is None:
        raise SourceManifestError("source ID unknown")
    lines = _read_primary_source(repository, source)
    if not lines:
        raise SourceManifestError("primary source empty")
    primary = _primary_artifact(source)
    starts = _heading_starts(lines)
    if starts:
        boundaries = starts
        if starts[0][0] > 1:
            boundaries = [(1, ContentType.EXCLUSION), *starts]
    else:
        boundaries = [(1, ContentType.EXCLUSION)]
    units: list[ManifestUnit] = []
    for index, (line_start, content_type) in enumerate(boundaries, start=1):
        line_end = boundaries[index][0] - 1 if index < len(boundaries) else len(lines)
        if line_end < line_start:
            continue
        chunk = b"".join(lines[line_start - 1 : line_end])
        units.append(
            ManifestUnit(
                source_id=source_id,
                unit_id=f"{source_id}.u{index:04d}",
                line_start=line_start,
                line_end=line_end,
                content_type=content_type,
                sha256=_sha256(chunk),
                exclusion_reason=(
                    "no_structural_heading"
                    if content_type is ContentType.EXCLUSION
                    else None
                ),
            )
        )
    return SourceManifest(
        schema_version=1,
        source_id=source_id,
        source_sha256=primary.sha256,
        source_line_count=len(lines),
        units=units,
    )


def source_manifest_hash(manifest: SourceManifest) -> str:
    payload = json.dumps(
        manifest.model_dump(mode="json"),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256(payload)


def render_source_manifest_jsonl(manifest: SourceManifest) -> str:
    header = {
        "schema_version": manifest.schema_version,
        "source_id": manifest.source_id,
        "source_sha256": manifest.source_sha256,
        "source_line_count": manifest.source_line_count,
    }
    rows: Iterable[dict[str, object]] = [header] + [
        unit.model_dump(mode="json") for unit in manifest.units
    ]
    return "".join(
        json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )


def load_source_manifest(path: Path) -> SourceManifest:
    try:
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceManifestError("manifest unreadable") from exc
    if not rows:
        raise SourceManifestError("manifest empty")
    header, *units = rows
    if not isinstance(header, dict) or any(not isinstance(row, dict) for row in units):
        raise SourceManifestError("manifest structure invalid")
    try:
        return SourceManifest.model_validate({**header, "units": units})
    except Exception as exc:
        raise SourceManifestError("manifest contract invalid") from exc


def validate_source_manifest(
    repository: Path, registry: SourceRegistry, manifest: SourceManifest
) -> None:
    try:
        validate_source_authority(repository, registry)
    except SourceAuthorityError as exc:
        raise SourceManifestError("source authority verification failed") from exc
    source = next(
        (item for item in registry.sources if item.source_id == manifest.source_id),
        None,
    )
    if source is None:
        raise SourceManifestError("manifest source unknown")
    primary = _primary_artifact(source)
    lines = _read_primary_source(repository.resolve(), source)
    if manifest.source_sha256 != primary.sha256 or manifest.source_line_count != len(
        lines
    ):
        raise SourceManifestError("manifest source identity mismatch")
    for unit in manifest.units:
        chunk = b"".join(lines[unit.line_start - 1 : unit.line_end])
        if _sha256(chunk) != unit.sha256:
            raise SourceManifestError("manifest unit hash mismatch")


def build_source_manifest_receipt(
    repository: Path, registry_path: Path, manifest_path: Path
) -> SourceManifestReceipt:
    registry = load_source_registry(registry_path)
    manifest = load_source_manifest(manifest_path)
    validate_source_manifest(repository, registry, manifest)
    return SourceManifestReceipt(
        schema_version=1,
        status="pass",
        source_id=manifest.source_id,
        unit_count=len(manifest.units),
        excluded_line_count=sum(
            unit.line_end - unit.line_start + 1
            for unit in manifest.units
            if unit.content_type is ContentType.EXCLUSION
        ),
        source_sha256=manifest.source_sha256,
        manifest_sha256=source_manifest_hash(manifest),
    )


def render_source_manifest_receipt_json(receipt: SourceManifestReceipt) -> str:
    return (
        json.dumps(
            receipt.model_dump(mode="json"), ensure_ascii=True, indent=2, sort_keys=True
        )
        + "\n"
    )


def render_source_manifest_receipt_markdown(receipt: SourceManifestReceipt) -> str:
    return "\n".join(
        [
            "# ESCALA Source Manifest Receipt",
            "",
            "- Status: `pass`",
            f"- Source ID: `{receipt.source_id}`",
            f"- Units verified: {receipt.unit_count}",
            f"- Excluded lines: {receipt.excluded_line_count}",
            f"- Source SHA-256: `{receipt.source_sha256}`",
            f"- Manifest SHA-256: `{receipt.manifest_sha256}`",
            "",
        ]
    )
