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
    Comparable,
    ResearchClaim,
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
# Long and short labels: a line first drops words from its prefix, never from
# the finding.
_STATUS = {
    "confirmado": ("confirmado", "conf."),
    "por_confirmar": ("por confirmar", "pend."),
}
_KIND = {
    "dato": ("Externo", "Ext."),
    "supuesto": ("Supuesto", "Sup."),
    "inferencia": ("Deducción", "Ded."),
}
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


def _short_month(value: date) -> str:
    return f"{_MONTHS[value.month - 1]}{value.year % 100:02d}"


def _line(prefixes: list[str], body: str) -> str | None:
    """The first ``prefix + body`` the diagnosis's output contract accepts.

    The contract (``validators/procedure_contract.py``) takes at most 12 words
    and 96 characters per line, without slashes, backslashes, URLs, control
    characters or source locators. Only the prefix gets shorter; the body is
    never cut. ``None`` when not even the shortest prefix fits.
    """
    body = " ".join(without_urls(body).split())
    if (
        not body
        or any(not char.isprintable() for char in body)
        or any(mark in body for mark in ("/", "\\", "://"))
        or body.lower().startswith("www.")
        or _UNSAFE_WORD.search(body)
    ):
        return None
    for prefix in prefixes:
        line = f"{prefix} {body}".strip()
        if len(line) <= _MAX_CHARS and len(line.split()) <= _MAX_WORDS:
            return line
    return None


def _finding_prefixes(kind: str, status: str, when: date, stale: bool) -> list[str]:
    long_kind, short_kind = _KIND[kind]
    long_status, short_status = _STATUS[status]
    if stale:
        mark = messages.STALE_MARK.strip()
        return [
            f"{mark} {long_kind} {long_status}, {_month(when)}:",
            f"{mark} {short_kind} {short_status}:",
            f"{mark} {short_kind}:",
        ]
    return [
        f"{long_kind} {long_status}, {_month(when)}:",
        f"{short_kind} {short_status} {_short_month(when)}:",
        f"{short_kind} {short_status}:",
    ]


def _comparable_prefixes(when: date, stale: bool) -> list[str]:
    mark = f"{messages.STALE_MARK.strip()} " if stale else ""
    return [
        f"{mark}Comparable por confirmar, {_month(when)}:",
        f"{mark}Comp. pend. {_short_month(when)}:",
        f"{mark}Comp.:",
    ]


def _cell_body(name: str, dimension: str, value: str) -> str:
    return f"{name}, {COLUMN_LABELS[dimension].lower()}: {value}"


def _gap_prefixes(when: date) -> list[str]:
    return [
        f"Falta, investigación {_month(when)}:",
        f"Falta {_short_month(when)}:",
        "Falta:",
    ]


def _doubt_prefixes(when: date) -> list[str]:
    return [f"En duda, hay fuentes en contra, {_month(when)}:", "En duda:"]


def _wait_prefixes(by_date: date) -> list[str]:
    return [f"Pendiente al {_day(by_date)}:", f"Para {_day(by_date)}:"]


def _only_in_report(when: date) -> str:
    return f"Investigación {_month(when)}: un hallazgo largo está sólo en el reporte"


def misfits(
    *,
    claims: list[ResearchClaim],
    comparables: list[Comparable],
    not_found: list[str],
    options: list[DecisionOption],
    as_of: date,
) -> list[str]:
    """Texts that would not fit the diagnosis whole, even stale (checked on save)."""
    bad = [
        claim.text
        for claim in claims
        if _line(
            _finding_prefixes(claim.kind, "por_confirmar", as_of, True)[-1:], claim.text
        )
        is None
    ]
    bad += [
        cell.value
        for item in comparables
        for dimension, cell in item.cells.items()
        if _line(
            _comparable_prefixes(as_of, True)[-1:],
            _cell_body(item.name, dimension, cell.value),
        )
        is None
    ]
    bad += [
        item for item in not_found if _line(_gap_prefixes(as_of)[-1:], item) is None
    ]
    bad += [
        option.missing_data
        for option in options
        if option.kind == "esperar"
        and option.missing_data
        and option.by_date
        and _line(_wait_prefixes(option.by_date)[-1:], option.missing_data) is None
    ]
    return list(dict.fromkeys(bad))


def _assumptions(report: ResearchReport, stale: bool) -> tuple[list[str], bool]:
    """Lines, and whether some text was left out because it did not fit whole."""
    when = report.researched_on
    lines: list[str | None] = [
        _line(_finding_prefixes(claim.kind, claim.status, when, stale), claim.text)
        for claim in report.claims
    ]
    lines += [
        _line(
            _comparable_prefixes(when, stale),
            _cell_body(item.name, dimension, cell.value),
        )
        for item in report.comparables
        if item.counted
        for dimension in DIMENSIONS
        if (cell := item.cells.get(dimension)) is not None
    ]
    kept = [line for line in lines if line is not None]
    return kept, len(kept) < len(lines)


def _open_questions(report: ResearchReport, left_out: bool) -> list[str]:
    when = report.researched_on
    lines: list[str | None] = [
        _line(_gap_prefixes(when), item) for item in report.not_found
    ]
    lines += [
        _line(_doubt_prefixes(when), claim.text)
        for claim in report.claims
        if claim.contrary
    ]
    if any(
        dimension not in item.cells
        for item in report.comparables
        if item.counted
        for dimension in DIMENSIONS
    ):
        lines.append(f"Comparables con datos «no encontrado», {_month(when)}")
    chosen = report.chosen
    if chosen is not None and chosen.kind == "esperar" and chosen.by_date:
        lines.append(_line(_wait_prefixes(chosen.by_date), chosen.missing_data or ""))
    kept = [line for line in lines if line is not None]
    if left_out or len(kept) < len(lines):
        kept.append(_only_in_report(when))
    return kept


def to_diagnostic_inputs(
    report: ResearchReport, reference: str, as_of: date
) -> DiagnosticInputs:
    """One saved research as diagnosis input; ``reference`` is its local path."""
    chosen = report.chosen
    if chosen is None:
        raise ValueError("needs_chosen_option")
    stale = as_of > report.review_by
    assumptions, left_out = _assumptions(report, stale)
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
        assumptions=_distinct(assumptions, MAX_ASSUMPTIONS),
        open_questions=_distinct(_open_questions(report, left_out), MAX_OPEN_QUESTIONS),
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
