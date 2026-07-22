"""Tests for the installer-machine workspace authority contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from escala_server.workspace.authority import (
    WorkspaceConfig,
    render_workspace_receipt_json,
    validate_workspace,
)


def _valid_config(tmp_path: Path) -> WorkspaceConfig:
    return WorkspaceConfig(
        platform="macos",
        data_root=tmp_path / "data",
        database_path=tmp_path / "data" / "escala.sqlite",
        exchange_root=tmp_path / "exchange",
    )


def test_valid_workspace_receipt_declares_local_authority_without_paths(
    tmp_path: Path,
) -> None:
    receipt = validate_workspace(_valid_config(tmp_path))

    assert receipt.status == "pass"
    assert receipt.runtime_authority == "installer_machine"
    assert receipt.data_authority == "installer_machine"
    assert receipt.team_exchange == "ordinary_filesystem_documents_only"
    assert receipt.authoritative_sqlite_sync == "forbidden"
    assert receipt.findings == ()

    serialized = render_workspace_receipt_json(receipt)
    assert str(tmp_path) not in serialized
    assert "escala.sqlite" not in serialized
    payload = json.loads(serialized)
    assert payload["status"] == "pass"
    assert payload["checks"]


def test_workspace_config_forbids_unknown_fields(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        WorkspaceConfig(
            platform="macos",
            data_root=tmp_path / "data",
            database_path=tmp_path / "data" / "escala.sqlite",
            exchange_root=tmp_path / "exchange",
            cloud_database_url="https://example.invalid",  # type: ignore[call-arg]
        )


def test_workspace_config_rejects_unsupported_schema_version(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValidationError):
        WorkspaceConfig(
            schema_version=2,  # type: ignore[arg-type]
            platform="macos",
            data_root=tmp_path / "data",
            database_path=tmp_path / "data" / "escala.sqlite",
            exchange_root=tmp_path / "exchange",
        )


def test_workspace_config_accepts_windows_platform_shape(tmp_path: Path) -> None:
    config = WorkspaceConfig(
        platform="windows",
        data_root=tmp_path / "data",
        database_path=tmp_path / "data" / "escala.sqlite",
        exchange_root=tmp_path / "exchange",
    )

    assert validate_workspace(config).status == "pass"
