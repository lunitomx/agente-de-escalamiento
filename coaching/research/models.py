# pyright: strict
"""Typed contract of a business research (E83 S83.1).

Names follow the E71 sketch so no second research taxonomy appears. There is
deliberately no source origin for "what the model remembers": model knowledge
may suggest what to search, never what is true.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from coaching.research.messages import LINK_IN_REPORT as URL_PLACEHOLDER

Mode = Literal["benchmark", "mercado", "fortalezas-tendencias"]
SearchMode = Literal["web", "sin_busqueda"]
Origin = Literal["web", "dueño", "archivo_empresa"]
ClaimKind = Literal["dato", "supuesto", "inferencia"]
ClaimStatus = Literal["confirmado", "por_confirmar"]
Confidence = Literal["alta", "media", "baja"]
DecisionArea = Literal["cash", "strategy", "people", "execution"]
OptionKind = Literal["decidir", "esperar"]
Side = Literal["fortaleza", "debilidad", "tendencia"]

Dimension = Literal["precio", "paquetes", "canales", "metricas"]
DIMENSIONS: tuple[Dimension, ...] = ("precio", "paquetes", "canales", "metricas")

EXCERPT_MAX = 300
# One freshness window for everything (D6, owner decision 2026-09-30).
FRESHNESS_DAYS = 90
MAX_CLAIMS = 3
MAX_COMPARABLES = 5


def normalize(text: str) -> str:
    """Lowercase, accents removed, single spaces."""
    ascii_text = (
        unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    )
    return " ".join(ascii_text.lower().split())


_URL = re.compile(
    r"(?:\b(?:https?|file)://|\bwww\.|\b[\w-]+(?:\.[\w-]+)+/)"
    r"\S*?(?=[.,;:!?)\]»\"']*(?:\s|$))",
    re.IGNORECASE,
)


def without_urls(text: str) -> str:
    """Text safe to leave the report: every link replaced (E83 S83.5).

    URLs live only inside the local report; the index and the diagnosis keep
    the report's local path instead.
    """
    return _URL.sub(URL_PLACEHOLDER, text)


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
    competitors: list[str] = Field(default_factory=list)
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
    # Only in ``fortalezas-tendencias`` (S83.4): which side of the SWT it
    # feeds and, for a strength or weakness, the comparables it is against.
    side: Side | None = None
    against: list[str] = Field(default_factory=list)

    _check_text = field_validator("text")(_required)


class BenchmarkCell(_Strict):
    """What one comparable does on one dimension, and where it says so."""

    value: str
    source_id: str | None = None

    _check_text = field_validator("value")(_required)

    @model_validator(mode="after")
    def _never_an_estimate(self) -> Self:
        if not (self.source_id and self.source_id.strip()):
            raise ValueError("cell_without_source")
        return self


class Comparable(_Strict):
    """A business with the same confirmed offer and geography."""

    name: str
    named_by_owner: bool = False
    owner_confirmed: bool = False
    found_in: str | None = None
    why: str | None = None
    cells: dict[Dimension, BenchmarkCell] = Field(
        default_factory=dict[Dimension, BenchmarkCell]
    )

    _check_text = field_validator("name")(_required)

    @property
    def counted(self) -> bool:
        """Only a business the owner named or said yes to enters the table."""
        return self.named_by_owner or self.owner_confirmed

    @model_validator(mode="after")
    def _candidate_is_traceable(self) -> Self:
        if not self.named_by_owner and not (
            self.found_in and self.found_in.strip() and self.why and self.why.strip()
        ):
            raise ValueError("candidate_needs_source_and_reason")
        return self


def check_comparables(
    frame: ResearchFrame, sources: list[SourceRecord], comparables: list[Comparable]
) -> None:
    """Rules a set of comparables must meet against its frame and sources.

    Comparable means same confirmed offer and geography; "named by the owner"
    means named in the frame; published numbers need a page with a link.
    """
    if not comparables:
        return
    if frame.mode not in ("benchmark", "fortalezas-tendencias"):
        raise ValueError("comparables_only_in_benchmark")
    if not (
        frame.offer_category
        and frame.offer_category.strip()
        and frame.geography
        and frame.geography.strip()
    ):
        raise ValueError("comparables_need_offer_and_geography")
    names = [normalize(item.name) for item in comparables]
    if len(names) != len(set(names)):
        raise ValueError("duplicate_comparable")
    named = {normalize(name) for name in frame.competitors}
    by_id = {source.source_id: source for source in sources}
    for item in comparables:
        if item.named_by_owner and normalize(item.name) not in named:
            raise ValueError("not_named_by_owner")
        cited = [cell.source_id for cell in item.cells.values()]
        if item.found_in:
            cited.append(item.found_in)
        if not all(source_id in by_id for source_id in cited):
            raise ValueError("unknown_source")
        metric = item.cells.get("metricas")
        if metric is not None and not by_id[metric.source_id or ""].url:
            raise ValueError("metric_needs_published_source")


SizeKind = Literal["estimado", "no_estimable"]


class SizeFigure(_Strict):
    """What one source says the size is, in the size's unit."""

    value: Decimal = Field(gt=0)
    source_id: str

    _check_text = field_validator("source_id")(_required)


