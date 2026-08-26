"""Regression coverage for the no-JSON public ScaleUp conversation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

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
    first_question = _say(command, project, "28")
    assert "Del 1 al 5" in first_question

    # A fresh process keeps the same question/answer state: the public command
    # receives only natural text, never onboarding or diagnosis keys.
    assert "core values" in _say(command, project, "3").lower()
    state = project / ".scaleup" / "agent" / "memory" / "conversation.yaml"
    assert state.is_file() and "people_q1: 3" in state.read_text(encoding="utf-8")
    for _ in range(19):
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
    assert "Del 1 al 5" in response
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
    assert run("no", base_path=root).lower().startswith("de acuerdo")
    close = ProjectMemorySessionClose(root)
    assert close.runtime.health().ready
    import sqlite3

    with sqlite3.connect(close.runtime.db_path) as db:
        assert (
            db.execute("SELECT COUNT(*) FROM confirmed_memory_entries").fetchone()[0]
            == 0
        )
