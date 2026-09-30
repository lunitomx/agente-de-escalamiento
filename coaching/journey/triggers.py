# pyright: strict
"""When ESCALA asks for the customer journey, and when it never does (E84 S84.1).

``should_ask_journey`` is pure: everything it needs arrives in
``JourneySignals`` (the procedure passes the per-conversation flag and the
last decline, which ``coaching.journey.asks`` reads from disk). Blockers
N1-N6 are evaluated **before** triggers T1-T5, so a trigger never overrides
"no insistir".

Triggers (ask when any holds):

- T1 the owner's words hit the closed sales / marketing / retention lexicon;
- T2 the diagnosed constraint is strategy, or cash because of sales or price;
- T3 the funnel has some stages counted and some not;
- T4 the board recommender needs journey stages;
- T5 a market decision or benchmark is about acquisition or channel.

Blockers (never ask when any holds), in the order they are reported:

- N6 cash or payroll emergency;
- N5 another flow is in progress (ask when it ends);
- N3 already asked in this conversation (at most once);
- N2 the owner said "no" or "después" in the last 30 days;
- N1 a current journey exists (not past its ``review_by``). An expired one is
  not a blocker: the question offers to update it instead of starting over;
- N4 the constraint is people or execution and there is no sales signal
  (T1, T4 or T5).
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from coaching.diagnose.models import FunnelMetrics
from coaching.journey import messages

FunnelStage = Literal["prospects", "conversations", "proposals", "wins"]
FUNNEL_STAGES: tuple[FunnelStage, ...] = (
    "prospects",
    "conversations",
    "proposals",
    "wins",
)

TriggerCode = Literal["T1", "T2", "T3", "T4", "T5"]
BlockerCode = Literal["N1", "N2", "N3", "N4", "N5", "N6"]
AskReason = TriggerCode | BlockerCode | Literal["sin_disparador"]

NO_REASK_DAYS = 30

# Closed list, compared on whole words after removing accents and case.
SALES_LEXICON: tuple[str, ...] = (
    "pocos compran",
    "no compran",
    "no me compran",
    "nadie me compra",
    "no regresan",
    "no vuelven",
    "se me van",
    "no vendo",
    "vendo poco",
    "marketing",
    "prospecto",
    "prospectos",
    "no me llegan clientes",
    "no llegan clientes",
)


class JourneySignals(BaseModel):
    """Everything the decision needs; the module never sees the conversation."""

    model_config = ConfigDict(extra="forbid")

    owner_text: str = ""
    constraint_area: Literal["cash", "people", "strategy", "execution"] | None = None
    cash_topic: Literal["ventas", "precio", "liquidez", "cobranza"] | None = None
    funnel_known: list[FunnelStage] = Field(default_factory=list[FunnelStage])
    funnel_missing: list[FunnelStage] = Field(default_factory=list[FunnelStage])
    board_needs_stages: bool = False
    research_topic_acquisition: bool = False
    journey_review_by: date | None = None
    last_declined_on: date | None = None
    asked_this_conversation: bool = False
    other_flow_active: bool = False
    cash_emergency: bool = False
    today: date


class AskDecision(BaseModel):
    """Whether to ask, why (T1..T5 / N1..N6), and the one question to say."""

    model_config = ConfigDict(extra="forbid")

    ask: bool
    reason: AskReason
    message: str | None = None
    offer: Literal["nuevo", "actualizar"] | None = None


def normalize(text: str) -> str:
    """Lowercase, accents removed, only letters and digits, single spaces."""
    ascii_text = (
        unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    )
    return " ".join(re.sub(r"[^a-z0-9]+", " ", ascii_text.lower()).split())


def _words(text: str) -> str:
    return f" {normalize(text)} "


def has_sales_words(text: str) -> bool:
    """True when the owner's words hit the closed lexicon (whole words)."""
    padded = _words(text)
    return any(f" {phrase} " in padded for phrase in SALES_LEXICON)


def funnel_gaps(
    funnel: FunnelMetrics | None,
) -> tuple[list[FunnelStage], list[FunnelStage]]:
    """Stages with a count and stages without one; nothing is estimated."""
    if funnel is None:
        return [], list(FUNNEL_STAGES)
    known: list[FunnelStage] = [
        stage for stage in FUNNEL_STAGES if getattr(funnel, stage) is not None
    ]
    missing: list[FunnelStage] = [
        stage for stage in FUNNEL_STAGES if getattr(funnel, stage) is None
    ]
    return known, missing


def _blocker(signals: JourneySignals, sales_signal: bool) -> BlockerCode | None:
    if signals.cash_emergency:
        return "N6"
    if signals.other_flow_active:
        return "N5"
    if signals.asked_this_conversation:
        return "N3"
    declined = signals.last_declined_on
    if declined is not None and (signals.today - declined).days <= NO_REASK_DAYS:
        return "N2"
    review_by = signals.journey_review_by
    if review_by is not None and signals.today <= review_by:
        return "N1"
    if signals.constraint_area in ("people", "execution") and not sales_signal:
        return "N4"
    return None


def _trigger(signals: JourneySignals, t1: bool) -> TriggerCode | None:
    if t1:
        return "T1"
    if signals.constraint_area == "strategy" or (
        signals.constraint_area == "cash" and signals.cash_topic in ("ventas", "precio")
    ):
        return "T2"
    if signals.funnel_known and signals.funnel_missing:
        return "T3"
    if signals.board_needs_stages:
        return "T4"
    if signals.research_topic_acquisition:
        return "T5"
    return None


def should_ask_journey(signals: JourneySignals) -> AskDecision:
    """Decide whether to ask for the journey: blockers first, then triggers."""
    t1 = has_sales_words(signals.owner_text)
    sales_signal = (
        t1 or signals.board_needs_stages or signals.research_topic_acquisition
    )
    blocker = _blocker(signals, sales_signal)
    if blocker is not None:
        return AskDecision(ask=False, reason=blocker)
    trigger = _trigger(signals, t1)
    if trigger is None:
        return AskDecision(ask=False, reason="sin_disparador")
    if signals.journey_review_by is not None:  # expired: offer to update it
        return AskDecision(
            ask=True, reason=trigger, message=messages.ASK_UPDATE, offer="actualizar"
        )
    return AskDecision(
        ask=True, reason=trigger, message=messages.ASK_NEW, offer="nuevo"
    )
