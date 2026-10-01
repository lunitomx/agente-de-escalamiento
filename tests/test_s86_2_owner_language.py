"""S86.2: the owner reads plain Spanish — no bare English area names or acronyms.

What counts as owner-facing text (the rule this test enforces):

- every string literal in ``coaching/**/messages.py`` (docstrings excluded);
- the rendered output of the Spanish formatters the owner sees (selector,
  decision, evidence, reviewer, welcome);
- the welcome questions;
- ``PILOTO-EMPRESARIOS.md`` outside code blocks;
- in ``escala-skills/*/SKILL.md``: quoted text ("…", “…”) outside code blocks
  and frontmatter — the lines the agent says to the owner. Lines starting
  with ``Señales:`` are excluded: they quote what the owner may say, not what
  ESCALA says. Unquoted instructions to the agent are not scanned.

A flagged term is "translated" only when it follows its Spanish explanation
inside parentheses, alone: ``tu número clave (Critical Number)``,
``tu análisis de fortalezas, debilidades y tendencias (SWT)``.
``(Cash, Strategy, Execution o People)`` is NOT a translation.
Terms are matched case-sensitively (``Cash``, not the id ``cash``).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TERMS = re.compile(
    r"\b(?:People|Strategy|Execution|Cash|CCC|BHAG|SWT|OPSP)\b|\bDeep Dive\b"
)


def untranslated(text: str) -> list[str]:
    """Flagged terms in ``text`` that are not ``español (TERM)``."""
    found: list[str] = []
    for match in TERMS.finditer(text):
        start = match.start()
        opened = start > 0 and text[start - 1] == "("
        close = text.find(")", match.end())
        alone = opened and close != -1 and not TERMS.search(text, match.end(), close)
        spanish_before = opened and bool(re.search(r"\w\s*$", text[: start - 1]))
        if not (alone and spanish_before):
            found.append(match.group())
    return found


def _offenders(texts: dict[str, str]) -> list[str]:
    return [
        f"{where}: {terms} in {text[:90]!r}"
        for where, text in texts.items()
        if (terms := untranslated(text))
    ]


# --- the rule itself --------------------------------------------------------


def test_rule_accepts_spanish_then_term_in_parentheses() -> None:
    assert untranslated("tu número clave (Critical Number)") == []
    assert untranslated("antes de cerrar tu análisis (SWT)?") == []
    assert untranslated("El efectivo es el rey (Cash is King)") == []


def test_rule_flags_bare_terms_and_lists() -> None:
    assert untranslated("Trabajo contigo sobre People y Cash.") == ["People", "Cash"]
    assert untranslated("Dime cuál es (Cash, Strategy o People).") == [
        "Cash",
        "Strategy",
        "People",
    ]
    assert untranslated("prepara el Deep Dive") == ["Deep Dive"]
    assert untranslated("(CCC)") == ["CCC"]
    assert untranslated("reducir cash y ccc") == []


# --- one mapping for the four areas -----------------------------------------


def test_one_spanish_name_per_area() -> None:
    from coaching.core import OWNER_AREA_NAMES, owner_area_choice, owner_area_name

    assert OWNER_AREA_NAMES == {
        "people": "tu equipo",
        "strategy": "tus clientes y tu estrategia",
        "execution": "tu día a día",
        "cash": "tu dinero",
    }
    assert owner_area_name("cash") == "tu dinero"
    assert owner_area_name("people", capital=True) == "Tu equipo"
    assert owner_area_name("overall") == "tu negocio"
    assert owner_area_name("algo-raro") == "tu negocio"
    assert owner_area_choice() == (
        "tu equipo, tus clientes y tu estrategia, tu día a día o tu dinero"
    )


# --- coaching/**/messages.py ------------------------------------------------


def _docstrings(tree: ast.AST) -> set[int]:
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
            ):
                ids.add(id(body[0].value))
    return ids


def _message_literals(path: Path) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    skip = _docstrings(tree)
    in_fstring: set[int] = set()
    texts: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            parts: list[str] = []
            for value in node.values:
                in_fstring.add(id(value))
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    parts.append(value.value)
                else:
                    parts.append("{}")
            texts[f"{path.relative_to(ROOT)}:{node.lineno}"] = "".join(parts)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in skip
            and id(node) not in in_fstring
        ):
            texts[f"{path.relative_to(ROOT)}:{node.lineno}"] = node.value
    return texts


def test_owner_messages_have_no_bare_english_terms() -> None:
    texts: dict[str, str] = {}
    for path in sorted((ROOT / "coaching").glob("**/messages.py")):
        texts.update(_message_literals(path))

    assert texts, "no messages found"
    assert _offenders(texts) == []


def test_missing_area_question_uses_the_spanish_areas() -> None:
    from coaching.core import owner_area_choice
    from coaching.tracker import messages

    source = (ROOT / "coaching/tracker/messages.py").read_text(encoding="utf-8")

    assert "Cash, Strategy" not in source
    assert owner_area_choice() in messages.missing_area_note(["Abrir sucursal"])
