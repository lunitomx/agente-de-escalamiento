from __future__ import annotations

from pathlib import Path

from validators.epic_closure import validate_audited_epic_closures


ROOT = Path(__file__).resolve().parents[1]


def test_audited_epic_closures_are_governance_consistent() -> None:
    assert validate_audited_epic_closures(ROOT) == []


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


def test_active_epic_cannot_claim_complete_tag(tmp_path: Path) -> None:
    target = tmp_path / "work/epics/e31-scaleup-pipeline-runtime-runner"
    target.mkdir(parents=True)
    (target / "scope.md").write_text(
        """---
status: "active"
---

# E31

Do not use epic/e31-complete.
""",
        encoding="utf-8",
    )

    errors = validate_audited_epic_closures(tmp_path)

    assert any("E31: forbidden closure phrase present" in error for error in errors)
