"""Regression tests for E26 portable shared business workspaces."""

from __future__ import annotations

import hashlib
import sqlite3
import subprocess
from pathlib import Path

from escala_server.project_memory import ProjectMemoryRuntime
from escala_server.project_memory_context import ProjectMemorySessionContext
from escala_server.workspace import (
    WorkspaceIndexer,
    create_contribution,
    create_workspace,
    load_workspace,
    reconcile_canonical_document,
)


def _write_profile(root: Path, name: str = "Lumen Casa") -> Path:
    profile = root / "company" / "profile.yaml"
    profile.write_text(
        f"owner: directora\nstatus: confirmed\nname: {name}\n", encoding="utf-8"
    )
    return profile


def test_workspace_manifest_is_portable_and_rejects_unexpected_fields(tmp_path: Path) -> None:
    root = tmp_path / "empresa"
    created = create_workspace(root, "Lumen Casa")

    assert created.ready
    assert created.manifest is not None
    assert (root / "areas" / "cash").is_dir()
    manifest = root / "scaleup-workspace.yaml"
    assert "path" not in manifest.read_text(encoding="utf-8").lower()
    assert load_workspace(root).ready

    manifest.write_text(
        "schema_version: 1\nworkspace_id: "
        + created.manifest.workspace_id
        + "\nname: Lumen Casa\nsecret: nope\n",
        encoding="utf-8",
    )
    invalid = load_workspace(root)
    assert not invalid.ready
    assert "unsupported" in (invalid.reason or "")


def test_workspace_never_creates_sqlite_under_shared_root(tmp_path: Path) -> None:
    root = tmp_path / "shared"
    state = tmp_path / "local-state"
    created = create_workspace(root, "Lumen Casa")
    assert created.ready and created.manifest is not None

    runtime = ProjectMemoryRuntime(root, local_state_root=state)
    result = runtime.ensure_memory()

    assert result.ready
    assert result.db_path == state / created.manifest.workspace_id / "escala.db"
    assert not any(root.rglob("escala.db"))
    assert not any(root.rglob("escala.db-wal"))
    assert not any(root.rglob("escala.db-shm"))


def test_invalid_manifest_cannot_fall_back_to_legacy_sqlite_path(tmp_path: Path) -> None:
    (tmp_path / "scaleup-workspace.yaml").write_text("workspace_id: invalid\n")

    result = ProjectMemoryRuntime(tmp_path).ensure_memory()

    assert not result.ready
    assert "manifest is invalid" in (result.reason or "")
    assert not (tmp_path / ".scaleup" / "memory" / "escala.db").exists()


