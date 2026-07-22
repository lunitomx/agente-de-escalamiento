"""Cross-meeting signals and evidence-bounded executive review."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
import hashlib
from typing import Iterable

from .intake import _normalize
from .models import (
    ExecutiveReview,
    MeetingRecord,
    MeetingFact,
    TeamSignal,
    TeamSignalAnalysis,
)


def build_team_signals(
    records: Iterable[MeetingRecord],
    *,
    as_of: date,
) -> TeamSignalAnalysis:
    """Detect repeated, overdue, unresolved and changing evidence."""

    ordered = tuple(
        sorted(
            records,
            key=lambda record: (
                record.context.meeting_date or date.max,
                record.extraction.source_id,
            ),
        )
    )
    source_ids = tuple(sorted({record.extraction.source_id for record in ordered}))
    signals: list[TeamSignal] = []
    for kind in ("blocker", "commitment"):
        grouped = _group_facts(ordered, kind)
        for normalized_value, facts in sorted(grouped.items()):
            source_group = tuple(sorted({fact.source_id for fact in facts}))
            if len(source_group) >= 2:
                signal_kind = (
                    "repeated_blocker" if kind == "blocker" else "repeated_commitment"
                )
                signals.append(
                    _signal(
                        signal_kind,
                        normalized_value,
                        source_group,
                        len(facts),
                    )
                )

    overdue = _group_overdue(ordered, as_of)
    for normalized_value, facts in sorted(overdue.items()):
        source_group = tuple(sorted({fact.source_id for fact in facts}))
        signals.append(
            _signal("overdue_commitment", normalized_value, source_group, len(facts))
        )

    for record in ordered:
        if any(
            question.code == "decision_unresolved"
            for question in record.extraction.questions
        ):
            signals.append(
                _signal(
                    "unresolved_decision",
                    "decision_unresolved",
                    (record.extraction.source_id,),
                    1,
                )
            )

    trend = _trend_signal(ordered)
    if trend is not None:
        signals.append(trend)
    ordered_signals = tuple(
        sorted(signals, key=lambda signal: (signal.kind, signal.value))
    )
    return TeamSignalAnalysis(
        signals=ordered_signals,
        evidence_source_ids=source_ids,
    )


def build_executive_review(
    records: Iterable[MeetingRecord],
    *,
    as_of: date,
) -> ExecutiveReview:
    """Build a daily review without fabricating findings from empty evidence."""

    record_tuple = tuple(records)
    analysis = build_team_signals(record_tuple, as_of=as_of)
    question_codes = sorted(
        {
            question.code
            for record in record_tuple
            for question in record.extraction.questions
        }
    )
    if not record_tuple:
        health = "evidence_limited"
        questions = ("evidence_missing",)
        material_changes: tuple[str, ...] = ()
    elif question_codes and not analysis.signals:
        health = "unresolved"
        questions = tuple(question_codes)
        material_changes = ()
    elif analysis.signals:
        health = "watch"
        questions = tuple(question_codes)
        material_changes = tuple(
            f"{signal.kind}:{signal.value}" for signal in analysis.signals
        )
    else:
        health = "evidence_supported"
        questions = tuple(question_codes)
        material_changes = ()
    review_id = hashlib.sha256(
        "\0".join(
            [
                "v1",
                as_of.isoformat(),
                *analysis.evidence_source_ids,
                *(signal.signal_id for signal in analysis.signals),
            ]
        ).encode("utf-8")
    ).hexdigest()
    return ExecutiveReview(
        review_id=review_id,
        review_date=as_of,
        health=health,
        material_changes=material_changes,
        questions=questions,
        signals=analysis.signals,
        evidence_source_ids=analysis.evidence_source_ids,
    )


def _group_facts(
    records: tuple[MeetingRecord, ...], kind: str
) -> dict[str, list[MeetingFact]]:
    grouped: dict[str, list[MeetingFact]] = defaultdict(list)
    for record in records:
        for fact in record.extraction.facts:
            if fact.kind == kind:
                grouped[_normalize(fact.value)].append(fact)
    return grouped


def _group_overdue(
    records: tuple[MeetingRecord, ...],
    as_of: date,
) -> dict[str, list[MeetingFact]]:
    grouped: dict[str, list[MeetingFact]] = defaultdict(list)
    for record in records:
        for fact in record.extraction.facts:
            if (
                fact.kind in {"action", "commitment"}
                and fact.due_date
                and fact.due_date < as_of
            ):
                grouped[_normalize(fact.value)].append(fact)
    return grouped


def _trend_signal(records: tuple[MeetingRecord, ...]) -> TeamSignal | None:
    if len(records) < 2:
        return None
    midpoint = max(1, len(records) // 2)
    before = records[:midpoint]
    after = records[midpoint:]
    before_count = sum(
        1
        for record in before
        for fact in record.extraction.facts
        if fact.kind == "blocker"
    )
    after_count = sum(
        1
        for record in after
        for fact in record.extraction.facts
        if fact.kind == "blocker"
    )
    if after_count <= before_count:
        return None
    source_ids = tuple(sorted({record.extraction.source_id for record in records}))
    return _signal(
        "trend",
        f"blocker_frequency_increased:{before_count}->{after_count}",
        source_ids,
        after_count,
    )


def _signal(
    kind: str,
    value: str,
    source_ids: tuple[str, ...],
    evidence_count: int,
) -> TeamSignal:
    signal_id = hashlib.sha256(
        "\0".join(["v1", kind, value, *source_ids]).encode("utf-8")
    ).hexdigest()
    return TeamSignal(
        signal_id=signal_id,
        kind=kind,  # type: ignore[arg-type]
        value=value,
        evidence_source_ids=source_ids,
        evidence_count=evidence_count,
        confidence="high" if evidence_count >= 2 else "medium",
    )
