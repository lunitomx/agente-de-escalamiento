# pyright: strict
"""The journey model (E84 S84.2), folding in E71's ``JourneyHypothesis``.

Each ``JourneyStage`` keeps stage, need, touchpoint (dónde pasa), friction,
evidence, confidence, an optional count with its own period and local source,
and an optional experiment. Every piece of evidence says where it comes from:

- ``dueño_dice``: what the owner says;
- ``dato_con_periodo``: a local file, CRM or fact, with its period;
- ``clientes_dijeron``: first hand, and only when the owner says when and how
  many customers he asked;
- ``supuesto``: an approximation or a guess.

E71's rule: without ``clientes_dijeron`` evidence nobody claims customers were
asked. A missing value stays ``None`` (shown as "Falta"); nothing is estimated.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from coaching.journey.interview import OWNER_SOURCE, STAGES, JourneyDraft, Stage

Origin = Literal["dueño_dice", "dato_con_periodo", "clientes_dijeron", "supuesto"]
CountOrigin = Literal["dueño_dice", "dato_con_periodo", "supuesto"]
Confidence = Literal["alta", "media", "baja"]

_PERIOD = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_REMOTE = re.compile(r"https?:|://|\bwww\.", re.IGNORECASE)
FIRST_HAND: frozenset[Origin] = frozenset({"dato_con_periodo", "clientes_dijeron"})


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _local_source(value: str | None) -> str | None:
    if value is not None and (not value.strip() or _REMOTE.search(value)):
        raise ValueError("source_must_be_local")
    return value


def _period(value: str | None) -> str | None:
    if value is not None and not _PERIOD.match(value):
        raise ValueError("period_must_be_yyyy_mm")
    return value


class JourneyEvidence(_Strict):
    """One piece of evidence for a stage, with its origin."""

    origin: Origin
    text: str = Field(min_length=1)
    source: str | None = None
    period: str | None = None
    asked_on: date | None = None
    asked_count: int | None = Field(default=None, ge=1)

    _check_source = field_validator("source")(_local_source)
    _check_period = field_validator("period")(_period)

    @model_validator(mode="after")
    def _origin_needs_its_proof(self) -> Self:
        if self.origin == "dato_con_periodo" and not (self.source and self.period):
            raise ValueError("data_needs_source_and_period")
        if self.origin == "clientes_dijeron" and not (
            self.asked_on and self.asked_count
        ):
            raise ValueError("customers_said_needs_when_and_how_many")
        return self


class StageCount(_Strict):
    """How many customers went through a stage in one period (``AAAA-MM``)."""

    value: int = Field(ge=0)
    upper: int | None = Field(default=None, ge=0)
    period: str
    source: str
    origin: CountOrigin

    _check_source = field_validator("source")(_local_source)
    _check_period = field_validator("period")(_period)


class JourneyStage(_Strict):
    """One stage of how a customer gets to buy (E71's ``JourneyHypothesis``)."""

    stage: Stage
    need: str | None = None
    touchpoint: str | None = None
    friction: str | None = None
    evidence: list[JourneyEvidence] = Field(default_factory=list[JourneyEvidence])
    confidence: Confidence = "baja"
    count: StageCount | None = None
    experiment: str | None = None

    @model_validator(mode="after")
    def _high_needs_first_hand(self) -> Self:
        if self.confidence == "alta" and not any(
            item.origin in FIRST_HAND for item in self.evidence
        ):
            raise ValueError("high_confidence_needs_first_hand_evidence")
        return self


class Journey(_Strict):
    """The five stages, in their fixed order, built on one day."""

    built_on: date
    stages: list[JourneyStage]

    @model_validator(mode="after")
    def _five_fixed_stages(self) -> Self:
        if tuple(item.stage for item in self.stages) != STAGES:
            raise ValueError("journey_needs_the_five_stages_in_order")
        return self


def heard_from_customers(journey: Journey) -> bool:
    """True only when some evidence is first hand from customers."""
    return any(
        item.origin == "clientes_dijeron"
        for stage in journey.stages
        for item in stage.evidence
    )


def from_draft(draft: JourneyDraft, built_on: date) -> Journey:
    """The interview's draft as a journey: everything is what the owner said.

    Approximate counts are ``supuesto``; what he did not know stays missing.
    """
    stages: list[JourneyStage] = []
    for item in draft.stages:
        count = (
            None
            if item.conteo is None
            else StageCount(
                value=item.conteo,
                upper=item.conteo_hasta,
                period=draft.period,
                source=item.fuente_conteo or OWNER_SOURCE,
                origin="supuesto" if item.conteo_supuesto else "dueño_dice",
            )
        )
        evidence = (
            []
            if item.friccion is None
            else [JourneyEvidence(origin="dueño_dice", text=item.friccion)]
        )
        stages.append(
            JourneyStage(
                stage=item.stage,
                touchpoint=item.que_pasa,
                friction=item.friccion,
                evidence=evidence,
                count=count,
            )
        )
    return Journey(built_on=built_on, stages=stages)
