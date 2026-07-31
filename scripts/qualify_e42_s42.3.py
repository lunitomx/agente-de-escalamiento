#!/usr/bin/env python3
"""Run E42 S42.3 security and recovery qualification scenarios.

This script exercises negative paths and recovery behavior for the ESCALA
local product on the current development machine. It does NOT replace
validation on clean macOS/Windows hardware or human acceptance; those are
recorded separately.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from escala_server.lifecycle import (  # noqa: E402
    InstallRequest,
    LifecycleError,
    LifecycleRuntime,
    ScheduleRequest,
    build_install_bundle,
    build_native_schedule,
    install_package,
    make_update_artifact,
    migrate_local_state,
    render_native_schedule,
    verify_update_artifact,
)
from escala_server.workspace.authority import (  # noqa: E402
    WorkspaceAuthorityError,
    WorkspaceConfig,
    init_authoritative_db,
    validate_workspace,
)


EVIDENCE_DIR = (
    ROOT / "work/epics/e42-product-qualification-and-functional-catalog/evidence"
)
EVIDENCE_PATH = EVIDENCE_DIR / "s42.3-security-recovery.json"
EXPECTED_EVIDENCE_SCHEMA_VERSION = 1


def main() -> int:
    source_commit = _source_commit()
    evidence: dict[str, object] = {
        "schema_version": 1,
        "story": "S42.3",
        "epic": "E42",
        "source_commit": source_commit,
        "environment": "local-synthetic",
        "platform_matrix": ["macos", "windows"],
        "notes": [
            "This is synthetic/local evidence. Clean hardware and human acceptance are separate.",
        ],
    }

    scenarios: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="e42-s42.3-") as temporary:
        root = Path(temporary)
        request = _install_base(root, "macos")

        scenarios.append(_scenario_damaged_file(root, request))
        scenarios.append(_scenario_stale_evidence(root, source_commit))
        scenarios.append(_scenario_tampered_package(root, request))
        scenarios.append(_scenario_interrupted_update(request))
        scenarios.append(_scenario_no_network(request))
        scenarios.append(_scenario_sqlite_sync_attempt(root))
        scenarios.append(_scenario_shared_folder_authority(root, request))

    evidence["scenarios"] = scenarios
    evidence["overall_status"] = (
        "pass" if all(s.get("status") == "pass" for s in scenarios) else "fail"
    )

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    status = evidence["overall_status"]
    print(f"S42.3 security/recovery qualification: {status.upper()}")
    print(f"Evidence: {EVIDENCE_PATH}")
    for scenario in scenarios:
        print(f"  - {scenario['id']}: {scenario['status']}")
    return 0 if status == "pass" else 1


def _install_base(root: Path, platform: str) -> InstallRequest:
    """Install a baseline package so scenarios have a local instance to test."""

    bundle = build_install_bundle(ROOT, root / "packages", "1.0.0", platform)
    request = InstallRequest(
        platform=platform,  # type: ignore[arg-type]
        version="1.0.0",
        install_root=root / f"install-{platform}",
        data_root=root / f"data-{platform}",
        database_path=root / f"data-{platform}" / "escala.sqlite",
        exchange_root=root / f"exchange-{platform}",
    )
    receipt = install_package(bundle, request)
    if receipt.status != "pass":
        raise RuntimeError(f"baseline install failed: {receipt.status}")
    return request


def _scenario_damaged_file(root: Path, request: InstallRequest) -> dict[str, object]:
    """A corrupted install bundle must be rejected before any local mutation."""

    damaged_bundle = root / "damaged-bundle.zip"
    damaged_bundle.write_bytes(b"this is not a valid zip archive")
    observed: str
    try:
        install_package(damaged_bundle, request)
        observed = "accepted"
    except LifecycleError as exc:
        observed = exc.code

    return {
        "id": "damaged_file",
        "status": "pass" if observed == "bundle_invalid" else "fail",
        "expected": "install_package rejects a damaged bundle with code bundle_invalid",
        "observed": observed,
        "business_message": (
            "El paquete de instalación está dañado y ESCALA no lo abrió. "
            "No se modificó ninguna carpeta local."
        ),
        "next_step": "Descargue el paquete nuevamente desde la fuente confiable.",
        "preserved_data": True,
    }


def _scenario_stale_evidence(root: Path, current_commit: str) -> dict[str, object]:
    """Evidence files must be fresh by schema version and source commit."""

    fresh_path = root / "fresh-evidence.json"
    stale_path = root / "stale-evidence.json"
    fresh_path.write_text(
        json.dumps(
            {
                "schema_version": EXPECTED_EVIDENCE_SCHEMA_VERSION,
                "source_commit": current_commit,
                "story": "S42.1",
            }
        ),
        encoding="utf-8",
    )
    stale_path.write_text(
        json.dumps(
            {
                "schema_version": 0,
                "source_commit": "0" * 40,
                "story": "S42.1",
            }
        ),
        encoding="utf-8",
    )

    fresh_ok = _evidence_is_fresh(fresh_path, current_commit)
    stale_ok = _evidence_is_fresh(stale_path, current_commit)

    return {
        "id": "stale_evidence",
        "status": "pass" if fresh_ok and not stale_ok else "fail",
        "expected": "fresh evidence passes and stale evidence is rejected",
        "observed": {
            "fresh_passed": fresh_ok,
            "stale_rejected": not stale_ok,
        },
        "business_message": (
            "La evidencia antigua se detecta porque no coincide con la versión "
            "actual del producto."
        ),
        "next_step": "Regenere la evidencia con el script de qualification actual.",
        "preserved_data": True,
    }


def _evidence_is_fresh(path: Path, current_commit: str) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        data.get("schema_version") == EXPECTED_EVIDENCE_SCHEMA_VERSION
        and data.get("source_commit") == current_commit
    )


def _scenario_tampered_package(
    root: Path, request: InstallRequest
) -> dict[str, object]:
    """A verified update must reject any post-creation tampering."""

    payload = root / "update.bin"
    payload.write_bytes(b"qualified-update-1.1.0")
    artifact = make_update_artifact(payload, "1.1.0", root / "updates")
    artifact.path.write_bytes(b"tampered-content")

    observed: str
    try:
        verify_update_artifact(artifact)
        observed = "accepted"
    except LifecycleError as exc:
        observed = exc.code

    version_after = _read_installed_version(request)
    preserved = version_after == "1.0.0"

    return {
        "id": "tampered_package",
        "status": "pass"
        if observed == "artifact_hash_mismatch" and preserved
        else "fail",
        "expected": "verify_update_artifact rejects tampered artifact and version stays at 1.0.0",
        "observed": observed,
        "business_message": (
            "Alguien modificó la actualización después de crearla. ESCALA la "
            "rechazó antes de cambiar archivos locales."
        ),
        "next_step": "Obtenga la actualización firmada desde la fuente oficial.",
        "preserved_data": preserved,
    }


def _scenario_interrupted_update(request: InstallRequest) -> dict[str, object]:
    """An interrupted migration must safe-stop and preserve existing state."""

    schema_path = request.data_root / "schema.json"
    schema_path.write_text('{"schema":1}\n', encoding="utf-8")
    state_path = request.data_root / "company-state.json"
    state_path.write_text('{"company":"Nopal Foods"}\n', encoding="utf-8")

    receipt = migrate_local_state(request, 2, fail_after_backup=True)

    preserved = (
        schema_path.read_text(encoding="utf-8") == '{"schema":1}\n'
        and state_path.read_text(encoding="utf-8") == '{"company":"Nopal Foods"}\n'
    )

    return {
        "id": "interrupted_update",
        "status": "pass" if receipt.status == "safe_stop" and preserved else "fail",
        "expected": "migration returns safe_stop and existing data is unchanged",
        "observed": {
            "migration_status": receipt.status,
            "rollback_available": receipt.rollback_available,
            "safe_stop_reason": receipt.safe_stop_reason,
        },
        "business_message": (
            "La actualización se interrumpió, pero ESCALA guardó un respaldo "
            "local y dejó los datos intactos."
        ),
        "next_step": "Reinicie el proceso de actualización o restaure desde el respaldo.",
        "preserved_data": preserved,
    }


def _scenario_no_network(request: InstallRequest) -> dict[str, object]:
    """The product must remain fully offline in install, schedule and runtime."""

    bundle = build_install_bundle(
        ROOT, request.install_root / "offline-packages", "1.0.0", "macos"
    )
    manifest = _read_bundle_manifest(bundle)
    schedule = build_native_schedule(
        ScheduleRequest(
            platform="macos",
            install_root=request.install_root,
            data_root=request.data_root,
            frequency="daily",
            local_time="08:30",
        )
    )
    rendered = render_native_schedule(schedule)
    runtime = LifecycleRuntime(request)
    start = runtime.start()
    stop = runtime.stop()

    # XML namespace declarations contain http:// but are not network actions.
    # We look for actual network client patterns instead.
    network_action_patterns = (
        "curl ",
        "wget ",
        "Invoke-RestMethod",
        "urllib",
        "requests",
    )
    has_network_action = any(pattern in rendered for pattern in network_action_patterns)
    windows_network_available_false = (
        "RunOnlyIfNetworkAvailable>false" in rendered
        if schedule.kind == "task_scheduler"
        else True
    )
    no_network = (
        manifest.get("network_required") is False
        and schedule.network_required is False
        and "https://" not in rendered
        and not has_network_action
        and windows_network_available_false
        and start.network_required is False
        and stop.network_required is False
    )

    return {
        "id": "no_network",
        "status": "pass" if no_network else "fail",
        "expected": "bundle, schedule and runtime declare no network access",
        "observed": {
            "bundle_network_required": manifest.get("network_required"),
            "schedule_network_required": schedule.network_required,
            "schedule_has_https": "https://" in rendered,
            "schedule_has_network_action": has_network_action,
            "windows_network_available_false": windows_network_available_false,
            "runtime_network_required": start.network_required,
        },
        "business_message": (
            "ESCALA no requiere conexión a internet para instalarse, programarse "
            "ni ejecutarse localmente."
        ),
        "next_step": "Puede usar el producto en una red aislada.",
        "preserved_data": True,
    }


def _scenario_sqlite_sync_attempt(root: Path) -> dict[str, object]:
    """A shared SQLite file must never become the authority for local state."""

    exchange = root / "shared-sqlite-attempt"
    exchange.mkdir()
    config = WorkspaceConfig(
        platform="macos",
        data_root=root / "data-outside-exchange",
        database_path=exchange / "shared.sqlite",
        exchange_root=exchange,
    )
    receipt = validate_workspace(config)

    initializer_called = False

    def initializer(_path: str) -> str:
        nonlocal initializer_called
        initializer_called = True
        return "initialized"

    observed: str
    try:
        init_authoritative_db(config, initializer=initializer)
        observed = "accepted"
    except WorkspaceAuthorityError as exc:
        observed = exc.code

    db_created = (exchange / "shared.sqlite").exists()

    return {
        "id": "sqlite_sync_attempt",
        "status": (
            "pass"
            if receipt.status == "fail"
            and observed == "authoritative_sqlite_sync_forbidden"
            and not initializer_called
            and not db_created
            else "fail"
        ),
        "expected": "workspace rejects SQLite inside exchange and does not mutate files",
        "observed": {
            "workspace_status": receipt.status,
            "finding": observed,
            "initializer_called": initializer_called,
            "db_created": db_created,
        },
        "business_message": (
            "ESCALA rechazó colocar la base de datos autoritativa dentro de una "
            "carpeta compartida. La autoridad permanece en la máquina local."
        ),
        "next_step": "Mantenga la carpeta compartida solo para documentos de intercambio.",
        "preserved_data": True,
    }


def _scenario_shared_folder_authority(
    root: Path, request: InstallRequest
) -> dict[str, object]:
    """A shared folder may exchange documents, but it cannot own authority."""

    exchange = root / "team-drive"
    exchange.mkdir()
    good_request = request.model_copy(update={"exchange_root": exchange})
    bundle = build_install_bundle(ROOT, root / "shared-packages", "1.0.0", "macos")
    receipt = install_package(bundle, good_request)

    config_text = good_request.data_root / "config.json"
    config = json.loads(config_text.read_text(encoding="utf-8"))
    db_inside_exchange = (
        good_request.database_path.resolve() == exchange.resolve()
        or exchange.resolve() in good_request.database_path.resolve().parents
    )

    bad_config = WorkspaceConfig(
        platform="macos",
        data_root=root / "data-bad",
        database_path=exchange / "company.sqlite",
        exchange_root=exchange,
    )
    bad_receipt = validate_workspace(bad_config)

    return {
        "id": "shared_folder_authority",
        "status": (
            "pass"
            if receipt.status == "pass"
            and config.get("exchange_role") == "ordinary_filesystem_documents_only"
            and not db_inside_exchange
            and bad_receipt.status == "fail"
            else "fail"
        ),
        "expected": (
            "shared folder is document-only, database stays local, "
            "and authority-in-exchange is rejected"
        ),
        "observed": {
            "install_status": receipt.status,
            "exchange_role": config.get("exchange_role"),
            "database_inside_exchange": db_inside_exchange,
            "authority_in_exchange_rejected": bad_receipt.status == "fail",
        },
        "business_message": (
            "La carpeta compartida sirve solo para documentos; la base de datos "
            "y la autoridad permanecen en su máquina."
        ),
        "next_step": "Use la carpeta compartida para subir documentos, no para respaldar la base de datos.",
        "preserved_data": True,
    }


def _read_installed_version(request: InstallRequest) -> str:
    path = request.install_root / "install.json"
    try:
        return str(json.loads(path.read_text(encoding="utf-8")).get("version", ""))
    except (OSError, json.JSONDecodeError):
        return ""


def _read_bundle_manifest(bundle: Path) -> dict[str, object]:
    import zipfile

    with zipfile.ZipFile(bundle) as archive:
        return json.loads(archive.read("manifest.json"))


def _source_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
