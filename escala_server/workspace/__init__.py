"""Installer-machine workspace contracts for the local Escala runtime."""

from .authority import (
    WorkspaceAuthorityError,
    WorkspaceConfig,
    WorkspaceReceipt,
    init_authoritative_db,
    render_workspace_receipt_json,
    render_workspace_receipt_markdown,
    validate_workspace,
)
from .ingestion import (
    FormatCapability,
    SourceIdentity,
    SourceIngestionError,
    SourceRegistry,
    build_source_identity,
)

__all__ = [
    "WorkspaceAuthorityError",
    "WorkspaceConfig",
    "WorkspaceReceipt",
    "init_authoritative_db",
    "render_workspace_receipt_json",
    "render_workspace_receipt_markdown",
    "validate_workspace",
    "FormatCapability",
    "SourceIdentity",
    "SourceIngestionError",
    "SourceRegistry",
    "build_source_identity",
]
