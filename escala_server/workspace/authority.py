"""Strict local workspace authority contracts.

This module owns the product boundary between installer-local authoritative
state and an ordinary filesystem document exchange.  Path containment and the
pre-initialization database guard are added in subsequent S37.1 tasks; the
initial contract deliberately keeps receipts free of machine paths.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    """Return a safe baseline receipt for a workspace configuration.

    Containment and symlink checks are intentionally introduced by T2.  This
    first task establishes the closed, local-only contract and its redacted
    output shape.
    """

    checks = (
        WorkspaceCheck(id="config_schema", status="pass"),
        WorkspaceCheck(id="local_authority", status="pass"),
        WorkspaceCheck(id="exchange_role", status="pass"),
    )
    return WorkspaceReceipt(status="pass", checks=checks)


def render_workspace_receipt_json(receipt: WorkspaceReceipt) -> str:
    """Render a deterministic JSON receipt with no internal path fields."""

    return json.dumps(
        receipt.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
