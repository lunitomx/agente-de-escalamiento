"""Source-manifest bound checks for E59 foundational candidate review."""

from __future__ import annotations

import re

from validators.ontology_v2 import CandidateNode, EvidenceRef, ReviewQueue
from validators.source_manifest import SourceManifest


class FoundationsFidelityError(ValueError):
    """Raised without disclosing private source text."""


_WHITESPACE = re.compile(r"\s+")


def _evidence_units(evidence: list[EvidenceRef]) -> set[tuple[str, str]]:
    return {
        (entry.source_id, unit_id) for entry in evidence for unit_id in entry.unit_ids
    }


def _normalized_working_text(value: str) -> str:
    return _WHITESPACE.sub(" ", value).strip().casefold()


def validate_foundation_candidates_against_manifest(
    candidates: list[CandidateNode], manifest: SourceManifest
) -> None:
    """Validate candidate evidence and locators against an authenticated manifest."""

    known_units = {unit.unit_id for unit in manifest.units}
    seen_text: set[str] = set()
    for candidate in candidates:
        text = _normalized_working_text(candidate.working_text)
        if len(text.split()) < 4:
            raise FoundationsFidelityError("candidate working text is not semantic")
        if text in seen_text:
            raise FoundationsFidelityError("candidate working text must be distinct")
        seen_text.add(text)

        evidence_units = _evidence_units(candidate.proposed_node.evidence)
        if not evidence_units:
            raise FoundationsFidelityError("candidate has no evidence")
        if any(source_id != manifest.source_id for source_id, _ in evidence_units):
            raise FoundationsFidelityError(
                "candidate evidence source differs from manifest"
            )
        if {unit_id for _, unit_id in evidence_units} != set(candidate.locators):
            raise FoundationsFidelityError("candidate locator and evidence mismatch")
        if not set(candidate.locators).issubset(known_units):
            raise FoundationsFidelityError("candidate locator is absent from manifest")


def validate_foundations_review_queue(
    queue: ReviewQueue, manifest: SourceManifest
) -> None:
    """Bind an E59 queue to one private structural manifest."""

    # model_copy(update=...) bypasses Pydantic validation. Re-validate at the
    # boundary so callers cannot pass an unsafe in-memory queue to this gate.
    queue = ReviewQueue.model_validate(queue.model_dump(mode="json"))
    validate_foundation_candidates_against_manifest(queue.candidates, manifest)
    candidates = {candidate.candidate_id: candidate for candidate in queue.candidates}
    for decision in queue.decisions:
        candidate = candidates[decision.candidate_id]
        if _evidence_units(decision.evidence) != _evidence_units(
            candidate.proposed_node.evidence
        ):
            raise FoundationsFidelityError(
                "review decision evidence differs from candidate"
            )
