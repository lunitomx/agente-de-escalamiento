"""Fail-closed entity resolution for multi-source onboarding."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Literal, Sequence

from pydantic import BaseModel, Field

ResolutionStatus = Literal["resolved", "ambiguous", "unresolved"]


class EntityCandidate(BaseModel):
    candidate_id: str = Field(..., min_length=1)
    entity_type: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    primary_id: str | None = None
    source: str = Field(..., min_length=1)


class EntityResolution(BaseModel):
    status: ResolutionStatus
    candidate_ids: tuple[str, str]
    reason: str


def resolve_entities(candidates: Sequence[EntityCandidate]) -> list[EntityResolution]:
    """Resolve only exact identities; leave every weak match explicitly open."""
    grouped: dict[tuple[str, str], list[EntityCandidate]] = defaultdict(list)
    for candidate in candidates:
        key = (candidate.entity_type, candidate.primary_id or "")
        grouped[key].append(candidate)

    results: list[EntityResolution] = []
    for (entity_type, primary_id), group in grouped.items():
        if primary_id:
            for left, right in combinations(group, 2):
                if left.name.casefold().strip() == right.name.casefold().strip():
                    results.append(
                        EntityResolution(
                            status="resolved",
                            candidate_ids=(left.candidate_id, right.candidate_id),
                            reason=(
                                f"{entity_type} comparte identificador primario y "
                                "nombre exacto normalizado."
                            ),
                        )
                    )
                else:
                    results.append(
                        EntityResolution(
                            status="ambiguous",
                            candidate_ids=(left.candidate_id, right.candidate_id),
                            reason=(
                                f"{entity_type} comparte identificador primario pero "
                                "el nombre difiere; no se fusiona automáticamente."
                            ),
                        )
                    )

    without_primary: dict[tuple[str, str], list[EntityCandidate]] = defaultdict(list)
    for candidate in candidates:
        if candidate.primary_id is None:
            without_primary[
                (candidate.entity_type, candidate.name.casefold().strip())
            ].append(candidate)
    for (entity_type, _), group in without_primary.items():
        for left, right in combinations(group, 2):
            results.append(
                EntityResolution(
                    status="unresolved",
                    candidate_ids=(left.candidate_id, right.candidate_id),
                    reason=(
                        f"{entity_type} coincide por nombre pero no tiene identificador "
                        "primario; requiere confirmación humana."
                    ),
                )
            )
    return results
