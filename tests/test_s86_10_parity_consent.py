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

import pytest

from adapters.agent_plugins.build_plugin import build_agent_plugin
from adapters.codex.build_adapter import build_codex_adapter
from escala_server.capabilities import load_capability_catalog, route_request
from tests.test_public_skill_installation import _portable_artifact
from tests.test_s86_4_front_door import AREA_ENTRIES, PHRASES, _plain
from validators.agent_plugin import AgentPluginError, load_agent_plugin

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


# --- T3: each package carries the list and the procedures the door needs -----

CATALOG_JSON = ROOT / "capabilities" / "mvp" / "catalog.json"


def _plugin_door(tmp_path: Path) -> Path:
    root = tmp_path / "plugin"
    root.mkdir(parents=True)
    package = build_agent_plugin(output=root / "escala", allowed_root=root)
    return package / "skills" / "escala"


def _codex_door(tmp_path: Path) -> Path:
    root = tmp_path / "codex-package"
    root.mkdir(parents=True)
    package = build_codex_adapter(
        catalog_path=CATALOG_JSON, output=root / "escala", allowed_root=root
    )
    return package / "skills" / "escala"


PACKAGES = {"plugin": _plugin_door, "codex": _codex_door}


def _package_reaches(door_dir: Path, phrase: str, procedure: str, hint: str | None) -> bool:
    """S86.4's reachability, read only from files inside the package."""
    procedures = door_dir / "references" / "procedures"
    catalog = load_capability_catalog(door_dir / "references" / "catalog.yaml")
    target = route_request(phrase, catalog=catalog).capability_id
    if not (procedures / f"{target}.md").is_file():
        return False
    if hint is None:
        return target == procedure
    if target not in AREA_ENTRIES or not (procedures / f"{procedure}.md").is_file():
        return False
    rows = [
        line
        for line in (procedures / f"{target}.md").read_text(encoding="utf-8").splitlines()
        if line.startswith("|")
    ]
    return any(f"`{procedure}`" in row and _plain(hint) in _plain(row) for row in rows)


@pytest.mark.parametrize("package", sorted(PACKAGES))
def test_owner_phrases_reach_procedures_inside_each_package(
    package: str, tmp_path: Path
) -> None:
    door_dir = PACKAGES[package](tmp_path)

    missing = [
        procedure
        for procedure, (phrase, hint) in sorted(PHRASES.items())
        if not _package_reaches(door_dir, phrase, procedure, hint)
    ]
    assert not missing


@pytest.mark.parametrize("package", sorted(PACKAGES))
def test_package_bundle_is_the_repo_byte_for_byte_and_hides_procedures(
    package: str, tmp_path: Path
) -> None:
    door_dir = PACKAGES[package](tmp_path)
    catalog = load_capability_catalog(ROOT / "escala-skills" / "catalog.yaml")
    ids = {c.id for c in catalog.capabilities} - {catalog.public_entrypoint}

    assert (door_dir / "references" / "catalog.yaml").read_bytes() == (
        ROOT / "escala-skills" / "catalog.yaml"
    ).read_bytes()
    shipped = {p.stem for p in (door_dir / "references" / "procedures").iterdir()}
    assert shipped == ids
    for procedure in ids:
        assert (door_dir / "references" / "procedures" / f"{procedure}.md").read_bytes() == (
            ROOT / "escala-skills" / procedure / "SKILL.md"
        ).read_bytes()
    # Only the door is a skill: no platform discovers a procedure as a command.
    package_root = door_dir.parents[1]
    assert [p.relative_to(package_root).as_posix() for p in package_root.rglob("SKILL.md")] == [
        "skills/escala/SKILL.md"
    ]


def test_door_says_where_the_list_and_procedures_live_in_a_package() -> None:
    door = DOOR.read_text(encoding="utf-8")

    assert "`references/catalog.yaml`" in door
    assert "`references/procedures/escala-*.md`" in door


def test_door_carries_the_product_python_rule_for_every_platform() -> None:
    door = re.sub(r"\s+", " ", DOOR.read_text(encoding="utf-8"))

    assert "`python3`" in door and "`.venv/bin/python`" in door


