from __future__ import annotations

from pathlib import Path
import subprocess

import pytest
from pydantic import ValidationError

from validators.repository_truth import (
    FindingCode,
    load_repository_truth_policy,
    repository_truth_policy_hash,
    verify_repository,
)


VALID_POLICY = """\
schema_version: 1
canonical_source:
  role: private_canonical
  remote: origin
  development_branch: main
  required_upstream: origin/main
allowed_remotes:
  - origin
disallowed_remotes:
  - gitlab
public_distribution:
  role: generated_artifact
  mode: allowlisted_clean_export
  automatic_mirror: false
"""


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _write_policy(tmp_path: Path, content: str = VALID_POLICY) -> Path:
    policy_path = tmp_path / "repository-truth.yaml"
    policy_path.write_text(content, encoding="utf-8")
    return policy_path


def _create_synchronized_repository(tmp_path: Path) -> tuple[Path, Path]:
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    subprocess.run(
        ["git", "init", "--bare", "--initial-branch=main", str(remote)],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "init", "--initial-branch=main", str(work)],
        check=True,
        capture_output=True,
        text=True,
    )
    _git(work, "config", "user.email", "tests@example.invalid")
    _git(work, "config", "user.name", "Repository Truth Tests")
    (work / "README.md").write_text("initial\n", encoding="utf-8")
    _git(work, "add", "README.md")
    _git(work, "commit", "-m", "initial")
    _git(work, "remote", "add", "origin", str(remote))
    _git(work, "push", "-u", "origin", "main")
    return work, remote


def _finding_codes(receipt: object) -> set[FindingCode]:
    return {finding.code for finding in receipt.findings}  # type: ignore[attr-defined]


def test_policy_loads_strict_roles_and_has_stable_hash(tmp_path: Path) -> None:
    policy = load_repository_truth_policy(_write_policy(tmp_path))

    assert policy.schema_version == 1
    assert policy.canonical_source.role == "private_canonical"
    assert policy.canonical_source.remote == "origin"
    assert policy.canonical_source.required_upstream == "origin/main"
    assert policy.allowed_remotes == ["origin"]
    assert policy.disallowed_remotes == ["gitlab"]
    assert policy.public_distribution.role == "generated_artifact"
    assert policy.public_distribution.mode == "allowlisted_clean_export"
    assert policy.public_distribution.automatic_mirror is False
    assert repository_truth_policy_hash(policy) == repository_truth_policy_hash(
        load_repository_truth_policy(_write_policy(tmp_path))
    )
    assert len(repository_truth_policy_hash(policy)) == 64


@pytest.mark.parametrize(
    "invalid_fragment",
    [
        "unknown_root: true\n",
        "canonical_source:\n  role: public\n  remote: origin\n"
        "  development_branch: main\n  required_upstream: origin/main\n",
        "public_distribution:\n  role: generated_artifact\n  mode: mirror\n"
        "  automatic_mirror: false\n",
    ],
)
def test_policy_rejects_unknown_fields_and_roles(
    tmp_path: Path,
    invalid_fragment: str,
) -> None:
    if invalid_fragment.startswith("unknown_root"):
        content = VALID_POLICY + invalid_fragment
    elif invalid_fragment.startswith("canonical_source"):
        content = VALID_POLICY.replace(
            "canonical_source:\n  role: private_canonical\n  remote: origin\n"
            "  development_branch: main\n  required_upstream: origin/main\n",
            invalid_fragment,
        )
    else:
        content = VALID_POLICY.replace(
            "public_distribution:\n  role: generated_artifact\n"
            "  mode: allowlisted_clean_export\n  automatic_mirror: false\n",
            invalid_fragment,
        )

    with pytest.raises(ValidationError):
        load_repository_truth_policy(_write_policy(tmp_path, content))


@pytest.mark.parametrize(
    "content",
    [
        VALID_POLICY.replace(
            "required_upstream: origin/main", "required_upstream: origin/dev"
        ),
        VALID_POLICY.replace("  - origin\n", "  - origin\n  - origin\n", 1),
        VALID_POLICY.replace(
            "disallowed_remotes:\n  - gitlab", "disallowed_remotes:\n  - origin"
        ),
        VALID_POLICY.replace("remote: origin", "remote: unsafe@remote", 1),
    ],
)
def test_policy_rejects_incoherent_or_unsafe_configuration(
    tmp_path: Path,
    content: str,
) -> None:
    with pytest.raises(ValidationError):
        load_repository_truth_policy(_write_policy(tmp_path, content))


