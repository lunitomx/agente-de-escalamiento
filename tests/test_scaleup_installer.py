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

    for platform in (".claude", ".hermes"):
        platform_root = tmp_path / platform
        runtime_root = platform_root / "scaleup"
        skills = list((platform_root / "skills").glob("scaleup-*/SKILL.md"))

        assert len(skills) == 39
        assert (runtime_root / "VERSION").read_text().strip() == "1.0.0"
        assert (runtime_root / "coaching" / "welcome" / "__init__.py").is_file()

        for skill_name, validator_name in (
            ("scaleup-welcome", "welcome.py"),
            ("scaleup-diagnose", "diagnose.py"),
        ):
            skill = (platform_root / "skills" / skill_name / "SKILL.md").read_text()
            assert "sys.path.insert(0, '.')" not in skill
            assert f"sys.path.insert(0, '{runtime_root}')" in skill
            assert str(runtime_root / "agent" / "validators" / validator_name) in skill


def test_clean_project_flow_is_equivalent_for_claude_and_hermes(tmp_path):
    _install(tmp_path)

    claude_welcome, claude_diagnose = _run_flow(
        tmp_path / ".claude" / "scaleup", tmp_path / "claude-project"
    )
    hermes_welcome, hermes_diagnose = _run_flow(
        tmp_path / ".hermes" / "scaleup", tmp_path / "hermes-project"
    )

    assert claude_welcome["output"] == hermes_welcome["output"]
    assert claude_welcome["artifacts"]["profile"] == hermes_welcome["artifacts"]["profile"]
    assert claude_diagnose["output"] == hermes_diagnose["output"]
    assert claude_diagnose["artifacts"]["scores"] == hermes_diagnose["artifacts"]["scores"]
    assert claude_diagnose["artifacts"]["priority"] == "cash"
