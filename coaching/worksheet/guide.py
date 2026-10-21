# pyright: strict
"""ToolGuide contract (E87 S87.2): guided steps, sourced tips and a view spec.

Optional: only sheets that carry a ``guide`` key are validated. Sheets that
still use ``metadata.fields`` load as before (``parse_guide`` returns None).

The public-vocabulary rule for tip sources is NOT coded here: writing the
forbidden terms in ``coaching/`` would break that same rule. It lives in a
test under ``tests/`` that reads the terms from the governance file.
"""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
WorksheetId = Annotated[
    str, StringConstraints(pattern=r"^worksheet-[a-z0-9]+(-[a-z0-9]+)*$")
]


class NextSheet(BaseModel):
    """Bridge to the sheet the owner fills next.

    Shape only: the target is not checked against the registry, because some
    targets are written by later stories (S87.4 decision D2).
    """

    model_config = ConfigDict(extra="forbid")

    id: WorksheetId
    title: Text


class GuideStep(BaseModel):
    """One guided step: question, how to fill it, and a real example."""

    model_config = ConfigDict(extra="forbid")

    id: Slug
    question: Text
    how: Text
    example: Text
    next_sheet: NextSheet | None = None


class Guide(BaseModel):
    """Ordered guided steps with unique ids."""

    model_config = ConfigDict(extra="forbid")

    steps: list[GuideStep] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_ids(self) -> Guide:
        ids = [step.id for step in self.steps]
        repeated = sorted({i for i in ids if ids.count(i) > 1})
        if repeated:
            raise ValueError(f"ids de paso repetidos: {', '.join(repeated)}")
        return self


class Tip(BaseModel):
    """A sourced tip; ``step`` None means it applies to the whole sheet."""

    model_config = ConfigDict(extra="forbid")

    text: Text
    source: Text
    step: str | None = None


class AiPrompt(BaseModel):
    """Spanish paraphrase of the sheet's AI prompt (no page numbers)."""

    model_config = ConfigDict(extra="forbid")

    text: Text


class ViewSection(BaseModel):
    """A block of the view, grouping step ids."""

    model_config = ConfigDict(extra="forbid")

    title: Text
    steps: list[str] = Field(min_length=1)


class ViewSpec(BaseModel):
    """How the saved sheet is shown: cards (one column) or canvas (grid)."""

    model_config = ConfigDict(extra="forbid")

    layout: Literal["cards", "canvas"] = "cards"
    sections: list[ViewSection] = Field(default_factory=lambda: list[ViewSection]())


class DerivedSource(BaseModel):
    """Shape only: S87.7 validates it against the registry."""

    model_config = ConfigDict(extra="forbid")

    sheet: Text
    fields: list[str]
    into: Text
    required: bool = True


class ToolGuide(BaseModel):
    """The guided part of a sheet. Receives the whole sheet; ignores the rest."""

    model_config = ConfigDict(extra="ignore")

    guide: Guide
    tips: list[Tip] = Field(min_length=3)
    ai_prompt: AiPrompt | None = None
    view: ViewSpec = Field(default_factory=ViewSpec)
    derived_from: list[DerivedSource] = Field(
        default_factory=lambda: list[DerivedSource]()
    )

    @model_validator(mode="after")
    def _references_exist(self) -> ToolGuide:
        step_ids = [step.id for step in self.guide.steps]
        known = set(step_ids)
        for tip in self.tips:
            if tip.step is not None and tip.step not in known:
                raise ValueError(f"tip con paso inexistente: {tip.step}")
        shown: set[str] = set()
        for section in self.view.sections:
            for step_id in section.steps:
                if step_id not in known:
                    raise ValueError(
                        f"la sección '{section.title}' nombra un paso inexistente: {step_id}"
                    )
                shown.add(step_id)
        if self.view.sections:
            missing = [i for i in step_ids if i not in shown]
            if missing:
                raise ValueError(f"pasos sin sección en la vista: {', '.join(missing)}")
        return self


_INTERNAL_SOURCE = re.compile(r"^work/research/[^#]+#(f\d+)$")


def source_label(source: str) -> str:
    """What the owner reads as a tip's source.

    An internal research anchor (``work/research/...#f1``) stays in the YAML
    as metadata; the owner sees a neutral label without the repo path.
    """
    match = _INTERNAL_SOURCE.match(source)
    if match:
        return f"Investigación ESCALA (nota interna {match.group(1)})"
    return source


def parse_guide(content: dict[str, Any]) -> ToolGuide | None:
    """Validate a sheet's guide; None when the sheet has no ``guide`` key.

    Raises ``pydantic.ValidationError`` when the guide breaks the contract.
    """
    if "guide" not in content:
        return None
    return ToolGuide.model_validate(content)
