"""Typed, read-only verification of canonical Git repository truth."""

from __future__ import annotations

from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

try:
    import yaml
except ImportError as exc:  # pragma: no cover - project dependency
    raise ImportError("PyYAML required: pip install pyyaml") from exc


_SAFE_REMOTE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SAFE_BRANCH_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
_COMMIT_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RepositoryRole(str, Enum):
    PRIVATE_CANONICAL = "private_canonical"
    GENERATED_ARTIFACT = "generated_artifact"


class DistributionMode(str, Enum):
    ALLOWLISTED_CLEAN_EXPORT = "allowlisted_clean_export"


class CheckStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"


class CheckId(str, Enum):
    CANONICAL_REMOTE = "canonical_remote"
    ALLOWED_REMOTES = "allowed_remotes"
    REMOTE_CREDENTIALS = "remote_credentials"
    BRANCH_EXISTS = "branch_exists"
    UPSTREAM = "upstream"
    REMOTE_BRANCH = "remote_branch"
    SYNCHRONIZED = "synchronized"


class FindingCode(str, Enum):
    INVALID_POLICY = "invalid_policy"
    GIT_COMMAND_FAILED = "git_command_failed"
    MISSING_CANONICAL_REMOTE = "missing_canonical_remote"
    UNEXPECTED_REMOTE = "unexpected_remote"
    DISALLOWED_REMOTE = "disallowed_remote"
    CREDENTIAL_BEARING_REMOTE_URL = "credential_bearing_remote_url"
    MISSING_BRANCH = "missing_branch"
    MISSING_UPSTREAM = "missing_upstream"
    WRONG_UPSTREAM = "wrong_upstream"
    MISSING_REMOTE_BRANCH = "missing_remote_branch"
    BRANCH_DIVERGED = "branch_diverged"


class CanonicalSource(_StrictModel):
    role: Literal[RepositoryRole.PRIVATE_CANONICAL]
    remote: str = Field(min_length=1, max_length=128)
    development_branch: str = Field(min_length=1, max_length=256)
    required_upstream: str = Field(min_length=3, max_length=385)

    @field_validator("remote")
    @classmethod
    def validate_remote(cls, value: str) -> str:
        return _validate_remote_name(value)

    @field_validator("development_branch")
    @classmethod
    def validate_development_branch(cls, value: str) -> str:
        return _validate_branch_name(value)

    @model_validator(mode="after")
    def validate_required_upstream(self) -> CanonicalSource:
        expected = f"{self.remote}/{self.development_branch}"
        if self.required_upstream != expected:
            raise ValueError(f"required_upstream must equal {expected!r}")
        return self


class PublicDistribution(_StrictModel):
    role: Literal[RepositoryRole.GENERATED_ARTIFACT]
    mode: Literal[DistributionMode.ALLOWLISTED_CLEAN_EXPORT]
    automatic_mirror: Literal[False]


class RepositoryTruthPolicy(_StrictModel):
    schema_version: Literal[1]
    canonical_source: CanonicalSource
    allowed_remotes: list[str] = Field(min_length=1)
    disallowed_remotes: list[str] = Field(default_factory=list)
    public_distribution: PublicDistribution

    @field_validator("allowed_remotes", "disallowed_remotes")
    @classmethod
    def validate_remote_lists(cls, value: list[str]) -> list[str]:
        validated = [_validate_remote_name(name) for name in value]
        if len(set(validated)) != len(validated):
            raise ValueError("remote lists must not contain duplicates")
        return sorted(validated)

    @model_validator(mode="after")
    def validate_remote_policy(self) -> RepositoryTruthPolicy:
        canonical = self.canonical_source.remote
        if canonical not in self.allowed_remotes:
            raise ValueError("canonical remote must be allowed")
        overlap = set(self.allowed_remotes) & set(self.disallowed_remotes)
        if overlap:
            raise ValueError("allowed and disallowed remotes must not overlap")
        return self


class RepositoryCheck(_StrictModel):
    id: CheckId
    status: CheckStatus


class RepositoryFinding(_StrictModel):
    code: FindingCode
    subject: str = Field(min_length=1, max_length=256)


class RepositoryTruthReceipt(_StrictModel):
    schema_version: Literal[1] = 1
    status: CheckStatus
    policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    verifier_source_commit: str | None = None
    checked_branch: str
    checked_branch_commit: str | None = None
    upstream: str | None = None
    behind: int | None = Field(default=None, ge=0)
    ahead: int | None = Field(default=None, ge=0)
    remotes: list[str]
    checks: list[RepositoryCheck]
    findings: list[RepositoryFinding]


