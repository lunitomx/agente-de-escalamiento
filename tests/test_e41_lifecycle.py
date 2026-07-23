from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from escala_server.lifecycle import (
    InstallRequest,
    LifecycleError,
    LifecycleRuntime,
    ScheduleRequest,
    UpdateManager,
    build_install_bundle,
    build_native_schedule,
    install_package,
    make_update_artifact,
    migrate_local_state,
    render_native_schedule,
    verify_update_artifact,
)
from escala_server.workspace.authority import WorkspaceAuthorityError


def _request(
    root: Path, platform: str = "macos", exchange: Path | None = None
) -> InstallRequest:
    install_root = root / f"install-{platform}"
    data_root = root / f"data-{platform}"
    return InstallRequest(
        platform=platform,  # type: ignore[arg-type]
        version="1.2.3",
        install_root=install_root,
        data_root=data_root,
        database_path=data_root / "escala.sqlite",
        exchange_root=exchange,
    )


def _bundle(tmp_path: Path, platform: str = "macos") -> tuple[Path, InstallRequest]:
    source = tmp_path / "source"
    (source / "escala_server").mkdir(parents=True)
    (source / "escala_server" / "__init__.py").write_text(
        "__version__ = '1.2.3'\n", encoding="utf-8"
    )
    bundle = build_install_bundle(source, tmp_path / "dist", "1.2.3", platform)  # type: ignore[arg-type]
    return bundle, _request(tmp_path, platform)


def test_build_and_install_bundle_has_no_repository_layout(tmp_path: Path) -> None:
    bundle, request = _bundle(tmp_path)

    receipt = install_package(bundle, request)

    assert receipt.status == "pass"
    assert receipt.repository_layout is False
    assert receipt.network_required is False
    assert (request.install_root / "app/escala_server/__init__.py").is_file()
    assert (request.data_root / "escala.sqlite").is_file()
    assert (request.install_root / "install.json").is_file()
    assert not (request.install_root / ".git").exists()


def test_install_rejects_cross_platform_bundle(tmp_path: Path) -> None:
    bundle, request = _bundle(tmp_path, "macos")
    windows_request = _request(tmp_path, "windows")

    with pytest.raises(LifecycleError, match="platform_mismatch"):
        install_package(bundle, windows_request)


def test_windows_install_uses_same_capability_set(tmp_path: Path) -> None:
    bundle, request = _bundle(tmp_path, "windows")

    receipt = install_package(bundle, request)

    assert receipt.status == "pass"
    assert receipt.platform == "windows"
    assert (request.install_root / "app/escala_server/__init__.py").exists()


def test_runtime_starts_reports_health_and_stops_locally(tmp_path: Path) -> None:
    bundle, request = _bundle(tmp_path)
    install_package(bundle, request)
    runtime = LifecycleRuntime(request)

    started = runtime.start()
    assert started.status == "healthy"
    assert started.hosted_service is False
    assert started.network_required is False
    assert started.version == "1.2.3"
    assert started.data_location == "data_root"
    assert runtime.status().status == "healthy"

    stopped = runtime.stop()
    assert stopped.status == "stopped"
    assert runtime.status().status == "stopped"


def test_runtime_fails_closed_when_workspace_is_in_exchange(tmp_path: Path) -> None:
    exchange = tmp_path / "exchange"
    exchange.mkdir()
    request = _request(tmp_path, exchange=exchange)
    bad = request.model_copy(update={"database_path": exchange / "shared.sqlite"})

    with pytest.raises(WorkspaceAuthorityError):
        LifecycleRuntime(bad).start()


def test_optional_exchange_is_documents_only_and_canonical_state_stays_local(
    tmp_path: Path,
) -> None:
    exchange = tmp_path / "Google Drive"
    exchange.mkdir()
    bundle, request = _bundle(tmp_path)
    request = request.model_copy(update={"exchange_root": exchange})

    receipt = install_package(bundle, request)

    assert receipt.exchange_configured is True
    assert request.database_path.parent != exchange
    config = json.loads((request.data_root / "config.json").read_text(encoding="utf-8"))
    assert config["exchange_role"] == "ordinary_filesystem_documents_only"
    assert not list(exchange.glob("*.sqlite"))


def test_update_verifies_hash_preserves_state_and_rolls_back(tmp_path: Path) -> None:
    bundle, request = _bundle(tmp_path)
    install_package(bundle, request)
    state = request.data_root / "company-state.json"
    state.write_text('{"company":"Nopal Foods"}\n', encoding="utf-8")
    update_file = tmp_path / "update.bin"
    update_file.write_bytes(b"qualified-update-2.0.0")
    artifact = make_update_artifact(update_file, "2.0.0", tmp_path / "updates")

    verified = verify_update_artifact(artifact)
    assert verified.verification == "verified"
    result = UpdateManager(request).apply(verified)
    assert result.status == "pass"
    assert result.rollback_available is True
    assert result.previous_version == "1.2.3"
    assert result.current_version == "2.0.0"
    assert state.read_text(encoding="utf-8") == '{"company":"Nopal Foods"}\n'

    rollback = UpdateManager(request).rollback(result)
    assert rollback.status == "pass"
    assert rollback.current_version == "1.2.3"
    assert (
        json.loads((request.install_root / "install.json").read_text())["version"]
        == "1.2.3"
    )


def test_update_rejects_tampered_artifact_before_writes(tmp_path: Path) -> None:
    bundle, request = _bundle(tmp_path)
    install_package(bundle, request)
    update_file = tmp_path / "update.bin"
    update_file.write_bytes(b"original")
    artifact = make_update_artifact(update_file, "2.0.0", tmp_path / "updates")
    artifact.path.write_bytes(b"tampered")

    with pytest.raises(LifecycleError, match="artifact_hash_mismatch"):
        verify_update_artifact(artifact)
    assert (
        json.loads((request.install_root / "install.json").read_text())["version"]
        == "1.2.3"
    )


def test_migration_creates_backup_and_safe_stops_on_failure(tmp_path: Path) -> None:
    bundle, request = _bundle(tmp_path)
    install_package(bundle, request)
    marker = request.data_root / "schema.json"
    marker.write_text('{"schema":1}\n', encoding="utf-8")

    safe_stop = migrate_local_state(request, 2, fail_after_backup=True)

    assert safe_stop.status == "safe_stop"
    assert safe_stop.backup_relative_path.startswith(".escala-backups/")
    assert marker.read_text(encoding="utf-8") == '{"schema":1}\n'
    assert safe_stop.rollback_available is True


@pytest.mark.parametrize("platform", ["macos", "windows"])
def test_native_schedule_is_offline_and_platform_specific(
    tmp_path: Path, platform: str
) -> None:
    request = _request(tmp_path, platform)
    schedule = build_native_schedule(
        ScheduleRequest(
            platform=platform,  # type: ignore[arg-type]
            install_root=request.install_root,
            data_root=request.data_root,
            frequency="daily",
            local_time="08:30",
        )
    )
    rendered = render_native_schedule(schedule)

    assert schedule.network_required is False
    assert schedule.kind == ("launchd" if platform == "macos" else "task_scheduler")
    assert "https://" not in rendered
    assert "localhost" not in rendered
    assert "Escala" in rendered


def test_bundle_manifest_hash_is_deterministic(tmp_path: Path) -> None:
    bundle, _ = _bundle(tmp_path)
    with zipfile.ZipFile(bundle) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        payload = archive.read("app/escala_server/__init__.py")
    assert manifest["files"][0]["sha256"] == hashlib.sha256(payload).hexdigest()
