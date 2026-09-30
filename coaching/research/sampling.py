# pyright: strict
"""Sample a saved report's web sources and check its quotes (E83 S83.5).

The agent opens each sampled link and hands back the page it got; this module
only says whether the quoted excerpt is on that page. Markup, spacing, case,
accents and punctuation do not count; words and figures do. An excerpt cut
with an ellipsis needs every piece.
"""

from __future__ import annotations

import html
import re
import unicodedata
from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict

from coaching.research.models import ResearchReport, SourceRecord

CheckResult = Literal["aparece", "no_aparece", "sin_revisar"]
SAMPLE_SIZE = 3

_HIDDEN = re.compile(
    r"<(script|style|noscript)\b.*?</\1\s*>", re.IGNORECASE | re.DOTALL
)
_TAG = re.compile(r"<[^>]*>")
_ELLIPSIS = re.compile(r"…|\.\.\.|\[\s*\.\.\.\s*\]")
_WORD = re.compile(r"\w+")


class SourceCheck(BaseModel):
    """One sampled source: does its quoted excerpt appear on the page?"""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    publisher: str
    url: str
    excerpt: str
    result: CheckResult


def _words(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text.casefold())
    plain = "".join(char for char in plain if not unicodedata.combining(char))
    return " ".join(_WORD.findall(plain))


def _page_words(page: str) -> str:
    return _words(html.unescape(_TAG.sub(" ", _HIDDEN.sub(" ", page))))


def excerpt_in_page(excerpt: str, page: str) -> bool:
    """True when every piece of ``excerpt`` is in the visible text of ``page``."""
    pieces = [words for part in _ELLIPSIS.split(excerpt) if (words := _words(part))]
    text = f" {_page_words(page)} "
    return bool(pieces) and all(f" {piece} " in text for piece in pieces)


def pick_sources(
    report: ResearchReport, limit: int = SAMPLE_SIZE
) -> list[SourceRecord]:
    """The first ``limit`` web sources, in the report's order."""
    return [source for source in report.sources if source.origin == "web"][:limit]


def check_sources(
    report: ResearchReport, pages: Mapping[str, str], limit: int = SAMPLE_SIZE
) -> list[SourceCheck]:
    """Sampled sources, each with its result against the page the agent got."""
    checks: list[SourceCheck] = []
    for source in pick_sources(report, limit):
        page = pages.get(source.source_id)
        result: CheckResult = (
            "sin_revisar"
            if page is None
            else "aparece"
            if excerpt_in_page(source.excerpt, page)
            else "no_aparece"
        )
        checks.append(
            SourceCheck(
                source_id=source.source_id,
                publisher=source.publisher,
                url=source.url or "",
                excerpt=source.excerpt,
                result=result,
            )
        )
    return checks
