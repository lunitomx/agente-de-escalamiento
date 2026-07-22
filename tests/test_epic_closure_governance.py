from __future__ import annotations

from pathlib import Path

import pytest

import validators.epic_closure as closure_module
from validators.epic_closure import (
    validate_audited_epic_closures,
    validate_backlog_draft_closures,
)
from validators.governance_contract import load_closure_disposition_policy


ROOT = Path(__file__).resolve().parents[1]
CLOSURE_POLICY_PATH = ROOT / "governance/closure-dispositions.yaml"


@pytest.fixture
def governed_root(tmp_path: Path) -> Path:
    target = tmp_path / "governance/closure-dispositions.yaml"
    target.parent.mkdir(parents=True)
    target.write_bytes(CLOSURE_POLICY_PATH.read_bytes())
    return tmp_path


def test_audited_epic_closures_are_governance_consistent() -> None:
    assert validate_audited_epic_closures(ROOT) == []


def test_backlog_draft_closures_are_not_complete_epics() -> None:
    assert validate_backlog_draft_closures(ROOT) == []


def test_complete_status_with_open_done_criteria_is_reported(
    governed_root: Path,
) -> None:
    target = governed_root / "work/epics/e24-escala-evolve"
    target.mkdir(parents=True)
    (target / "scope.md").write_text(
        """# E24

**Status:** Complete

## Done Criteria

- [ ] Cron semanal envía resumen de hallazgos
""",
        encoding="utf-8",
    )

    errors = validate_audited_epic_closures(governed_root)

    assert any("E24: expected status 'deferred/backlog'" in error for error in errors)


def test_backlog_draft_with_complete_status_is_reported(
    governed_root: Path,
) -> None:
    target = governed_root / "work/epics/e19-strategy-core-skills"
    target.mkdir(parents=True)
    (target / "scope.md").write_text(
        """# E19

**Status:** Complete

## Backlog Closure Review

Tag action: no `complete` tag should be created for this draft.
""",
        encoding="utf-8",
    )

    errors = validate_backlog_draft_closures(governed_root)

    assert any(
        "E19 Strategy Core Draft: expected status 'superseded/discarded'" in error
        for error in errors
    )


def test_deferred_backlog_scope_is_accepted(governed_root: Path) -> None:
    target = governed_root / "work/epics/e24-escala-evolve"
    target.mkdir(parents=True)
    (target / "scope.md").write_text(
        """# E24

**Status:** Deferred/Backlog

## Governance correction

Backlog action: reopen only through a newly scoped story with evidence.
""",
        encoding="utf-8",
    )

    errors = validate_audited_epic_closures(governed_root)

    assert [error for error in errors if error.startswith("E24:")] == []


def test_deferred_backlog_requires_backlog_action(governed_root: Path) -> None:
    target = governed_root / "work/epics/e24-escala-evolve"
    target.mkdir(parents=True)
    (target / "scope.md").write_text(
        """# E24

**Status:** Deferred/Backlog

## Governance correction

The old epic is not complete and is not active.
""",
        encoding="utf-8",
    )

    errors = validate_audited_epic_closures(governed_root)

    assert "E24: missing required evidence phrase: Backlog action" in errors


def test_unknown_audited_disposition_is_reported(governed_root: Path) -> None:
    target = governed_root / "work/epics/e24-escala-evolve"
    target.mkdir(parents=True)
    (target / "scope.md").write_text(
        """# E24

**Status:** Paused Somehow

## Governance correction

Backlog action: decide later.
""",
        encoding="utf-8",
    )

    errors = validate_audited_epic_closures(governed_root)

    assert "E24: expected status 'deferred/backlog', got 'paused somehow'" in errors


def test_superseded_discarded_draft_is_accepted(governed_root: Path) -> None:
    target = governed_root / "work/epics/e19-strategy-core-skills"
    target.mkdir(parents=True)
    (target / "scope.md").write_text(
        """# E19

**Status:** Superseded/Discarded

## Backlog Closure Review

Current backlog action: no active epic remains here.
Tag action: no `complete` tag should be created for this draft.
""",
        encoding="utf-8",
    )

    errors = validate_backlog_draft_closures(governed_root)

    assert [
        error for error in errors if error.startswith("E19 Strategy Core Draft:")
    ] == []