def test_synchronized_repository_passes(tmp_path: Path) -> None:
    work, _ = _create_synchronized_repository(tmp_path)
    policy = load_repository_truth_policy(_write_policy(tmp_path))

    receipt = verify_repository(work, policy)

    assert receipt.status == "pass"
    assert receipt.checked_branch == "main"
    assert receipt.upstream == "origin/main"
    assert receipt.behind == 0
    assert receipt.ahead == 0
    assert receipt.remotes == ["origin"]
    assert receipt.findings == []
    assert all(check.status == "pass" for check in receipt.checks)


def test_missing_canonical_remote_fails_closed(tmp_path: Path) -> None:
    work, _ = _create_synchronized_repository(tmp_path)
    policy = load_repository_truth_policy(_write_policy(tmp_path))
    _git(work, "remote", "remove", "origin")

    receipt = verify_repository(work, policy)

    assert receipt.status == "fail"
    assert FindingCode.MISSING_CANONICAL_REMOTE in _finding_codes(receipt)


def test_missing_upstream_fails_closed(tmp_path: Path) -> None:
    work, _ = _create_synchronized_repository(tmp_path)
    policy = load_repository_truth_policy(_write_policy(tmp_path))
    _git(work, "branch", "--unset-upstream", "main")

    receipt = verify_repository(work, policy)

    assert receipt.status == "fail"
    assert FindingCode.MISSING_UPSTREAM in _finding_codes(receipt)


def test_wrong_upstream_fails_closed(tmp_path: Path) -> None:
    work, remote = _create_synchronized_repository(tmp_path)
    policy = load_repository_truth_policy(_write_policy(tmp_path))
    _git(work, "remote", "add", "backup", str(remote))
    _git(work, "fetch", "backup", "main")
    _git(work, "branch", "--set-upstream-to=backup/main", "main")

    receipt = verify_repository(work, policy)

    assert receipt.status == "fail"
    assert FindingCode.WRONG_UPSTREAM in _finding_codes(receipt)
    assert FindingCode.UNEXPECTED_REMOTE in _finding_codes(receipt)


def test_local_ahead_is_reported_as_divergence(tmp_path: Path) -> None:
    work, _ = _create_synchronized_repository(tmp_path)
    policy = load_repository_truth_policy(_write_policy(tmp_path))
    (work / "local.txt").write_text("local\n", encoding="utf-8")
    _git(work, "add", "local.txt")
    _git(work, "commit", "-m", "local ahead")

    receipt = verify_repository(work, policy)

    assert receipt.status == "fail"
    assert receipt.behind == 0
    assert receipt.ahead == 1
    assert FindingCode.BRANCH_DIVERGED in _finding_codes(receipt)


def test_remote_ahead_is_reported_as_divergence(tmp_path: Path) -> None:
    work, remote = _create_synchronized_repository(tmp_path)
    policy = load_repository_truth_policy(_write_policy(tmp_path))
    other = tmp_path / "other"
    subprocess.run(
        ["git", "clone", str(remote), str(other)],
        check=True,
        capture_output=True,
        text=True,
    )
    _git(other, "config", "user.email", "tests@example.invalid")
    _git(other, "config", "user.name", "Repository Truth Tests")
    (other / "remote.txt").write_text("remote\n", encoding="utf-8")
    _git(other, "add", "remote.txt")
    _git(other, "commit", "-m", "remote ahead")
    _git(other, "push", "origin", "main")
    _git(work, "fetch", "origin", "main")

    receipt = verify_repository(work, policy)

    assert receipt.status == "fail"
    assert receipt.behind == 1
    assert receipt.ahead == 0
    assert FindingCode.BRANCH_DIVERGED in _finding_codes(receipt)


def test_missing_remote_branch_fails_closed(tmp_path: Path) -> None:
    work, _ = _create_synchronized_repository(tmp_path)
    policy = load_repository_truth_policy(_write_policy(tmp_path))
    _git(work, "update-ref", "-d", "refs/remotes/origin/main")

    receipt = verify_repository(work, policy)

    assert receipt.status == "fail"
    assert FindingCode.MISSING_REMOTE_BRANCH in _finding_codes(receipt)


def test_missing_development_branch_fails_closed(tmp_path: Path) -> None:
    work, _ = _create_synchronized_repository(tmp_path)
    content = VALID_POLICY.replace(
        "development_branch: main", "development_branch: absent"
    )
    content = content.replace(
        "required_upstream: origin/main", "required_upstream: origin/absent"
    )
    policy = load_repository_truth_policy(_write_policy(tmp_path, content))

    receipt = verify_repository(work, policy)

    assert receipt.status == "fail"
    assert FindingCode.MISSING_BRANCH in _finding_codes(receipt)
