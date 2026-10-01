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


# --- rendered Spanish formatters --------------------------------------------

AREAS = ("people", "strategy", "execution", "cash")


def _package(area: str, available: bool) -> object:
    from coaching.evidence.models import DecisionRef, EvidencePackage, EvidenceSource

    source = EvidenceSource(
        source_id="hoja-1",
        source_type="worksheet",
        title="Hoja de ejemplo",
        decision=area,
        status="available" if available else "missing",
        period="2026-07",
        confidence="high",
        reason="ejemplo sintético",
    )
    return EvidencePackage(
        decision_ref=DecisionRef(
            decision="¿Qué hago primero?",
            area=area,
            horizon="inmediato",
            outcome="mejorar",
        ),
        sources=[source] if available else [],
        missing=[] if available else [source],
        not_trustworthy=[],
        questions=[],
    )


def _selector_outputs() -> dict[str, str]:
    from coaching.evidence.models import EvidencePackage
    from coaching.selector.engine import select_tool

    outputs: dict[str, str] = {}
    for area in AREAS:
        for available in (True, False):
            package = _package(area, available)
            assert isinstance(package, EvidencePackage)
            result = select_tool(package)
            outputs[f"selector {area} {result.action}"] = "\n".join(
                [result.output, result.receipt.reason]
            )
    return outputs


def test_selector_output_speaks_spanish() -> None:
    outputs = _selector_outputs()

    assert _offenders(outputs) == []
    assert "**Área:** Tu dinero" in outputs["selector cash tool_selected"]


def test_selector_next_step_is_plain_spanish_not_a_command() -> None:
    for where, text in _selector_outputs().items():
        assert "/escala-" not in text, where
        assert "ejecutar" not in text, where
        assert "`" not in text, where
    assert "Próximo paso: ¿" in _selector_outputs()["selector cash tool_selected"]


def test_decision_evidence_and_reviewer_name_the_area_in_spanish() -> None:
    from coaching.decision.formatter import format_confirmed, format_draft
    from coaching.evidence.formatter import format_package
    from coaching.evidence.models import EvidencePackage
    from coaching.reviewer.formatter import format_report
    from coaching.reviewer.models import ReviewReport

    outputs: dict[str, str] = {}
    for area in AREAS:
        draft = {"decision": "Cobrar antes", "area": area, "horizon": "mes"}
        package = _package(area, True)
        assert isinstance(package, EvidencePackage)
        outputs[f"draft {area}"] = format_draft(draft)
        outputs[f"confirmed {area}"] = format_confirmed(draft)
        outputs[f"evidence {area}"] = format_package(package)
        outputs[f"reviewer {area}"] = format_report(
            ReviewReport(decision="Cobrar antes", area=area)
        )

    assert _offenders(outputs) == []
    assert "**Área:** Tu equipo" in outputs["draft people"]


# --- welcome ----------------------------------------------------------------


def test_welcome_questions_use_the_spanish_areas() -> None:
    from coaching.core import owner_area_choice
    from coaching.welcome.conversation import (
        WelcomeState,
        begin_welcome,
        respond_to_welcome,
    )

    texts = {
        "narrow": respond_to_welcome(WelcomeState(phase="concern"), "").question,
        "source": respond_to_welcome(
            WelcomeState(phase="concern"), "No me alcanza el efectivo"
        ).question,
        "returning": begin_welcome(returning=True, previous_focus="cash").question,
    }

    assert _offenders(texts) == []
    assert owner_area_choice() in texts["narrow"]
    assert "Para trabajar en tu dinero" in texts["source"]
    assert "La última vez trabajamos en tu dinero" in texts["returning"]


def test_welcome_profile_names_areas_in_spanish_without_commands() -> None:
    from coaching.welcome.formatter import format_summary

    text = format_summary({"company": {"name": "Ejemplo"}, "scores": {"cash": 3}})
    empty = format_summary({"company": {"name": "Ejemplo"}})

    assert _offenders({"scores": text, "empty": empty}) == []
    assert "**Tu dinero:** 3/5" in text
    assert "/escala-" not in empty


# --- A5: template names keep the sheet word, after a Spanish explanation ----

# The sheet of the group uses these names; the owner needs them to find the
# cell, so they stay, but the first mention in each message explains them.
GLOSSARY = {
    "Critical Number": "tu número clave (Critical Number",
    "Rocks": "metas del trimestre (Rocks",
    "Done": "terminados (Done",
}


def first_mention_unexplained(text: str) -> list[str]:
    """Glossary terms whose first mention in ``text`` is not explained."""
    missing: list[str] = []
    for term, explained in GLOSSARY.items():
        first = re.search(rf"\b{term}\b", text)
        if first and not text[: first.end()].endswith(explained):
            missing.append(term)
    return missing


def _item(text: str, due: str | None = "2026-09-01") -> object:
    from coaching.tracker.maintenance import ReviewedItem

    return ReviewedItem(
        focus_area=None, text=text, kpi=None, due=due, due_date=None, status=None
    )


def _tracker_texts() -> dict[str, str]:
    from datetime import date

    from coaching.tracker import messages as m
    from coaching.tracker.maintenance import MeetingPrep, ReviewedItem, RocksPrep
    from coaching.tracker.proposal import ProposedRow, QuarterCheck, RowProposal

    done = _item("Abrir sucursal")
    late = _item("Cobrar a Juan")
    assert isinstance(done, ReviewedItem) and isinstance(late, ReviewedItem)
    row = ProposedRow(focus_area="Cash", priority="Cobrar antes", kpi="días", due="")
    rocks = RocksPrep(quarter="Q4-2026", reviewed=1, overdue=[late])
    check = QuarterCheck(status="ask", sheet_quarter=None, plan_quarter="Q4-2026")
    texts = {
        name: value
        for name, value in vars(m).items()
        if name.isupper() and isinstance(value, str)
    }
    texts.update(
        {
            "cn different": m.proposal_message(
                RowProposal(
                    month="2026-10",
                    month_name="octubre",
                    rows=[row],
                    critical_number="different",
                    plan_critical_number="10 clientes",
                    sheet_critical_number="5 clientes",
                ),
                None,
                "Ana",
                "x",
            ),
            "cn add": m.proposal_message(
                RowProposal(
                    month="2026-10",
                    month_name="octubre",
                    rows=[row],
                    critical_number="add",
                    plan_critical_number="10 clientes",
                ),
                None,
                "Ana",
                "x",
            ),
            "ask quarter": m.ask_quarter_message(check),
            "quarter mismatch": m.quarter_mismatch_message(
                QuarterCheck(
                    status="mismatch", quarter="Q3-2026", plan_quarter="Q4-2026"
                )
            ),
            "prep": m.prep_message(
                MeetingPrep(
                    today=date(2026, 10, 1), reviewed=2, finished=[done], rocks=rocks
                ),
                None,
                "Ana",
                "x",
            ),
            "prep only rocks": m.prep_message(
                MeetingPrep(today=date(2026, 10, 1), rocks=rocks), None, "Ana", "x"
            ),
        }
    )
    return texts


def test_rule_wants_the_first_mention_explained() -> None:
    assert first_mention_unexplained("tu número clave (Critical Number) y Rocks") == [
        "Rocks"
    ]
    assert first_mention_unexplained("tus metas del trimestre (Rocks): Rocks") == []


def test_tracker_explains_template_names_the_first_time() -> None:
    texts = _tracker_texts()

    offenders = {
        where: missing
        for where, text in texts.items()
        if (missing := first_mention_unexplained(text))
    }

    assert offenders == {}
    assert "tu número clave (Critical Number)" in texts["cn add"]
