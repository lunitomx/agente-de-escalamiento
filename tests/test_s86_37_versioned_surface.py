"""S86.37: checks read what git versions, never local ignored leftovers.

Each test builds a throwaway git repository, leaves a bad case as an ignored
local file (it must not count) and then force-adds the same bad case (it must
fail again). That proves the checks still guard the versioned surface.
"""

from __future__ import annotations

import subprocess
from pathlib import Path, PurePosixPath

import pytest

from validators.adapter_parity import claude_public_skills, discoverable_legacy_aliases
from validators.governance_contract import load_closure_disposition_policy
from validators.scope_inventory import (
    ScopeInventory,
    ScopeInventoryError,
    validate_scope_inventory,
)
from tests.versioned_evidence import require_local_evidence
from validators.versioned_files import is_versioned, versioned_files

ROOT = Path(__file__).resolve().parents[1]
CLOSURE_PATH = ROOT / "governance/closure-dispositions.yaml"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _repo(tmp_path: Path, ignore: str) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / ".gitignore").write_text(ignore, encoding="utf-8")
    return repo


def _write(repo: Path, relative: str, text: str = "x\n") -> Path:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_versioned_files_skips_ignored_and_keeps_forced_and_new(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path, "work/\n")
    _write(repo, "work/local-only.md")
    _write(repo, "work/forced.md")
    _write(repo, "work/new-not-ignored.md")
    _write(repo, "notes/new.md")
    _git(repo, "add", "-f", "work/forced.md")

    found = versioned_files(repo, "work")
    assert found == (PurePosixPath("work/forced.md"),)
    assert versioned_files(repo, "notes") == (PurePosixPath("notes/new.md"),)


def test_versioned_files_drops_tracked_files_deleted_on_disk(tmp_path: Path) -> None:
    repo = _repo(tmp_path, "")
    _write(repo, "a/one.md")
    _git(repo, "add", "a/one.md")
    (repo / "a/one.md").unlink()
    assert versioned_files(repo, "a") == ()
    assert is_versioned(repo, "a/one.md")


def test_versioned_files_without_git_reads_the_whole_disk(tmp_path: Path) -> None:
    plain = tmp_path / "plain"
    _write(plain, "work/local.md")
    assert versioned_files(plain, "work") == (PurePosixPath("work/local.md"),)
    assert not is_versioned(plain, "work/local.md")


def _inventory() -> ScopeInventory:
    return ScopeInventory.model_validate(
        {
            "schema_version": 1,
            "legacy_scopes": [
                {
                    "path": "work/epics/e1-kept/scope.md",
                    "kind": "archived_epic",
                    "legacy_id": "E1",
                    "disposition": "complete",
                    "evidence": "scope-declared",
                }
            ],
        }
    )


def test_scope_inventory_ignores_local_scope_but_catches_versioned_one(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path, "work/\n")
    _write(repo, "work/epics/e1-kept/scope.md", "# viejo\n")
    _git(repo, "add", "-f", "work/epics/e1-kept/scope.md")
    _write(repo, "work/epics/e13-local/scope.md", "# local sin versionar\n")
    policy = load_closure_disposition_policy(CLOSURE_PATH)

    validate_scope_inventory(repo, _inventory(), policy)

    _git(repo, "add", "-f", "work/epics/e13-local/scope.md")
    with pytest.raises(ScopeInventoryError, match="e13-local"):
        validate_scope_inventory(repo, _inventory(), policy)


def test_legacy_alias_in_ignored_agent_root_is_local_but_versioned_one_counts(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path, ".agents/\n")
    _write(repo, ".agents/skills/scaleup-pulse/SKILL.md")
    assert discoverable_legacy_aliases(repo) == []

    _git(repo, "add", "-f", ".agents/skills/scaleup-pulse/SKILL.md")
    assert discoverable_legacy_aliases(repo) == [
        ".agents/skills/scaleup-pulse/SKILL.md"
    ]


def test_claude_surface_ignores_local_dev_skills_but_not_versioned_ones(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path, ".claude/skills/rai-*/\n")
    _write(repo, "escala-skills/escala/SKILL.md")
    (repo / ".claude/skills").mkdir(parents=True)
    (repo / ".claude/skills/escala").symlink_to("../../escala-skills/escala")
    _git(repo, "add", ".")
    _write(repo, ".claude/skills/rai-story-start/SKILL.md")
    assert claude_public_skills(repo) == ["escala"]

    _git(repo, "add", "-f", ".claude/skills/rai-story-start/SKILL.md")
    assert claude_public_skills(repo) == ["escala", "rai-story-start"]


def test_missing_unversioned_evidence_skips_with_reason(tmp_path: Path) -> None:
    repo = _repo(tmp_path, "work/\n")
    with pytest.raises(pytest.skip.Exception, match="no versionada"):
        require_local_evidence(repo, "work/evidence/queue.json")


def test_versioned_evidence_never_skips_even_if_deleted(tmp_path: Path) -> None:
    repo = _repo(tmp_path, "work/\n")
    _write(repo, "work/evidence/queue.json", "{}")
    _git(repo, "add", "-f", "work/evidence/queue.json")
    assert require_local_evidence(repo, "work/evidence/queue.json") == (
        repo / "work/evidence/queue.json"
    )
    (repo / "work/evidence/queue.json").unlink()
    assert require_local_evidence(repo, "work/evidence/queue.json") == (
        repo / "work/evidence/queue.json"
    )
