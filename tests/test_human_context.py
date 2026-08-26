"""E23 contract tests for explicit, local human collaboration context."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from escala_server.human_context import HumanContextStore
from escala_server.project_memory import ProjectMemoryRuntime
from escala_server.workspace import create_workspace


def test_human_context_requires_field_level_confirmation_and_provenance(tmp_path: Path) -> None:
    store = HumanContextStore(tmp_path)

    unconfirmed = store.confirm("role", "Directora general", explicit_confirmation=False)
    assert not unconfirmed.ready
    assert store.list().entries == ()

    confirmed = store.confirm("role", "Directora general", explicit_confirmation=True)
    assert confirmed.ready and confirmed.entry is not None
    assert confirmed.entry.value == "Directora general"
    assert "decisiones" in confirmed.entry.purpose

    with sqlite3.connect(store.runtime.db_path) as db:
        row = db.execute(
            "SELECT field, source, status FROM human_context_entries WHERE id=?",
            (confirmed.entry.id,),
        ).fetchone()
    assert row == ("role", "explicit_user_statement", "active")


def test_sensitive_context_is_rejected_without_persistence(tmp_path: Path) -> None:
    store = HumanContextStore(tmp_path)

    rejected = store.confirm(
        "availability", "Estoy en tratamiento médico y sólo puedo martes",
        explicit_confirmation=True,
    )

    assert not rejected.ready
    assert rejected.suggested_generalization is not None
    assert store.list().entries == ()


def test_change_delete_and_relevant_consumer_projection_are_local_and_idempotent(
    tmp_path: Path,
) -> None:
    store = HumanContextStore(tmp_path)
    first = store.confirm("detail_level", "resumen ejecutivo", explicit_confirmation=True)
    replacement = store.confirm("detail_level", "con datos y alternativas", explicit_confirmation=True)
    availability = store.confirm("availability", "dos horas los viernes", explicit_confirmation=True)
    assert first.ready and replacement.ready and availability.ready

    board = store.project("board")
    assert [entry.field for entry in board.entries] == ["detail_level"]
    coaching = store.project("coaching")
    assert {entry.field for entry in coaching.entries} == {"availability", "detail_level"}

    with sqlite3.connect(store.runtime.db_path) as db:
        statuses = db.execute(
            "SELECT status FROM human_context_entries WHERE field='detail_level' ORDER BY consented_at, id"
        ).fetchall()
        accesses = db.execute(
            "SELECT consumer FROM human_context_accesses ORDER BY id"
        ).fetchall()
    assert sorted(status[0] for status in statuses) == ["active", "superseded"]
    assert accesses == [("board",), ("coaching",), ("coaching",)]

    assert store.delete("detail_level").ready
    assert store.delete("detail_level").ready
    assert [entry.field for entry in HumanContextStore(tmp_path).list().entries] == ["availability"]
    assert store.delete().ready
    assert HumanContextStore(tmp_path).list().entries == ()


def test_human_context_uses_workspace_local_sqlite_not_shared_folder(tmp_path: Path) -> None:
    shared = tmp_path / "shared"
    local = tmp_path / "local"
    assert create_workspace(shared, "Lumen Casa").ready

    store = HumanContextStore(shared)
    store.runtime = ProjectMemoryRuntime(shared, local_state_root=local)
    result = store.confirm("role", "Directora", explicit_confirmation=True)

    assert result.ready
    assert any(local.rglob("escala.db"))
    assert not any(shared.rglob("*.db"))


def test_human_context_conversation_is_optional_confirmed_editable_and_erasable(
    tmp_path: Path,
) -> None:
    from coaching.router.conversation import run

    root = tmp_path / "conversation"
    root.mkdir()
    run("quiero organizar mi empresa", base_path=root)
    run("Lumen Casa", base_path=root)
    run("Iluminación", base_path=root)
    offer = run("28", base_path=root)
    assert "personalizar" in offer.lower()
    assert "rol" in run("sí", base_path=root).lower()
    proposal = run("Soy directora general", base_path=root)
    assert "quieres guardarlo" in proposal.lower()
    assert "estilo" in run("sí", base_path=root).lower()
    run("saltar", base_path=root)
    run("saltar", base_path=root)
    run("saltar", base_path=root)

    seen = run("ver mi perfil personal", base_path=root)
    assert "Soy directora general" in seen
    assert "metadata" not in seen.lower()

    assert "rol" in run("cambia mi rol", base_path=root).lower()
    assert "guardar" in run("CEO operativa", base_path=root).lower()
    assert "actualicé" in run("sí", base_path=root)
    assert "CEO operativa" in run("ver mi perfil personal", base_path=root)
    assert "borré" in run("borra mi contexto personal", base_path=root)
    assert "No tengo" in run("ver mi perfil personal", base_path=root)


def test_sensitive_human_answer_is_not_saved_and_workspace_pending_state_is_local(
    tmp_path: Path, monkeypatch
) -> None:
    from coaching.router.conversation import run

    shared = tmp_path / "shared"
    local = tmp_path / "local-state"
    monkeypatch.setenv("SCALEUP_LOCAL_STATE_ROOT", str(local))
    assert create_workspace(shared, "Lumen Casa").ready

    reply = run("quiero personalizar cómo trabajo", base_path=shared)
    assert "rol" in reply.lower()
    warning = run("Tengo un diagnóstico médico", base_path=shared)
    assert "no lo guardaré" in warning.lower()
    assert HumanContextStore(shared).list().entries == ()
    assert not (shared / ".scaleup" / "agent" / "memory" / "conversation.yaml").exists()
    assert any(local.rglob("conversation.yaml"))
