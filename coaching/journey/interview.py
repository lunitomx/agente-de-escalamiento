# pyright: strict
"""The journey interview (E84 S84.1): ultra simple, at most ~6 questions.

One question per stage (5 stages) asks what happens there AND roughly how many
customers last month, in the same message. After the 5 stages, at most one
follow-up asks why customers are lost where the biggest drop is.

Stateless: the procedure passes every answer so far and gets back the next
question plus the draft built from those answers. "No sé" is a valid answer
and leaves the field missing. An approximate count ("unos 100", "entre 80 y
120") is kept as a supuesto and never asked again; only an answer with no
number at all gets one short retry for the count. The source of every count is
"lo dijo el dueño". The draft is never saved here: the decision and saving
belong to S84.2.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from coaching.journey.triggers import normalize

Stage = Literal["se_entera", "pregunta", "compra", "recibe", "regresa"]
AnswerField = Literal["paso", "conteo", "friccion"]
STAGES: tuple[Stage, ...] = ("se_entera", "pregunta", "compra", "recibe", "regresa")

STAGE_LABEL: dict[Stage, str] = {
    "se_entera": "Se entera de ti",
    "pregunta": "Te pregunta",
    "compra": "Te compra",
    "recibe": "Recibe lo que compró",
    "regresa": "Regresa a comprar",
}
# What happens + how many, in one question per stage.
_STAGE_QUESTION: dict[Stage, str] = {
    "se_entera": "¿cómo se enteran de ti tus clientes y más o menos cuántos "
    "se enteraron en {period}?",
    "pregunta": "¿por dónde te preguntan y más o menos cuántos te preguntaron "
    "en {period}?",
    "compra": "¿cómo te compran y más o menos cuántos te compraron en {period}?",
    "recibe": "¿cómo reciben lo que compraron y más o menos cuántos lo "
    "recibieron en {period}?",
    "regresa": "¿quiénes regresan a comprarte y más o menos cuántos regresaron "
    "en {period}?",
}
_STAGE_VERB: dict[Stage, str] = {
    "se_entera": "se enteraron de ti",
    "pregunta": "te preguntaron",
    "compra": "te compraron",
    "recibe": "recibieron lo que compraron",
    "regresa": "regresaron a comprarte",
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
# "no sé cuántos" inside a longer answer: the count is unknown, do not retry.
_UNKNOWN_COUNT = re.compile(r"\b(no se|no lo se|ni idea|no tengo idea|no sabria)\b")
_N = r"(\d{1,3}(?:[.,]\d{3})+|\d+)"
_NUMBER = re.compile(rf"(?<![\d.,]){_N}(?!\d|[.,]\d)")
_RANGE = re.compile(
    rf"\bentre\s+{_N}\s+y\s+{_N}|\bde\s+{_N}\s+a\s+{_N}|{_N}\s*(?:-|\ba\b)\s*{_N}"
)
_HEDGE = re.compile(
    r"\b(unos|unas|como|casi|aprox|aproximadamente|mas o menos|alrededor"
    r"|cerca de|poco mas|mas de|menos de)\b|~"
)

OWNER_SOURCE = "lo dijo el dueño"
INTRO = "Si algo no lo sabes, dime «no sé» y seguimos."
DONE = (
    "Listo, ya tengo los 5 pasos. Esto todavía no se guarda: primero lo revisamos "
    "juntos."
)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Answer(_Strict):
    """What the owner said to one question (his words, as said).

    ``paso`` answers the stage question, ``conteo`` the short count retry and
    ``friccion`` the single follow-up about the biggest drop.
    """

    stage: Stage
    field: AnswerField
    answer: str


class Count(_Strict):
    """A count as the owner gave it; ``supuesto`` when he gave an approximation."""

    value: int = Field(ge=0)
    upper: int | None = Field(default=None, ge=0)
    supuesto: bool = False

    def middle(self) -> float:
        """Used only to compare stages; never stored as the owner's number."""
        return self.value if self.upper is None else (self.value + self.upper) / 2

    def spoken(self) -> str:
        if self.upper is not None:
            return f"entre {self.value} y {self.upper}"
        return f"unos {self.value}" if self.supuesto else str(self.value)


