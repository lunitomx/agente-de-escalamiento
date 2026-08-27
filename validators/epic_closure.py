"""Governance checks for audited epic closure truth."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from pydantic import ValidationError

from validators.governance_contract import (
    ClosureDispositionPolicy,
    load_closure_disposition_policy,
)

try:
    import yaml
except ImportError as exc:  # pragma: no cover - project dependency
    raise ImportError("PyYAML required: pip install pyyaml") from exc


_POLICY_ERROR = "governance closure policy: unavailable or invalid"


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
        expected_status="active",
        allow_open_done_criteria=True,
        required_phrases=("Closure correction", "S10.10"),
    ),
    EpicClosureRule(
        epic_id="E11",
        path="work/epics/e11-agente-escalamiento/scope.md",
        expected_status="complete",
        required_phrases=("Retrospective evidence",),
    ),
    EpicClosureRule(
        epic_id="E1901",
        path="work/epics/e1901-book-ingestion/scope.md",
        expected_status="deferred/backlog",
        allow_open_done_criteria=True,
        required_phrases=("Governance correction", "Backlog action"),
    ),
    EpicClosureRule(
        epic_id="E2202",
        path="work/epics/e2202-verne-audit/scope.md",
        expected_status="absorbed/descoped",
        allow_open_done_criteria=True,
        required_phrases=("Absorption map", "Descoped"),
    ),
    EpicClosureRule(
        epic_id="E23",
        path="work/epics/e23-kokoro-agent/scope.md",
        expected_status="deferred/backlog",
        allow_open_done_criteria=True,
        required_phrases=("Governance correction", "Backlog action"),
    ),
    EpicClosureRule(
        epic_id="E24",
        path="work/epics/e24-escala-evolve/scope.md",
        expected_status="deferred/backlog",
        allow_open_done_criteria=True,
        required_phrases=("Governance correction", "Backlog action"),
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
        epic_id="E1902 Strategy Core Draft",
        path="work/epics/e1902-strategy-core-skills/scope.md",
        expected_status="superseded/discarded",
        allow_open_done_criteria=True,
        required_phrases=(
            "Backlog Closure Review",
            "Current backlog action",
            "no `complete` tag",
        ),
    ),
    EpicClosureRule(
        epic_id="E2002 Voice of Customer Draft",
        path="work/epics/e2002-voice-of-customer-evidence-capture/scope.md",
        expected_status="superseded/discarded",
        allow_open_done_criteria=True,
        required_phrases=(
            "Backlog Closure Review",
            "Current backlog action",
            "no `complete` tag",
        ),
    ),
    EpicClosureRule(
        epic_id="E2101 Transcript Intelligence Draft",
        path="work/epics/e2101-transcript-intelligence-for-escala/scope.md",
        expected_status="deprecated/discarded",
        allow_open_done_criteria=True,
        required_phrases=(
            "Backlog Closure Review",
            "Current backlog action",
            "no `complete` tag",
        ),
    ),
    EpicClosureRule(
        epic_id="E2201 Validation Drift Draft",
        path="work/epics/e2201-validation-drift-governance/scope.md",
        expected_status="superseded/discarded",
        allow_open_done_criteria=True,
        required_phrases=(
            "Backlog Closure Review",
            "Current backlog action",
            "no `complete` tag",
        ),
    ),
)


def validate_audited_epic_closures(root: Path) -> list[str]:
    """Return closure governance errors for the E32 audited epic set."""
    return _validate_epic_rules_with_policy(root, AUDITED_EPIC_RULES)


def validate_backlog_draft_closures(root: Path) -> list[str]:
    """Return governance errors for draft epics closed as backlog."""
    return _validate_epic_rules_with_policy(root, BACKLOG_DRAFT_RULES)


def _validate_epic_rules_with_policy(
    root: Path,
    rules: tuple[EpicClosureRule, ...],
) -> list[str]:
    try:
        policy = load_closure_disposition_policy(
            root / "governance/closure-dispositions.yaml"
        )
    except (OSError, UnicodeError, yaml.YAMLError, ValidationError):
        return [_POLICY_ERROR]

    accepted = {item.id for item in policy.dispositions}
    if any(rule.expected_status not in accepted for rule in rules):
        return [_POLICY_ERROR]
    return _validate_epic_rules(root, rules, policy)


def _validate_epic_rules(
    root: Path,
    rules: tuple[EpicClosureRule, ...],
    policy: ClosureDispositionPolicy,
) -> list[str]:
    errors: list[str] = []

    for rule in rules:
        path = root / rule.path
        if not path.exists():
            errors.append(f"{rule.epic_id}: missing scope file: {rule.path}")
            continue

        text = path.read_text(encoding="utf-8")
        status = _extract_status(text, policy)
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


def _extract_status(text: str, policy: ClosureDispositionPolicy) -> str:
    patterns = (
        r'^status:\s*["\']?([^"\'\n]+)',
        r"^\*\*Status:\*\*\s*(.+)$",
        r"^Status:\s*(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            clean = match.group(1).strip()
            if len(clean) >= 2 and clean[0] == clean[-1] and clean[0] in "\"'":
                clean = clean[1:-1].strip()
            clean = re.sub(r"\s+", " ", clean).casefold()
            canonical = {item.id.casefold(): item.id for item in policy.dispositions}
            return canonical.get(clean, clean)
    return "unknown"


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
