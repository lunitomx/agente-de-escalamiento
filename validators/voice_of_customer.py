"""Voice of Customer evidence contract validation."""

from __future__ import annotations

from datetime import date
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


def _format_validation_error(error: Mapping[str, Any]) -> str:
    location = ".".join(str(part) for part in error.get("loc", ())) or "record"
    message = str(error.get("msg", "invalid value"))
    return f"{location}: {message}"
