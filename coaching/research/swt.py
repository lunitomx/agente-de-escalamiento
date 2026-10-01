# pyright: strict
"""Saved outside findings as external evidence for the one SWT (E83 S83.4).

D9: there is no second SWT. ``escala-strategy-swt`` keeps writing its own
file; this only hands it the newest ``fortalezas-tendencias`` research that is
still current, each finding marked as outside ("Según fuentes externas, [mes]")
and graded (confirmado / por confirmar), separate from the internal evidence.

- A research past ``review_by`` does not enter; the owner is offered a refresh.
- Texts arrive whole, without URLs; the local report is the reference.
- Nothing here writes a file.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from coaching.research import messages
from coaching.research.models import (
    ClaimStatus,
    ResearchReport,
    Side,
    without_urls,
)
from coaching.research.report import load_index, load_saved_report

_SIDES: tuple[Side, ...] = ("fortaleza", "debilidad", "tendencia")


class SwtEvidence(BaseModel):
    """One outside finding, ready to sit apart from the internal evidence."""

    model_config = ConfigDict(extra="forbid")

    side: Side
    text: str
    status: ClaimStatus
    label: str
    against: list[str] = Field(default_factory=list)
    reference: str
    researched_on: date


class SwtInputs(BaseModel):
    """What the SWT receives: the evidence, its report, or a refresh offer."""

    model_config = ConfigDict(extra="forbid")

    evidence: list[SwtEvidence] = Field(default_factory=list[SwtEvidence])
    reference: str | None = None
    refresh_offer: str | None = None


def to_swt_evidence(report: ResearchReport, reference: str) -> list[SwtEvidence]:
    """Every finding with a side, in SWT order (strengths, weaknesses, trends)."""
    label = messages.outside_label(report.researched_on)
    items = [
        SwtEvidence(
            side=claim.side,
            text=" ".join(without_urls(claim.text).split()),
            status=claim.status,
            label=label,
            against=[without_urls(name) for name in claim.against],
            reference=reference,
            researched_on=report.researched_on,
        )
        for claim in report.claims
        if claim.side is not None
    ]
    return sorted(items, key=lambda item: _SIDES.index(item.side))


def load_swt_evidence(base: Path, as_of: date) -> SwtInputs:
    """The newest saved ``fortalezas-tendencias`` research, if still current."""
    entries = sorted(
        (
            (position, entry)
            for position, entry in enumerate(load_index(base))
            if entry.mode == "fortalezas-tendencias"
        ),
        key=lambda pair: (pair[1].researched_on, pair[0]),
        reverse=True,
    )
    if not entries:
        return SwtInputs()
    entry = entries[0][1]
    if as_of > entry.review_by:
        return SwtInputs(
            refresh_offer=messages.stale_offer(
                without_urls(entry.question), entry.researched_on, entry.review_by
            )
        )
    report = load_saved_report(base, entry)
    if report is None:
        return SwtInputs()
    return SwtInputs(
        evidence=to_swt_evidence(report, entry.reference), reference=entry.reference
    )


def swt_message(inputs: SwtInputs) -> str:
    """Short Spanish: grouped by side, each line graded; ends in a question."""
    if inputs.refresh_offer is not None:
        return inputs.refresh_offer
    if not inputs.evidence:
        return messages.SWT_ASK
    lines = [f"{inputs.evidence[0].label}:"]
    for side in _SIDES:
        group = [item for item in inputs.evidence if item.side == side]
        if not group:
            continue
        lines.append(f"{messages.SWT_TITLES[side]}:")
        lines += [
            f"- {messages.STATUS_WORDS[item.status]} — {item.text}"
            + (
                f" (frente a {messages.join_names(item.against)})"
                if item.against
                else ""
            )
            for item in group
        ]
    lines.append(messages.SWT_ADD)
    return "\n".join(lines)
