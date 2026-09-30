# pyright: strict
"""Deterministic rules of a business research (E83 S83.1).

- ``grade_claim``: "confirmado" only with three or more **independent**
  (different publisher) **dated** sources inside the freshness window, and
  only for a ``dato``. Contrary evidence caps confidence at ``media``.
- ``build_queries`` / ``check_queries``: searches are built only from the
  public fields of the confirmed frame, and any search carrying the company's
  name, its people or its figures is rejected (privacy test).
- One freshness window of 90 days for everything (D6): sources older than
  that do not count, and a report is due for review 90 days after research.

The search itself runs in the client agent, outside this module: these rules
prove what is graded, not what the agent typed (design U7).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field

from coaching.research.models import (
    Confidence,
    Mode,
    PrivateTerms,
    ResearchClaim,
    ResearchFrame,
    SourceRecord,
)

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


RejectReason = Literal["empresa", "persona", "cifra"]

# Words too generic to identify a company or a person on their own.
_GENERIC = frozenset(
    "de del la las el los y e en con sa cv sc srl sas sapi rl and the of".split()
)
_NUMBER = re.compile(r"\d[\d.,]*\d|\d")


class RejectedQuery(BaseModel):
    query: str
    reason: RejectReason


class QueryCheck(BaseModel):
    accepted: list[str] = Field(default_factory=list)
    rejected: list[RejectedQuery] = Field(default_factory=list[RejectedQuery])


def _words(text: str) -> list[str]:
    return re.sub(r"[^a-z0-9]+", " ", normalize(text)).split()


def _distinctive(name: str) -> set[str]:
    return {word for word in _words(name) if len(word) >= 3 and word not in _GENERIC}


def _numbers(text: str) -> set[str]:
    return {re.sub(r"[.,]", "", match) for match in _NUMBER.findall(text)}


def _phrase_in(phrase: str, words: list[str]) -> bool:
    wanted = _words(phrase)
    return bool(wanted) and f" {' '.join(wanted)} " in f" {' '.join(words)} "


def _reject_reason(
    query: str, private: PrivateTerms, public_words: set[str]
) -> RejectReason | None:
    words = _words(query)
    present = set(words)
    for company in private.company_names:
        if (
            _phrase_in(company, words)
            or (_distinctive(company) - public_words) & present
        ):
            return "empresa"
    for person in private.people:
        if _phrase_in(person, words) or _distinctive(person) & present:
            return "persona"
    figures = set[str]().union(*(_numbers(figure) for figure in private.figures))
    if figures & _numbers(query):
        return "cifra"
    return None


def check_queries(frame: ResearchFrame, private: PrivateTerms) -> QueryCheck:
    """Split ``frame.queries`` into accepted and rejected (with the reason).

    A word of the company name is allowed only when it is also a word of the
    confirmed offer category or geography (e.g. "tortillería" in "Tortillería
    Zorblax"); the full company name, people's names and private figures never
    are.
    """
    public_words = set(_words(frame.offer_category or "")) | set(
        _words(frame.geography or "")
    )
    result = QueryCheck()
    for query in frame.queries:
        reason = _reject_reason(query, private, public_words)
        if reason is None:
            result.accepted.append(query)
        else:
            result.rejected.append(RejectedQuery(query=query, reason=reason))
    return result


def _join(*parts: str | None) -> str:
    return " ".join(part for part in parts if part)


def build_queries(frame: ResearchFrame) -> list[str]:
    """Two or three searches from the frame's public fields only.

    The owner's concern and question are never used: they are his words and
    may carry names or figures. Without an offer category there is nothing to
    search yet.
    """
    offer = frame.offer_category
    if not offer:
        return []
    where = f"en {frame.geography}" if frame.geography else None
    segment, horizon = frame.segment, frame.horizon
    templates: dict[Mode, list[str]] = {
        "benchmark": [
            _join(f"precios de {offer}", where, horizon),
            _join(offer, segment, where, "paquetes y tarifas"),
            _join(offer, where, "canales de venta"),
        ],
        "mercado": [
            _join(f"demanda de {offer}", where, horizon),
            _join(f"clientes de {offer}", segment, where),
            _join(f"tamaño del mercado de {offer}", where),
        ],
        "fortalezas-tendencias": [
            _join(f"tendencias de {offer}", where, horizon),
            _join(f"qué valoran los clientes de {offer}", segment, where),
            _join(offer, where, "cambios y regulación", horizon),
        ],
    }
    return templates[frame.mode]
