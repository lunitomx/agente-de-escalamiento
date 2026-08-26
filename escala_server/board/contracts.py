"""Strict serializable contracts for the synthetic board lens."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

Category = Literal["people", "strategy", "execution", "cash"]
Kind = Literal["source_summary", "company_observation", "inference"]
CATEGORIES = {"people", "strategy", "execution", "cash"}
SCHEMA_VERSION = "board-response-v1"
PROFILE_VERSION = "verne-lens-v1"


@dataclass(frozen=True)
class CompanyFact:
    id: str
    text: str
    category: Category

    def __post_init__(self) -> None:
        if not self.id or not self.text or self.category not in CATEGORIES:
            raise ValueError("invalid company fact")


@dataclass(frozen=True)
class EvidenceRef:
    id: str
    entity_name: str
    entity_type: str
    description: str
    line_refs: tuple[int, ...]
    chapter_ids: tuple[int, ...]
    retrieved_by: str

    def __post_init__(self) -> None:
        if not self.id or not self.entity_name or not self.line_refs:
            raise ValueError("evidence requires identity, name, and line references")


@dataclass(frozen=True)
class AdviceItem:
    text: str
    kind: Kind
    company_fact_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    confidence: Literal["low", "medium", "high"] = "low"

    def __post_init__(self) -> None:
        if not self.text or self.kind not in {"source_summary", "company_observation", "inference"}:
            raise ValueError("invalid advice item")
        if self.kind == "source_summary" and not self.evidence_ids:
            raise ValueError("source summary requires evidence")
        if self.kind == "company_observation" and not self.company_fact_ids:
            raise ValueError("company observation requires a company fact")
        if self.kind == "inference" and not (self.company_fact_ids or self.evidence_ids):
            raise ValueError("inference requires a fact or evidence")


@dataclass(frozen=True)
class EvidencePacket:
    schema_version: str
    category: Category
    company_facts: tuple[CompanyFact, ...] = ()
    source_evidence: tuple[EvidenceRef, ...] = ()
    gaps: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    profile_version: str = PROFILE_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != "evidence-packet-v1" or self.category not in CATEGORIES:
            raise ValueError("invalid evidence packet")


@dataclass(frozen=True)
class BoardResponse:
    schema_version: str
    mode: Literal["daily_review", "decision_consult"]
    disclosure: str
    summary: str
    observations: tuple[AdviceItem, ...] = ()
    questions: tuple[str, ...] = ()
    recommended_actions: tuple[AdviceItem, ...] = ()
    limitations: tuple[str, ...] = ()
    evidence: tuple[EvidenceRef, ...] = ()
    profile_version: str = PROFILE_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("invalid board response schema")
        if self.mode not in {"daily_review", "decision_consult"}:
            raise ValueError("invalid board response mode")
        if not self.disclosure:
            raise ValueError("board disclosure is required")
        if len(self.observations) > 3 or len(self.recommended_actions) > 3:
            raise ValueError("board response is limited to three recommendations")
        known_facts = {item for advice in self.observations + self.recommended_actions for item in advice.company_fact_ids}
        known_evidence = {item.id for item in self.evidence}
        for advice in self.observations + self.recommended_actions:
            if advice.kind == "source_summary" and not set(advice.evidence_ids) <= known_evidence:
                raise ValueError("source summary references unavailable evidence")
            if advice.evidence_ids and not set(advice.evidence_ids) <= known_evidence:
                raise ValueError("advice references unavailable evidence")
            if advice.company_fact_ids and not set(advice.company_fact_ids) <= known_facts:
                raise ValueError("advice references unavailable facts")

    def to_dict(self) -> dict:
        return asdict(self)
