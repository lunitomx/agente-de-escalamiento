"""What the ESCALA door needs beside it inside a package (S86.10).

The door reads one list (``catalog.yaml``) and follows the internal procedure
it names.  In the repository copy those live in ``escala-skills/``; a package
(Agent Plugin, Codex adapter) carries them under the door's ``references/``.
Procedures are named ``<id>.md`` there, never ``SKILL.md``, so no platform
discovers them as public skills.  Every file is the repository file byte for
byte: the package never rewrites a procedure.

The Maestro Humberto's Cash cards (S86.11) travel the same way, under
``references/knowledge/cash/``, so a packaged ESCALA quotes him from the very
cards the repository holds.
"""

from __future__ import annotations

from pathlib import Path
import shutil

from escala_server.capabilities import load_capability_catalog

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPOSITORY_ROOT / "escala-skills"
REFERENCES_DIRECTORY = "references"
CATALOG_REFERENCE = f"{REFERENCES_DIRECTORY}/catalog.yaml"
PROCEDURES_DIRECTORY = f"{REFERENCES_DIRECTORY}/procedures"
KNOWLEDGE_DIRECTORY = f"{REFERENCES_DIRECTORY}/knowledge"
CASH_KNOWLEDGE_DIRECTORY = f"{KNOWLEDGE_DIRECTORY}/cash"
CASH_KNOWLEDGE_ROOT = REPOSITORY_ROOT / ".escala" / "knowledge" / "cash"


class DoorBundleError(ValueError):
    """The bundle beside a packaged door is missing or differs from the repo."""


def door_bundle(skills_root: Path = SKILLS_ROOT) -> dict[str, Path]:
    """Map each path relative to the packaged door folder to its repo source."""
    catalog_path = skills_root / "catalog.yaml"
    catalog = load_capability_catalog(catalog_path)
    files = {CATALOG_REFERENCE: catalog_path}
    for capability in catalog.capabilities:
        if capability.id == catalog.public_entrypoint:
            continue
        files[f"{PROCEDURES_DIRECTORY}/{capability.id}.md"] = (
            skills_root / capability.id / "SKILL.md"
        )
    for card in sorted(CASH_KNOWLEDGE_ROOT.glob("*.md")):
        files[f"{CASH_KNOWLEDGE_DIRECTORY}/{card.name}"] = card
    return files


def door_bundle_paths() -> frozenset[str]:
    """Every file and directory the bundle adds beside the door."""
    return frozenset(
        {
            REFERENCES_DIRECTORY,
            PROCEDURES_DIRECTORY,
            KNOWLEDGE_DIRECTORY,
            CASH_KNOWLEDGE_DIRECTORY,
            *door_bundle(),
        }
    )


def copy_door_bundle(door_dir: Path) -> None:
    """Copy the list, the procedures and the cards beside a packaged door."""
    for relative, source in door_bundle().items():
        target = door_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def validate_door_bundle(door_dir: Path) -> None:
    """Fail unless every bundled file equals its repository source."""
    for relative, source in door_bundle().items():
        packaged = door_dir / relative
        try:
            same = packaged.read_bytes() == source.read_bytes()
        except OSError as exc:
            raise DoorBundleError("door_bundle_unavailable") from exc
        if not same or packaged.is_symlink():
            raise DoorBundleError("door_bundle_drift")
