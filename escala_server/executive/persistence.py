"""Atomic local persistence for E40 derived execution state."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile

from ..workspace.authority import (
    WorkspaceAuthorityError,
    WorkspaceConfig,
    validate_workspace,
)
from .models import ExecutionState, StateReceipt


class PersistenceError(ValueError):
    """Safe state read/write error without machine paths in its message."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


_STATE_RELATIVE_PATH = ".escala-executive/execution.json"


def save_execution_state(
    config: WorkspaceConfig, state: ExecutionState
) -> StateReceipt:
    """Validate authority and atomically persist a deterministic state snapshot."""

    _validate_authority(config)
    output_dir = (
        config.data_root.expanduser().resolve(strict=False) / ".escala-executive"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    content = (
        json.dumps(
            state.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    _atomic_write(output_dir / "execution.json", content)
    return StateReceipt(
        path=_STATE_RELATIVE_PATH,
        content_sha256=hashlib.sha256(content).hexdigest(),
    )


def load_execution_state(config: WorkspaceConfig) -> ExecutionState | None:
    """Validate authority and read the local snapshot, failing on corruption."""

    _validate_authority(config)
    path = config.data_root.expanduser().resolve(strict=False) / _STATE_RELATIVE_PATH
    if not path.is_file():
        return None
    try:
        return ExecutionState.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        raise PersistenceError("state_invalid") from None


def save_state(config: WorkspaceConfig, state: ExecutionState) -> StateReceipt:
    """Compatibility alias for callers that use the shorter state name."""

    return save_execution_state(config, state)


def _validate_authority(config: WorkspaceConfig) -> None:
    receipt = validate_workspace(config)
    if receipt.status != "pass":
        code = receipt.findings[0].code if receipt.findings else "workspace_invalid"
        raise WorkspaceAuthorityError(code)


def _atomic_write(path: Path, content: bytes) -> None:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
