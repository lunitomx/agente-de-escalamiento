# pyright: strict
"""Deterministic rules of a business research (E83 S83.1).

- ``grade_claim``: "confirmado" only with three or more **independent**
  (different publisher) **dated** sources inside the freshness window, and
  only for a ``dato``. Contrary evidence caps confidence at ``media``.
- One freshness window of 90 days for everything (D6): sources older than
  that do not count, and a report is due for review 90 days after research.

The search itself runs in the client agent, outside this module: these rules
prove what is graded, not what the agent typed (design U7).
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from datetime import date, timedelta

from coaching.research.models import Confidence, ResearchClaim, SourceRecord

FRESHNESS_DAYS = 90
CONFIRMING_SOURCES = 3


def normalize(text: str) -> str:
    """Lowercase, accents removed, single spaces."""
    ascii_text = (
        unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    )
    return " ".join(ascii_text.lower().split())


def review_date(researched_on: date) -> date:
    return researched_on + timedelta(days=FRESHNESS_DAYS)


def _counts(source: SourceRecord, as_of: date) -> bool:
    published = source.published_on
    return (
        published is not None
        and published <= as_of
        and (as_of - published).days <= FRESHNESS_DAYS
    )


def independent_dated_sources(
    ids: list[str], sources: Mapping[str, SourceRecord], as_of: date
) -> int:
    """How many distinct publishers back ``ids`` with a fresh date."""
    publishers = {
        normalize(sources[source_id].publisher)
        for source_id in ids
        if source_id in sources and _counts(sources[source_id], as_of)
    }
    return len(publishers)


def grade_claim(
    claim: ResearchClaim, sources: Mapping[str, SourceRecord], as_of: date
) -> ResearchClaim:
    """Grade a claim from its sources; any status the agent set is ignored."""
    count = independent_dated_sources(claim.supporting, sources, as_of)
    confirmed = claim.kind == "dato" and count >= CONFIRMING_SOURCES
    confidence: Confidence
    if confirmed:
        confidence = "media" if claim.contrary else "alta"
    elif count >= CONFIRMING_SOURCES - 1:
        confidence = "media"
    else:
        confidence = "baja"
    return claim.model_copy(
        update={
            "status": "confirmado" if confirmed else "por_confirmar",
            "confidence": confidence,
        }
    )
