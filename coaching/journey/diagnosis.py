# pyright: strict
"""A saved journey as input for the next diagnosis (E84 S84.2, as E83 S83.5).

The diagnosis contract (``coaching/diagnose``) does not change:

- the owner's chosen decision → one ``DiagnosticEvidence`` with
  ``source_kind="conversation"``, ``answer_status="fact"`` and the local path
  of the journey as ``source_ref`` (never a URL), in the ``strategy`` area;
- every ``supuesto`` (evidence or approximate count) → ``assumptions``;
- every missing count, an unknown loss and the data a "todavía no" waits for
  → ``open_questions``;
- past ``review_by`` → ``stale``, low confidence and an offer to review it.

Lines follow the diagnosis output contract: at most 12 words and 96
characters; a line that does not fit whole stays only in the local file.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from coaching.diagnose.models import DiagnosticEvidence
from coaching.journey import messages
from coaching.journey.decision import SavedJourney, load_saved, option_text
from coaching.journey.interview import STAGE_LABEL
from coaching.journey.view import biggest_loss, spoken
from coaching.research.diagnosis import DiagnosticInputs

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
_MAX_WORDS = 12
_MAX_CHARS = 96
_RATIONALE = (
    "Decisión que el dueño eligió al revisar cómo llega un cliente hasta que le "
    "compra; el detalle está en el archivo local."
)
ONLY_IN_FILE = "Journey: una línea larga está sólo en el archivo local"


def _fits(line: str) -> bool:
    return (
        len(line) <= _MAX_CHARS
        and len(line.split()) <= _MAX_WORDS
        and "/" not in line
        and "://" not in line
    )


def _month(period: str) -> str:
    year, month = period.split("-")
    return f"{_MONTHS[int(month) - 1]} {year}"


def _day(value: date) -> str:
    return f"{value.day} {_MONTHS[value.month - 1]} {value.year}"


def _assumptions(saved: SavedJourney) -> list[str]:
    lines: list[str] = []
    for stage in saved.journey.stages:
        label = STAGE_LABEL[stage.stage]
        lines += [
            f"Supuesto, {label}: {item.text}"
            for item in stage.evidence
            if item.origin == "supuesto"
        ]
        count = stage.count
        if count is not None and (count.origin == "supuesto" or count.upper):
            lines.append(
                f"Supuesto, {label}: {spoken(count)} en {_month(count.period)}"
            )
    return lines


def _open_questions(saved: SavedJourney) -> list[str]:
    lines = [
        f"Falta: cuántos en {STAGE_LABEL[stage.stage]}"
        for stage in saved.journey.stages
        if stage.count is None
    ]
    if biggest_loss(saved.journey) is None:
        lines.append("Falta: dos pasos seguidos contados en el mismo mes")
    chosen = next(
        (o for o in saved.decision.options if o.label == saved.decision.chosen), None
    )
    if chosen is not None and chosen.kind == "esperar" and chosen.by_date:
        when = _day(chosen.by_date)
        lines.append(
            next(
                (
                    line
                    for prefix in (f"Pendiente al {when}:", f"Para {when}:")
                    if _fits(line := f"{prefix} {chosen.missing_data}")
                ),
                f"Pendiente al {when}: {chosen.missing_data}",
            )
        )
    return lines


def _kept(lines: list[str]) -> tuple[list[str], bool]:
    kept = list(dict.fromkeys(line for line in lines if _fits(line)))
    return kept, len(kept) < len(set(lines))


def to_diagnostic_inputs(saved: SavedJourney, as_of: date) -> DiagnosticInputs:
    """The saved journey's decision, supuestos and gaps for the diagnosis."""
    chosen = next(
        (o for o in saved.decision.options if o.label == saved.decision.chosen), None
    )
    if chosen is None:
        raise ValueError("needs_chosen_option")
    stale = as_of > saved.review_by
    value = (
        "Tras revisar cómo llega un cliente hasta que le compra, el dueño "
        f"decidió: {option_text(chosen)}"
    )
    fact = DiagnosticEvidence(
        evidence_id=f"journey.{saved.saved_on.isoformat()}",
        question_id="journey.decision",
        decision="strategy",
        value=value,
        answer_status="fact",
        source_kind="conversation",
        source_ref=saved.reference,
        captured_at=saved.saved_on,
        freshness="stale" if stale else "current",
        confidence="low" if stale else "high",
        rationale=_RATIONALE,
    )
    assumptions, cut_a = _kept(_assumptions(saved))
    questions, cut_q = _kept(_open_questions(saved))
    if cut_a or cut_q:
        questions.append(ONLY_IN_FILE)
    return DiagnosticInputs(
        evidence=[fact],
        assumptions=assumptions,
        open_questions=questions,
        refresh_offers=[messages.ASK_UPDATE] if stale else [],
    )


def load_diagnostic_inputs(base: Path, as_of: date) -> DiagnosticInputs:
    """The saved journey, if any, as input for the next diagnosis."""
    saved = load_saved(base)
    if saved is None or saved.decision.chosen is None:
        return DiagnosticInputs()
    return to_diagnostic_inputs(saved, as_of)
