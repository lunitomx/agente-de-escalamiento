"""coaching.responder.models — Pydantic models for executive responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExecutiveResponse(BaseModel):
    """A five-block executive response for a confirmed decision."""

    decision: str = Field(..., min_length=1)
    area: str = Field(..., min_length=1)
    what_i_see: str = Field(..., min_length=1)
    why_it_matters: str = Field(..., min_length=1)
    evidence: list[str] = Field(default_factory=list)
    what_i_dont_know: str = Field(..., min_length=1)
    next_step: str = Field(..., min_length=1)
    can_proceed: bool = Field(default=True)
