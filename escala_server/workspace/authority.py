"""Strict local workspace authority contracts.

This module owns the product boundary between installer-local authoritative
state and an ordinary filesystem document exchange. Receipts deliberately keep
machine paths internal and expose only stable role and finding codes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


_InitializerResult = TypeVar("_InitializerResult")


class _StrictModel(BaseModel):
    """Base for immutable, closed contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class WorkspaceAuthorityError(ValueError):
    """Safe failure raised when a workspace cannot be trusted."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class WorkspaceConfig(_StrictModel):
    """Installer-local roots and the logical document exchange role."""

    schema_version: Literal[1] = 1
    platform: Literal["macos", "windows"]
    data_root: Path
    database_path: Path
    exchange_root: Path

    @field_validator("data_root", "database_path", "exchange_root", mode="before")
    @classmethod
    def validate_path_input(cls, value: object) -> object:
        """Reject empty or NUL-bearing path inputs before Path coercion."""

        if value is None:
            raise ValueError("workspace path is required")
        if isinstance(value, str) and (not value.strip() or "\x00" in value):
            raise ValueError("workspace path is invalid")
        return value


class WorkspaceCheck(_StrictModel):
    """One deterministic, non-sensitive workspace check result."""

    id: str = Field(min_length=1, max_length=80)
    status: Literal["pass", "fail"]


class SafeFinding(_StrictModel):
    """A stable finding code without a path, value, or raw exception."""

    code: str = Field(min_length=1, max_length=100)


class WorkspaceReceipt(_StrictModel):
    """Redacted authority result suitable for JSON or Markdown output."""

    schema_version: Literal[1] = 1
    status: Literal["pass", "fail"]
    checks: tuple[WorkspaceCheck, ...] = ()
    findings: tuple[SafeFinding, ...] = ()
    runtime_authority: Literal["installer_machine"] = "installer_machine"
    data_authority: Literal["installer_machine"] = "installer_machine"
    team_exchange: Literal["ordinary_filesystem_documents_only"] = (
        "ordinary_filesystem_documents_only"
    )
    authoritative_sqlite_sync: Literal["forbidden"] = "forbidden"


def validate_workspace(config: WorkspaceConfig) -> WorkspaceReceipt:
    """Validate local roots and return a redacted deterministic receipt."""

    findings: list[str] = []
    try:
        data_root = _resolve(config.data_root)
        database_path = _resolve(config.database_path)
        exchange_root = _resolve(config.exchange_root)
    except (OSError, RuntimeError):
        findings.append("path_resolution_failed")
        return _build_receipt(findings)

    roots_overlap = _paths_overlap(data_root, exchange_root, config.platform)
    if roots_overlap:
        findings.append("ambiguous_root")

    if not roots_overlap:
        database_in_exchange = _is_contained(
            database_path, exchange_root, config.platform
        )
        if database_in_exchange:
            if _path_has_symlink(config.database_path):
                findings.append("symlink_inside_exchange")
            else:
                findings.append("authoritative_sqlite_sync_forbidden")
        elif not _is_contained(database_path, data_root, config.platform):
            findings.append("database_outside_data_root")

    return _build_receipt(findings)


def init_authoritative_db(
    config: WorkspaceConfig,
    initializer: Callable[[str], _InitializerResult],
) -> _InitializerResult:
    """Validate authority before invoking an existing SQLite initializer."""

    receipt = validate_workspace(config)
    if receipt.status != "pass":
        code = receipt.findings[0].code if receipt.findings else "workspace_invalid"
        raise WorkspaceAuthorityError(code)
    return initializer(str(_resolve(config.database_path)))


def _resolve(path: Path) -> Path:
    """Resolve a path without requiring a file or directory to exist."""

    return path.expanduser().resolve(strict=False)


def _is_contained(candidate: Path, parent: Path, platform: str) -> bool:
    """Return whether candidate equals or is below parent after resolution."""

    if platform == "windows":
        candidate_text = str(candidate).replace("/", "\\").rstrip("\\").casefold()
        parent_text = str(parent).replace("/", "\\").rstrip("\\").casefold()
        return candidate_text == parent_text or candidate_text.startswith(
            f"{parent_text}\\"
        )
    return candidate == parent or parent in candidate.parents


def _paths_overlap(first: Path, second: Path, platform: str) -> bool:
    """Return whether either root contains the other."""

    return _is_contained(first, second, platform) or _is_contained(
        second, first, platform
    )


def _path_has_symlink(path: Path) -> bool:
    """Detect a symlink in the path's existing or prospective parents."""

    current = path.expanduser()
    for candidate in (current, *current.parents):
        try:
            if candidate.is_symlink():
                return True
        except OSError:
            return True
    return False


def _build_receipt(codes: list[str]) -> WorkspaceReceipt:
    """Build sorted checks/findings without copying sensitive inputs."""

    unique_codes = tuple(sorted(set(codes)))
    failure_set = set(unique_codes)
    local_failure = bool(
        failure_set
        & {
            "ambiguous_root",
            "database_outside_data_root",
            "path_resolution_failed",
        }
    )
    database_failure = bool(
        failure_set
        & {
            "authoritative_sqlite_sync_forbidden",
            "database_outside_data_root",
            "path_resolution_failed",
            "symlink_inside_exchange",
        }
    )
    checks = (
        WorkspaceCheck(id="config_schema", status="pass"),
        WorkspaceCheck(
            id="local_authority", status="fail" if local_failure else "pass"
        ),
        WorkspaceCheck(
            id="database_location", status="fail" if database_failure else "pass"
        ),
        WorkspaceCheck(id="exchange_role", status="pass"),
    )
    return WorkspaceReceipt(
        status="fail" if unique_codes else "pass",
        checks=checks,
        findings=tuple(SafeFinding(code=code) for code in unique_codes),
    )


def render_workspace_receipt_json(receipt: WorkspaceReceipt) -> str:
    """Render a deterministic JSON receipt with no internal path fields."""

    return json.dumps(
        receipt.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def render_workspace_receipt_markdown(receipt: WorkspaceReceipt) -> str:
    """Render the same safe receipt fields as bounded human-readable Markdown."""

    lines = [
        "# Workspace Authority Receipt",
        "",
        f"- status: {receipt.status}",
        f"- runtime_authority: {receipt.runtime_authority}",
        f"- data_authority: {receipt.data_authority}",
        f"- team_exchange: {receipt.team_exchange}",
        f"- authoritative_sqlite_sync: {receipt.authoritative_sqlite_sync}",
        "",
        "## Checks",
    ]
    lines.extend(f"- {check.id}: {check.status}" for check in receipt.checks)
    lines.append("")
    lines.append("## Findings")
    if receipt.findings:
        lines.extend(f"- {finding.code}" for finding in receipt.findings)
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"
