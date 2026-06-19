"""Voice of Customer evidence contract validation."""

from __future__ import annotations

from datetime import date
import hashlib
from pathlib import Path
from typing import Literal, Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError

try:
    import yaml
except ImportError as exc:  # pragma: no cover - project dependency
    raise ImportError("PyYAML required: pip install pyyaml") from exc


SourceType = Literal["interview", "testimonial", "audio", "review", "survey", "note"]
ReviewStatus = Literal["draft", "reviewed", "approved", "rejected"]


class CustomerEvidenceRecord(BaseModel):
    """Typed Voice of Customer evidence record."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    source_type: SourceType
    source_label: str = Field(min_length=1)
    captured_at: date
    context: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    customer_segment: str = Field(min_length=1)
    evidence_tags: list[str] = Field(min_length=1)
    review_status: ReviewStatus
    is_fixture: bool
    notes: str | None = None

    @property
    def strategy_usable(self) -> bool:
        """Return whether this record can support strategy claims."""
        return self.review_status == "approved" and not self.is_fixture


CustomerEvidenceRecord.model_rebuild()


class RawCustomerQuote(BaseModel):
    """Raw operator-provided customer quote before evidence normalization."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    source_type: SourceType = "note"
    source_label: str | None = None
    captured_at: date | None = None
    context: str | None = None
    quote: str = Field(min_length=1)
    customer_segment: str = Field(min_length=1)
    evidence_tags: list[str] = Field(min_length=1)
    notes: str | None = None


class NormalizationResult(BaseModel):
    """Batch normalization output for raw customer quotes."""

    records: list[CustomerEvidenceRecord]
    duplicates: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


RawCustomerQuote.model_rebuild()
NormalizationResult.model_rebuild()


def load_evidence_records(evidence_path: Path) -> list[CustomerEvidenceRecord]:
    """Load Voice of Customer evidence records from a YAML list."""
    data = yaml.safe_load(evidence_path.read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise ValueError("Voice of Customer evidence file must contain a list")
    return [CustomerEvidenceRecord.model_validate(item) for item in data]


def validate_evidence_file(evidence_path: Path) -> list[str]:
    """Return readable validation errors for a Voice of Customer evidence file."""
    try:
        load_evidence_records(evidence_path)
    except ValidationError as exc:
        return [_format_validation_error(error) for error in exc.errors()]
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [str(exc)]
    return []


def normalize_raw_quotes(raw_quotes: list[Mapping[str, Any]]) -> NormalizationResult:
    """Normalize raw quote dictionaries into Voice of Customer evidence records."""
    records: list[CustomerEvidenceRecord] = []
    duplicates: list[str] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()

    for index, raw_quote in enumerate(raw_quotes):
        try:
            quote = RawCustomerQuote.model_validate(raw_quote)
        except ValidationError as exc:
            errors.extend(
                f"raw_quotes[{index}].{_format_validation_error(error)}"
                for error in exc.errors()
            )
            continue

        source_label = quote.source_label or "REVIEW_REQUIRED: missing source_label"
        duplicate_key = (source_label.strip().lower(), quote.quote.strip().lower())
        if duplicate_key in seen:
            duplicates.append(f"duplicate raw quote for source={source_label!r}")
            continue
        seen.add(duplicate_key)

        missing = _missing_provenance(quote)
        is_complete = not missing
        record = CustomerEvidenceRecord(
            id=quote.id or _stable_evidence_id(source_label, quote.quote),
            source_type=quote.source_type,
            source_label=source_label,
            captured_at=quote.captured_at or date(1970, 1, 1),
            context=quote.context or "REVIEW_REQUIRED: missing context",
            quote=quote.quote,
            customer_segment=quote.customer_segment,
            evidence_tags=quote.evidence_tags,
            review_status="approved" if is_complete else "draft",
            is_fixture=not is_complete,
            notes=quote.notes or _missing_provenance_note(missing),
        )
        records.append(record)

    return NormalizationResult(records=records, duplicates=duplicates, errors=errors)


def _format_validation_error(error: Mapping[str, Any]) -> str:
    location = ".".join(str(part) for part in error.get("loc", ())) or "record"
    message = str(error.get("msg", "invalid value"))
    return f"{location}: {message}"


def _stable_evidence_id(source_label: str, quote: str) -> str:
    digest = hashlib.sha1(f"{source_label}|{quote}".encode("utf-8")).hexdigest()
    return f"voc-{digest[:10]}"


def _missing_provenance(quote: RawCustomerQuote) -> list[str]:
    missing: list[str] = []
    if not quote.source_label:
        missing.append("source_label")
    if quote.captured_at is None:
        missing.append("captured_at")
    if not quote.context:
        missing.append("context")
    return missing


def _missing_provenance_note(missing: list[str]) -> str | None:
    if not missing:
        return None
    return "Missing provenance: " + ", ".join(missing)