def test_legacy_database_is_copied_once_to_local_state(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    legacy = ProjectMemoryRuntime(root)
    assert legacy.ensure_memory().ready
    with sqlite3.connect(legacy.db_path) as db:
        db.execute("INSERT INTO companies (id, name) VALUES ('lumen', 'Lumen Casa')")

    assert create_workspace(root, "Lumen Casa").ready
    migrated = ProjectMemoryRuntime(root, local_state_root=tmp_path / "local")
    assert migrated.ensure_memory().ready

    assert migrated.db_path != legacy.db_path
    assert not legacy.db_path.exists()
    archive = migrated.backups_root / "legacy-e22" / "escala-before-workspace-migration.db"
    assert archive.is_file()
    with sqlite3.connect(migrated.db_path) as db:
        assert db.execute("SELECT name FROM companies WHERE id='lumen'").fetchone()[0] == "Lumen Casa"


def test_two_local_indexes_converge_without_shared_sqlite(tmp_path: Path) -> None:
    root = tmp_path / "empresa"
    assert create_workspace(root, "Lumen Casa").ready
    _write_profile(root)
    cash = create_contribution(
        root,
        area="cash",
        author="Ana",
        role="Contadora",
        source="Cierre mensual",
        content={"runway_days": 90},
        status="confirmed",
    )
    execution = create_contribution(
        root,
        area="execution",
        author="Luis",
        role="Director",
        source="Reunión semanal",
        content={"prioridad": "Reducir tiempos de entrega"},
        status="confirmed",
    )
    assert cash.ready and execution.ready

    left = WorkspaceIndexer(root, local_state_root=tmp_path / "left").rebuild()
    right = WorkspaceIndexer(root, local_state_root=tmp_path / "right").rebuild()

    assert left.ready and right.ready
    assert left.db_path != right.db_path
    assert left.digest == right.digest
    assert len(left.indexed) == 3
    assert not any(root.rglob("*.db"))


def test_confirmed_workspace_documents_are_recovered_in_a_new_session(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "empresa"
    state = tmp_path.parent / f"{tmp_path.name}-local-state"
    monkeypatch.setenv("SCALEUP_LOCAL_STATE_ROOT", str(state))
    assert create_workspace(root, "Lumen Casa").ready
    (root / "company" / "profile.yaml").write_text(
        "owner: directora\nstatus: confirmed\nname: Lumen Casa\nindustry: interiores\n",
        encoding="utf-8",
    )
    rebuilt = WorkspaceIndexer(root, local_state_root=state).rebuild()
    assert rebuilt.ready

    context = ProjectMemorySessionContext(root).load()

    assert context.ready
    assert any(
        item.key == "workspace:company/profile.yaml:name" and item.value == "Lumen Casa"
        for item in context.items
    )


def test_rename_removes_old_facts_without_duplicating_the_document(tmp_path: Path) -> None:
    root = tmp_path / "empresa"
    assert create_workspace(root, "Lumen Casa").ready
    profile = _write_profile(root)
    indexer = WorkspaceIndexer(root, local_state_root=tmp_path / "local")
    first = indexer.rebuild()
    profile.rename(root / "company" / "identity.yaml")
    second = indexer.rebuild()

    assert first.ready and second.ready
    assert second.removed == ("company/profile.yaml",)
    with sqlite3.connect(second.db_path) as db:
        paths = {
            row[0]
            for row in db.execute(
                "SELECT relative_path FROM workspace_facts ORDER BY relative_path"
            )
        }
    assert paths == {"company/identity.yaml"}


def test_stale_contribution_requires_explicit_reconciliation(tmp_path: Path) -> None:
    root = tmp_path / "empresa"
    assert create_workspace(root, "Lumen Casa").ready
    profile = _write_profile(root)
    base_sha256 = hashlib.sha256(profile.read_bytes()).hexdigest()
    contribution = create_contribution(
        root,
        area="cash",
        author="Ana",
        role="Contadora",
        source="Cierre mensual",
        content={"runway_days": 90},
        status="confirmed",
        target="company/profile.yaml",
        base_sha256=base_sha256,
    )
    assert contribution.ready and contribution.contribution_id
    profile.write_text(
        "owner: directora\nstatus: confirmed\nname: Lumen Casa Nueva\n",
        encoding="utf-8",
    )
    indexer = WorkspaceIndexer(root, local_state_root=tmp_path / "local")
    conflict = indexer.rebuild()
    contribution_path = contribution.path.relative_to(root).as_posix()  # type: ignore[union-attr]
    assert contribution_path in conflict.conflicts

    without_confirmation = reconcile_canonical_document(
        root,
        target="company/profile.yaml",
        owner="directora",
        content={"name": "Lumen Casa Nueva", "runway_days": 90},
        resolved_contribution_ids=(contribution.contribution_id,),
    )
    assert not without_confirmation.ready
    reconciled = reconcile_canonical_document(
        root,
        target="company/profile.yaml",
        owner="directora",
        content={"name": "Lumen Casa Nueva", "runway_days": 90},
        resolved_contribution_ids=(contribution.contribution_id,),
        confirm=True,
    )
    assert reconciled.ready
    assert reconciled.record_path is not None and reconciled.record_path.is_file()
    assert indexer.rebuild().conflicts == ()


def test_offline_contributions_converge_and_provider_conflict_copy_is_preserved(
    tmp_path: Path,
) -> None:
    """Model two machines reconnecting through a normal synced folder.

    The folder itself is the only exchange medium: each machine keeps its own
    SQLite index. A provider-style conflicted copy is retained and surfaced,
    never selected as a winning version.
    """
    shared = tmp_path / "shared"
    assert create_workspace(shared, "Lumen Casa").ready

    cash = create_contribution(
        shared,
        area="cash",
        author="Ana",
        role="Contadora",
        source="Cierre offline de agosto",
        content={"runway_days": 90},
        status="confirmed",
    )
    execution = create_contribution(
        shared,
        area="execution",
        author="Luis",
        role="Director",
        source="Prioridad offline semanal",
        content={"prioridad": "Reducir tiempos de entrega"},
        status="confirmed",
    )
    assert cash.ready and execution.ready

    ana = WorkspaceIndexer(shared, local_state_root=tmp_path / "ana-local").rebuild()
    luis = WorkspaceIndexer(shared, local_state_root=tmp_path / "luis-local").rebuild()
    assert ana.ready and luis.ready and ana.digest == luis.digest
    assert ana.db_path != luis.db_path

    original = shared / "company" / "profile.yaml"
    _write_profile(shared)
    conflicted_copy = shared / "company" / "profile (copia en conflicto).yaml"
    conflicted_copy.write_text(original.read_text(encoding="utf-8"), encoding="utf-8")

    after_conflict = WorkspaceIndexer(
        shared, local_state_root=tmp_path / "ana-local"
    ).rebuild()
    assert after_conflict.ready
    assert "company/profile (copia en conflicto).yaml" in after_conflict.conflicts
    assert WorkspaceIndexer(shared, local_state_root=tmp_path / "ana-local").doctor().state == "attention"
    assert not any(shared.rglob("*.db"))


def test_sensitive_data_is_rejected_before_shared_write_and_doctor_detects_db(tmp_path: Path) -> None:
    root = tmp_path / "empresa"
    assert create_workspace(root, "Lumen Casa").ready
    rejected = create_contribution(
        root,
        area="cash",
        author="Ana",
        role="Contadora",
        source="Cierre mensual",
        content={"api_key": "not-for-sharing"},
    )
    assert not rejected.ready
    assert not list((root / "contributions").rglob("*.yaml"))

    accidental = root / "escala.db"
    accidental.write_bytes(b"SQLite format 3\x00")
    doctor = WorkspaceIndexer(root, local_state_root=tmp_path / "local").doctor()
    assert not doctor.ready
    assert doctor.state == "blocked"
    assert doctor.shared_database_artifacts == ("escala.db",)


def test_public_conversation_prepares_and_checks_current_folder(tmp_path: Path, monkeypatch) -> None:
    from coaching.router.conversation import run

    local_state = tmp_path.parent / f"{tmp_path.name}-local-state"
    monkeypatch.setenv("SCALEUP_LOCAL_STATE_ROOT", str(local_state))
    prompt = run("Quiero compartir esta carpeta con mi equipo", base_path=tmp_path)
    assert "¿Quieres preparar esta carpeta ahora?" in prompt
    ready = run("sí", base_path=tmp_path)
    assert "ya tiene una estructura empresarial" in ready
    assert (tmp_path / "scaleup-workspace.yaml").is_file()
    health = run("revisa la carpeta compartida", base_path=tmp_path)
    assert "necesita reconstruir su memoria local" in health
    assert not any(tmp_path.rglob("escala.db"))
    rebuilt = run("reconstruye la carpeta compartida", base_path=tmp_path)
    assert "reconstruí la memoria local" in rebuilt
    assert not any(tmp_path.rglob("escala.db"))
    assert any(local_state.rglob("escala.db"))


def test_claude_installation_runs_workspace_conversation(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parent.parent
    installer = repo / ".scaleup" / "install.sh"
    subprocess.run(
        [
            "bash",
            str(installer),
            "--target",
            "claude",
            "--destination-root",
            str(tmp_path),
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    runtime = tmp_path / ".claude" / "scaleup"
    project = tmp_path / "company"
    project.mkdir()
    response = subprocess.run(
        [str(runtime / "bin" / "scaleup-frontdoor"), "conversation", "quiero compartir esta carpeta con mi equipo"],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    assert (runtime / "escala_server" / "workspace.py").is_file()
    assert "¿Quieres preparar esta carpeta ahora?" in response


def test_installer_distributes_workspace_runtime(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parent.parent
    installer = repo / ".scaleup" / "install.sh"
    subprocess.run(
        [
            "bash",
            str(installer),
            "--target",
            "codex",
            "--destination-root",
            str(tmp_path),
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    runtime = tmp_path / ".codex" / "scaleup"
    command = runtime / "bin" / "scaleup-frontdoor"
    project = tmp_path / "company"
    project.mkdir()

    response = subprocess.run(
        [str(command), "conversation", "quiero compartir esta carpeta con mi equipo"],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    assert (runtime / "escala_server" / "workspace.py").is_file()
    assert "¿Quieres preparar esta carpeta ahora?" in response
