"""End-to-end acceptance tests for the E10 cross-platform installer."""

import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALLER = REPO_ROOT / ".scaleup" / "install.sh"
ANSWERS = {
    f"{decision}_q{number}": score
    for decision, score in (
        ("people", 3),
        ("strategy", 2),
        ("execution", 4),
        ("cash", 1),
    )
    for number in range(1, 6)
}


def _install(destination_root: Path) -> None:
    subprocess.run(
        [
            "bash",
            str(INSTALLER),
            "--target",
            "all",
            "--destination-root",
            str(destination_root),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _installer(destination_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "bash",
            str(INSTALLER),
            "--destination-root",
            str(destination_root),
            *args,
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _say(command: Path, project: Path, message: str) -> str:
    return subprocess.run(
        [str(command), "conversation", message],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _memory_rows(project: Path) -> list[tuple[str, str, str, float]]:
    database = project / ".scaleup" / "memory" / "escala.db"
    if not database.is_file():
        return []
    with sqlite3.connect(database) as connection:
        return connection.execute(
            """SELECT statement, source, status, confirmation_confidence
               FROM confirmed_memory_entries ORDER BY id"""
        ).fetchall()


def _stable_memory_state(project: Path) -> list[tuple[str, str, str, float]]:
    return [
        (statement, json.loads(source)["origin"], status, confidence)
        for statement, source, status, confidence in _memory_rows(project)
    ]


def _memory_digest_and_counts(project: Path) -> tuple[str | None, tuple[int, int, int]]:
    database = project / ".scaleup" / "memory" / "escala.db"
    if not database.is_file():
        return None, (0, 0, 0)
    tables = (
        "project_memory_sessions",
        "session_memory_proposals",
        "confirmed_memory_entries",
    )
    with sqlite3.connect(database) as connection:
        rows = tuple(
            (table, tuple(connection.execute(f"SELECT * FROM {table} ORDER BY id")))
            for table in tables
        )
    counts = tuple(len(table_rows) for _, table_rows in rows)
    return hashlib.sha256(repr(rows).encode()).hexdigest(), counts


def _installed_memory(
    runtime: Path, project: Path, action: str, backup: Path | None = None
) -> dict:
    code = """
import json
import sys
from escala_server import ProjectMemoryRuntime

runtime = ProjectMemoryRuntime(sys.argv[1])
if sys.argv[2] == "backup":
    result = runtime.backup()
elif sys.argv[2] == "restore":
    result = runtime.restore(sys.argv[3])
else:
    result = runtime.ensure_memory()
print(json.dumps({"ready": result.ready, "reason": result.reason,
                  "backup_path": str(result.backup_path) if result.backup_path else None}))
"""
    arguments = [sys.executable, "-c", code, str(project), action]
    if backup is not None:
        arguments.append(str(backup))
    result = subprocess.run(
        arguments,
        env={"PYTHONPATH": str(runtime)},
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def _run_engine(runtime_root: Path, project: Path, module: str, context: dict) -> dict:
    code = (
        f"from coaching.{module} import run; "
        "import json, sys; "
        "print(json.dumps(run(json.loads(sys.stdin.read())), ensure_ascii=False))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=project,
        input=json.dumps(context),
        env={"PYTHONPATH": str(runtime_root)},
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def _run_flow(runtime_root: Path, project: Path) -> tuple[dict, dict]:
    project.mkdir()
    welcome = _run_engine(
        runtime_root,
        project,
        "welcome",
        {
            "company_name": "Clean Room Co",
            "industry": "Software",
            "employees": 25,
            "entry_methodology": "bmc",
            "base_path": ".",
        },
    )
    assert welcome["errors"] == []

    profile = project / ".scaleup" / "agent" / "memory" / "company-profile.yaml"
    subprocess.run(
        [
            sys.executable,
            str(runtime_root / "agent" / "validators" / "welcome.py"),
            str(profile),
        ],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
    )

    diagnose = _run_engine(
        runtime_root,
        project,
        "diagnose",
        {"answers": ANSWERS, "base_path": ".", "mode": "full"},
    )
    assert diagnose["errors"] == []
    subprocess.run(
        [
            sys.executable,
            str(runtime_root / "agent" / "validators" / "diagnose.py"),
            str(profile),
        ],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
    )
    return welcome, diagnose


def test_installer_targets_are_isolated_and_adapted(tmp_path):
    _install(tmp_path)

    for platform in (".claude", ".hermes", ".codex"):
        platform_root = tmp_path / platform
        runtime_root = platform_root / "scaleup"
        skills_root = platform_root / "skills"

        assert sorted(path.name for path in skills_root.iterdir()) == ["scaleup"]
        assert (runtime_root / "VERSION").read_text().strip() == "1.0.0"
        assert (runtime_root / "coaching" / "welcome" / "__init__.py").is_file()
        assert (runtime_root / "coaching" / "summary" / "__init__.py").is_file()
        assert (runtime_root / "coaching" / "opsp.py").is_file()
        assert (runtime_root / "bin" / "scaleup-frontdoor").is_file()
        skill = (skills_root / "scaleup" / "SKILL.md").read_text()
        assert "python3 -c" not in skill
        assert str(runtime_root / "bin" / "scaleup-frontdoor") in skill
        assert ".scaleup/agent" not in skill
        assert "validate-opsp" in skill


def test_installer_never_distributes_source_company_memory_or_backups(tmp_path):
    """Source-company data is never part of the distributed runtime payload."""
    source = tmp_path / "source"
    shutil.copytree(
        REPO_ROOT,
        source,
        ignore=shutil.ignore_patterns(".git", "__pycache__"),
    )
    agent_memory = source / ".scaleup" / "agent" / "memory"
    scaleup_memory = source / ".scaleup" / "memory"
    for path in (
        agent_memory / "company-profile.yaml",
        agent_memory / "conversation.yaml",
        agent_memory / "escala.db",
        agent_memory / "backups" / "snapshot.db",
        scaleup_memory / "escala.db",
        scaleup_memory / "backups" / "snapshot.db",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"source-company-data")

    destination = tmp_path / "destination"
    subprocess.run(
        [
            "bash",
            str(source / ".scaleup" / "install.sh"),
            "--target",
            "all",
            "--destination-root",
            str(destination),
        ],
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
    )

    for platform in (".claude", ".hermes", ".codex"):
        runtime = destination / platform / "scaleup"
        assert not (runtime / "agent" / "memory").exists()
        assert not any(
            path.name in {"company-profile.yaml", "conversation.yaml", "escala.db"}
            or "backups" in path.parts
            for path in runtime.rglob("*")
        )


def test_clean_project_flow_is_equivalent_for_claude_and_hermes(tmp_path):
    _install(tmp_path)

    claude_welcome, claude_diagnose = _run_flow(
        tmp_path / ".claude" / "scaleup", tmp_path / "claude-project"
    )
    hermes_welcome, hermes_diagnose = _run_flow(
        tmp_path / ".hermes" / "scaleup", tmp_path / "hermes-project"
    )

    assert claude_welcome["output"] == hermes_welcome["output"]
    assert (
        claude_welcome["artifacts"]["profile"] == hermes_welcome["artifacts"]["profile"]
    )
    assert claude_diagnose["output"] == hermes_diagnose["output"]
    assert (
        claude_diagnose["artifacts"]["scores"] == hermes_diagnose["artifacts"]["scores"]
    )
    assert claude_diagnose["artifacts"]["priority"] == "cash"


def test_codex_install_update_and_targeted_uninstall_preserve_company_data(tmp_path):
    _installer(tmp_path, "--target", "codex")

    codex = tmp_path / ".codex"
    runtime = codex / "scaleup"
    skills = codex / "skills"
    company_note = runtime / "my-company" / "worksheets" / "important.txt"
    company_note.write_text("keep me")
    legacy_skill = skills / "scaleup-welcome"
    legacy_skill.mkdir()
    (legacy_skill / "SKILL.md").write_text("legacy")
    unrelated_skill = skills / "scaleup-unrelated"
    unrelated_skill.mkdir()
    (unrelated_skill / "SKILL.md").write_text("third party")
    stale_knowledge = runtime / "knowledge" / "obsolete.txt"
    stale_knowledge.write_text("stale")
    stale_agent = runtime / "agent" / "obsolete.txt"
    stale_agent.write_text("stale")

    # A repeat install is an upgrade: managed content is synchronized, company
    # content is not part of the managed payload and must survive.
    _installer(tmp_path, "--target", "codex")
    assert company_note.read_text() == "keep me"
    assert not legacy_skill.exists()
    assert unrelated_skill.joinpath("SKILL.md").read_text() == "third party"
    assert not stale_knowledge.exists()
    assert not stale_agent.exists()
    assert sorted(path.name for path in skills.iterdir()) == [
        "scaleup",
        "scaleup-unrelated",
    ]
    assert runtime.joinpath("VERSION").read_text().strip() == "1.0.0"

    _installer(tmp_path, "--target", "codex", "--uninstall")
    assert company_note.read_text() == "keep me"
    assert not runtime.joinpath("coaching").exists()
    assert not skills.joinpath("scaleup").exists()
    assert unrelated_skill.joinpath("SKILL.md").read_text() == "third party"

    _installer(tmp_path, "--target", "codex", "--uninstall", "--purge")
    assert not runtime.exists()


def test_bare_uninstall_removes_all_managed_targets_and_preserves_company_data(
    tmp_path,
):
    _installer(tmp_path, "--target", "codex")

    runtime = tmp_path / ".codex" / "scaleup"
    skills = tmp_path / ".codex" / "skills"
    company_note = runtime / "my-company" / "worksheets" / "important.txt"
    company_note.write_text("keep me")

    _installer(tmp_path, "--uninstall")

    assert company_note.read_text() == "keep me"
    assert not runtime.joinpath("coaching").exists()
    assert not runtime.joinpath("VERSION").exists()
    assert not skills.joinpath("scaleup").exists()


def test_installed_codex_runtime_recovers_progress_and_validates_opsp(tmp_path):
    _installer(tmp_path, "--target", "codex")
    runtime, project = tmp_path / ".codex" / "scaleup", tmp_path / "clean-project"
    project.mkdir()
    welcome = _run_engine(
        runtime,
        project,
        "welcome",
        {
            "company_name": "Lumen Casa",
            "industry": "Retail",
            "employees": 28,
            "entry_methodology": "bmc",
            "base_path": ".",
        },
    )
    assert welcome["errors"] == []
    progress = _run_engine(runtime, project, "progress", {"base_path": "."})
    assert (
        progress["errors"] == [] and progress["artifacts"]["next_step"] == "diagnosis"
    )
    plan = _run_engine(
        runtime,
        project,
        "opsp",
        {
            "base_path": ".",
            "complete": True,
            "data": {
                "company_name": "Lumen Casa",
                "core_values": ["Diseño", "Servicio", "Cumplimiento"],
                "purpose": "Iluminar hogares",
                "bhag": "Ser líder nacional",
                "bhag_date": "2036",
                "sandbox": {"market": "México"},
                "brand_promise": {"promise": "Entrega 72 horas", "kpi": "% puntual"},
                "quarter": "Q3 2026",
                "critical_number": "95% puntual",
                "year": "2026",
                "annual_revenue": "$10M",
                "annual_profit": "$1M",
                "annual_priorities": [
                    {"priority": "Crecer", "owner": "Ana", "kpi": "Ventas"}
                ],
                "quarterly_priorities": [
                    {"priority": "Inventario", "owner": "Luis", "kpi": "Faltantes"}
                ],
            },
        },
    )
    assert plan["errors"] == [] and plan["artifacts"]["status"] == "completed"
    artifact = project / "work" / "strategy" / "opsp.md"
    subprocess.run(
        [
            sys.executable,
            str(runtime / "agent" / "validators" / "opsp.py"),
            str(artifact),
        ],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
    )


def test_installed_public_journey_never_exposes_legacy_commands(tmp_path):
    _install(tmp_path)
    welcome, diagnose = _run_flow(
        tmp_path / ".codex" / "scaleup", tmp_path / "natural-project"
    )
    assert "/scaleup-" not in welcome["output"]
    assert "/scaleup-" not in diagnose["output"]


def test_safe_frontdoor_executes_in_checkout_and_installed_runtime(tmp_path):
    project = tmp_path / "natural-project"
    project.mkdir()
    _installer(tmp_path, "--target", "codex")
    commands = (
        REPO_ROOT / ".scaleup" / "bin" / "scaleup-frontdoor",
        tmp_path / ".codex" / "scaleup" / "bin" / "scaleup-frontdoor",
    )
    for index, command in enumerate(commands):
        command_project = project / str(index)
        command_project.mkdir()
        response = subprocess.run(
            [str(command), "no sé por dónde empezar"],
            cwd=command_project,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "¿Cómo se llama y a qué se dedica" in response.stdout
        welcome = subprocess.run(
            [
                str(command),
                "run",
                "welcome",
                json.dumps(
                    {
                        "company_name": "Lumen Casa",
                        "industry": "Retail",
                        "employees": 28,
                        "entry_methodology": "bmc",
                    }
                ),
            ],
            cwd=command_project,
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(welcome.stdout)["errors"] == []
        for action, payload in (
            ("diagnose", {"answers": ANSWERS, "mode": "full"}),
            ("progress", {}),
            ("opsp", {"data": {}}),
        ):
            handoff = subprocess.run(
                [str(command), "run", action, json.dumps(payload)],
                cwd=command_project,
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(handoff.stdout)
            assert {"output", "artifacts", "errors"} <= result.keys()
        validation = subprocess.run(
            [str(command), "validate-opsp", "work/strategy/opsp.md"],
            cwd=command_project,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "valid" in json.loads(validation.stdout)
        invalid = subprocess.run(
            [str(command), "run", "unexpected", "{}"],
            cwd=command_project,
            capture_output=True,
            text=True,
            check=False,
        )
        assert invalid.returncode == 2


def test_installer_copies_local_memory_runtime_and_preserves_memory_data(tmp_path):
    _install(tmp_path)

    for platform in (".claude", ".hermes", ".codex"):
        runtime = tmp_path / platform / "scaleup"
        memory_runtime = runtime / "escala_server"
        assert (memory_runtime / "project_memory.py").is_file()
        assert (memory_runtime / "project_memory_migration.py").is_file()
        assert (memory_runtime / "schema.py").is_file()
        assert not (memory_runtime / "server.py").exists()
        project = tmp_path / f"{platform}-project"
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                "from escala_server import ProjectMemoryRuntime; "
                "assert ProjectMemoryRuntime('"
                + str(project)
                + "').ensure_memory().ready",
            ],
            env={"PYTHONPATH": str(runtime)},
            check=True,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0

    runtime = tmp_path / ".codex" / "scaleup"
    memory_note = runtime / "memory" / "keep.txt"
    memory_note.parent.mkdir(parents=True)
    memory_note.write_text("keep me")
    _installer(tmp_path, "--target", "codex")
    _installer(tmp_path, "--target", "codex", "--uninstall")
    assert memory_note.read_text() == "keep me"


def test_installed_runtime_migrates_legacy_project_without_checkout(tmp_path):
    """The installed module owns the real, idempotent legacy migration."""
    _installer(tmp_path, "--target", "codex")
    runtime = tmp_path / ".codex" / "scaleup"
    project = tmp_path / "legacy-project"
    profile = project / ".scaleup" / "agent" / "memory" / "company-profile.yaml"
    profile.parent.mkdir(parents=True)
    profile.write_text(
        "company:\n  name: Lumen Casa\n  industry: Interiores\n"
        "scores:\n  strategy: 6\n",
        encoding="utf-8",
    )

    code = """
import json
import sqlite3
import sys
from escala_server.project_memory_migration import ProjectMemoryMigrator

project = sys.argv[1]
first = ProjectMemoryMigrator(project).migrate()
second = ProjectMemoryMigrator(project).migrate()
with sqlite3.connect(first.db_path) as connection:
    source = connection.execute(
        "SELECT relative_path, source_kind FROM migration_sources"
    ).fetchall()
    applications = connection.execute(
        "SELECT COUNT(*) FROM migration_applications"
    ).fetchone()[0]
    company = connection.execute("SELECT name FROM companies").fetchone()[0]
print(json.dumps({
    "first_ready": first.ready,
    "first_imported": first.imported,
    "second_imported": second.imported,
    "second_skipped": second.skipped,
    "source": source,
    "applications": applications,
    "company": company,
}))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code, str(project)],
        cwd=project,
        env={"PYTHONPATH": str(runtime)},
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)

    assert result["first_ready"] is True
    assert result["first_imported"] == {"company-profile": 1}
    assert result["second_imported"] == {}
    assert (
        result["second_skipped"][".scaleup/agent/memory/company-profile.yaml"]
        == "unchanged"
    )
    assert result["source"] == [
        [".scaleup/agent/memory/company-profile.yaml", "company-profile"]
    ]
    assert result["applications"] == 1
    assert result["company"] == "Lumen Casa"


def test_installed_frontdoors_reconcile_legacy_sources_idempotently(tmp_path):
    _install(tmp_path)
    for platform in ("claude", "codex"):
        runtime = tmp_path / f".{platform}" / "scaleup"
        command = runtime / "bin" / "scaleup-frontdoor"
        project = tmp_path / f"{platform}-legacy"
        profile = project / ".scaleup" / "agent" / "memory" / "company-profile.yaml"
        profile.parent.mkdir(parents=True)
        profile.write_text(
            "company:\n  name: Lumen Casa\n  industry: Interiores\n"
            "scores:\n  strategy: 6\n",
            encoding="utf-8",
        )

        resumed = _say(command, project, "retomemos")
        database = project / ".scaleup" / "memory" / "escala.db"
        with sqlite3.connect(database) as connection:
            first = connection.execute(
                "SELECT content_sha256 FROM migration_sources"
            ).fetchone()[0]
            assert (
                connection.execute(
                    "SELECT COUNT(*) FROM migration_applications"
                ).fetchone()[0]
                == 1
            )
        assert "6" in resumed

        _say(command, project, "retomemos")
        with sqlite3.connect(database) as connection:
            second = connection.execute(
                "SELECT content_sha256 FROM migration_sources"
            ).fetchone()[0]
            assert (
                connection.execute(
                    "SELECT COUNT(*) FROM migration_applications"
                ).fetchone()[0]
                == 1
            )
        assert second == first


def test_installed_handoff_reconciles_new_profile_idempotently(tmp_path):
    _installer(tmp_path, "--target", "codex")
    runtime = tmp_path / ".codex" / "scaleup"
    command = runtime / "bin" / "scaleup-frontdoor"
    project = tmp_path / "welcome-project"
    project.mkdir()
    payload = json.dumps(
        {
            "company_name": "Lumen Casa",
            "industry": "Interiores",
            "employees": 12,
            "entry_methodology": "bmc",
        }
    )

    for _ in range(2):
        result = subprocess.run(
            [str(command), "run", "welcome", payload],
            cwd=project,
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(result.stdout)["errors"] == []

    database = project / ".scaleup" / "memory" / "escala.db"
    with sqlite3.connect(database) as connection:
        source = connection.execute(
            "SELECT relative_path, content_sha256 FROM migration_sources"
        ).fetchall()
        applications = connection.execute(
            "SELECT COUNT(*) FROM migration_applications"
        ).fetchone()[0]
    assert source == [(".scaleup/agent/memory/company-profile.yaml", source[0][1])]
    assert applications == 1


def test_installed_frontdoor_pauses_confirms_and_resumes_naturally(tmp_path):
    _installer(tmp_path, "--target", "codex")
    runtime = tmp_path / ".codex" / "scaleup"
    command = runtime / "bin" / "scaleup-frontdoor"
    project = tmp_path / "continuity-project"
    project.mkdir()

    def say(message: str) -> str:
        return subprocess.run(
            [str(command), "conversation", message],
            cwd=project,
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    assert (runtime / "escala_server" / "project_memory_public_text.py").is_file()
    pause = say("quiero pausar")
    assert "qué decisión o dato" in pause.lower()
    proposal = say("Contrataremos una líder de ventas en septiembre")
    assert "quieres que lo recuerde" in proposal.lower()
    confirmed = say("sí")
    assert "próxima vez" in confirmed.lower()
    resumed = say("retomemos")
    assert "líder de ventas" in resumed.lower()
    assert all(
        forbidden not in resumed.lower()
        for forbidden in (
            ".scaleup",
            "sqlite",
            "database",
            "base de datos",
            "session",
            "sesión",
            "skill",
            "comando",
            "ruta",
        )
    )


def test_installed_frontdoor_rejection_and_ambiguity_only_write_expected_state(
    tmp_path,
):
    _installer(tmp_path, "--target", "codex")
    command = tmp_path / ".codex" / "scaleup" / "bin" / "scaleup-frontdoor"

    rejected = tmp_path / "rejected"
    rejected.mkdir()
    assert _memory_digest_and_counts(rejected) == (None, (0, 0, 0))
    assert "qué decisión o dato" in _say(command, rejected, "quiero pausar").lower()
    assert (
        "quieres que lo recuerde"
        in _say(command, rejected, "Abriremos una oficina en Querétaro").lower()
    )
    proposed_digest, proposed_counts = _memory_digest_and_counts(rejected)
    assert proposed_digest is not None and proposed_counts == (1, 1, 0)
    assert "no lo voy a guardar" in _say(command, rejected, "no").lower()
    rejected_digest, rejected_counts = _memory_digest_and_counts(rejected)
    assert rejected_digest != proposed_digest and rejected_counts == (1, 1, 0)
    assert _memory_rows(rejected) == []

    ambiguous = tmp_path / "ambiguous"
    ambiguous.mkdir()
    assert _memory_digest_and_counts(ambiguous) == (None, (0, 0, 0))
    _say(command, ambiguous, "quiero pausar")
    _say(command, ambiguous, "Abriremos una oficina en Querétaro")
    before_digest, before_counts = _memory_digest_and_counts(ambiguous)
    assert before_digest is not None and before_counts == (1, 1, 0)
    assert "no lo voy a dar por hecho" in _say(command, ambiguous, "tal vez").lower()
    assert _memory_digest_and_counts(ambiguous) == (before_digest, before_counts)
    assert _memory_rows(ambiguous) == []


def test_release_installed_frontdoors_preserve_local_memory_and_isolation(tmp_path):
    _install(tmp_path)
    statement = "Contrataremos una líder de ventas en septiembre"
    journeys = {}
    persisted_state = {}
    for target in ("claude", "codex", "hermes"):
        runtime = tmp_path / f".{target}" / "scaleup"
        command = runtime / "bin" / "scaleup-frontdoor"
        project = tmp_path / f"{target}-company"
        project.mkdir()

        assert sorted(
            path.name for path in (tmp_path / f".{target}" / "skills").iterdir()
        ) == ["scaleup"]
        assert command.is_file()
        assert not (runtime / ".scaleup").exists()
        assert not (runtime / "memory").exists()
        pause = _say(command, project, "quiero pausar")
        proposal = _say(command, project, statement)
        confirmed = _say(command, project, "sí")
        resumed = _say(command, project, "retomemos")
        assert "qué decisión o dato" in pause.lower()
        assert "quieres que lo recuerde" in proposal.lower()
        assert "próxima vez" in confirmed.lower()
        resumed = resumed.lower()
        assert statement.lower() in resumed
        assert all(
            token not in resumed
            for token in (
                ".scaleup",
                "sqlite",
                "database",
                "base de datos",
                "skill",
                "comando",
                "ruta",
            )
        )
        rows = _memory_rows(project)
        assert len(rows) == 1
        assert rows[0][0] == statement
        assert json.loads(rows[0][1])["origin"] == "explicit_user_statement"
        assert rows[0][2:] == ("active", 1.0)
        journeys[target] = (pause, proposal, confirmed, resumed)
        persisted_state[target] = _stable_memory_state(project)

    assert journeys["claude"] == journeys["codex"] == journeys["hermes"]
    assert (
        persisted_state["claude"]
        == persisted_state["codex"]
        == persisted_state["hermes"]
    )
    isolated = tmp_path / "isolated-company"
    isolated.mkdir()
    assert statement not in _say(
        tmp_path / ".codex" / "scaleup" / "bin" / "scaleup-frontdoor",
        isolated,
        "retomemos",
    )
    assert (tmp_path / "claude-company" / ".scaleup" / "memory" / "escala.db").is_file()
    assert (tmp_path / "codex-company" / ".scaleup" / "memory" / "escala.db").is_file()
    assert not any(
        (tmp_path / f".{target}" / "scaleup" / "memory").exists() for target in journeys
    )


def test_release_installed_frontdoor_rejects_sensitive_text_and_falls_back_without_writes(
    tmp_path,
):
    _installer(tmp_path, "--target", "codex")
    runtime = tmp_path / ".codex" / "scaleup"
    command = runtime / "bin" / "scaleup-frontdoor"
    sensitive = "La contraseña del ERP es 1234"
    project = tmp_path / "sensitive-company"
    project.mkdir()

    assert "qué decisión o dato" in _say(command, project, "quiero pausar").lower()
    reply = _say(command, project, sensitive).lower()
    assert "no voy a guardar nada" in reply
    assert sensitive.lower() not in reply
    assert _memory_rows(project) == []
    assert (
        sensitive.lower()
        not in (project / ".scaleup" / "memory" / "escala.db")
        .read_bytes()
        .decode("latin1")
        .lower()
    )

    for fixture in ("absent", "empty", "corrupt"):
        baseline, candidate = (
            tmp_path / f"baseline-{fixture}",
            tmp_path / f"candidate-{fixture}",
        )
        baseline.mkdir()
        candidate.mkdir()
        if fixture == "empty":
            assert _installed_memory(runtime, candidate, "ensure")["ready"] is True
        elif fixture == "corrupt":
            database = candidate / ".scaleup" / "memory" / "escala.db"
            database.parent.mkdir(parents=True)
            database.write_bytes(b"not a sqlite database")
            profile = (
                candidate / ".scaleup" / "agent" / "memory" / "company-profile.yaml"
            )
            profile.parent.mkdir(parents=True)
            profile.write_text("company:\n  name: Lumen Casa\n", encoding="utf-8")
            baseline_profile = (
                baseline / ".scaleup" / "agent" / "memory" / "company-profile.yaml"
            )
            baseline_profile.parent.mkdir(parents=True)
            baseline_profile.write_bytes(profile.read_bytes())
        before = (
            (candidate / ".scaleup" / "memory" / "escala.db").read_bytes()
            if fixture == "corrupt"
            else None
        )
        profile_before = profile.read_bytes() if fixture == "corrupt" else None
        actual = _say(command, candidate, "retomemos")
        if fixture == "corrupt":
            assert "ahora revisaremos cuatro áreas" in actual.lower()
        else:
            assert actual == _say(command, baseline, "retomemos")
        database = candidate / ".scaleup" / "memory" / "escala.db"
        if fixture == "absent":
            assert not database.exists()
        elif fixture == "corrupt":
            assert database.read_bytes() == before
            assert profile.read_bytes() == profile_before
        else:
            assert _memory_rows(candidate) == []


def test_release_backup_restore_and_targeted_removal_are_conservative(tmp_path):
    _installer(tmp_path, "--target", "codex")
    runtime = tmp_path / ".codex" / "scaleup"
    command = runtime / "bin" / "scaleup-frontdoor"
    project, other = tmp_path / "company", tmp_path / "other-company"
    project.mkdir()
    other.mkdir()
    _say(command, project, "quiero pausar")
    _say(command, project, "Abriremos una tienda en Monterrey")
    _say(command, project, "sí")
    expected = _memory_rows(project)
    backup = _installed_memory(runtime, project, "backup")
    assert backup["ready"] is True
    backup_path = Path(backup["backup_path"])
    assert backup_path.is_file() and backup_path.is_relative_to(
        project / ".scaleup" / "memory" / "backups"
    )
    database = project / ".scaleup" / "memory" / "escala.db"
    database.unlink()
    assert _installed_memory(runtime, project, "restore", backup_path)["ready"] is True
    assert _memory_rows(project) == expected
    assert "abriremos una tienda" in _say(command, project, "retomemos").lower()

    _say(command, other, "quiero pausar")
    _say(command, other, "Mantendremos el almacén actual")
    _say(command, other, "sí")
    other_before = _memory_digest_and_counts(other)
    cross_company = _installed_memory(runtime, other, "restore", backup_path)
    assert cross_company["ready"] is False
    assert _memory_digest_and_counts(other) == other_before

    invalid = project / ".scaleup" / "memory" / "backups" / "invalid.db"
    invalid.write_bytes(b"not a sqlite database")
    preserved = _memory_rows(project)
    assert _installed_memory(runtime, project, "restore", invalid)["ready"] is False
    assert _memory_rows(project) == preserved
    assert "abriremos una tienda" not in _say(command, other, "retomemos").lower()

    company_note = runtime / "my-company" / "worksheets" / "keep.txt"
    company_note.write_text("keep")
    _installer(tmp_path, "--target", "codex")
    _installer(tmp_path, "--target", "codex", "--uninstall")
    assert company_note.read_text() == "keep"
    assert _memory_rows(project) == expected and backup_path.is_file()
    _installer(tmp_path, "--target", "codex", "--uninstall", "--purge")
    assert not runtime.exists()
    assert _memory_rows(project) == expected and backup_path.is_file()
