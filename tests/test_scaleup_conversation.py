"""Regression coverage for the no-JSON public ScaleUp conversation."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from coaching.core import write_yaml
from escala_server.project_memory import ProjectMemoryRuntime
from escala_server.project_memory_session_close import ProjectMemorySessionClose

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALLER = REPO_ROOT / ".scaleup" / "install.sh"


def _say(command: Path, project: Path, message: str) -> str:
    result = subprocess.run(
        [str(command), "conversation", message],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _journey(command: Path, project: Path) -> None:
    assert "¿Cómo se llama" in _say(command, project, "quiero organizar mi empresa")
    assert "Lumen Casa" in _say(command, project, "Lumen Casa")
    assert "Cuántas personas" in _say(
        command, project, "Vendemos iluminación para hogares"
    )
    offer = _say(command, project, "28")
    assert "personalizar" in offer.lower()
    first_question = _say(command, project, "ahora no")
    assert "escucharte antes de poner números" in first_question

    # A fresh process keeps narrative state, while a number remains an optional shortcut.
    assert "strategy" in _say(command, project, "3").lower()
    state = project / ".scaleup" / "agent" / "memory" / "conversation.yaml"
    assert state.is_file() and "people_q1: 3" in state.read_text(encoding="utf-8")
    for _ in range(3):
        _say(command, project, "3")

    assert "plan en una hoja" in _say(
        command, project, "quiero hacer mi plan en una hoja"
    )
    answers = (
        "Nos importan diseño honesto, cumplir lo prometido y resolver rápido.",
        "Iluminar hogares",
        "Ser líder nacional",
        "2036",
        "México",
        "Entrega en 72 horas; porcentaje puntual",
        "Q3 2026",
        "95% puntual",
        "2026",
        "$10M",
        "$1M",
        "Crecer; Ana; ventas",
        "Inventario; Luis; faltantes",
    )
    for answer in answers:
        _say(command, project, answer)
    artifact = project / "work" / "strategy" / "opsp.md"
    assert artifact.is_file()
    artifact_text = artifact.read_text(encoding="utf-8")
    assert "Nos importan diseño honesto" not in artifact_text
    assert "diseño honesto" in artifact_text
    valid = subprocess.run(
        [str(command), "validate-opsp", str(artifact)],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(valid.stdout) == {"valid": True, "errors": []}
    assert "Dashboard de Progreso" in _say(command, project, "¿Qué sigue?")


def _combined_demo_intake(command: Path, project: Path) -> None:
    assert "¿Cómo se llama" in _say(command, project, "quiero organizar mi empresa")
    assert "¿Cómo se llama tu empresa?" in _say(command, project, "todavía no lo sé")
    assert not (
        project / ".scaleup" / "agent" / "memory" / "company-profile.yaml"
    ).exists()
    response = _say(
        command,
        project,
        "Se llama Lumen Casa. Vendemos iluminación decorativa… Somos 28 personas.",
    )
    assert "personalizar" in response.lower()
    assert "escucharte antes de poner números" in _say(command, project, "ahora no")
    profile = (
        project / ".scaleup" / "agent" / "memory" / "company-profile.yaml"
    ).read_text(encoding="utf-8")
    assert "name: Lumen Casa" in profile
    assert "industry: iluminación decorativa" in profile
    assert "employees: 28" in profile


def test_conversation_persists_natural_journey_in_checkout(tmp_path):
    project = tmp_path / "checkout"
    project.mkdir()
    _journey(REPO_ROOT / ".scaleup" / "bin" / "scaleup-frontdoor", project)
    combined = tmp_path / "checkout-combined"
    combined.mkdir()
    _combined_demo_intake(
        REPO_ROOT / ".scaleup" / "bin" / "scaleup-frontdoor", combined
    )


def test_natural_plan_request_collects_company_before_plan(tmp_path):
    project = tmp_path / "new-company"
    project.mkdir()
    command = REPO_ROOT / ".scaleup" / "bin" / "scaleup-frontdoor"
    assert "¿Cómo se llama?" in _say(
        command, project, "quiero hacer mi plan en una hoja"
    )
    _say(command, project, "Lumen Casa")
    _say(command, project, "Iluminación")
    response = _say(command, project, "28")
    assert "tres valores" in response
    assert (
        project / ".scaleup" / "agent" / "memory" / "company-profile.yaml"
    ).is_file()


def test_conversation_persists_natural_journey_after_clean_install(tmp_path):
    destination, project = tmp_path / "home", tmp_path / "installed"
    project.mkdir()
    subprocess.run(
        [
            "bash",
            str(INSTALLER),
            "--target",
            "codex",
            "--destination-root",
            str(destination),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    command = destination / ".codex" / "scaleup" / "bin" / "scaleup-frontdoor"
    _journey(command, project)
    combined = tmp_path / "installed-combined"
    combined.mkdir()
    _combined_demo_intake(command, combined)


def test_pause_confirmation_and_resume_use_only_natural_language(
    tmp_path: Path,
) -> None:
    from coaching.router.conversation import run

    root = tmp_path / "continuity"
    root.mkdir()
    question = run("quiero pausar", base_path=root)
    assert "qué decisión o dato" in question.lower()
    proposal = run("Contrataremos una líder de ventas en septiembre", base_path=root)
    assert "quieres que lo recuerde" in proposal.lower()
    confirmed = run("sí", base_path=root)
    assert "próxima vez" in confirmed.lower()
    resumed = run("retomemos", base_path=root)
    assert "líder de ventas" in resumed.lower()
    assert all(
        token not in resumed.lower() for token in (".scaleup", "sqlite", "skill")
    )


def test_pause_no_and_ambiguous_never_confirm_an_entry(tmp_path: Path) -> None:
    from coaching.router.conversation import run

    root = tmp_path / "consent"
    root.mkdir()
    run("quiero pausar", base_path=root)
    run("La meta de septiembre es 1.2 M MXN", base_path=root)
    ambiguous = run("tal vez", base_path=root)
    assert "no lo voy a dar por hecho" in ambiguous.lower()
    close = ProjectMemorySessionClose(root)
    proposed_state_digest = _memory_state_digest(root)
    assert close.runtime.health().ready
    with sqlite3.connect(close.runtime.db_path) as db:
        assert (
            db.execute("SELECT COUNT(*) FROM project_memory_sessions").fetchone()[0]
            == 1
        )
        assert (
            db.execute("SELECT COUNT(*) FROM session_memory_proposals").fetchone()[0]
            == 1
        )
        assert (
            db.execute("SELECT COUNT(*) FROM confirmed_memory_entries").fetchone()[0]
            == 0
        )
        assert (
            db.execute(
                "SELECT response_state FROM session_memory_proposals"
            ).fetchone()[0]
            == "proposed"
        )
        assert (
            db.execute("SELECT status FROM project_memory_sessions").fetchone()[0]
            == "open"
        )

    assert run("no", base_path=root).lower().startswith("de acuerdo")
    with sqlite3.connect(close.runtime.db_path) as db:
        assert (
            db.execute("SELECT COUNT(*) FROM project_memory_sessions").fetchone()[0]
            == 1
        )
        assert (
            db.execute("SELECT COUNT(*) FROM session_memory_proposals").fetchone()[0]
            == 1
        )
        assert (
            db.execute("SELECT COUNT(*) FROM confirmed_memory_entries").fetchone()[0]
            == 0
        )
        assert (
            db.execute(
                "SELECT response_state FROM session_memory_proposals"
            ).fetchone()[0]
            == "rejected"
        )
        assert (
            db.execute("SELECT status FROM project_memory_sessions").fetchone()[0]
            == "closed"
        )
    assert _memory_state_digest(root) != proposed_state_digest


def test_ambiguous_confirmation_can_continue_without_persisting(tmp_path: Path) -> None:
    from coaching.router.conversation import run

    root = tmp_path / "continue-after-ambiguous"
    root.mkdir()
    run("quiero pausar", base_path=root)
    run("Contrataremos una líder de ventas en septiembre", base_path=root)
    assert "no lo voy a dar por hecho" in run("tal vez", base_path=root).lower()
    before = _memory_digest(root)
    before_state = _memory_state_digest(root)
    before_counts = _memory_counts(root)

    continued = run("sigamos", base_path=root)

    assert "¿cómo se llama" in continued.lower()
    assert "recuerde para la próxima vez" not in continued.lower()
    close = ProjectMemorySessionClose(root)
    assert _memory_digest(root) == before
    assert _memory_state_digest(root) == before_state
    assert _memory_counts(root) == before_counts == (1, 1, 0)

    with sqlite3.connect(close.runtime.db_path) as db:
        assert (
            db.execute("SELECT COUNT(*) FROM project_memory_sessions").fetchone()[0]
            == 1
        )
        assert (
            db.execute("SELECT COUNT(*) FROM session_memory_proposals").fetchone()[0]
            == 1
        )
        assert (
            db.execute("SELECT COUNT(*) FROM confirmed_memory_entries").fetchone()[0]
            == 0
        )
        assert (
            db.execute(
                "SELECT response_state FROM session_memory_proposals"
            ).fetchone()[0]
            == "proposed"
        )
        assert (
            db.execute("SELECT status FROM project_memory_sessions").fetchone()[0]
            == "open"
        )


def test_business_goal_with_cerrar_does_not_start_memory(tmp_path: Path) -> None:
    from coaching.router.conversation import run

    root = tmp_path / "close-more-sales"
    root.mkdir()

    response = run("quiero cerrar más ventas", base_path=root)

    assert "¿cómo se llama" in response.lower()
    assert not (root / ".scaleup" / "memory" / "escala.db").exists()


def _memory_digest(root: Path) -> str | None:
    path = root / ".scaleup" / "memory" / "escala.db"
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _memory_state_digest(root: Path) -> str | None:
    """Digest the observable memory state; SQLite may put writes in its WAL."""
    path = root / ".scaleup" / "memory" / "escala.db"
    if not path.is_file():
        return None
    try:
        with sqlite3.connect(path) as db:
            state = {
                "sessions": db.execute(
                    "SELECT status FROM project_memory_sessions ORDER BY id"
                ).fetchall(),
                "proposals": db.execute(
                    "SELECT response_state FROM session_memory_proposals ORDER BY id"
                ).fetchall(),
                "entries": db.execute(
                    "SELECT COUNT(*) FROM confirmed_memory_entries"
                ).fetchone(),
            }
    except sqlite3.DatabaseError:
        return None
    return hashlib.sha256(json.dumps(state, sort_keys=True).encode("utf-8")).hexdigest()


def _memory_counts(root: Path) -> tuple[int, int, int] | None:
    path = root / ".scaleup" / "memory" / "escala.db"
    if not path.is_file():
        return None
    try:
        with sqlite3.connect(path) as db:
            return tuple(
                db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in (
                    "project_memory_sessions",
                    "session_memory_proposals",
                    "confirmed_memory_entries",
                )
            )
    except sqlite3.DatabaseError:
        return None


def _prepare_public_flow(root: Path, flow: str) -> None:
    root.mkdir()
    if flow == "onboarding":
        return
    write_yaml(
        root / ".scaleup" / "agent" / "memory" / "company-profile.yaml",
        {"company": {"name": "Lumen Casa", "industry": "Retail", "employees": 28}},
    )
    states = {
        "diagnosis": {"stage": "diagnosis", "diagnosis_index": 0, "answers": {}},
        "plan": {"stage": "plan", "plan_step": 0, "plan": {}},
        "progress": {"stage": "post_plan"},
    }
    write_yaml(
        root / ".scaleup" / "agent" / "memory" / "conversation.yaml", states[flow]
    )


def _prepare_memory_fixture(root: Path, fixture: str) -> None:
    path = root / ".scaleup" / "memory" / "escala.db"
    if fixture == "empty":
        assert ProjectMemoryRuntime(root).ensure_memory().ready
    elif fixture == "corrupt":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"not a sqlite database")


@pytest.mark.parametrize("fixture", ("absent", "empty", "corrupt"))
@pytest.mark.parametrize("flow", ("onboarding", "diagnosis", "plan", "progress"))
def test_resume_fallback_preserves_each_public_flow_without_memory_writes(
    tmp_path: Path, fixture: str, flow: str
) -> None:
    from coaching.router.conversation import run

    baseline, project = tmp_path / "baseline", tmp_path / fixture
    _prepare_public_flow(baseline, flow)
    _prepare_public_flow(project, flow)
    _prepare_memory_fixture(project, fixture)
    before = _memory_digest(project)
    before_counts = _memory_counts(project)

    expected = run("retomemos", base_path=baseline)
    actual = run("retomemos", base_path=project)

    assert actual == expected
    assert _memory_digest(project) == before
    assert _memory_counts(project) == before_counts


def test_narrative_diagnosis_keeps_detail_qualitative_before_any_optional_score(tmp_path):
    from coaching.router.conversation import run

    root = tmp_path / "narrative-diagnosis"
    root.mkdir()
    run("quiero organizar mi empresa", base_path=root)
    run("Lumen Casa", base_path=root)
    run("Vendemos iluminación para hogares", base_path=root)
    run("12", base_path=root)
    first = run("ahora no", base_path=root)
    assert "escucharte antes de poner números" in first
    summary = run(
        "Tenemos dos líderes fuertes, pero ventas no tiene responsable claro y eso retrasó dos contratos este mes.",
        base_path=root,
    )
    assert "Entendí esto" in summary and "diagnóstico cualitativo" in summary
    next_question = run("sin calificación", base_path=root)
    assert "Strategy" in next_question
    assert "Respóndeme sólo con un número" not in summary


def test_intake_keeps_logo_and_url_as_references_not_company_description(tmp_path):
    from coaching.core import read_yaml
    from coaching.router.conversation import run

    root = tmp_path / "raise-intake"
    root.mkdir()
    run("quiero organizar mi empresa", base_path=root)
    question = run("RAISE te dejo el logo", base_path=root)
    assert "RAISE" in question and "logo" not in question.lower()
    url_reply = run("https://docs.raiseframework.ai/3.1/", base_path=root)
    assert "enlace como referencia" in url_reply
    run("Ayudamos a equipos a construir y mejorar agentes de IA.", base_path=root)
    run("5", base_path=root)
    profile = read_yaml(root / ".scaleup" / "agent" / "memory" / "company-profile.yaml")
    assert profile["company"]["name"] == "RAISE"
    assert "docs.raiseframework.ai" not in profile["company"]["industry"]
    assert profile["company"]["declared_references"][0]["kind"] == "attachment_reference"



def test_narrative_can_flow_into_cash_evidence_with_per_field_consent(tmp_path: Path) -> None:
    from coaching.router.conversation import run
    from escala_server.evidence import EvidenceStore

    root = tmp_path / "cash-evidence"
    root.mkdir()
    run("quiero organizar mi empresa", base_path=root)
    run("Lumen Casa", base_path=root)
    run("Vendemos iluminación", base_path=root)
    run("12", base_path=root)
    run("ahora no", base_path=root)
    offer = run("Tenemos dos líderes, pero no hay dueño claro de ventas.", base_path=root)
    assert "diagnóstico cualitativo" in offer
    run("mantener cualitativo", base_path=root)
    run("Atendemos hogares y queremos aclarar por qué nos eligen.", base_path=root)
    run("mantener cualitativo", base_path=root)
    run("La prioridad se atasca porque no la seguimos semanalmente.", base_path=root)
    run("mantener cualitativo", base_path=root)
    cash_offer = run("La cobranza se atrasa y no sabemos qué parte del efectivo queda atrapada.", base_path=root)
    assert "diagnóstico cualitativo" in cash_offer
    choice = run("cuantificar", base_path=root)
    assert "siete variables" in choice
    assert "precio" in choice and "días de pago" in choice
    assert "dato mínimo" in run("manual", base_path=root)
    for value in ("100", "50", "40", "1200", "30", "20", "15"):
        response = run(value, base_path=root)
    assert "Revisemos uno por uno" in response
    for _ in range(7):
        response = run("sí", base_path=root)
    assert "campos confirmados" in response
    snapshot = EvidenceStore(root).snapshot("cash")
    assert all(item["state"] == "confirmed" for item in snapshot["fields"].values())
    assert snapshot["fields"]["price"]["value"] == 100.0
