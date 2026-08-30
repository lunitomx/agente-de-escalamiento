"""Private visual-layout attestation contract for source-bounded forms."""

from __future__ import annotations

from datetime import date
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


_REFERENCE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")


class FormLayoutCheck(_StrictModel):
    tool_ref: str = Field(min_length=3, max_length=128)
    form_part: Literal["front", "back"] | None = None
    page: int = Field(ge=1, le=99)
    topology_status: Literal["matched"]
    checked_axes: int = Field(ge=1, le=32)
    checked_fields: int = Field(ge=1, le=64)
    mismatch_count: Literal[0]


class FormLayoutReviewReceipt(_StrictModel):
    schema_version: Literal[1]
    domain: Literal["people", "strategy", "execution"]
    status: Literal["pass"]
    reviewer_ref: str = Field(min_length=3, max_length=64)
    reviewed_on: date
    source_url: HttpUrl
    source_edition: str = Field(min_length=3, max_length=160)
    rights_state: Literal["private-validation-only"]
    asset_persisted: Literal[False]
    method: Literal["manual-visual-inspection"]
    forms: list[FormLayoutCheck] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def validate_private_review(self) -> "FormLayoutReviewReceipt":
        if not _REFERENCE.fullmatch(self.reviewer_ref):
            raise ValueError("reviewer reference must be an opaque identifier")
        repeated_refs = {
            item.tool_ref
            for item in self.forms
            if sum(other.tool_ref == item.tool_ref for other in self.forms) > 1
        }
        for tool_ref in repeated_refs:
            matching = [item for item in self.forms if item.tool_ref == tool_ref]
            if (
                any(item.form_part is None for item in matching)
                and len({item.page for item in matching}) > 1
            ):
                raise ValueError("repeated visual form requires an explicit part")
        form_keys = [(item.tool_ref, item.form_part) for item in self.forms]
        if len(form_keys) != len(set(form_keys)):
            raise ValueError("visual review repeats a form")
        return self


def validate_form_layout_review(receipt: FormLayoutReviewReceipt) -> None:
    """Keep a named boundary for callers and future receipt versions."""
    FormLayoutReviewReceipt.model_validate(receipt.model_dump(mode="json"))
