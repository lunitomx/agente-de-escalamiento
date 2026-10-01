"""S86.3: when something breaks, the owner reads one fixed sentence with a way out.

A1 — every ``python -m coaching.<module>`` entry point catches what breaks
(including the import of its flow) and prints a JSON whose ``message`` is the
fixed text. stdout never carries a traceback; the technical detail goes to
stderr for the bug report, and the exit code is 1 (as an uncaught error).

Limitation (said on purpose): ``python -m coaching.<pkg>`` imports the package
``__init__`` before ``__main__`` runs, so a break *there* (or Python missing)
cannot be caught in Python. ``escala/SKILL.md`` tells the agent to say the same
fixed sentence when a module returns no JSON.

A2 — Drive: file not found, no access, and a platform-neutral connect text.
No owner-facing text says "tu Claude".
"""

from __future__ import annotations

import ast
import io
import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

FIXED = (
    "No pude abrir esa parte de ESCALA en tu computadora. No se perdió nada. "
    "Escribe 'reportar problema' y preparo un aviso para el equipo."
)

# module run with ``python -m`` -> the function its entry point ends up calling
MAINS: dict[str, str] = {
    "coaching.dashboard": "coaching.dashboard.run",
    "coaching.dashboard.boards": "coaching.dashboard.boards.flow.run",
    "coaching.decision": "coaching.decision._main",
    "coaching.diagnose": "coaching.diagnose._main",
    "coaching.evidence": "coaching.evidence._main",
    "coaching.execution_habits": "coaching.execution_habits._main",
    "coaching.export": "coaching.export.run",
    "coaching.journey": "coaching.journey.flow.run",
    "coaching.level": "coaching.level._main",
    "coaching.people_facchart": "coaching.people_facchart._main",
    "coaching.progress": "coaching.progress._main",
    "coaching.pulse": "coaching.pulse.run",
    "coaching.qualifier": "coaching.qualifier._main",
    "coaching.research": "coaching.research.flow.run",
    "coaching.responder": "coaching.responder._main",
    "coaching.reviewer": "coaching.reviewer._main",
    "coaching.router": "coaching.router._main",
    "coaching.selector": "coaching.selector._main",
    "coaching.strategy_opsp": "coaching.strategy_opsp._main",
    "coaching.summary": "coaching.summary._main",
    "coaching.tracker": "coaching.tracker.flow.run",
    "coaching.welcome": "coaching.welcome._main",
    "coaching.worksheet": "coaching.worksheet._main",
}

# entry points whose flow is imported lazily, so a broken import is caught too
FLOWS = [
    "coaching.dashboard.boards",
    "coaching.journey",
    "coaching.research",
    "coaching.tracker",
]


def _boom(*_args: object, **_kwargs: object) -> object:
    raise RuntimeError("simulated failure: disk unplugged")