class RepositoryFingerprint(_StrictModel):
    schema_version: Literal[1] = 1
    label: str = Field(min_length=1, max_length=128)
    head: str = Field(pattern=r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
    branch: str = Field(min_length=1, max_length=256)
    dirty_entry_count: int = Field(ge=0)
    status_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    worktree_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    config_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    index_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    refs_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


RepositoryTruthPolicy.model_rebuild()
RepositoryTruthReceipt.model_rebuild()
RepositoryFingerprint.model_rebuild()


def load_repository_truth_policy(policy_path: Path) -> RepositoryTruthPolicy:
    """Load and strictly validate a repository-truth YAML policy."""
    data: Any = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    return RepositoryTruthPolicy.model_validate(data)


def repository_truth_policy_hash(policy: RepositoryTruthPolicy) -> str:
    """Return a stable SHA-256 for normalized policy semantics."""
    payload = json.dumps(
        policy.model_dump(mode="json"),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def render_repository_truth_json(receipt: RepositoryTruthReceipt) -> str:
    """Render a deterministic JSON receipt with typed, sanitized fields only."""
    return (
        json.dumps(
            receipt.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def render_repository_truth_markdown(receipt: RepositoryTruthReceipt) -> str:
    """Render a deterministic human-readable receipt without local paths."""
    lines = [
        "# Repository Truth Receipt",
        "",
        f"- Status: `{receipt.status.value}`",
        f"- Policy SHA-256: `{receipt.policy_sha256}`",
        f"- Verifier source commit: `{receipt.verifier_source_commit or 'unavailable'}`",
        f"- Checked branch: `{receipt.checked_branch}`",
        f"- Checked branch commit: `{receipt.checked_branch_commit or 'unavailable'}`",
        f"- Upstream: `{receipt.upstream or 'unavailable'}`",
        f"- Behind / ahead: `{_count_label(receipt.behind)} / {_count_label(receipt.ahead)}`",
        f"- Remotes: `{', '.join(receipt.remotes) or 'none'}`",
        "",
        "## Checks",
        "",
    ]
    lines.extend(
        f"- `{check.id.value}`: `{check.status.value}`" for check in receipt.checks
    )
    lines.extend(["", "## Findings", ""])
    if receipt.findings:
        lines.extend(
            f"- `{finding.code.value}`: `{finding.subject}`"
            for finding in receipt.findings
        )
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def write_repository_truth_receipts(
    receipt: RepositoryTruthReceipt,
    *,
    json_output: Path | None = None,
    markdown_output: Path | None = None,
) -> None:
    """Write only explicitly requested deterministic receipt files."""
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(render_repository_truth_json(receipt), encoding="utf-8")
    if markdown_output is not None:
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(
            render_repository_truth_markdown(receipt),
            encoding="utf-8",
        )


def fingerprint_repository(
    repository_root: Path,
    *,
    label: str,
) -> RepositoryFingerprint:
    """Return a path- and filename-free fingerprint of repository state."""
    safe_label = _validate_branch_name(label)
    head = _read_commit(repository_root, "HEAD")
    branch_result = _run_git(repository_root, "symbolic-ref", "--short", "HEAD")
    status_result = _run_git(repository_root, "status", "--porcelain=v1", "-z")
    config_result = _run_git(repository_root, "config", "--local", "--list", "--null")
    index_result = _run_git(repository_root, "ls-files", "--stage", "-z")
    refs_result = _run_git(repository_root, "show-ref")
    if (
        head is None
        or status_result is None
        or config_result is None
        or index_result is None
        or refs_result is None
    ):
        raise ValueError("repository fingerprint failed")
    branch = _safe_label(branch_result) if branch_result else "detached"
    entries = [entry for entry in status_result.split("\0") if entry]
    return RepositoryFingerprint(
        label=safe_label,
        head=head,
        branch=branch,
        dirty_entry_count=len(entries),
        status_sha256=_text_sha256(status_result),
        worktree_sha256=_worktree_sha256(repository_root),
        config_sha256=_text_sha256(config_result),
        index_sha256=_text_sha256(index_result),
        refs_sha256=_text_sha256(refs_result),
    )


def verify_repository(
    repository_root: Path,
    policy: RepositoryTruthPolicy,
) -> RepositoryTruthReceipt:
    """Observe Git repository truth without mutating repository state."""
    checks: list[RepositoryCheck] = []
    findings: list[RepositoryFinding] = []
    canonical = policy.canonical_source

    head_commit = _read_commit(repository_root, "HEAD")

    remote_result = _run_git(repository_root, "remote")
    if remote_result is None:
        raw_remotes: list[str] = []
        findings.append(_finding(FindingCode.GIT_COMMAND_FAILED, "remote_inventory"))
    else:
        raw_remotes = sorted(line for line in remote_result.splitlines() if line)
    safe_remotes = sorted(_safe_label(name) for name in raw_remotes)

    canonical_present = canonical.remote in raw_remotes
    checks.append(_check(CheckId.CANONICAL_REMOTE, canonical_present))
    if not canonical_present:
        findings.append(
            _finding(FindingCode.MISSING_CANONICAL_REMOTE, canonical.remote)
        )

    remotes_allowed = remote_result is not None
    for remote in raw_remotes:
        if remote in policy.disallowed_remotes:
            remotes_allowed = False
            findings.append(_finding(FindingCode.DISALLOWED_REMOTE, remote))
        elif remote not in policy.allowed_remotes:
            remotes_allowed = False
            findings.append(_finding(FindingCode.UNEXPECTED_REMOTE, remote))
    checks.append(_check(CheckId.ALLOWED_REMOTES, remotes_allowed))

    credential_remotes = _credential_bearing_remote_names(repository_root)
    credentials_clear = credential_remotes is not None and not credential_remotes
    if credential_remotes is None:
        findings.append(_finding(FindingCode.GIT_COMMAND_FAILED, "remote_url_check"))
    else:
        for remote in sorted(credential_remotes):
            findings.append(_finding(FindingCode.CREDENTIAL_BEARING_REMOTE_URL, remote))
    checks.append(_check(CheckId.REMOTE_CREDENTIALS, credentials_clear))

    checked_branch = canonical.development_branch
    branch_commit = _read_commit(
        repository_root,
        f"refs/heads/{canonical.development_branch}",
    )
    branch_exists = branch_commit is not None
    checks.append(_check(CheckId.BRANCH_EXISTS, branch_exists))
    if not branch_exists:
        findings.append(_finding(FindingCode.MISSING_BRANCH, checked_branch))

    remote_branch_exists = False
    if canonical_present:
        remote_branch_exists = _git_ref_exists(
            repository_root,
            f"refs/remotes/{canonical.remote}/{canonical.development_branch}",
        )
    checks.append(_check(CheckId.REMOTE_BRANCH, remote_branch_exists))
    if not remote_branch_exists:
        findings.append(
            _finding(FindingCode.MISSING_REMOTE_BRANCH, canonical.required_upstream)
        )

    upstream: str | None = None
    upstream_correct = False
    if branch_exists:
        upstream_result = _run_git(
            repository_root,
            "rev-parse",
            "--abbrev-ref",
            f"{canonical.development_branch}@{{upstream}}",
        )
        if upstream_result:
            upstream = _safe_label(upstream_result)
            upstream_correct = upstream_result == canonical.required_upstream
            if not upstream_correct:
                findings.append(
                    _finding(FindingCode.WRONG_UPSTREAM, canonical.development_branch)
                )
        else:
            findings.append(
                _finding(FindingCode.MISSING_UPSTREAM, canonical.development_branch)
            )
    checks.append(_check(CheckId.UPSTREAM, upstream_correct))

    behind: int | None = None
    ahead: int | None = None
    synchronized = False
    if branch_exists and remote_branch_exists and upstream_correct:
        counts_result = _run_git(
            repository_root,
            "rev-list",
            "--left-right",
            "--count",
            f"{canonical.required_upstream}...{canonical.development_branch}",
        )
        if counts_result is None:
            findings.append(
                _finding(FindingCode.GIT_COMMAND_FAILED, "divergence_check")
            )
        else:
            parsed_counts = _parse_divergence_counts(counts_result)
            if parsed_counts is None:
                findings.append(
                    _finding(FindingCode.GIT_COMMAND_FAILED, "divergence_check")
                )
            else:
                behind, ahead = parsed_counts
                synchronized = behind == 0 and ahead == 0
                if not synchronized:
                    findings.append(
                        _finding(FindingCode.BRANCH_DIVERGED, checked_branch)
                    )
    checks.append(_check(CheckId.SYNCHRONIZED, synchronized))

    status = (
        CheckStatus.PASS
        if all(check.status is CheckStatus.PASS for check in checks) and not findings
        else CheckStatus.FAIL
    )
    return RepositoryTruthReceipt(
        status=status,
        policy_sha256=repository_truth_policy_hash(policy),
        verifier_source_commit=head_commit,
        checked_branch=checked_branch,
        checked_branch_commit=branch_commit,
        upstream=upstream,
        behind=behind,
        ahead=ahead,
        remotes=safe_remotes,
        checks=checks,
        findings=findings,
    )


def _validate_remote_name(value: str) -> str:
    if not _SAFE_REMOTE_PATTERN.fullmatch(value):
        raise ValueError("unsafe Git remote name")
    return value


def _validate_branch_name(value: str) -> str:
    invalid = (
        not _SAFE_BRANCH_PATTERN.fullmatch(value)
        or ".." in value
        or "//" in value
        or "@{" in value
        or value.endswith(("/", ".", ".lock"))
    )
    if invalid:
        raise ValueError("unsafe Git branch name")
    return value


def _safe_label(value: str) -> str:
    if (
        _SAFE_BRANCH_PATTERN.fullmatch(value)
        and ".." not in value
        and "@{" not in value
    ):
        return value
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"redacted-{digest}"


def _safe_commit(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    return normalized if _COMMIT_PATTERN.fullmatch(normalized) else None


def _run_git(repository_root: Path, *arguments: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository_root), *arguments],
            check=False,
            capture_output=True,
            env=_read_only_git_environment(),
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _credential_bearing_remote_names(repository_root: Path) -> set[str] | None:
    """Inspect URL values in memory and return remote names only."""
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repository_root),
                "config",
                "--get-regexp",
                r"^remote\..*\.url$",
            ],
            check=False,
            capture_output=True,
            env=_read_only_git_environment(),
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode == 1:
        return set()
    if result.returncode != 0:
        return None

    credential_remotes: set[str] = set()
    for line in result.stdout.splitlines():
        try:
            key, remote_url = line.split(maxsplit=1)
        except ValueError:
            return None
        match = re.fullmatch(r"remote\.(.+)\.url", key)
        if match is None:
            return None
        if _has_embedded_http_credentials(remote_url):
            credential_remotes.add(match.group(1))
    return credential_remotes


def _has_embedded_http_credentials(remote_url: str) -> bool:
    try:
        parsed = urlsplit(remote_url)
    except ValueError:
        authority = remote_url.partition("://")[2].partition("/")[0]
        return remote_url.startswith(("http://", "https://")) and "@" in authority
    return parsed.scheme.lower() in {"http", "https"} and parsed.username is not None


def _read_commit(repository_root: Path, reference: str) -> str | None:
    result = _run_git(repository_root, "rev-parse", "--verify", reference)
    return _safe_commit(result)


def _git_ref_exists(repository_root: Path, reference: str) -> bool:
    return _run_git(repository_root, "show-ref", "--verify", reference) is not None


def _parse_divergence_counts(value: str) -> tuple[int, int] | None:
    parts = value.split()
    if len(parts) != 2:
        return None
    try:
        behind, ahead = (int(part) for part in parts)
    except ValueError:
        return None
    if behind < 0 or ahead < 0:
        return None
    return behind, ahead


def _check(check_id: CheckId, passed: bool) -> RepositoryCheck:
    return RepositoryCheck(
        id=check_id,
        status=CheckStatus.PASS if passed else CheckStatus.FAIL,
    )


def _finding(code: FindingCode, subject: str) -> RepositoryFinding:
    return RepositoryFinding(code=code, subject=_safe_label(subject))


def _count_label(value: int | None) -> str:
    return str(value) if value is not None else "unavailable"


def _read_only_git_environment() -> dict[str, str]:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    environment["GIT_TERMINAL_PROMPT"] = "0"
    return environment


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _worktree_sha256(repository_root: Path) -> str:
    """Hash names, types, modes, links, and bytes outside the root .git dir."""
    root = repository_root.resolve()
    if not root.is_dir():
        raise ValueError("repository fingerprint failed")

    digest = hashlib.sha256()
    try:
        for current_root, directory_names, file_names in os.walk(
            root,
            topdown=True,
            followlinks=False,
        ):
            current_path = Path(current_root)
            if current_path == root:
                directory_names[:] = [
                    name for name in directory_names if name != ".git"
                ]
                file_names = [name for name in file_names if name != ".git"]
            directory_names.sort()
            file_names.sort()

            for name in directory_names:
                path = current_path / name
                _hash_path_entry(digest, root, path)
            for name in file_names:
                path = current_path / name
                _hash_path_entry(digest, root, path)
    except OSError:
        raise ValueError("repository fingerprint failed") from None
    return digest.hexdigest()


def _hash_path_entry(
    digest: Any,
    root: Path,
    path: Path,
) -> None:
    relative = path.relative_to(root).as_posix().encode("utf-8")
    mode = path.lstat().st_mode & 0o7777
    digest.update(len(relative).to_bytes(8, "big"))
    digest.update(relative)
    digest.update(mode.to_bytes(4, "big"))

    if path.is_symlink():
        digest.update(b"L")
        target = os.readlink(path).encode("utf-8")
        digest.update(len(target).to_bytes(8, "big"))
        digest.update(target)
        return
    if path.is_dir():
        digest.update(b"D")
        return
    if path.is_file():
        digest.update(b"F")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return
    digest.update(b"O")
