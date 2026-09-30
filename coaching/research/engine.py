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
from decimal import Decimal
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


RejectReason = Literal["empresa", "persona", "cifra", "caracteres"]

# Words too generic to identify a company or a person on their own.
_GENERIC = frozenset(
    "de del la las el los y e en con sa cv sc srl sas sapi rl and the of".split()
)
# Digit groups joined by spaces, dots, commas or apostrophes ("1 200 000",
# "1.200.000", "1'200,000"), and amounts written with a scale ("1.2 millones").
_GROUPS = re.compile(r"\d+(?:[ .,'’]\d+)*")
_SEPARATOR = re.compile(r"[ .,'’]")
_SCALED = re.compile(r"(\d+)(?:[.,](\d+))?\s?(millones|millon|mdp|mil|k|m)(?![a-z0-9])")
_SCALE = {
    "mil": 1_000,
    "k": 1_000,
    "millones": 1_000_000,
    "millon": 1_000_000,
    "mdp": 1_000_000,
    "m": 1_000_000,
}


class RejectedQuery(BaseModel):
    query: str
    reason: RejectReason


class QueryCheck(BaseModel):
    accepted: list[str] = Field(default_factory=list)
    rejected: list[RejectedQuery] = Field(default_factory=list[RejectedQuery])


def sanitize_query(query: str) -> str:
    """The exact text that is checked and, if accepted, searched.

    NFKC folds fullwidth and other compatibility forms; every whitespace
    becomes one space; invisible, control, private-use and unassigned
    characters (Unicode category C*) are dropped.
    """
    kept: list[str] = []
    for char in unicodedata.normalize("NFKC", query):
        if char.isspace():
            kept.append(" ")
        elif not unicodedata.category(char).startswith("C"):
            kept.append(char)
    return " ".join("".join(kept).split())


def _folds_to_ascii(char: str) -> bool:
    base = "".join(
        part
        for part in unicodedata.normalize("NFKD", char)
        if not unicodedata.combining(part)
    )
    return base.isascii()


def _foreign_characters(query: str) -> bool:
    """Letters or digits that do not fold to plain ASCII (e.g. a Cyrillic "о").

    Spanish accents and "ñ" fold; look-alikes from other scripts do not, so
    they could hide a name from the check while the search engine reads it.
    """
    return any(char.isalnum() and not _folds_to_ascii(char) for char in query)


def _words(text: str) -> list[str]:
    return re.sub(r"[^a-z0-9]+", " ", normalize(text)).split()


def _merge_letters(words: list[str]) -> list[str]:
    """Runs of single characters as one word ("z o r b l a x" -> "zorblax")."""
    merged: list[str] = []
    run: list[str] = []
    for word in [*words, ""]:
        if len(word) == 1:
            run.append(word)
            continue
        if len(run) > 1:
            merged.append("".join(run))
        run = []
        if word:
            merged.append(word)
    return merged


def _word_views(text: str) -> list[list[str]]:
    """The query read three ways: split on punctuation, glued across it
    ("zor-blax" -> "zorblax"), and with spelled-out letters merged."""
    split = _words(text)
    glued = [
        word
        for word in (
            re.sub(r"[^a-z0-9]", "", chunk) for chunk in normalize(text).split()
        )
        if word
    ]
    return [split, glued, _merge_letters(split)]


def _distinctive(name: str) -> set[str]:
    return {word for word in _words(name) if len(word) >= 3 and word not in _GENERIC}


def _phrase_in(phrase: str, words: list[str]) -> bool:
    wanted = _words(phrase)
    return bool(wanted) and f" {' '.join(wanted)} " in f" {' '.join(words)} "


def _name_in(name: str, views: list[list[str]], allowed: set[str]) -> bool:
    wanted = _distinctive(name) - allowed
    return any(_phrase_in(name, words) or wanted & set(words) for words in views)


# An amount is (value, precision): "1.2 millones" is 1 200 000 give or take
# 100 000; a plain number is exact (precision 1).
_Amount = tuple[Decimal, Decimal]


def _scaled(text: str) -> tuple[list[_Amount], list[tuple[int, int]]]:
    amounts: list[_Amount] = []
    spans: list[tuple[int, int]] = []
    for match in _SCALED.finditer(text):
        whole, fraction, unit = match.group(1), match.group(2), match.group(3)
        scale = Decimal(_SCALE[unit])
        digits = fraction or ""
        amounts.append(
            (Decimal(f"{whole}.{digits or 0}") * scale, scale / 10 ** len(digits))
        )
        if len(digits) == 3:  # "1.200 millones" may mean 1 200 millions
            amounts.append((Decimal(whole + digits) * scale, scale))
        spans.append(match.span())
    return amounts, spans


def _outside(span: tuple[int, int], taken: list[tuple[int, int]]) -> bool:
    return all(span[1] <= start or span[0] >= end for start, end in taken)


def _private_amounts(figure: str) -> list[_Amount]:
    """A private figure as whole amounts: every group joined, or scaled."""
    text = normalize(sanitize_query(figure))
    amounts, spans = _scaled(text)
    for match in _GROUPS.finditer(text):
        if _outside(match.span(), spans):
            amounts.append((Decimal(_SEPARATOR.sub("", match.group())), Decimal(1)))
    return [amount for amount in amounts if amount[0] > 0]


def _query_amounts(query: str) -> list[_Amount]:
    """Every number a search could carry, including neighbour groups joined
    ("tortillas 2026 4321" carries 2026, 4321 and 20264321)."""
    text = normalize(query)
    amounts, _ = _scaled(text)
    for match in _GROUPS.finditer(text):
        groups = _SEPARATOR.split(match.group())
        for first in range(len(groups)):
            for last in range(first + 1, len(groups) + 1):
                amounts.append((Decimal("".join(groups[first:last])), Decimal(1)))
    return amounts


def _same_amount(one: _Amount, other: _Amount) -> bool:
    return abs(one[0] - other[0]) < max(one[1], other[1])


def _reject_reason(
    query: str, private: PrivateTerms, public_words: set[str]
) -> RejectReason | None:
    if _foreign_characters(query):
        return "caracteres"
    views = _word_views(query)
    if any(_name_in(company, views, public_words) for company in private.company_names):
        return "empresa"
    if any(_name_in(person, views, set()) for person in private.people):
        return "persona"
    figures = [
        amount for figure in private.figures for amount in _private_amounts(figure)
    ]
    carried = _query_amounts(query)
    if any(_same_amount(one, other) for one in figures for other in carried):
        return "cifra"
    return None


def check_queries(frame: ResearchFrame, private: PrivateTerms) -> QueryCheck:
    """Split ``frame.queries`` into accepted and rejected (with the reason).

    Each query is first sanitized (``sanitize_query``); the check runs on that
    text and the accepted list holds exactly that text, so what is checked is
    what is searched. A word of the company name is allowed only when it is
    also a word of the confirmed offer category or geography (e.g.
    "tortillería" in "Tortillería Zorblax"); the full company name, people's
    names, private figures (however grouped or scaled) and look-alike letters
    from other scripts never are.
    """
    public_words = set(_words(frame.offer_category or "")) | set(
        _words(frame.geography or "")
    )
    result = QueryCheck()
    for raw in frame.queries:
        query = sanitize_query(raw)
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
