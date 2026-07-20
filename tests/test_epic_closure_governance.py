from __future__ import annotations

from pathlib import Path

from validators.epic_closure import (
    validate_audited_epic_closures,
    validate_backlog_draft_closures,
)


ROOT = Path(__file__).resolve().parents[1]


def test_audited_epic_closures_are_governance_consistent() -> None:
    assert validate_audited_epic_closures(ROOT) == []


def test_backlog_draft_closures_are_not_complete_epics() -> None:
    assert validate_backlog_draft_closures(ROOT) == []


def test_complete_status_with_open_done_criteria_is_reported(tmp_path: Path) -> None:
    target = tmp_path / "work/epics/e24-escala-evolve"
    target.mkdir(parents=True)
    (target / "scope.md").write_text(
        """# E24

**Status:** Complete

## Done Criteria

- [ ] Cron semanal envía resumen de hallazgos
""",
        encoding="utf-8",
    )

    errors = validate_audited_epic_closures(tmp_path)

    assert any("E24: expected status 'deferred/backlog'" in error for error in errors)


def test_backlog_draft_with_complete_status_is_reported(tmp_path: Path) -> None:
    target = tmp_path / "work/epics/e19-strategy-core-skills"
    target.mkdir(parents=True)
    (target / "scope.md").write_text(
        """# E19

**Status:** Complete

## Backlog Closure Review

Tag action: no `complete` tag should be created for this draft.
""",
        encoding="utf-8",
    )

    errors = validate_backlog_draft_closures(tmp_path)

    assert any(
        "E19 Strategy Core Draft: expected status 'superseded/discarded'" in error
        for error in errors
    )


def test_deferred_backlog_scope_is_accepted(tmp_path: Path) -> None:
    target = tmp_path / "work/epics/e24-escala-evolve"
    target.mkdir(parents=True)
    (target / "scope.md").write_text(
        """# E24

**Status:** Deferred/Backlog

## Governance correction

Backlog action: reopen only through a newly scoped story with evidence.
""",
        encoding="utf-8",
    )

    errors = validate_audited_epic_closures(tmp_path)

    assert [error for error in errors if error.startswith("E24:")] == []


def test_deferred_backlog_requires_backlog_action(tmp_path: Path) -> None:
    target = tmp_path / "work/epics/e24-escala-evolve"
    target.mkdir(parents=True)
    (target / "scope.md").write_text(
        """# E24

**Status:** Deferred/Backlog

## Governance correction

The old epic is not complete and is not active.
""",
        encoding="utf-8",
    )

    errors = validate_audited_epic_closures(tmp_path)

    assert "E24: missing required evidence phrase: Backlog action" in errors


def test_unknown_audited_disposition_is_reported(tmp_path: Path) -> None:
    target = tmp_path / "work/epics/e24-escala-evolve"
    target.mkdir(parents=True)
    (target / "scope.md").write_text(
        """# E24

**Status:** Paused Somehow

## Governance correction

Backlog action: decide later.
""",
        encoding="utf-8",
    )

    errors = validate_audited_epic_closures(tmp_path)

    assert "E24: expected status 'deferred/backlog', got 'paused somehow'" in errors


def test_superseded_discarded_draft_is_accepted(tmp_path: Path) -> None:
    target = tmp_path / "work/epics/e19-strategy-core-skills"
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

    errors = validate_backlog_draft_closures(tmp_path)

    assert [
        error for error in errors if error.startswith("E19 Strategy Core Draft:")
    ] == []


def test_deprecated_discarded_draft_is_accepted(tmp_path: Path) -> None:
    target = tmp_path / "work/epics/e21-transcript-intelligence-for-escala"
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

    errors = validate_backlog_draft_closures(tmp_path)

    assert [
        error
        for error in errors
        if error.startswith("E21 Transcript Intelligence Draft:")
    ] == []


def test_discarded_draft_requires_no_complete_tag(tmp_path: Path) -> None:
    target = tmp_path / "work/epics/e19-strategy-core-skills"
    target.mkdir(parents=True)
    (target / "scope.md").write_text(
        """# E19

**Status:** Superseded/Discarded

## Backlog Closure Review

Current backlog action: no active epic remains here.
""",
        encoding="utf-8",
    )

    errors = validate_backlog_draft_closures(tmp_path)

    assert (
        "E19 Strategy Core Draft: missing required evidence phrase: no `complete` tag"
    ) in errors
