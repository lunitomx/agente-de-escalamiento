"""Local, deterministic source identity and format capability contracts.

This first ingestion seam deliberately does not parse or persist source data.
It establishes the safe identity and closed capability vocabulary consumed by
the later structural profilers and the synced-folder inbox.
"""

from __future__ import annotations

import csv
import hashlib
import io
import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from .authority import WorkspaceConfig


SourceFormat = Literal["csv", "tsv", "xlsx", "text", "transcript", "pdf", "unknown"]
CapabilityStatus = Literal["supported", "provider_unavailable", "unsupported"]
SourceStatus = Literal[
    "ready",
    "needs_clarification",
    "unsupported",
    "provider_unavailable",
    "corrupt",
]
FieldKind = Literal["date", "entity", "unit"]


class _StrictModel(BaseModel):
    """Closed immutable Pydantic contract shared by ingestion models."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceIngestionError(ValueError):
    """Safe local failure with a stable code and no path in the message."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class FormatCapability(_StrictModel):
    """Capability declaration for one normalized file extension."""

    extension: str = Field(min_length=1, max_length=20)
    format: SourceFormat
    status: CapabilityStatus
    adapter: str = Field(min_length=1, max_length=40)


class SourceIdentity(_StrictModel):
    """Stable, path-redacted identity for one source byte sequence."""

    relative_path: str = Field(min_length=1, max_length=512)
    format: SourceFormat
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str = Field(pattern=r"^[0-9a-f]{64}$")


class HeaderCandidate(_StrictModel):
    """A structural header candidate identified only by ordinal and score."""

    row_index: int = Field(ge=0)
    score: int = Field(ge=0)
    column_count: int = Field(ge=1)


class FieldCandidate(_StrictModel):
    """A semantic column hint without copying headers or cell values."""

    column_index: int = Field(ge=0)
    kind: FieldKind
    score: int = Field(ge=0)


class TableProfile(_StrictModel):
    """Bounded structural profile of one logical table."""

    table_ordinal: int = Field(ge=0)
    row_count: int = Field(ge=0)
    column_count: int = Field(ge=0)
    header_candidates: tuple[HeaderCandidate, ...] = ()
    field_candidates: tuple[FieldCandidate, ...] = ()


class SourceProfile(_StrictModel):
    """Non-content structural profile passed to later stories."""

    tables: tuple[TableProfile, ...] = ()


class SourceQuestion(_StrictModel):
    """Bounded ordinal clarification question for a material ambiguity."""

    code: str = Field(min_length=1, max_length=80)
    options: tuple[str, ...] = Field(min_length=2, max_length=5)


class IngestionResult(_StrictModel):
    """Profile outcome; it never contains a database handle or source bytes."""

    identity: SourceIdentity
    status: SourceStatus
    profile: SourceProfile | None = None
    questions: tuple[SourceQuestion, ...] = ()
    findings: tuple[str, ...] = ()


class SourceRegistry:
    """Closed local format registry; no dynamic plugins or network lookups."""

    _CAPABILITIES: tuple[FormatCapability, ...] = (
        FormatCapability(
            extension=".csv", format="csv", status="supported", adapter="delimited"
        ),
        FormatCapability(
            extension=".tsv", format="tsv", status="supported", adapter="delimited"
        ),
        FormatCapability(
            extension=".xlsx", format="xlsx", status="supported", adapter="xlsx"
        ),
        FormatCapability(
            extension=".txt", format="text", status="supported", adapter="text"
        ),
        FormatCapability(
            extension=".md", format="text", status="supported", adapter="text"
        ),
        FormatCapability(
            extension=".transcript",
            format="transcript",
            status="supported",
            adapter="text",
        ),
        FormatCapability(
            extension=".pdf",
            format="pdf",
            status="provider_unavailable",
            adapter="none",
        ),
    )

    @classmethod
    def default(cls) -> "SourceRegistry":
        """Return the deterministic built-in registry."""

        return cls()

    def capability_for(self, source: str | Path) -> FormatCapability:
        """Return capability by case-insensitive suffix, or safe unknown."""

        suffix = Path(source).suffix.casefold()
        for capability in self._CAPABILITIES:
            if capability.extension == suffix:
                return capability
        return FormatCapability(
            extension=suffix or ".unknown",
            format="unknown",
            status="unsupported",
            adapter="none",
        )


def build_source_identity(
    source_path: Path,
    exchange_root: Path,
    *,
    registry: SourceRegistry | None = None,
) -> SourceIdentity:
    """Hash a source inside exchange and return only relative provenance."""

    try:
        exchange = exchange_root.expanduser().resolve(strict=False)
        source = source_path.expanduser().resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        del exc
        raise SourceIngestionError("source_path_invalid") from None

    if not source.is_file():
        raise SourceIngestionError("source_not_file")
    try:
        relative = source.relative_to(exchange).as_posix()
    except ValueError:
        raise SourceIngestionError("source_outside_exchange") from None

    try:
        content = source.read_bytes()
    except OSError:
        raise SourceIngestionError("source_read_failed") from None

    content_sha256 = hashlib.sha256(content).hexdigest()
    source_id = hashlib.sha256(
        f"v1\0{relative}\0{content_sha256}".encode("utf-8")
    ).hexdigest()
    capability = (registry or SourceRegistry.default()).capability_for(source)
    return SourceIdentity(
        relative_path=relative,
        format=capability.format,
        content_sha256=content_sha256,
        source_id=source_id,
    )