class StageDraft(_Strict):
    """One stage as the owner told it; ``None`` means missing, never estimated."""

    stage: Stage
    que_pasa: str | None = None
    conteo: int | None = Field(default=None, ge=0)
    conteo_hasta: int | None = Field(default=None, ge=0)
    conteo_supuesto: bool = False
    fuente_conteo: str | None = None
    friccion: str | None = None


class Drop(_Strict):
    """Where the most customers are lost between two consecutive stages."""

    from_stage: Stage
    to_stage: Stage


class JourneyDraft(_Strict):
    """The interview's output. Not saved: ``saved`` is always ``False``."""

    period: str
    period_label: str
    stages: list[StageDraft] = Field(default_factory=list[StageDraft])
    biggest_drop: Drop | None = None
    missing: list[str] = Field(default_factory=list[str])
    saved: Literal[False] = False


class InterviewStep(_Strict):
    """The next single question (or the end) plus the draft so far."""

    done: bool
    stage: Stage | None = None
    field: AnswerField | None = None
    retry: bool = False
    message: str
    draft: JourneyDraft


def is_dont_know(answer: str) -> bool:
    """ "No sé" (and its usual forms, or an empty answer) is a valid answer."""
    return normalize(answer) in _DONT_KNOW


def _fold(text: str) -> str:
    """Lowercase, accents removed, punctuation kept (for "1,200" and "80-120")."""
    ascii_text = (
        unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    )
    return " ".join(ascii_text.lower().split())


def _int(token: str) -> int:
    return int(re.sub(r"[.,]", "", token))


def parse_count(answer: str) -> Count | None:
    """The single count in an answer, exact or approximate (a supuesto).

    ``None`` when there is no number, or several unrelated ones ("3 y 40"):
    the count is never guessed.
    """
    text = _fold(answer)
    numbers = [_int(token) for token in _NUMBER.findall(text)]
    if len(numbers) == 1:
        return Count(value=numbers[0], supuesto=bool(_HEDGE.search(normalize(text))))
    match = _RANGE.search(text) if len(numbers) == 2 else None
    if match is None:
        return None
    low, high = sorted(_int(part) for part in match.groups() if part is not None)
    return Count(value=low, upper=high, supuesto=True)


