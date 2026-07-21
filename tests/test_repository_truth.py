from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest
from pydantic import ValidationError

from validators.repository_truth import (
    FindingCode,
    RepositoryTruthReceipt,
    fingerprint_repository,
    load_repository_truth_policy,
    render_repository_truth_json,
    render_repository_truth_markdown,
    repository_truth_policy_hash,
    verify_repository,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_repository_truth.py"


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


def _finding_codes(receipt: RepositoryTruthReceipt) -> set[FindingCode]:
    return {finding.code for finding in receipt.findings}


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


def test_credential_bearing_url_is_detected_without_disclosure(
    tmp_path: Path,
) -> None:
    work, remote = _create_synchronized_repository(tmp_path)
    policy = load_repository_truth_policy(_write_policy(tmp_path))
    sentinel = "S36-SECRET-SENTINEL"
    sensitive_url = f"https://{sentinel}@example.invalid/private.git"
    _git(work, "remote", "add", "gitlab", sensitive_url)

    receipt = verify_repository(work, policy)
    serialized_surfaces = (
        receipt.model_dump_json(),
        render_repository_truth_json(receipt),
        render_repository_truth_markdown(receipt),
        repr(receipt),
    )

    assert receipt.status == "fail"
    assert FindingCode.DISALLOWED_REMOTE in _finding_codes(receipt)
    assert FindingCode.CREDENTIAL_BEARING_REMOTE_URL in _finding_codes(receipt)
    for surface in serialized_surfaces:
        assert sentinel not in surface
        assert sensitive_url not in surface
        assert str(remote) not in surface


def test_normal_ssh_remote_identity_is_not_a_credential_finding(
    tmp_path: Path,
) -> None:
    work, _ = _create_synchronized_repository(tmp_path)
    policy = load_repository_truth_policy(_write_policy(tmp_path))
    _git(work, "remote", "set-url", "origin", "git@example.invalid:owner/repo.git")

    receipt = verify_repository(work, policy)

    assert receipt.status == "pass"
    assert FindingCode.CREDENTIAL_BEARING_REMOTE_URL not in _finding_codes(receipt)


def test_verifier_does_not_mutate_git_configuration_or_refs(tmp_path: Path) -> None:
    work, _ = _create_synchronized_repository(tmp_path)
    policy = load_repository_truth_policy(_write_policy(tmp_path))
    config_before = (work / ".git/config").read_bytes()
    refs_before = _git(work, "show-ref")

    verify_repository(work, policy)

    assert (work / ".git/config").read_bytes() == config_before
    assert _git(work, "show-ref") == refs_before


def test_fingerprint_omits_root_and_dirty_filenames(tmp_path: Path) -> None:
    work, _ = _create_synchronized_repository(tmp_path)
    private_filename = "private-customer-name.txt"
    (work / private_filename).write_text("not committed\n", encoding="utf-8")

    first = fingerprint_repository(work, label="public_candidate")
    second = fingerprint_repository(work, label="public_candidate")
    serialized = first.model_dump_json()

    assert first == second
    assert first.label == "public_candidate"
    assert first.branch == "main"
    assert first.dirty_entry_count == 1
    assert len(first.status_sha256) == 64
    assert str(work) not in serialized
    assert private_filename not in serialized


def test_receipt_renderers_are_deterministic(tmp_path: Path) -> None:
    work, _ = _create_synchronized_repository(tmp_path)
    policy = load_repository_truth_policy(_write_policy(tmp_path))
    receipt = verify_repository(work, policy)

    first_json = render_repository_truth_json(receipt)
    first_markdown = render_repository_truth_markdown(receipt)

    assert first_json == render_repository_truth_json(receipt)
    assert first_markdown == render_repository_truth_markdown(receipt)
    assert first_json.endswith("\n")
    assert first_markdown.endswith("\n")
    assert '"status": "pass"' in first_json
    assert "# Repository Truth Receipt" in first_markdown
    assert "- Status: `pass`" in first_markdown


def test_cli_passes_and_writes_byte_identical_receipts(tmp_path: Path) -> None:
    work, _ = _create_synchronized_repository(tmp_path)
    policy_path = _write_policy(tmp_path)
    json_output = tmp_path / "evidence" / "receipt.json"
    markdown_output = tmp_path / "evidence" / "receipt.md"
    command = [
        sys.executable,
        str(SCRIPT),
        "--repo",
        str(work),
        "--policy",
        str(policy_path),
        "--format",
        "json",
        "--json-output",
        str(json_output),
        "--markdown-output",
        str(markdown_output),
    ]

    first = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    first_json = json_output.read_bytes()
    first_markdown = markdown_output.read_bytes()
    second = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert first.returncode == 0
    assert second.returncode == 0
    assert first.stderr == ""
    assert first.stdout == second.stdout
    assert first_json == json_output.read_bytes()
    assert first_markdown == markdown_output.read_bytes()


def test_cli_failure_never_prints_sensitive_remote_value(tmp_path: Path) -> None:
    work, _ = _create_synchronized_repository(tmp_path)
    policy_path = _write_policy(tmp_path)
    sentinel = "S36-CLI-SECRET"
    sensitive_url = f"https://{sentinel}@example.invalid/private.git"
    _git(work, "remote", "add", "gitlab", sensitive_url)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo",
            str(work),
            "--policy",
            str(policy_path),
            "--format",
            "text",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    combined = result.stdout + result.stderr

    assert result.returncode == 1
    assert sentinel not in combined
    assert sensitive_url not in combined
    assert str(work) not in combined
    assert "credential_bearing_remote_url" in result.stdout


def test_command_failure_is_sanitized(tmp_path: Path) -> None:
    policy = load_repository_truth_policy(_write_policy(tmp_path))
    missing_repository = tmp_path / "private-local-path"

    receipt = verify_repository(missing_repository, policy)
    serialized = render_repository_truth_json(receipt)

    assert receipt.status == "fail"
    assert FindingCode.GIT_COMMAND_FAILED in _finding_codes(receipt)
    assert str(missing_repository) not in serialized