class MarketSize(_Strict):
    """How big the market is: a range with method and assumptions, or "not
    estimable yet" with the data that would allow it (E83 S83.3, rule of E71).

    ``status`` and ``confidence`` are always set by the grader.
    """

    kind: SizeKind
    low: Decimal | None = None
    high: Decimal | None = None
    unit: str | None = None
    method: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    supporting: list[str] = Field(default_factory=list)
    figures: list[SizeFigure] = Field(default_factory=list[SizeFigure])
    missing_data: str | None = None
    next_source: str | None = None
    status: ClaimStatus = "por_confirmar"
    confidence: Confidence = "baja"

    @property
    def source_ids(self) -> list[str]:
        """Every source the size rests on, supporting and per-source figures."""
        return list(
            dict.fromkeys(
                [*self.supporting, *(item.source_id for item in self.figures)]
            )
        )

    @property
    def sources_disagree(self) -> bool:
        return len({item.value for item in self.figures}) > 1

    @model_validator(mode="after")
    def _never_a_lone_number(self) -> Self:
        if self.kind == "no_estimable":
            if not (self.missing_data and self.missing_data.strip()):
                raise ValueError("not_estimable_needs_missing_data")
            if self.low is not None or self.high is not None or self.figures:
                raise ValueError("not_estimable_has_no_number")
            return self
        low, high = self.low, self.high
        if low is None or high is None or not 0 < low < high:
            raise ValueError("size_needs_a_range")
        if not (
            self.unit and self.unit.strip() and self.method and self.method.strip()
        ):
            raise ValueError("size_needs_unit_and_method")
        if not any(item.strip() for item in self.assumptions):
            raise ValueError("size_needs_assumptions")
        if not self.source_ids:
            raise ValueError("size_needs_sources")
        # Sources that disagree are shown side by side, never averaged: the
        # range must hold what each one says.
        if any(not low <= item.value <= high for item in self.figures):
            raise ValueError("size_range_must_cover_every_source")
        return self


def has_segment_and_geography(frame: ResearchFrame) -> bool:
    return bool(
        frame.segment
        and frame.segment.strip()
        and frame.geography
        and frame.geography.strip()
    )


def check_market_size(
    frame: ResearchFrame, known: set[str], size: MarketSize | None
) -> None:
    """Rules a market size must meet against its frame and sources."""
    if frame.mode != "mercado":
        if size is not None:
            raise ValueError("size_only_in_mercado")
        return
    if size is None:
        # Without segment and geography the report builder states "not
        # estimable yet"; with them the size must be stated either way.
        raise ValueError("mercado_needs_size")
    if size.kind == "estimado" and not has_segment_and_geography(frame):
        raise ValueError("size_needs_segment_and_geography")
    if not set(size.source_ids) <= known:
        raise ValueError("unknown_source")
    if (
        frame.search_mode == "sin_busqueda"
        and size.kind == "estimado"
        and size.status == "por_confirmar"
        and not size.next_source
    ):
        raise ValueError("por_confirmar_needs_next_source")


def is_recent(source: SourceRecord, as_of: date) -> bool:
    """Dated, not in the future, and at most ``FRESHNESS_DAYS`` old."""
    published = source.published_on
    return (
        published is not None
        and published <= as_of
        and (as_of - published).days <= FRESHNESS_DAYS
    )


def check_sides(
    frame: ResearchFrame,
    sources: list[SourceRecord],
    comparables: list[Comparable],
    claims: list[ResearchClaim],
    as_of: date,
) -> None:
    """Rules of the outside strengths, weaknesses and trends (E83 S83.4).

    A strength or weakness is a position against businesses the owner named
    or confirmed, never against a candidate; a trend rests on at least one
    source dated within the freshness window.
    """
    if frame.mode != "fortalezas-tendencias":
        if any(claim.side is not None or claim.against for claim in claims):
            raise ValueError("side_only_in_fortalezas_tendencias")
        return
    counted = {normalize(item.name) for item in comparables if item.counted}
    by_id = {source.source_id: source for source in sources}
    for claim in claims:
        if claim.side is None:
            raise ValueError("claim_needs_side")
        if claim.side == "tendencia":
            if claim.against:
                raise ValueError("trend_has_no_comparable")
            if not any(
                source_id in by_id and is_recent(by_id[source_id], as_of)
                for source_id in claim.supporting
            ):
                raise ValueError("trend_needs_recent_source")
            continue
        if not claim.against or not all(
            normalize(name) in counted for name in claim.against
        ):
            raise ValueError("needs_a_confirmed_comparable")


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
    comparables: list[Comparable] = Field(
        default_factory=list[Comparable], max_length=MAX_COMPARABLES
    )
    market_size: MarketSize | None = None
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
        check_comparables(self.frame, self.sources, self.comparables)
        check_sides(
            self.frame, self.sources, self.comparables, self.claims, self.researched_on
        )
        check_market_size(self.frame, known, self.market_size)
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
