"""TDD contract tests for the local filesystem inbox."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from escala_server.workspace.authority import WorkspaceConfig
from escala_server.workspace.inbox import (
    InboxConfig,
    InboxError,
    InboxLedger,
    InboxLedgerEntry,
    load_inbox_ledger,
    scan_inbox,
    save_inbox_ledger,
)


def _config(tmp_path: Path) -> WorkspaceConfig:
    return WorkspaceConfig(
        platform="macos",
        data_root=tmp_path / "data",
        database_path=tmp_path / "data" / "escala.sqlite",
        exchange_root=tmp_path / "exchange",
    )


def test_ledger_round_trip_is_local_and_deterministic(tmp_path: Path) -> None:
    config = _config(tmp_path)
    entry = InboxLedgerEntry(
        source_id="a" * 64,
        relative_path="ventas.csv",
        disposition="accepted",
        codes=(),
    )
    ledger = InboxLedger(entries=(entry,))

    save_inbox_ledger(config, ledger)
    first_bytes = (config.data_root / ".escala-inbox-ledger.json").read_bytes()
    loaded = load_inbox_ledger(config)
    second_bytes = (config.data_root / ".escala-inbox-ledger.json").read_bytes()

    assert loaded == ledger
    assert first_bytes == second_bytes
    assert str(tmp_path) not in first_bytes.decode("utf-8")
    assert loaded.source_ids == ("a" * 64,)


def test_corrupt_ledger_fails_closed(tmp_path: Path) -> None:
    config = _config(tmp_path)
    config.data_root.mkdir()
    (config.data_root / ".escala-inbox-ledger.json").write_text(
        "{not-json", encoding="utf-8"
    )

    with pytest.raises(InboxError, match="ledger_corrupt"):
        load_inbox_ledger(config)


def test_ledger_contract_forbids_machine_paths() -> None:
    with pytest.raises(ValidationError):
        InboxLedgerEntry(
            source_id="b" * 64,
            relative_path="ventas.csv",
            disposition="accepted",
            codes=(),
            absolute_path="/private/company/ventas.csv",  # type: ignore[call-arg]
        )


def test_inbox_rejects_directories_symlinks_and_oversized_entries(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    config.exchange_root.mkdir()
    (config.exchange_root / "big.csv").write_text("1234567890", encoding="utf-8")
    (config.exchange_root / "nested").mkdir()
    target = config.exchange_root / "target.csv"
    target.write_text("fecha,cliente,importe\n2026-07-22,Acme,10\n", encoding="utf-8")
    link = config.exchange_root / "link.csv"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlinks unavailable in this environment")

    run = scan_inbox(InboxConfig(workspace=config, max_bytes=5))
    by_path = {item.relative_path: item for item in run.items}

    assert by_path["big.csv"].disposition == "quarantined"
    assert by_path["big.csv"].code == "source_too_large"
    assert by_path["nested"].disposition == "quarantined"
    assert by_path["nested"].code == "entry_directory"
    assert by_path["link.csv"].disposition == "quarantined"
    assert by_path["link.csv"].code == "entry_symlink"
    assert link.is_symlink()
