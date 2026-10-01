"""S86.10: the door asks for consent the same way on every platform (A4).

The old promise ("nunca envíes información fuera de la carpeta local") cannot
be kept on any hosted assistant: what the owner says is processed on the
assistant's servers (E85 spike §5c). The door now says what leaves and asks
for a separate "sí" before each step that sends or keeps something.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOOR = ROOT / "escala-skills" / "escala" / "SKILL.md"
INSTALLER = ROOT / "install.sh"
BEGIN = "<!-- ESCALA:BEGIN -->"
END = "<!-- ESCALA:END -->"

PLATFORM_NAMES = ("claude", "codex", "chatgpt", "openai", "anthropic", "hermes")


def consent_section(door: str) -> str:
    """The door's "## Consentimiento" section, title removed, one-line spaces."""
    match = re.search(r"^## Consentimiento\n(.*?)(?=^## |\Z)", door, re.M | re.S)
    assert match, "the door has no '## Consentimiento' section"
    return re.sub(r"\s+", " ", match.group(1)).strip()


def test_old_local_only_promise_is_gone() -> None:
    door = DOOR.read_text(encoding="utf-8")

    assert "fuera de la carpeta local" not in door
    assert "nunca sale de tu computadora" not in door.lower()


def test_consent_section_is_platform_neutral_and_short() -> None:
    consent = consent_section(DOOR.read_text(encoding="utf-8"))

    assert not [name for name in PLATFORM_NAMES if name in consent.lower()]
    assert len(consent.split()) <= 260


def test_consent_tells_the_truth_about_transmission() -> None:
    consent = consent_section(DOOR.read_text(encoding="utf-8"))

    assert "servidores" in consent
    assert "No le prometas que nada sale de su computadora" in consent


def test_consent_asks_before_each_step_with_a_real_example() -> None:
    consent = consent_section(DOOR.read_text(encoding="utf-8"))

    for step in ("Buscar en internet", "Guardar", "Escribir en su hoja", "Leer un archivo"):
        assert step in consent, step
    assert (
        "Para buscar precios de tu competencia voy a mandar a internet sólo "
        "'panadería en Puebla', sin tus números. ¿Va?"
    ) in consent
    # A "no" ends it for the conversation.
    assert "no lo vuelvas a pedir" in consent


def test_private_figures_never_leave_even_with_a_yes() -> None:
    """E83: searches never carry the company's names, people or figures."""
    consent = consent_section(DOOR.read_text(encoding="utf-8"))

    assert "ni con su sí" in consent
    assert "cifras" in consent


# --- T2: Codex gets the same ESCALA contract as Claude -----------------------


def _fake_bin(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    for name in ("claude", "codex"):
        stub = bin_dir / name
        stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        stub.chmod(0o755)
    return bin_dir


def _install(home: Path, bin_dir: Path, *platforms: str) -> subprocess.CompletedProcess[str]:
    args = ["bash", str(INSTALLER), "--skills-only"]
    for platform in platforms:
        args += ["--platform", platform]
    return subprocess.run(
        args,
        cwd=ROOT,
        env={"HOME": str(home), "PATH": str(bin_dir) + ":" + os.environ["PATH"]},
        capture_output=True,
        text=True,
        check=False,
        stdin=subprocess.DEVNULL,
    )


def _block(text: str) -> list[str]:
    lines = text.splitlines()
    return lines[lines.index(BEGIN) : lines.index(END) + 1]


def test_codex_install_writes_the_escala_contract_with_the_product_python(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    completed = _install(home, _fake_bin(tmp_path), "codex")

    assert completed.returncode == 0, completed.stderr
    agents = (home / ".codex" / "AGENTS.md").read_text(encoding="utf-8")
    assert agents.count(BEGIN) == 1 and agents.count(END) == 1
    assert f"{ROOT}/escala-skills/escala/SKILL.md" in agents
    assert f"`{ROOT}/.venv/bin/python`" in agents
    assert "# ESCALA for Codex" in agents


def test_codex_contract_keeps_owner_text_and_is_idempotent(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    agents_path = home / ".codex" / "AGENTS.md"
    agents_path.write_text("# Mis reglas\n\nHabla de tú.\n", encoding="utf-8")
    bin_dir = _fake_bin(tmp_path)

    for _ in range(2):
        assert _install(home, bin_dir, "codex").returncode == 0

    agents = agents_path.read_text(encoding="utf-8")
    assert agents.startswith("# Mis reglas\n\nHabla de tú.\n")
    assert agents.count(BEGIN) == 1


def test_malformed_codex_contract_is_not_touched_and_nothing_is_linked(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    agents_path = home / ".codex" / "AGENTS.md"
    agents_path.write_text(f"Mío\n{BEGIN}\nsin cierre\n", encoding="utf-8")

    completed = _install(home, _fake_bin(tmp_path), "codex")

    assert completed.returncode != 0
    assert agents_path.read_text(encoding="utf-8") == f"Mío\n{BEGIN}\nsin cierre\n"
    assert not (home / ".codex" / "skills" / "escala").exists()


def test_claude_and_codex_contracts_say_the_same_except_the_title(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    assert _install(home, _fake_bin(tmp_path), "claude", "codex").returncode == 0

    claude = _block((home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8"))
    codex = _block((home / ".codex" / "AGENTS.md").read_text(encoding="utf-8"))

    assert claude[1] == "# ESCALA for Claude Code"
    assert codex[1] == "# ESCALA for Codex"
    assert claude[:1] + claude[2:] == codex[:1] + codex[2:]


def test_codex_reuses_the_claude_template_without_a_second_copy() -> None:
    """One template, so the two contracts cannot drift; no new public file.

    A separate Codex template would be a new public-export selection and
    re-pin the master-acceptance ledger (36 receipts) for a one-line title.
    """
    assert not (ROOT / "adapters" / "codex" / "AGENTS.template.md").exists()
    policy = (ROOT / "governance" / "public-export.yaml").read_text(encoding="utf-8")
    assert "AGENTS.template.md" not in policy


def test_portable_export_carries_the_codex_contract(tmp_path: Path) -> None:
    """The owner's portable copy must install Codex the same way (no git)."""
    from tests.test_public_skill_installation import _portable_artifact

    artifact = _portable_artifact(tmp_path / "escala")

    home = tmp_path / "home"
    completed = subprocess.run(
        ["bash", str(artifact / "install.sh"), "--skills-only", "--platform", "codex"],
        cwd=artifact,
        env={"HOME": str(home), "PATH": str(_fake_bin(tmp_path)) + ":" + os.environ["PATH"]},
        capture_output=True,
        text=True,
        check=False,
        stdin=subprocess.DEVNULL,
    )

    assert completed.returncode == 0, completed.stderr
    assert f"`{artifact}/.venv/bin/python`" in (home / ".codex" / "AGENTS.md").read_text(
        encoding="utf-8"
    )
