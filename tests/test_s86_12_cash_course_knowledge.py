"""S86.11/S86.12: ESCALA answers about money with what the Cash course taught.

The cards in ``.escala/knowledge/cash/`` come from the Cash course the group
took.  ESCALA quotes the course only from a card and never names who gave it
(S86.12: no attribution to a person, so nothing fiscal or legal lands on him).
Every package carries the cards byte for byte.  The course audios and
transcripts never enter the repository (it is public).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from validators.door_bundle import (
    DoorBundleError,
    copy_door_bundle,
    door_bundle,
    door_bundle_paths,
    validate_door_bundle,
)

ROOT = Path(__file__).resolve().parents[1]
CASH = ROOT / ".escala" / "knowledge" / "cash"
DOOR = ROOT / "escala-skills" / "escala" / "SKILL.md"
CASH_SKILL = ROOT / "escala-skills" / "escala-cash" / "SKILL.md"
CREDIT = "*Fuente: el curso de cash que vimos (2025).*"
CITATION = "Según el curso de cash que vimos, recuerda"
# Built in pieces so this file does not trip its own search.
INSTRUCTOR = re.compile("hum" + "berto|mart[ií]nez +bar+[oó]n", re.I)
SECTIONS = (
    "## La idea",
    "## Según el curso",
    "## Ejemplo del curso",
    "## Cuándo usarla",
)
# Course participants and a real businessman named in the audios.
PEOPLE = (
    "Esperanza",
    "Toño",
    "Luis",
    "Abraham",
    "Carlos",
    "Oscar",
    "Óscar",
    "Yesenia",
    "César",
    "Mata",
)
# Tax talk and crude words from the course that ESCALA never puts in the course's mouth.
EXCLUDED = (
    "factura falsa",
    "comprar facturas",
    "compro facturas",
    "travesura",
    "dividendo",
    "deducible",
    "deducir",
    "deducción",
    "evadir",
    "SAT",
    "coño",
    "mames",
)


def cards() -> list[Path]:
    return sorted(CASH.glob("[0-9][0-9]-*.md"))


def front_matter(text: str) -> dict[str, str]:
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert match, "card without front matter"
    pairs = (line.split(":", 1) for line in match.group(1).splitlines())
    return {key.strip(): value.strip() for key, value in pairs}


def quote(text: str) -> str:
    section = text.split("## Según el curso", 1)[1]
    section = section.split("\n## ", 1)[0]
    lines = [line[1:].strip() for line in section.splitlines() if line.startswith(">")]
    return " ".join(lines)


def test_there_is_a_card_for_each_idea_of_the_course() -> None:
    assert len(cards()) >= 12


@pytest.mark.parametrize("card", cards(), ids=lambda path: path.stem)
def test_every_card_has_the_idea_the_quote_the_example_and_the_credit(
    card: Path,
) -> None:
    text = card.read_text(encoding="utf-8")
    meta = front_matter(text)
    assert card.stem.endswith(meta["id"])
    assert meta["audio"] in {"1", "2", "3", "4"}
    for heading in SECTIONS:
        assert heading in text, f"{card.name} has no '{heading}'"
    said = quote(text)
    assert said, f"{card.name} has no quote from the course"
    assert len(said.split()) <= 45, f"{card.name}: the quote must stay short"
    assert text.rstrip().endswith(CREDIT)


@pytest.mark.parametrize(
    "path",
    [*cards(), CASH / "overview.md"],
    ids=lambda path: path.stem,
)
def test_no_participant_and_no_tax_advice_in_the_cards(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for name in PEOPLE:
        assert not re.search(rf"\b{name}\b", text), f"{path.name} names {name}"
    lowered = text.lower()
    for word in EXCLUDED:
        found = re.search(rf"\b{re.escape(word.lower())}", lowered)
        if word == "SAT":
            found = re.search(r"\bSAT\b", text)
        assert not found, f"{path.name} says '{word}'"


def test_overview_lists_every_card_and_the_citation_rule() -> None:
    overview = (CASH / "overview.md").read_text(encoding="utf-8")
    for card in cards():
        assert card.name in overview, f"overview does not list {card.name}"
    assert CITATION in overview
    assert "contador" in overview  # tax questions go to the owner's accountant


def test_there_is_no_author_card() -> None:
    assert not (CASH / "autor.md").exists()


def test_no_tracked_file_names_the_instructor() -> None:
    listed = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    offenders = [
        name
        for name in listed
        if INSTRUCTOR.search(name)
        or (
            (ROOT / name).is_file()
            and INSTRUCTOR.search(
                (ROOT / name).read_text(encoding="utf-8", errors="ignore")
            )
        )
    ]
    assert offenders == []


def test_the_course_audios_and_transcripts_never_enter_the_repository() -> None:
    listed = subprocess.run(
        ["git", "ls-files", "sources/curso-cash"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split("\n")
    assert [name for name in listed if name and not name.endswith(".gitignore")] == []


def test_every_package_carries_the_cards() -> None:
    bundle = door_bundle()
    for path in [*cards(), CASH / "overview.md"]:
        assert bundle[f"references/knowledge/cash/{path.name}"] == path
    assert "references/knowledge/cash/autor.md" not in bundle
    assert {"references/knowledge", "references/knowledge/cash"} <= door_bundle_paths()


def test_a_packaged_card_is_the_repository_card_byte_for_byte(tmp_path: Path) -> None:
    copy_door_bundle(tmp_path)
    validate_door_bundle(tmp_path)
    packaged = tmp_path / "references" / "knowledge" / "cash" / "overview.md"
    packaged.write_text("otra cosa", encoding="utf-8")
    with pytest.raises(DoorBundleError, match="door_bundle_drift"):
        validate_door_bundle(tmp_path)


def test_the_door_quotes_the_course_only_from_the_cards() -> None:
    door = DOOR.read_text(encoding="utf-8")
    assert ".escala/knowledge/cash/" in door
    assert "references/knowledge/cash/" in door
    assert CITATION in door
    assert "una vez por tema" in door
    assert "nunca le atribuyas" in door


def test_the_cash_procedure_reads_the_cards_and_cites_the_course() -> None:
    skill = CASH_SKILL.read_text(encoding="utf-8")
    assert ".escala/knowledge/cash/" in skill
    assert CITATION in skill