def test_plugin_rejects_a_tampered_or_extra_procedure(tmp_path: Path) -> None:
    door_dir = _plugin_door(tmp_path / "a")
    tampered = door_dir / "references" / "procedures" / "escala-diagnose.md"
    tampered.write_text(tampered.read_text(encoding="utf-8") + "\nOtra cosa.\n", encoding="utf-8")
    with pytest.raises(AgentPluginError, match="door_bundle_drift"):
        load_agent_plugin(door_dir.parents[1])

    door_dir = _plugin_door(tmp_path / "b")
    (door_dir / "references" / "procedures" / "escala-extra.md").write_text("x", encoding="utf-8")
    with pytest.raises(AgentPluginError, match="package_surface_invalid"):
        load_agent_plugin(door_dir.parents[1])


# --- T4: the four surfaces say the same thing and reach the same places -------

FAILURE_SENTENCE = (
    "No pude abrir esa parte de ESCALA en tu computadora. No se perdió nada. "
    "Escribe 'reportar problema' y preparo un aviso para el equipo."
)
CATALOG_REFERENCES = (
    "../../capabilities/mvp/catalog.json",
    "references/capability-catalog.json",
    "../../core/escala-capability-contract.json",
)


class _Surface:
    """Where the door, its list and its procedures are on one platform."""

    def __init__(self, door_dir: Path, *, packaged: bool) -> None:
        self.door = (door_dir / "SKILL.md").read_text(encoding="utf-8")
        if packaged:
            self.catalog = door_dir / "references" / "catalog.yaml"
            self._procedures = door_dir / "references" / "procedures"
        else:
            self.catalog = door_dir / ".." / "catalog.yaml"
            self._procedures = door_dir / ".."
        self.packaged = packaged

    def procedure(self, procedure_id: str) -> Path:
        if self.packaged:
            return self._procedures / f"{procedure_id}.md"
        return self._procedures / procedure_id / "SKILL.md"

    def reaches(self, phrase: str, procedure_id: str, hint: str | None) -> bool:
        catalog = load_capability_catalog(self.catalog)
        target = route_request(phrase, catalog=catalog).capability_id
        if not self.procedure(target).is_file():
            return False
        if hint is None:
            return target == procedure_id
        if target not in AREA_ENTRIES or not self.procedure(procedure_id).is_file():
            return False
        rows = [
            line
            for line in self.procedure(target).read_text(encoding="utf-8").splitlines()
            if line.startswith("|")
        ]
        return any(
            f"`{procedure_id}`" in row and _plain(hint) in _plain(row) for row in rows
        )


def _surfaces(tmp_path: Path) -> dict[str, _Surface]:
    home = tmp_path / "home"
    completed = _install(home, _fake_bin(tmp_path), "claude", "codex")
    assert completed.returncode == 0, completed.stderr
    return {
        "claude-install": _Surface(home / ".claude" / "skills" / "escala", packaged=False),
        "codex-install": _Surface(home / ".codex" / "skills" / "escala", packaged=False),
        "plugin": _Surface(_plugin_door(tmp_path), packaged=True),
        "codex-package": _Surface(_codex_door(tmp_path), packaged=True),
    }


def _neutral(door: str) -> str:
    for reference in CATALOG_REFERENCES:
        door = door.replace(reference, "<catalog.json>")
    return door


def test_all_surfaces_show_the_same_door_consent_and_failure_sentence(
    tmp_path: Path,
) -> None:
    surfaces = _surfaces(tmp_path)
    canonical = _neutral(DOOR.read_text(encoding="utf-8"))

    for name, surface in surfaces.items():
        assert _neutral(surface.door) == canonical, name
    consents = {consent_section(s.door) for s in surfaces.values()}
    assert len(consents) == 1
    for name, surface in surfaces.items():
        assert FAILURE_SENTENCE in surface.door, name


def test_all_surfaces_reach_the_same_procedures(tmp_path: Path) -> None:
    surfaces = _surfaces(tmp_path)

    reached = {
        name: {
            procedure
            for procedure, (phrase, hint) in PHRASES.items()
            if surface.reaches(phrase, procedure, hint)
        }
        for name, surface in surfaces.items()
    }

    assert all(found == set(PHRASES) for found in reached.values()), {
        name: sorted(set(PHRASES) - found) for name, found in reached.items()
    }


def test_all_surfaces_close_a_diagnosis_with_the_same_procedure(tmp_path: Path) -> None:
    """S86.5's closing (action + sheet offer) lives in escala-diagnose."""
    surfaces = _surfaces(tmp_path)
    source = (ROOT / "escala-skills" / "escala-diagnose" / "SKILL.md").read_bytes()

    for name, surface in surfaces.items():
        assert surface.procedure("escala-diagnose").read_bytes() == source, name
        assert surface.procedure("escala-bugreport").is_file(), name
