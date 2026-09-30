# pyright: strict
"""A saved research as input for the next diagnosis (E83 S83.5).

The diagnosis contract (``coaching/diagnose``) does not change; a research
arrives through the fields it already has:

- the owner's confirmed decision → one ``DiagnosticEvidence`` with
  ``source_kind="conversation"``, ``answer_status="fact"`` and the local path
  of the report as ``source_ref`` (never a URL), in the frame's decision area;
- every finding and every counted comparable → one line in ``assumptions``
  with its status and month (outside findings are never facts); the diagnosis
  output contract caps a line at 12 words and 96 characters, so publishers and
  dates of each source stay in the report the fact points to;
- what was not found, and the data a "not yet" waits for → ``open_questions``;
- a report past ``review_by`` → ``freshness="stale"`` and an offer to refresh
  it before using it.

No URL leaves the report: every text goes through ``without_urls``.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from coaching.diagnose.models import DiagnosticEvidence
from coaching.research import messages
from coaching.research.models import (
    DIMENSIONS,
    DecisionArea,
    DecisionOption,
    IndexEntry,
    Mode,
    ResearchReport,
    without_urls,
)
from coaching.research.report import (
    COLUMN_LABELS,
    decision_text,
    load_index,
    load_saved_report,
)

# Room left for the diagnosis's own lines: the primary-constraint request
# takes at most 20 assumptions and 20 open questions, the narrative
# assessment at most 12 open questions.
MAX_ASSUMPTIONS = 10
MAX_OPEN_QUESTIONS = 6

_QUESTION_ID = "research.decision"
_RATIONALE = (
    "Decisión que el dueño confirmó al cerrar una investigación; las fuentes "
    "están en el reporte local."
)
_OPTION_LETTER = re.compile(r"^\s*\w{1,3}\)\s*")
_STATUS_WORD = {"confirmado": "confirmado", "por_confirmar": "por confirmar"}
_KIND_LABEL = {"dato": "Externo", "supuesto": "Supuesto", "inferencia": "Deducción"}
_MONTHS = (
    "ene",
    "feb",
    "mar",
    "abr",
    "may",
    "jun",
    "jul",
    "ago",
    "sep",
    "oct",
    "nov",
    "dic",
)
# The diagnosis's output contract, as ``validators/procedure_contract.py`` has it.
_MAX_WORDS = 12
_MAX_CHARS = 96
_UNSAFE_WORD = re.compile(
    r"\b(source[_ -]?id|source text|verbatim|copyright|all rights reserved|page \d+)\b",
    re.IGNORECASE,
)


class DiagnosticInputs(BaseModel):
    """What the diagnosis receives through the fields it already has."""

    model_config = ConfigDict(extra="forbid")

    evidence: list[DiagnosticEvidence] = Field(default_factory=list[DiagnosticEvidence])
    assumptions: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    refresh_offers: list[str] = Field(default_factory=list)


def _distinct(lines: list[str], limit: int) -> list[str]:
    return list(dict.fromkeys(line for line in lines if line.strip()))[:limit]


def _evidence_id(reference: str) -> str:
    stem = re.sub(r"[^a-z0-9_.-]+", "-", Path(reference).stem.lower()).strip("-.")
    return f"research.{stem or 'report'}"


def _fact(
    *,
    reference: str,
    area: DecisionArea,
    value: str,
    researched_on: date,
    stale: bool,
) -> DiagnosticEvidence:
    return DiagnosticEvidence(
        evidence_id=_evidence_id(reference),
        question_id=_QUESTION_ID,
        decision=area,
        value=without_urls(value),
        answer_status="fact",
        source_kind="conversation",
        source_ref=reference,
        captured_at=researched_on,
        freshness="stale" if stale else "current",
        confidence="low" if stale else "high",
        rationale=_RATIONALE,
    )


def _decision_value(report: ResearchReport, chosen: DecisionOption) -> str:
    value = (
        f"Tras investigar «{report.frame.question}» el "
        f"{messages.spanish_date(report.researched_on)}, el dueño decidió: "
        f"{decision_text(chosen)}."
    )
    if chosen.label == report.recommendation:
        value += f" Razón: {report.recommendation_reason}."
    return value


def _month(value: date) -> str:
    return f"{_MONTHS[value.month - 1]} {value.year}"


def _day(value: date) -> str:
    return f"{value.day} {_MONTHS[value.month - 1]} {value.year}"


def _fit(prefix: str, body: str) -> str:
    """One line the diagnosis's output contract accepts as it is.

    The contract (``validators/procedure_contract.py``) takes at most 12 words
    and 96 characters per line, without slashes, backslashes, URLs or source
    locators; what does not fit stays in the report, which the fact points to.
    """
    clean = _UNSAFE_WORD.sub(
        "", without_urls(body).replace("/", "-").replace("\\", "-")
    )
    words = "".join(char if char.isprintable() else " " for char in clean).split()
    head = prefix.split()
    kept = words[: _MAX_WORDS - len(head)]
    while True:
        cut = "…" if len(kept) < len(words) else ""
        line = " ".join([*head, *kept]) + cut
        if len(line) <= _MAX_CHARS or not kept:
            return line[:_MAX_CHARS].rstrip()
        kept = kept[:-1]


def _assumptions(report: ResearchReport, stale: bool) -> list[str]:
    mark = messages.STALE_MARK.strip() if stale else ""
    when = _month(report.researched_on)
    lines: list[str] = []
    for claim in report.claims:
        prefix = (
            f"{mark} {_KIND_LABEL[claim.kind]} {_STATUS_WORD[claim.status]}, {when}:"
        )
        lines.append(_fit(prefix, claim.text))
    for item in report.comparables:
        if not item.counted or not item.cells:
            continue
        cells = ", ".join(
            f"{COLUMN_LABELS[dimension].lower()} {cell.value}"
            for dimension in DIMENSIONS
            if (cell := item.cells.get(dimension)) is not None
        )
        lines.append(_fit(f"{mark} Por confirmar, {when}:", f"{item.name}, {cells}"))
    return lines


def _open_questions(report: ResearchReport) -> list[str]:
    when = _month(report.researched_on)
    lines = [_fit(f"Falta, investigación {when}:", item) for item in report.not_found]
    lines += [
        _fit(f"En duda, hay fuentes en contra, {when}:", claim.text)
        for claim in report.claims
        if claim.contrary
    ]
    if any(
        dimension not in item.cells
        for item in report.comparables
        if item.counted
        for dimension in DIMENSIONS
    ):
        lines.append(f"Comparables con datos «no encontrado», {when}")
    chosen = report.chosen
    if chosen is not None and chosen.kind == "esperar" and chosen.by_date:
        lines.append(
            _fit(f"Pendiente al {_day(chosen.by_date)}:", chosen.missing_data or "")
        )
    return lines


def to_diagnostic_inputs(
    report: ResearchReport, reference: str, as_of: date
) -> DiagnosticInputs:
    """One saved research as diagnosis input; ``reference`` is its local path."""
    chosen = report.chosen
    if chosen is None:
        raise ValueError("needs_chosen_option")
    stale = as_of > report.review_by
    return DiagnosticInputs(
        evidence=[
            _fact(
                reference=reference,
                area=report.frame.decision_area,
                value=_decision_value(report, chosen),
                researched_on=report.researched_on,
                stale=stale,
            )
        ],
        assumptions=_distinct(_assumptions(report, stale), MAX_ASSUMPTIONS),
        open_questions=_distinct(_open_questions(report), MAX_OPEN_QUESTIONS),
        refresh_offers=(
            [
                messages.stale_offer(
                    without_urls(report.frame.question),
                    report.researched_on,
                    report.review_by,
                )
            ]
            if stale
            else []
        ),
    )


def _from_index(entry: IndexEntry, as_of: date) -> DiagnosticInputs:
    """The decision alone, when the structured report cannot be read."""
    stale = as_of > entry.review_by
    value = (
        f"Tras investigar «{entry.question}» el "
        f"{messages.spanish_date(entry.researched_on)}, el dueño decidió: "
        f"{_OPTION_LETTER.sub('', entry.decision)}."
    )
    return DiagnosticInputs(
        evidence=[
            _fact(
                reference=entry.reference,
                area=entry.decision_area,
                value=value,
                researched_on=entry.researched_on,
                stale=stale,
            )
        ],
        open_questions=[
            f"Investigación {_month(entry.researched_on)}: {messages.DETAIL_UNREADABLE}"
        ],
        refresh_offers=(
            [
                messages.stale_offer(
                    without_urls(entry.question), entry.researched_on, entry.review_by
                )
            ]
            if stale
            else []
        ),
    )


def _latest_per_topic(entries: list[IndexEntry]) -> list[IndexEntry]:
    """Newest first; a newer research on the same mode and area replaces older."""
    latest: dict[tuple[Mode, DecisionArea], IndexEntry] = {}
    ordered = sorted(
        enumerate(entries),
        key=lambda pair: (pair[1].researched_on, pair[0]),
        reverse=True,
    )
    for _, entry in ordered:
        latest.setdefault((entry.mode, entry.decision_area), entry)
    return list(latest.values())


def load_diagnostic_inputs(base: Path, as_of: date) -> DiagnosticInputs:
    """Every saved research that still stands, as input for the next diagnosis."""
    parts: list[DiagnosticInputs] = []
    for entry in _latest_per_topic(load_index(base)):
        report = load_saved_report(base, entry)
        parts.append(
            _from_index(entry, as_of)
            if report is None or report.chosen is None
            else to_diagnostic_inputs(report, entry.reference, as_of)
        )
    return DiagnosticInputs(
        evidence=[item for part in parts for item in part.evidence],
        assumptions=_distinct(
            [line for part in parts for line in part.assumptions], MAX_ASSUMPTIONS
        ),
        open_questions=_distinct(
            [line for part in parts for line in part.open_questions],
            MAX_OPEN_QUESTIONS,
        ),
        refresh_offers=[line for part in parts for line in part.refresh_offers],
    )
