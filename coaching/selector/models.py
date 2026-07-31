"""coaching.selector.models — Pydantic models for tool selection receipts.

Guarantees that every selection result has a stable contract and a traceable
receipt, including the clarify action when minimum evidence is missing.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SelectionAction = Literal["tool_selected", "clarify"]


class ToolSelection(BaseModel):
    """A tool available for analysing a decision in a given area."""

    tool: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    skills: list[str] = Field(default_factory=list)


class SelectionReceipt(BaseModel):
    """Traceable record of why a tool was chosen or why clarification is needed."""

    area: str = Field(..., min_length=1)
    decision: str = Field(..., min_length=1)
    tool: str | None = Field(default=None)
    label: str | None = Field(default=None)
    skills: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)
    reason: str = Field(default="")
    missing_minimum: bool = Field(default=False)


class SelectionResult(BaseModel):
    """Structured result returned by the selection engine."""

    action: SelectionAction
    receipt: SelectionReceipt
    output: str = Field(..., min_length=1)
    questions: list[str] = Field(default_factory=list)
