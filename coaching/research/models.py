# pyright: strict
"""Typed contract of a business research (E83 S83.1).

Names follow the E71 sketch so no second research taxonomy appears. There is
deliberately no source origin for "what the model remembers": model knowledge
may suggest what to search, never what is true.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Mode = Literal["benchmark", "mercado", "fortalezas-tendencias"]
SearchMode = Literal["web", "sin_busqueda"]
Origin = Literal["web", "dueño", "archivo_empresa"]
ClaimKind = Literal["dato", "supuesto", "inferencia"]
ClaimStatus = Literal["confirmado", "por_confirmar"]
Confidence = Literal["alta", "media", "baja"]
DecisionArea = Literal["cash", "strategy", "people", "execution"]
OptionKind = Literal["decidir", "esperar"]

EXCERPT_MAX = 300
MAX_CLAIMS = 3


def _required(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("empty")
    return stripped


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ResearchFrame(_Strict):
    """The owner's concern turned into a researchable question."""

    concern: str
    question: str
    decision_informed: str
    mode: Mode
    decision_area: DecisionArea = "strategy"
    segment: str | None = None
    geography: str | None = None
    offer_category: str | None = None
    horizon: str | None = None
    queries: list[str] = Field(default_factory=list)
    search_mode: SearchMode = "web"
    confirmed: bool = False

    _check_text = field_validator("concern", "question", "decision_informed")(_required)


class SourceRecord(_Strict):
    """One source actually consulted (a web page opened, or one the owner gave)."""

    source_id: str
    origin: Origin
    title: str
    publisher: str
    url: str | None = None
    published_on: date | None = None
    consulted_on: date
    excerpt: str = Field(max_length=EXCERPT_MAX)

    _check_text = field_validator("source_id", "title", "publisher", "excerpt")(
        _required
    )

    @model_validator(mode="after")
    def _web_needs_url(self) -> Self:
        if self.origin == "web" and not (
            self.url and self.url.startswith(("https://", "http://"))
        ):
            raise ValueError("web_source_needs_url")
        return self


class ResearchClaim(_Strict):
    """One finding. ``status`` and ``confidence`` are always set by the grader."""

    text: str
    kind: ClaimKind
    supporting: list[str] = Field(default_factory=list)
    contrary: list[str] = Field(default_factory=list)
    status: ClaimStatus = "por_confirmar"
    confidence: Confidence = "baja"
    next_source: str | None = None

    _check_text = field_validator("text")(_required)


class DecisionOption(_Strict):
    """One of the 2-3 options the research ends in."""

    label: str
    text: str
    kind: OptionKind = "decidir"
    missing_data: str | None = None
    by_date: date | None = None

    _check_text = field_validator("label", "text")(_required)

    @model_validator(mode="after")
    def _waiting_needs_data_and_date(self) -> Self:
        if self.kind == "esperar" and not (
            self.missing_data and self.missing_data.strip() and self.by_date
        ):
            raise ValueError("waiting_needs_missing_data_and_date")
        return self


class ResearchReport(_Strict):
    """A full research: frame, sources, graded findings and the decision."""

    frame: ResearchFrame
    researched_on: date
    sources: list[SourceRecord] = Field(default_factory=list[SourceRecord])
    claims: list[ResearchClaim] = Field(
        default_factory=list[ResearchClaim], max_length=MAX_CLAIMS
    )
    not_found: list[str] = Field(default_factory=list)
    limits: list[str] = Field(default_factory=list)
    options: list[DecisionOption] = Field(min_length=2, max_length=3)
    recommendation: str
    recommendation_reason: str
    chosen: DecisionOption | None = None
    review_by: date

    _check_text = field_validator("recommendation", "recommendation_reason")(_required)

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if not self.frame.confirmed:
            raise ValueError("frame_not_confirmed")
        ids = [source.source_id for source in self.sources]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate_source_id")
        known = set(ids)
        for claim in self.claims:
            if not set(claim.supporting + claim.contrary) <= known:
                raise ValueError("unknown_source")
        if self.frame.search_mode == "sin_busqueda":
            if any(source.origin == "web" for source in self.sources):
                raise ValueError("web_source_without_search")
            if any(
                claim.status == "por_confirmar" and not claim.next_source
                for claim in self.claims
            ):
                raise ValueError("por_confirmar_needs_next_source")
        labels = [option.label for option in self.options]
        if len(labels) != len(set(labels)):
            raise ValueError("duplicate_option")
        if self.recommendation not in labels:
            raise ValueError("recommendation_not_an_option")
        if self.chosen is not None and self.chosen not in self.options:
            raise ValueError("chosen_not_an_option")
        return self


class PrivateTerms(_Strict):
    """What must never travel in a search: the company, its people, its figures."""

    company_names: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    figures: list[str] = Field(default_factory=list)


class IndexEntry(_Strict):
    """One line of ``.escala/my-company/research/index.yaml`` (no URLs)."""

    reference: str
    mode: Mode
    question: str
    decision_area: DecisionArea
    decision: str
    researched_on: date
    review_by: date
