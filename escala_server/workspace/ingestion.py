"""Local, deterministic source identity and format capability contracts.

This first ingestion seam deliberately does not parse or persist source data.
It establishes the safe identity and closed capability vocabulary consumed by
the later structural profilers and the synced-folder inbox.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SourceFormat = Literal["csv", "tsv", "xlsx", "text", "transcript", "pdf", "unknown"]
CapabilityStatus = Literal["supported", "provider_unavailable", "unsupported"]


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