def profile_source(
    config: "WorkspaceConfig",
    source_path: Path,
    *,
    registry: SourceRegistry | None = None,
) -> IngestionResult:
    """Profile a supported delimited source without persisting any state."""

    from .authority import validate_workspace

    if validate_workspace(config).status != "pass":
        raise SourceIngestionError("workspace_invalid")

    active_registry = registry or SourceRegistry.default()
    identity = build_source_identity(
        source_path, config.exchange_root, registry=active_registry
    )
    capability = active_registry.capability_for(source_path)
    if capability.status == "unsupported":
        return IngestionResult(
            identity=identity, status="unsupported", findings=("format_unsupported",)
        )
    if capability.status == "provider_unavailable":
        return IngestionResult(
            identity=identity,
            status="provider_unavailable",
            findings=("provider_unavailable",),
        )
    if capability.format not in {"csv", "tsv"}:
        return IngestionResult(
            identity=identity,
            status="provider_unavailable",
            findings=("adapter_pending",),
        )

    try:
        raw = source_path.expanduser().resolve(strict=True).read_bytes()
        text = raw.decode("utf-8-sig")
        delimiter = "\t" if capability.format == "tsv" else ","
        rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    except (OSError, UnicodeDecodeError, csv.Error):
        return IngestionResult(
            identity=identity, status="corrupt", findings=("source_unreadable",)
        )

    profile, questions = _profile_delimited(rows)
    if questions:
        return IngestionResult(
            identity=identity,
            status="needs_clarification",
            profile=profile,
            questions=questions,
            findings=("material_ambiguity",),
        )
    return IngestionResult(identity=identity, status="ready", profile=profile)


def _profile_delimited(
    rows: list[list[str]],
) -> tuple[SourceProfile, tuple[SourceQuestion, ...]]:
    """Infer structural candidates from bounded delimited rows."""

    if not rows:
        return SourceProfile(), (
            SourceQuestion(code="table_empty", options=("review", "retry")),
        )

    candidates: list[HeaderCandidate] = []
    for row_index, row in enumerate(rows[:5]):
        nonempty = [cell.strip() for cell in row if cell.strip()]
        if not nonempty:
            continue
        token_score = sum(1 for cell in nonempty if _header_token(cell))
        score = token_score * 10 + len(nonempty)
        if token_score or row_index == 0:
            candidates.append(
                HeaderCandidate(
                    row_index=row_index,
                    score=score,
                    column_count=len(row),
                )
            )

    candidates.sort(key=lambda candidate: (-candidate.score, candidate.row_index))
    questions: tuple[SourceQuestion, ...] = ()
    if len(candidates) > 1 and candidates[0].score == candidates[1].score:
        tied = tuple(
            f"row_{candidate.row_index}"
            for candidate in candidates
            if candidate.score == candidates[0].score
        )
        questions = (SourceQuestion(code="header_row_ambiguous", options=tied),)

    header_index = candidates[0].row_index if candidates else 0
    header = rows[header_index] if header_index < len(rows) else []
    field_candidates: list[FieldCandidate] = []
    for column_index, value in enumerate(header):
        kind = _field_kind(value)
        if kind is not None:
            field_candidates.append(
                FieldCandidate(column_index=column_index, kind=kind, score=10)
            )

    profile = SourceProfile(
        tables=(
            TableProfile(
                table_ordinal=0,
                row_count=len(rows),
                column_count=max((len(row) for row in rows), default=0),
                header_candidates=tuple(candidates),
                field_candidates=tuple(field_candidates),
            ),
        )
    )
    return profile, questions


def _normalize_token(value: str) -> str:
    """Normalize a header token for local, accent-insensitive heuristics."""

    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _header_token(value: str) -> bool:
    """Return whether a cell looks like a semantic header token."""

    token = _normalize_token(value)
    aliases = {
        "fecha",
        "date",
        "cliente",
        "customer",
        "empresa",
        "importe",
        "monto",
        "amount",
        "unidad",
        "unit",
        "cantidad",
        "quantity",
    }
    return token in aliases


def _field_kind(value: str) -> FieldKind | None:
    """Map a header token to a bounded structural field kind."""

    token = _normalize_token(value)
    if token in {"fecha", "date", "dia", "day"}:
        return "date"
    if token in {
        "cliente",
        "customer",
        "empresa",
        "company",
        "proveedor",
        "supplier",
    }:
        return "entity"
    if token in {
        "importe",
        "monto",
        "amount",
        "unidad",
        "unit",
        "cantidad",
        "quantity",
        "valor",
        "value",
    }:
        return "unit"
    return None
