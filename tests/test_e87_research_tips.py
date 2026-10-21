"""S87.3: research files with triangulated tips for 8 Strategy workbook tools.

The files live in ``work/research/e87-tips/`` and are versioned with
``git add -f``. This test does not skip and does not use the network.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
TIPS_DIR = ROOT / "work" / "research" / "e87-tips"
WORKBOOK = ROOT / "metodologias_parsed" / "strategy_workbook.md"

TOOLS: tuple[str, ...] = (
    "bmc",
    "strategy-canvas",
    "brand-promise",
    "core-customer",
    "differentiating-activities",
    "sandbox",
    "vision-summary",
    "oppp-vision-boards",
)

REQUIRED_KEYS = ("id", "tip", "triangulated", "sources")
FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
YAML_BLOCK_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)
ANCHOR_RE = re.compile(r'<a id="(f\d+)"></a>')
BLUE_OCEAN_RE = re.compile(r"oc[eé]ano azul|blue ocean|kim|mauborgne", re.IGNORECASE)
WORD_RE = re.compile(r"[a-z0-9']+")
SHINGLE = 10


def _text(tool: str) -> str:
    return (TIPS_DIR / f"{tool}.md").read_text(encoding="utf-8")


def _front_matter(text: str) -> dict[str, Any]:
    match = FRONT_MATTER_RE.match(text)
    assert match, "missing YAML front matter"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict)
    return data


def _findings(text: str) -> list[dict[str, Any]]:
    body = FRONT_MATTER_RE.sub("", text, count=1)
    findings: list[dict[str, Any]] = []
    for block in YAML_BLOCK_RE.findall(body):
        data = yaml.safe_load(block)
        if isinstance(data, dict) and "id" in data:
            findings.append(data)
    return findings


def _rule_errors(finding: dict[str, Any]) -> list[str]:
    """Return why a finding breaks the triangulation rule (D1); empty if ok.

    Independence is counted by ``family`` when a source has one, else by
    ``origin``: three Scaling Up network firms or three summaries of one book
    are one origin, not three.
    """
    if finding.get("triangulated") is not True:
        return []
    sources = finding.get("sources") or []
    urls = [
        s
        for s in sources
        if isinstance(s, dict) and re.match(r"https?://", str(s.get("url", "")))
    ]
    # A source's family (e.g. Rhythm Systems -> scaling-up) wins over its origin.
    origins = {
        str(s.get("family") or s.get("origin", "")).strip().lower() for s in urls
    }
    origins.discard("")
    errors: list[str] = []
    if len(urls) < 3:
        errors.append(f"{finding.get('id')}: {len(urls)} sources with URL (<3)")
    if len(origins) < 3:
        errors.append(f"{finding.get('id')}: {len(origins)} distinct origins (<3)")
    return errors


def _shingles(text: str) -> set[tuple[str, ...]]:
    words = WORD_RE.findall(text.lower())
    return {tuple(words[i : i + SHINGLE]) for i in range(len(words) - SHINGLE + 1)}


@pytest.fixture(scope="module")
def workbook_shingles() -> set[tuple[str, ...]]:
    return _shingles(WORKBOOK.read_text(encoding="utf-8"))


def test_eight_research_files_exist() -> None:
    present = {p.stem for p in TIPS_DIR.glob("*.md")}
    assert present == set(TOOLS)


@pytest.mark.parametrize("tool", TOOLS)
def test_front_matter(tool: str) -> None:
    meta = _front_matter(_text(tool))
    assert meta.get("tool") == tool
    assert meta.get("title_es")
    assert meta.get("workbook_pages"), "workbook_pages must not be empty"
    assert meta.get("question")


@pytest.mark.parametrize("tool", TOOLS)
def test_findings_parse(tool: str) -> None:
    text = _text(tool)
    findings = _findings(text)
    assert findings, "no findings"
    ids = [f.get("id") for f in findings]
    assert ids == [f"f{n}" for n in range(1, len(ids) + 1)], ids
    anchors = ANCHOR_RE.findall(text)
    assert anchors == ids, (anchors, ids)
    for finding in findings:
        for key in REQUIRED_KEYS:
            assert key in finding, f"{finding.get('id')}: missing {key}"
        assert isinstance(finding["triangulated"], bool)
        tip = str(finding["tip"])
        assert 20 <= len(tip) <= 200, f"{finding['id']}: tip length {len(tip)}"


@pytest.mark.parametrize("tool", TOOLS)
def test_triangulated_rule(tool: str) -> None:
    errors = [e for f in _findings(_text(tool)) for e in _rule_errors(f)]
    assert not errors, errors


# Known shortfalls after the family rule (S87.3 review). Each needs a third
# independent family before S87.8/S87.9 copy its tips; remove it when fixed.
SHORTFALL: dict[str, int] = {
    "vision-summary": 1,
    "oppp-vision-boards": 2,
}


@pytest.mark.parametrize("tool", TOOLS)
def test_min_three_triangulated(tool: str) -> None:
    count = sum(1 for f in _findings(_text(tool)) if f["triangulated"] is True)
    if tool in SHORTFALL:
        assert count == SHORTFALL[tool], f"{tool}: update SHORTFALL ({count})"
        return
    assert count >= 3, f"{tool}: {count} triangulated findings"


def test_rule_rejects_two_sources() -> None:
    finding: dict[str, Any] = {
        "id": "f1",
        "tip": "Una promesa sin medida no se puede cumplir ni romper.",
        "triangulated": True,
        "sources": [
            {"url": "https://scalingup.com/a", "origin": "scaling-up"},
            {"url": "https://gazelles.com/b", "origin": "scaling-up"},
            {"url": "https://hbr.org/c", "origin": "hbr"},
        ],
    }
    assert _rule_errors(finding)
    finding["triangulated"] = False
    assert not _rule_errors(finding)


def test_rule_counts_one_family_once() -> None:
    """Sources of one family (Scaling Up network, EOS, one book) are one origin."""
    finding: dict[str, Any] = {
        "id": "f1",
        "tip": "Las prioridades del trimestre son de 3 a 5, cada una con un dueño.",
        "triangulated": True,
        "sources": [
            {"url": "https://scalingup.com/a", "origin": "scaling-up"},
            {
                "url": "https://rhythmsystems.com/b",
                "origin": "rhythm-systems",
                "family": "scaling-up",
            },
            {"url": "https://jimcollins.com/c", "origin": "jim-collins"},
        ],
    }
    assert _rule_errors(finding)
    finding["triangulated"] = False
    assert not _rule_errors(finding)


def test_strategy_canvas_is_scaling_up() -> None:
    text = _text("strategy-canvas")
    findings = _findings(text)
    for finding in findings:
        first = finding["sources"][0]
        assert not BLUE_OCEAN_RE.search(str(first.get("origin", ""))), finding["id"]
        assert not BLUE_OCEAN_RE.search(str(first.get("title", ""))), finding["id"]
        assert not re.search(
            r"oc[eé]ano azul|blue ocean", str(finding["tip"]), re.IGNORECASE
        ), finding["id"]
    lowered = text.lower()
    for piece in (
        "cliente central",
        "promesa de marca",
        "actividades diferenciadoras",
        "caja de arena",
    ):
        assert piece in lowered, piece


@pytest.mark.parametrize("tool", TOOLS)
def test_no_workbook_copy(tool: str, workbook_shingles: set[tuple[str, ...]]) -> None:
    text = _text(tool)
    assert "![" not in text
    assert not re.search(r"\.(png|jpe?g)\b", text, re.IGNORECASE)
    copied = _shingles(text) & workbook_shingles
    assert not copied, sorted(" ".join(s) for s in copied)[:3]
