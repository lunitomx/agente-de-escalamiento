"""E24 contract tests for local, opt-in weekly GTD cadence."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from escala_server.weekly_cadence import WeeklyCadenceStore


def _setup(store: WeeklyCadenceStore, now: datetime) -> None:
    result = store.configure(
        weekday=0, timezone="America/Mexico_City", duration_minutes=30,
        owner="Eduardo", priority="Mejorar cobranza", project="Cobranza Q3",
        desired_outcome="Reducir facturas vencidas", next_action="Llamar a Ana para revisar vencidos",
        explicit_confirmation=True, now=now,
    )
    assert result.ready


def test_cadence_requires_confirmation_concrete_action_and_is_due_deterministically(tmp_path: Path) -> None:
    store = WeeklyCadenceStore(tmp_path)
    now = datetime(2026, 8, 24, 9, tzinfo=ZoneInfo("America/Mexico_City"))
    no = store.configure(
        weekday=0, timezone="America/Mexico_City", duration_minutes=30,
        owner="Eduardo", priority="Cobranza", project="Q3",
        desired_outcome="Menos vencido", next_action="Mejorar cobranza",
        explicit_confirmation=False, now=now,
    )
    assert not no.ready
    _setup(store, now)
    waiting = store.status(now=now)
    assert waiting.ready and not waiting.due and waiting.next_review_on == "2026-08-31"
    due = store.status(now=datetime(2026, 8, 31, 9, tzinfo=ZoneInfo("America/Mexico_City")))
    assert due.due and due.commitment is not None


def test_review_preserves_result_blocker_and_confirmed_next_action(tmp_path: Path) -> None:
    store = WeeklyCadenceStore(tmp_path)
    now = datetime(2026, 8, 24, 9, tzinfo=ZoneInfo("America/Mexico_City"))
    _setup(store, now)
    result = store.review(
        outcome="blocked", result="No recibimos la lista de facturas",
        blocker="Ana debe confirmar las facturas vencidas",
        priority="Mejorar cobranza", project="Cobranza Q3",
        desired_outcome="Tener lista validada", next_action="Pedir a Ana la lista validada",
        owner="Eduardo", explicit_confirmation=True,
        now=datetime(2026, 8, 31, 9, tzinfo=ZoneInfo("America/Mexico_City")),
    )
    assert result.ready and result.commitment is not None
    with sqlite3.connect(store.runtime.db_path) as db:
        review = db.execute("SELECT outcome, blocker FROM weekly_reviews").fetchone()
        old = db.execute("SELECT status FROM weekly_commitments WHERE status='blocked'").fetchone()
    assert review == ("blocked", "Ana debe confirmar las facturas vencidas")
    assert old == ("blocked",)


def test_pause_resume_and_automation_proposal_never_executes_without_acceptance(tmp_path: Path) -> None:
    store = WeeklyCadenceStore(tmp_path)
    now = datetime(2026, 8, 24, 9, tzinfo=ZoneInfo("America/Mexico_City"))
    _setup(store, now)
    assert store.pause().ready
    assert not store.status(now=datetime(2026, 9, 1, 9, tzinfo=ZoneInfo("America/Mexico_City"))).due
    assert store.resume(now=now).ready

    proposal = store.propose_automation(
        kind="swt_review", purpose="Revisar si SWT sigue vigente", frequency_months=3,
        data_minimum="SWT confirmado", host_capability="Tareas programadas del host si existen",
        manual_alternative="Revisarlo al abrir ScaleUp",
    )
    with sqlite3.connect(store.runtime.db_path) as db:
        assert db.execute("SELECT COUNT(*) FROM cadence_automation_preferences").fetchone()[0] == 0
    assert not store.respond_automation(proposal, state="accepted", explicit_confirmation=False).ready
    assert store.respond_automation(proposal, state="accepted", explicit_confirmation=True).ready
    with sqlite3.connect(store.runtime.db_path) as db:
        row = db.execute("SELECT state, host_state FROM cadence_automation_preferences").fetchone()
    assert row == ("accepted", "not_configured")


def test_cadence_conversation_is_opt_in_pauseable_and_never_claims_host_execution(
    tmp_path: Path,
) -> None:
    from coaching.router.conversation import run

    root = tmp_path / "conversation"
    root.mkdir()
    assert "opcional" in run("quiero activar una revisión semanal", base_path=root).lower()
    assert "zona horaria" in run("lunes", base_path=root).lower()
    assert "minutos" in run("Ciudad de México", base_path=root).lower()
    assert "responsable" in run("30 minutos", base_path=root).lower()
    assert "prioridad" in run("Eduardo", base_path=root).lower()
    assert "proyecto" in run("Mejorar cobranza", base_path=root).lower()
    assert "resultado" in run("Cobranza Q3", base_path=root).lower()
    assert "acción" in run("Reducir vencidos", base_path=root).lower()
    proposed = run("Llamar a Ana para revisar vencidos", base_path=root)
    assert "memoria local" in proposed.lower()
    active = run("sí", base_path=root)
    assert "no enviaré notificaciones" in active.lower()
    assert "pausé" in run("pausa mi revisión semanal", base_path=root).lower()
    reminder = run("automatiza mi revisión semanal", base_path=root)
    assert "no puedo crearlo" in reminder.lower()


def test_weekly_review_conversation_records_blocker_and_confirmed_next_action(tmp_path: Path) -> None:
    from coaching.router.conversation import run

    root = tmp_path / "review"
    root.mkdir()
    store = WeeklyCadenceStore(root)
    _setup(store, datetime(2026, 8, 24, 9, tzinfo=ZoneInfo("America/Mexico_City")))
    with sqlite3.connect(store.runtime.db_path) as db:
        db.execute("UPDATE weekly_cadences SET next_review_on='2000-01-01'")
        db.commit()

    assert "cómo terminó" in run("hacer mi revisión semanal", base_path=root).lower()
    assert "resultado" in run("bloqueado", base_path=root).lower()
    assert "bloqueo" in run("No recibimos facturas", base_path=root).lower()
    assert "siguiente acción" in run("Ana debe validar los vencidos", base_path=root).lower()
    assert "confirmas" in run("Pedir a Ana la lista validada", base_path=root).lower()
    assert "cerramos" in run("sí", base_path=root).lower()
    with sqlite3.connect(store.runtime.db_path) as db:
        assert db.execute("SELECT COUNT(*) FROM weekly_reviews").fetchone()[0] == 1