def test_deprecated_discarded_draft_is_accepted(governed_root: Path) -> None:
    target = governed_root / "work/epics/e21-transcript-intelligence-for-escala"
    target.mkdir(parents=True)
    (target / "scope.md").write_text(
        """# E21

**Status:** Deprecated/Discarded

## Backlog Closure Review

Current backlog action: no active epic remains here.
Tag action: no `complete` tag should be created for this draft.
""",
        encoding="utf-8",
    )

    errors = validate_backlog_draft_closures(governed_root)

    assert [
        error
        for error in errors
        if error.startswith("E21 Transcript Intelligence Draft:")
    ] == []


def test_discarded_draft_requires_no_complete_tag(governed_root: Path) -> None:
    target = governed_root / "work/epics/e19-strategy-core-skills"
    target.mkdir(parents=True)
    (target / "scope.md").write_text(
        """# E19

**Status:** Superseded/Discarded

## Backlog Closure Review

Current backlog action: no active epic remains here.
""",
        encoding="utf-8",
    )

    errors = validate_backlog_draft_closures(governed_root)

    assert (
        "E19 Strategy Core Draft: missing required evidence phrase: no `complete` tag"
    ) in errors


@pytest.mark.parametrize("corrupt", [False, True])
def test_missing_or_corrupt_policy_fails_closed_safely(
    tmp_path: Path,
    corrupt: bool,
) -> None:
    if corrupt:
        target = tmp_path / "governance/closure-dispositions.yaml"
        target.parent.mkdir(parents=True)
        target.write_text("schema_version: [", encoding="utf-8")

    assert validate_audited_epic_closures(tmp_path) == [
        "governance closure policy: unavailable or invalid"
    ]
    assert validate_backlog_draft_closures(tmp_path) == [
        "governance closure policy: unavailable or invalid"
    ]


@pytest.mark.parametrize(
    ("status", "normalized"),
    [
        ("Complete eventually", "complete eventually"),
        ("Active but complete", "active but complete"),
        ("Partial/Backlog", "partial/backlog"),
        ("Backlog/Not Completed", "backlog/not completed"),
        ("Deferred/Backlog later", "deferred/backlog later"),
        ("Deferred/Backlog ✅", "deferred/backlog ✅"),
    ],
)
def test_status_substrings_and_suffixes_do_not_resolve(
    governed_root: Path,
    status: str,
    normalized: str,
) -> None:
    target = governed_root / "work/epics/e24-escala-evolve"
    target.mkdir(parents=True)
    (target / "scope.md").write_text(
        f"""# E24

**Status:** {status}

## Governance correction

Backlog action: decide later.
""",
        encoding="utf-8",
    )

    errors = validate_audited_epic_closures(governed_root)

    assert f"E24: expected status 'deferred/backlog', got {normalized!r}" in errors


def test_missing_status_does_not_resolve(governed_root: Path) -> None:
    target = governed_root / "work/epics/e24-escala-evolve"
    target.mkdir(parents=True)
    (target / "scope.md").write_text(
        "# E24\n\nBacklog action: decide later.\n",
        encoding="utf-8",
    )

    errors = validate_audited_epic_closures(governed_root)

    assert "E24: expected status 'deferred/backlog', got 'unknown'" in errors


@pytest.mark.parametrize(
    "disposition",
    [
        item.id
        for item in load_closure_disposition_policy(CLOSURE_POLICY_PATH).dispositions
    ],
)
def test_exact_policy_dispositions_are_extracted_without_semantic_copy(
    disposition: str,
) -> None:
    policy = load_closure_disposition_policy(CLOSURE_POLICY_PATH)

    assert (
        closure_module._extract_status(
            f'**Status:** "  {disposition.upper()}  "',
            policy,
        )
        == disposition
    )


def test_e12_uses_the_canonical_cancelled_absorbed_disposition() -> None:
    text = (ROOT / "work/epics/e12-codex-and-update/scope.md").read_text(
        encoding="utf-8"
    )

    assert "**Status:** Cancelled/Absorbed" in text
    assert "CANCELLED — Absorbido por E11" not in text