def last_month(today: date) -> tuple[str, str]:
    """``("2026-09", "septiembre de 2026")`` for any day of October 2026."""
    year, month = (
        (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
    )
    return f"{year:04d}-{month:02d}", f"{_MONTHS[month - 1]} de {year}"


def _latest(answers: list[Answer]) -> dict[tuple[Stage, AnswerField], str]:
    latest: dict[tuple[Stage, AnswerField], str] = {}
    for item in answers:
        latest[(item.stage, item.field)] = item.answer
    return latest


def _needs_retry(paso: str) -> bool:
    """Only an answer with no number at all, and no "no sé", gets a retry."""
    if is_dont_know(paso) or _UNKNOWN_COUNT.search(normalize(paso)):
        return False
    return parse_count(paso) is None


def _stage_count(
    stage: Stage, latest: dict[tuple[Stage, AnswerField], str]
) -> Count | None:
    paso = latest.get((stage, "paso"))
    if paso is None or is_dont_know(paso):
        return None
    count = parse_count(paso)
    if count is None and _needs_retry(paso):
        retry = latest.get((stage, "conteo"))
        count = parse_count(retry) if retry is not None else None
    return count


def _stage_draft(
    stage: Stage, latest: dict[tuple[Stage, AnswerField], str]
) -> StageDraft:
    paso = latest.get((stage, "paso"))
    friccion = latest.get((stage, "friccion"))
    count = _stage_count(stage, latest)
    return StageDraft(
        stage=stage,
        que_pasa=None if paso is None or is_dont_know(paso) else paso.strip(),
        conteo=None if count is None else count.value,
        conteo_hasta=None if count is None else count.upper,
        conteo_supuesto=False if count is None else count.supuesto,
        fuente_conteo=None if count is None else OWNER_SOURCE,
        friccion=None
        if friccion is None or is_dont_know(friccion)
        else friccion.strip(),
    )


def _biggest_drop(
    counts: list[Count | None],
) -> tuple[int, Count, Count] | None:
    best: tuple[float, int, Count, Count] | None = None
    for index in range(len(STAGES) - 1):
        high, low = counts[index], counts[index + 1]
        if high is None or low is None or high.middle() <= 0:
            continue
        loss = (high.middle() - low.middle()) / high.middle()
        if loss > 0 and (best is None or loss > best[0]):
            best = (loss, index, high, low)
    return None if best is None else best[1:]


def _missing(drafts: list[StageDraft], period_label: str) -> list[str]:
    missing: list[str] = []
    for draft in drafts:
        label = STAGE_LABEL[draft.stage]
        if draft.que_pasa is None:
            missing.append(f"{label}: qué pasa")
        if draft.conteo is None:
            missing.append(f"{label}: cuántos en {period_label}")
    return missing


def _stage_question(stage: Stage, period_label: str) -> str:
    number = STAGES.index(stage) + 1
    question = _STAGE_QUESTION[stage].format(period=period_label)
    return f"Paso {number} de 5: {question}"


def _retry_question(stage: Stage, period_label: str) -> str:
    return (
        f"¿Y más o menos cuántos {_STAGE_VERB[stage]} en {period_label}? Un número "
        "aproximado sirve; si no lo sabes, dime «no sé»."
    )


def _follow_up_question(high: Stage, low: Stage, a: Count, b: Count) -> str:
    return (
        f"Donde más se te van es entre «{STAGE_LABEL[high]}» y "
        f"«{STAGE_LABEL[low]}»: de {a.spoken()} a {b.spoken()}. "
        "¿Qué crees que los frena ahí?"
    )


def interview_step(answers: list[Answer], today: date) -> InterviewStep:
    """Next single question, or the end, with the draft built so far."""
    period, period_label = last_month(today)
    latest = _latest(answers)
    drafts = [_stage_draft(stage, latest) for stage in STAGES]
    counts = [_stage_count(stage, latest) for stage in STAGES]
    drop = (
        _biggest_drop(counts)
        if all((stage, "paso") in latest for stage in STAGES)
        else None
    )
    draft = JourneyDraft(
        period=period,
        period_label=period_label,
        stages=drafts,
        biggest_drop=None
        if drop is None
        else Drop(from_stage=STAGES[drop[0]], to_stage=STAGES[drop[0] + 1]),
        missing=_missing(drafts, period_label),
    )

    def ask(stage: Stage, field: AnswerField, message: str) -> InterviewStep:
        return InterviewStep(
            done=False,
            stage=stage,
            field=field,
            retry=field == "conteo",
            message=message,
            draft=draft,
        )

    for stage in STAGES:
        paso = latest.get((stage, "paso"))
        if paso is None:
            message = _stage_question(stage, period_label)
            return ask(stage, "paso", f"{message} {INTRO}" if not latest else message)
        if _needs_retry(paso) and (stage, "conteo") not in latest:
            return ask(stage, "conteo", _retry_question(stage, period_label))
    if drop is not None:
        index, high, low = drop
        lost_at = STAGES[index + 1]
        if (lost_at, "friccion") not in latest:
            return ask(
                lost_at,
                "friccion",
                _follow_up_question(STAGES[index], lost_at, high, low),
            )
    return InterviewStep(done=True, message=DONE, draft=draft)
