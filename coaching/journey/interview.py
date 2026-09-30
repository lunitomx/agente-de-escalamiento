# pyright: strict
"""The journey interview (E84 S84.1): 5 fixed stages, one question per message.

Stateless: the procedure passes every answer so far and gets back the next
question plus the draft built from those answers. "No sé" is a valid answer
and leaves the field missing; a count is taken only as a plain number (never
"unos 100") and refers to last month. The draft is never saved here: the
decision and saving belong to S84.2.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from coaching.journey.triggers import normalize

Stage = Literal["se_entera", "pregunta", "compra", "recibe", "regresa"]
StageField = Literal[
    "necesidad", "donde", "friccion", "como_lo_sabe", "conteo", "fuente_conteo"
]
STAGES: tuple[Stage, ...] = ("se_entera", "pregunta", "compra", "recibe", "regresa")
FIELDS: tuple[StageField, ...] = (
    "necesidad",
    "donde",
    "friccion",
    "como_lo_sabe",
    "conteo",
    "fuente_conteo",
)

STAGE_LABEL: dict[Stage, str] = {
    "se_entera": "Se entera de ti",
    "pregunta": "Te pregunta",
    "compra": "Te compra",
    "recibe": "Recibe lo que compró",
    "regresa": "Regresa a comprar",
}
_STAGE_MOMENT: dict[Stage, str] = {
    "se_entera": "cuando se entera de ti",
    "pregunta": "cuando te pregunta",
    "compra": "cuando te compra",
    "recibe": "cuando recibe lo que compró",
    "regresa": "cuando regresa a comprarte",
}
_MISSING_LABEL: dict[StageField, str] = {
    "necesidad": "qué necesita",
    "donde": "dónde pasa",
    "friccion": "qué lo frena",
    "como_lo_sabe": "cómo lo sabes",
    "conteo": "cuántos en {period}",
    "fuente_conteo": "de dónde sale el número",
}
_MONTHS = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)
_DONT_KNOW = frozenset(
    {"", "no se", "nose", "no lo se", "ni idea", "no tengo idea", "no sabria"}
)
_COUNT = re.compile(r"\d+|\d{1,3}(?:[.,]\d{3})+")

INTRO = "Si algo no lo sabes, dime «no sé» y seguimos."
COUNT_RETRY = "Necesito sólo el número, por ejemplo 120. Si no lo tienes, dime «no sé»."
DONE = (
    "Listo, ya tengo los 5 pasos. Esto todavía no se guarda: primero lo revisamos "
    "juntos."
)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Answer(_Strict):
    """What the owner said for one field of one stage (his words, as said)."""

    stage: Stage
    field: StageField
    answer: str


class StageDraft(_Strict):
    """One stage as the owner told it; ``None`` means missing, never estimated."""

    stage: Stage
    necesidad: str | None = None
    donde: str | None = None
    friccion: str | None = None
    como_lo_sabe: str | None = None
    conteo: int | None = Field(default=None, ge=0)
    fuente_conteo: str | None = None


class JourneyDraft(_Strict):
    """The interview's output. Not saved: ``saved`` is always ``False``."""

    period: str
    period_label: str
    stages: list[StageDraft] = Field(default_factory=list[StageDraft])
    missing: list[str] = Field(default_factory=list[str])
    saved: Literal[False] = False


class InterviewStep(_Strict):
    """The next single question (or the end) plus the draft so far."""

    done: bool
    stage: Stage | None = None
    field: StageField | None = None
    retry: bool = False
    message: str
    draft: JourneyDraft


def is_dont_know(answer: str) -> bool:
    """ "No sé" (and its usual forms, or an empty answer) is a valid answer."""
    return normalize(answer) in _DONT_KNOW


def parse_count(answer: str) -> int | None:
    """A plain whole number ("120", "1,200"); anything else is not a count."""
    text = answer.strip()
    if not _COUNT.fullmatch(text):
        return None
    return int(re.sub(r"[.,]", "", text))


