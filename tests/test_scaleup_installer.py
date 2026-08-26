"""End-to-end acceptance tests for the E10 cross-platform installer."""

import json
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