def _run_main(
    module: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> tuple[int | str | None, str, str]:
    monkeypatch.setattr(sys, "stdin", io.StringIO("{}"))
    monkeypatch.setattr(sys, "argv", [module])
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_module(module, run_name="__main__")
    out, err = capsys.readouterr()
    return exit_info.value.code, out, err


def _assert_fixed_failure(code: int | str | None, out: str, err: str) -> None:
    assert code == 1
    assert "Traceback" not in out
    result = json.loads(out)
    assert result["message"] == FIXED
    assert result["output"] == FIXED
    assert result["errors"] == ["internal_error"]
    assert result["artifacts"] == {}
    assert "Traceback" in err


def test_every_entry_point_is_covered() -> None:
    found = {
        ".".join(path.parent.relative_to(ROOT).parts)
        for path in (ROOT / "coaching").rglob("__main__.py")
    }
    assert found == set(MAINS)


def test_fixed_message_is_the_shared_one() -> None:
    from coaching.core.failsafe import SOMETHING_FAILED

    assert SOMETHING_FAILED == FIXED


@pytest.mark.parametrize("module", sorted(MAINS))
def test_a_broken_module_answers_with_the_fixed_message(
    module: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = MAINS[module]
    owner, _, name = target.rpartition(".")
    __import__(owner)
    monkeypatch.setattr(sys.modules[owner], name, _boom)

    code, out, err = _run_main(module, monkeypatch, capsys)

    _assert_fixed_failure(code, out, err)
    assert "disk unplugged" not in out
    assert "disk unplugged" in err


@pytest.mark.parametrize("module", FLOWS)
def test_a_broken_import_answers_with_the_fixed_message(
    module: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # ``None`` in sys.modules makes ``import`` raise ImportError, like a
    # missing dependency would.
    monkeypatch.setitem(sys.modules, f"{module}.flow", None)

    code, out, err = _run_main(module, monkeypatch, capsys)

    _assert_fixed_failure(code, out, err)


def test_a_real_process_keeps_the_traceback_out_of_stdout() -> None:
    script = (
        "import sys, runpy\n"
        "sys.modules['coaching.tracker.flow'] = None\n"
        "runpy.run_module('coaching.tracker', run_name='__main__')\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        input="{}",
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=60,
    )

    _assert_fixed_failure(proc.returncode, proc.stdout, proc.stderr)


def test_a_healthy_module_still_answers_normally(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"action": "ask_name"}'))
    monkeypatch.setattr(sys, "argv", ["coaching.tracker"])

    runpy.run_module("coaching.tracker", run_name="__main__")

    result = json.loads(capsys.readouterr().out)
    assert result["action"] == "ask_name"
    assert result["errors"] == []


# --- the skills say the same sentence ------------------------------------


def _skill(name: str) -> str:
    return (ROOT / "escala-skills" / name / "SKILL.md").read_text(encoding="utf-8")


def test_the_door_says_the_fixed_sentence_when_a_module_does_not_answer() -> None:
    door = _skill("escala")
    assert FIXED in door
    assert "internal_error" in door


@pytest.mark.parametrize("name", ["escala-dashboard", "escala-export", "escala-pulse"])
def test_skills_that_explain_errors_use_the_message_on_internal_error(
    name: str,
) -> None:
    assert "internal_error" in _skill(name)


def test_reportar_problema_opens_the_bug_report() -> None:
    assert "reportar problema" in _skill("escala-bugreport")


# --- A2: Drive ------------------------------------------------------------


def test_drive_file_not_found_asks_for_the_link() -> None:
    from coaching.tracker.flow import run

    result = run({"action": "drive_not_found"})

    assert result.message == (
        "Conecté Drive pero no veo tu archivo. ¿Me pegas el link de la hoja?"
    )
    assert result.errors == []


def test_drive_without_permission_offers_two_ways_out() -> None:
    from coaching.tracker.flow import run

    result = run({"action": "drive_no_access"})

    assert result.message == (
        "No tengo permiso para abrir ese archivo; pídele acceso a quien lo "
        "compartió o pega tu pestaña aquí."
    )
    assert result.errors == []


def test_connect_text_is_platform_neutral() -> None:
    from coaching.tracker.flow import run

    message = run({"action": "connect"}).message

    assert "en la configuración de este asistente, en Conectores o Apps" in message
    assert "Claude" not in message
    assert "ChatGPT" not in message


def test_tracker_skill_says_when_to_use_each_drive_case() -> None:
    skill = _skill("escala-execution-tracker")
    assert '"action": "drive_not_found"' in skill
    assert '"action": "drive_no_access"' in skill


def _python_literals(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]


def _owner_sources() -> dict[str, list[str]]:
    sources: dict[str, list[str]] = {}
    for path in (ROOT / "coaching").rglob("*.py"):
        if "tests" in path.parts or path.name.startswith("test_"):
            continue
        sources[str(path.relative_to(ROOT))] = _python_literals(path)
    for path in (ROOT / "escala-skills").rglob("*.md"):
        sources[str(path.relative_to(ROOT))] = [path.read_text(encoding="utf-8")]
    return sources


def test_no_owner_text_says_tu_claude() -> None:
    offenders = [
        where
        for where, texts in _owner_sources().items()
        if any("tu claude" in text.lower() for text in texts)
    ]
    assert offenders == []
