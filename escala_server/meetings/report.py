"""Local schedule and executive report artifacts for E39."""

from __future__ import annotations

from datetime import date
from html import escape
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable

from escala_server.workspace.authority import WorkspaceConfig, validate_workspace

from .analysis import build_executive_review
from .models import (
    ExecutiveReview,
    LocalSchedule,
    MeetingExchangeReceipt,
    MeetingRecord,
    MeetingReportArtifact,
)


class MeetingReportError(ValueError):
    """Stable local report failure without machine paths."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def validate_report_exchange(config: WorkspaceConfig) -> MeetingExchangeReceipt:
    """Validate local authority and reject database files in the exchange."""

    workspace_receipt = validate_workspace(config)
    findings = [finding.code for finding in workspace_receipt.findings]
    exchange = config.exchange_root.expanduser().resolve(strict=False)
    if not exchange.exists() or not exchange.is_dir():
        findings.append("exchange_missing")
    else:
        try:
            for path in exchange.rglob("*"):
                if path.is_file() and path.suffix.casefold() in {
                    ".sqlite",
                    ".sqlite3",
                    ".db",
                }:
                    findings.append("authoritative_sqlite_sync_forbidden")
                    break
        except OSError:
            findings.append("exchange_unreadable")
    unique = tuple(sorted(set(findings)))
    return MeetingExchangeReceipt(
        status="fail" if unique else "pass",
        findings=unique,
    )


def schedule_daily_review(
    config: WorkspaceConfig,
    *,
    run_date: date,
) -> LocalSchedule:
    """Persist a deterministic pull schedule under data_root."""

    _ensure_ready(config)
    schedule_id = hashlib.sha256(
        f"v1\0daily\0{run_date.isoformat()}".encode("utf-8")
    ).hexdigest()
    schedule = LocalSchedule(
        schedule_id=schedule_id,
        frequency="daily",
        run_date=run_date,
        manifest_path=".escala-meeting-schedule.json",
    )
    _atomic_write(
        config.data_root.expanduser().resolve(strict=False) / schedule.manifest_path,
        json.dumps(
            schedule.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
    )
    return schedule


def write_executive_report(
    config: WorkspaceConfig,
    review: ExecutiveReview,
) -> MeetingReportArtifact:
    """Write deterministic local Markdown, HTML and JSON review artifacts."""

    _ensure_ready(config)
    report_id = hashlib.sha256(
        "\0".join(
            [
                "v1",
                review.review_id,
                review.review_date.isoformat(),
                *review.evidence_source_ids,
            ]
        ).encode("utf-8")
    ).hexdigest()
    basename = f"executive-review-{review.review_date.isoformat()}-{report_id[:12]}"
    root = (
        config.data_root.expanduser().resolve(strict=False) / ".escala-meeting-reports"
    )
    artifact = MeetingReportArtifact(
        report_id=report_id,
        review_id=review.review_id,
        html_path=f".escala-meeting-reports/{basename}.html",
        markdown_path=f".escala-meeting-reports/{basename}.md",
        json_path=f".escala-meeting-reports/{basename}.json",
        source_ids=review.evidence_source_ids,
    )
    markdown = _render_markdown(review)
    html = _render_html(review)
    payload = json.dumps(
        {
            "report_id": artifact.report_id,
            "review_id": artifact.review_id,
            "review_date": review.review_date.isoformat(),
            "health": review.health,
            "material_changes": review.material_changes,
            "questions": review.questions,
            "signals": [signal.model_dump(mode="json") for signal in review.signals],
            "evidence_source_ids": review.evidence_source_ids,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    _atomic_write(root / f"{basename}.html", html)
    _atomic_write(root / f"{basename}.md", markdown)
    _atomic_write(root / f"{basename}.json", payload)
    return artifact


def run_daily_review(
    config: WorkspaceConfig,
    records: Iterable[MeetingRecord],
    *,
    run_date: date,
) -> tuple[ExecutiveReview, LocalSchedule, MeetingReportArtifact]:
    """Run the complete local pull workflow without a daemon or cloud call."""

    review = build_executive_review(tuple(records), as_of=run_date)
    schedule = schedule_daily_review(config, run_date=run_date)
    artifact = write_executive_report(config, review)
    return review, schedule, artifact


def render_meeting_report_receipt_json(artifact: MeetingReportArtifact) -> str:
    """Render only safe artifact identity and relative paths."""

    return json.dumps(
        {
            "status": "ready",
            "report_id": artifact.report_id,
            "review_id": artifact.review_id,
            "html_path": artifact.html_path,
            "markdown_path": artifact.markdown_path,
            "json_path": artifact.json_path,
            "source_count": len(artifact.source_ids),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def render_meeting_report_receipt_markdown(artifact: MeetingReportArtifact) -> str:
    """Render a bounded human-readable receipt."""

    return (
        "# Meeting Report Receipt\n\n"
        "- status: ready\n"
        f"- report_id: {artifact.report_id}\n"
        f"- html_path: {artifact.html_path}\n"
        f"- markdown_path: {artifact.markdown_path}\n"
        f"- json_path: {artifact.json_path}\n"
        f"- source_count: {len(artifact.source_ids)}\n"
    )


def _ensure_ready(config: WorkspaceConfig) -> None:
    receipt = validate_report_exchange(config)
    if receipt.status != "pass":
        raise MeetingReportError(
            receipt.findings[0] if receipt.findings else "workspace_invalid"
        )
    config.data_root.expanduser().resolve(strict=False).mkdir(
        parents=True, exist_ok=True
    )


def _render_markdown(review: ExecutiveReview) -> str:
    lines = [
        "# Executive Meeting Review",
        "",
        f"- date: {review.review_date.isoformat()}",
        f"- health: {review.health}",
        "",
        "## Material changes",
    ]
    lines.extend(f"- {change}" for change in review.material_changes) or lines.append(
        "- none"
    )
    lines.extend(["", "## Questions"])
    lines.extend(f"- {question}" for question in review.questions) or lines.append(
        "- none"
    )
    lines.extend(["", "## Evidence"])
    lines.extend(
        f"- source: {source_id}" for source_id in review.evidence_source_ids
    ) or lines.append("- none")
    return "\n".join(lines) + "\n"


def _render_html(review: ExecutiveReview) -> str:
    changes = (
        "".join(f"<li>{escape(change)}</li>" for change in review.material_changes)
        or "<li>none</li>"
    )
    questions = (
        "".join(f"<li>{escape(question)}</li>" for question in review.questions)
        or "<li>none</li>"
    )
    sources = (
        "".join(
            f"<li>{escape(source_id)}</li>" for source_id in review.evidence_source_ids
        )
        or "<li>none</li>"
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Executive Meeting Review</title></head><body>"
        f"<h1>Executive Meeting Review</h1><p>Date: {escape(review.review_date.isoformat())}</p>"
        f"<p>Health: {escape(review.health)}</p><h2>Material changes</h2><ul>{changes}</ul>"
        f"<h2>Questions</h2><ul>{questions}</ul><h2>Evidence</h2><ul>{sources}</ul>"
        "</body></html>"
    )


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    try:
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)
    except OSError:
        raise MeetingReportError("report_write_failed") from None
