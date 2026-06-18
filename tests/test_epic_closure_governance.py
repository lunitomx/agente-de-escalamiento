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

    assert any("E24: expected status 'partial/backlog'" in error for error in errors)


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
        "E19 Strategy Core Draft: expected status 'backlog/not completed'" in error
        for error in errors
    )
