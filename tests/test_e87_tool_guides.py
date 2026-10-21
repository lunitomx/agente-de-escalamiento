"""S87.2: guided sheets follow the ToolGuide contract and cite safe sources.

The public-vocabulary terms are read from ``governance/public-boundary.yaml``;
this file never writes them (decision D5 of S87.2).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from coaching.worksheet.guide import parse_guide

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "conocimiento"
POLICY = ROOT / "governance" / "public-boundary.yaml"
CORE_CUSTOMER = KNOWLEDGE / "strategy" / "worksheets" / "core-customer.yaml"
BRAND_PROMISE_CONCEPT = KNOWLEDGE / "strategy" / "concepts" / "brand-promise.yaml"
BRAND_PROMISE = KNOWLEDGE / "strategy" / "worksheets" / "brand-promise.yaml"
ANCHOR_SOURCE_RE = re.compile(r"^(work/research/e87-tips/[a-z0-9-]+\.md)#(f\d+)$")
YAML_BLOCK_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)


def _load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _guided_sheets() -> list[Path]:
    return sorted(p for p in KNOWLEDGE.rglob("*.yaml") if "guide" in _load(p))


def _forbidden_terms() -> list[str]:
    policy = _load(POLICY)
    terms: list[str] = []
    for rule in policy["vocabulary_rules"]:
        terms.extend(str(t) for t in rule["terms"])
    return terms


def _findings(research: Path) -> dict[str, dict[str, Any]]:
    text = research.read_text(encoding="utf-8")
    found: dict[str, dict[str, Any]] = {}
    for block in YAML_BLOCK_RE.findall(text):
        data = yaml.safe_load(block)
        if isinstance(data, dict) and "id" in data:
            found[str(data["id"])] = data
    return found


def test_core_customer_passes_the_contract() -> None:
    guide = parse_guide(_load(CORE_CUSTOMER))
    assert guide is not None
    assert [s.id for s in guide.guide.steps] == [
        "top-5-clientes",
        "atributos",
        "top-atributos",
        "quien-es",
        "necesidad",
        "chequeo-promesa",
    ]
    assert len(guide.tips) >= 3
    assert guide.view.layout == "cards"
    assert len(guide.view.sections) == 3


def test_brand_promise_passes_the_contract() -> None:
    guide = parse_guide(_load(BRAND_PROMISE))
    assert guide is not None
    assert [s.id for s in guide.guide.steps] == [
        "cuentan-esperan-solo-tu",
        "promesa-principal",
        "promesas-de-apoyo",
        "medidas",
        "prueba-de-promesa",
        "lealtad",
        "garantia",
        "antipromesas",
    ]
    assert all(s.example.startswith("Tortillería El Sol:") for s in guide.guide.steps)
    assert len(guide.tips) >= 3
    assert guide.view.layout == "cards"
    assert len(guide.view.sections) == 4


def test_brand_promise_tips_are_only_f1_f2_f5() -> None:
    guide = parse_guide(_load(BRAND_PROMISE))
    assert guide is not None
    assert sorted(t.source for t in guide.tips) == [
        "work/research/e87-tips/brand-promise.md#f1",
        "work/research/e87-tips/brand-promise.md#f2",
        "work/research/e87-tips/brand-promise.md#f5",
    ]


def test_brand_promise_ai_prompt_has_no_page() -> None:
    prompt = _load(BRAND_PROMISE)["ai_prompt"]
    assert set(prompt) == {"text"}


def test_brand_promise_concept_names_main_supporting_guarantee_anti() -> None:
    summary = " ".join(_load(BRAND_PROMISE_CONCEPT)["summary"].split()).lower()
    assert "10-20 word" not in summary
    for piece in ("1 main", "2 supporting", "weekly measure", "guarantee"):
        assert piece in summary, piece
    assert "anti-promise" in summary


def test_core_customer_keeps_legacy_fields() -> None:
    assert len(_load(CORE_CUSTOMER)["metadata"]["fields"]) == 6


def test_at_least_one_guided_sheet_exists() -> None:
    assert CORE_CUSTOMER in _guided_sheets()


@pytest.mark.parametrize("sheet", _guided_sheets(), ids=lambda p: p.stem)
def test_tip_sources_are_triangulated_anchors_or_clean(sheet: Path) -> None:
    guide = parse_guide(_load(sheet))
    assert guide is not None
    terms = [t.lower() for t in _forbidden_terms()]
    for tip in guide.tips:
        match = ANCHOR_SOURCE_RE.match(tip.source)
        if match:
            research = ROOT / match.group(1)
            assert research.is_file(), f"{sheet.name}: {tip.source}"
            assert f'<a id="{match.group(2)}"></a>' in research.read_text(
                encoding="utf-8"
            ), f"{sheet.name}: ancla inexistente {tip.source}"
            finding = _findings(research)[match.group(2)]
            assert finding["triangulated"] is True, (
                f"{sheet.name}: {tip.source} no está triangulado"
            )
        else:
            lowered = tip.source.lower()
            hits = [t for t in terms if t in lowered]
            assert not hits, f"{sheet.name}: fuente con término prohibido"


def test_guided_sheet_has_no_root_source_key() -> None:
    for sheet in _guided_sheets():
        assert "source" not in _load(sheet), sheet.name