def last_month(today: date) -> tuple[str, str]:
    """``("2026-09", "septiembre de 2026")`` for any day of October 2026."""
    year, month = (
        (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
    )
    return f"{year:04d}-{month:02d}", f"{_MONTHS[month - 1]} de {year}"


def _question(stage: Stage, field: StageField, period_label: str) -> str:
    moment = _STAGE_MOMENT[stage]
    number = STAGES.index(stage) + 1
    questions: dict[StageField, str] = {
        "necesidad": (
            f"Paso {number} de 5, {moment}: ¿qué necesita tu cliente en ese momento?"
        ),
        "donde": (
            f"¿Dónde pasa eso, {moment}? Por ejemplo: WhatsApp, tu local, "
            "Instagram o por teléfono."
        ),
        "friccion": f"¿Qué lo frena o lo hace dudar {moment}?",
        "como_lo_sabe": (
            "¿Cómo lo sabes: lo ves tú, lo tienes anotado o te lo dijeron tus clientes?"
        ),
        "conteo": (
            f"¿Cuántos clientes llegaron a este paso en {period_label}? "
            "Sólo el número; si no lo tienes, dime «no sé»."
        ),
        "fuente_conteo": (
            "¿De dónde sale ese número? Por ejemplo: tu cuaderno, tu WhatsApp o "
            "tu sistema de ventas."
        ),
    }
    return questions[field]


def _latest(answers: list[Answer]) -> dict[tuple[Stage, StageField], str]:
    latest: dict[tuple[Stage, StageField], str] = {}
    for item in answers:
        latest[(item.stage, item.field)] = item.answer
    return latest


def _stage_draft(
    stage: Stage, latest: dict[tuple[Stage, StageField], str]
) -> StageDraft:
    values: dict[str, str | int | None] = {"stage": stage}
    for field in FIELDS:
        raw = latest.get((stage, field))
        if raw is None or is_dont_know(raw):
            continue
        values[field] = parse_count(raw) if field == "conteo" else raw.strip()
    draft = StageDraft.model_validate(values)
    if draft.conteo is None:
        # A source for a count that does not exist is meaningless.
        draft = draft.model_copy(update={"fuente_conteo": None})
    return draft


def _missing(drafts: list[StageDraft], period_label: str) -> list[str]:
    missing: list[str] = []
    for draft in drafts:
        for field in FIELDS:
            if field == "fuente_conteo" and draft.conteo is None:
                continue
            if getattr(draft, field) is None:
                label = _MISSING_LABEL[field].format(period=period_label)
                missing.append(f"{STAGE_LABEL[draft.stage]}: {label}")
    return missing


def _pending(
    latest: dict[tuple[Stage, StageField], str],
) -> tuple[Stage, StageField, bool] | None:
    for stage in STAGES:
        for field in FIELDS:
            raw = latest.get((stage, field))
            if field == "fuente_conteo":
                count = latest.get((stage, "conteo"))
                if count is None or parse_count(count) is None:
                    continue
            if raw is None:
                return stage, field, False
            if field == "conteo" and not is_dont_know(raw) and parse_count(raw) is None:
                return stage, field, True
    return None


def interview_step(answers: list[Answer], today: date) -> InterviewStep:
    """Next single question, or the end, with the draft built so far."""
    period, period_label = last_month(today)
    latest = _latest(answers)
    drafts = [_stage_draft(stage, latest) for stage in STAGES]
    draft = JourneyDraft(
        period=period,
        period_label=period_label,
        stages=drafts,
        missing=_missing(drafts, period_label),
    )
    pending = _pending(latest)
    if pending is None:
        return InterviewStep(done=True, message=DONE, draft=draft)
    stage, field, retry = pending
    message = _question(stage, field, period_label)
    if retry:
        message = f"{COUNT_RETRY} {message}"
    elif not latest:
        message = f"{message} {INTRO}"
    return InterviewStep(
        done=False, stage=stage, field=field, retry=retry, message=message, draft=draft
    )
