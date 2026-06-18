"""Governance checks for audited epic closure truth."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class EpicClosureRule:
    """Expected closure posture for a governance-audited epic."""

    epic_id: str
    path: str
    expected_status: str
    allow_open_done_criteria: bool = False
    required_phrases: tuple[str, ...] = ()
    forbidden_phrases: tuple[str, ...] = ()


AUDITED_EPIC_RULES: tuple[EpicClosureRule, ...] = (
    EpicClosureRule(
        epic_id="E10",
        path="work/epics/e10-cross-platform-distribution/scope.md",
        expected_status="complete",
        required_phrases=("Historical Milestones", "Legacy backlog"),
    ),
    EpicClosureRule(
        epic_id="E11",
        path="work/epics/e11-agente-escalamiento/scope.md",
        expected_status="complete",
        required_phrases=("Retrospective evidence",),
    ),
    EpicClosureRule(
        epic_id="E19",
        path="work/epics/e19-book-ingestion/scope.md",
        expected_status="partial",
        allow_open_done_criteria=True,
        required_phrases=("Governance correction", "required follow-up"),
    ),
    EpicClosureRule(
        epic_id="E22",
        path="work/epics/e22-verne-audit/scope.md",
        expected_status="absorbed/descoped",
        allow_open_done_criteria=True,
        required_phrases=("Absorption map", "Descoped"),
    ),
    EpicClosureRule(
        epic_id="E23",
        path="work/epics/e23-kokoro-agent/scope.md",
        expected_status="partial",
        allow_open_done_criteria=True,
        required_phrases=("Governance correction", "required follow-up"),
    ),
    EpicClosureRule(
        epic_id="E24",
        path="work/epics/e24-escala-evolve/scope.md",
        expected_status="partial/backlog",
        allow_open_done_criteria=True,
        required_phrases=("Governance correction", "required follow-up"),
    ),
    EpicClosureRule(
        epic_id="E29",
        path="work/epics/e29-governance-repair/scope.md",
        expected_status="complete",
        required_phrases=("retrospective.md",),
    ),
    EpicClosureRule(
        epic_id="E30",
        path="work/epics/e30-scaleup-skill-pipelines/scope.md",
        expected_status="complete",
        required_phrases=("registry-and-alignment scope",),
    ),
    EpicClosureRule(
        epic_id="E31",
        path="work/epics/e31-scaleup-pipeline-runtime-runner/scope.md",
        expected_status="complete",
        required_phrases=("Final Status", "S31.3 is now complete"),
    ),
)


BACKLOG_DRAFT_RULES: tuple[EpicClosureRule, ...] = (
    EpicClosureRule(
        epic_id="E19 Strategy Core Draft",
        path="work/epics/e19-strategy-core-skills/scope.md",
        expected_status="backlog/not completed",
        allow_open_done_criteria=True,
        required_phrases=("Backlog Closure Review", "no `complete` tag"),
    ),
    EpicClosureRule(
        epic_id="E20 Voice of Customer Draft",
        path="work/epics/e20-voice-of-customer-evidence-capture/scope.md",
        expected_status="backlog/not completed",
        allow_open_done_criteria=True,
        required_phrases=("Backlog Closure Review", "no `complete` tag"),
    ),
    EpicClosureRule(
        epic_id="E21 Transcript Intelligence Draft",
        path="work/epics/e21-transcript-intelligence-for-escala/scope.md",
        expected_status="backlog/not completed",
        allow_open_done_criteria=True,
        required_phrases=("Backlog Closure Review", "no `complete` tag"),
    ),
    EpicClosureRule(
        epic_id="E22 Validation Drift Draft",
        path="work/epics/e22-validation-drift-governance/scope.md",
        expected_status="backlog/not completed",
        allow_open_done_criteria=True,
        required_phrases=("Backlog Closure Review", "no `complete` tag"),
    ),
)


def validate_audited_epic_closures(root: Path) -> list[str]:
    """Return closure governance errors for the E32 audited epic set."""
    return _validate_epic_rules(root, AUDITED_EPIC_RULES)


def validate_backlog_draft_closures(root: Path) -> list[str]:
    """Return governance errors for draft epics closed as backlog."""
    return _validate_epic_rules(root, BACKLOG_DRAFT_RULES)


def _validate_epic_rules(root: Path, rules: tuple[EpicClosureRule, ...]) -> list[str]:
    errors: list[str] = []

    for rule in rules:
        path = root / rule.path
        if not path.exists():
            errors.append(f"{rule.epic_id}: missing scope file: {rule.path}")
            continue

        text = path.read_text(encoding="utf-8")
        status = _extract_status(text)
        if status != rule.expected_status:
            errors.append(
                f"{rule.epic_id}: expected status {rule.expected_status!r}, got {status!r}"
            )

        if not rule.allow_open_done_criteria:
            open_items = _open_done_criteria_items(text)
            if open_items:
                errors.append(
                    f"{rule.epic_id}: open Done Criteria under closed status: "
                    + "; ".join(open_items)
                )

        for phrase in rule.required_phrases:
            if phrase not in text:
                errors.append(
                    f"{rule.epic_id}: missing required evidence phrase: {phrase}"
                )

        for phrase in rule.forbidden_phrases:
            if phrase in text:
                errors.append(
                    f"{rule.epic_id}: forbidden closure phrase present: {phrase}"
                )

    return errors


def _extract_status(text: str) -> str:
    patterns = (
        r'^status:\s*["\']?([^"\'\n]+)',
        r"^\*\*Status:\*\*\s*(.+)$",
        r"^Status:\s*(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return _normalize_status(match.group(1))
    return "unknown"


def _normalize_status(value: str) -> str:
    clean = value.strip().strip('"').strip("'").lower()
    clean = clean.replace("✅", "").strip()
    clean = re.sub(r"\s+", " ", clean)
    if "partial/backlog" in clean:
        return "partial/backlog"
    if "backlog/not completed" in clean:
        return "backlog/not completed"
    if "absorbed/descoped" in clean:
        return "absorbed/descoped"
    if "partial" in clean:
        return "partial"
    if "active" in clean:
        return "active"
    if "complete" in clean:
        return "complete"
    return clean


def _open_done_criteria_items(text: str) -> list[str]:
    body = _section_body(text, "Done Criteria")
    return [
        line.strip()
        for line in body.splitlines()
        if re.match(r"^-\s+\[\s\]", line.strip())
    ]


def _section_body(text: str, heading: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if not match:
        return ""

    rest = text[match.end() :]
    next_heading = re.search(r"^##\s+", rest, flags=re.MULTILINE)
    if next_heading:
        return rest[: next_heading.start()]
    return rest
