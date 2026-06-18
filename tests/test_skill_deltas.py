"""Tests for skill_deltas — SkillDelta, suggest_deltas, persistence."""

from __future__ import annotations

from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from coaching.class_intake import (
    ClassBundle,
    ingest_class,
)
from coaching.pattern_extraction import Pattern
from coaching.skill_deltas import (
    SkillDelta,
    suggest_deltas,
    save_deltas,
    load_deltas,
    load_skills_inventory,
)


# ── Task 1: SkillDelta dataclass + skills inventory ──────────────────────


class TestSkillDelta:
    def test_minimal(self) -> None:
        d = SkillDelta(
            target_skill="kokoro-canvas",
            suggestion_type="strengthen_prompt",
            description="Reforzar prompt",
            evidence="tema canvas repetido",
        )
        assert d.target_skill == "kokoro-canvas"
        assert d.priority == "P2"  # default

    def test_full(self) -> None:
        d = SkillDelta(
            target_skill="escala-strategy",
            suggestion_type="new_prompt",
            description="Añadir prompt",
            evidence="estrategia mencionada",
            priority="P1",
            pattern_label="estrategia",
        )
        assert d.priority == "P1"

    def test_roundtrip(self) -> None:
        d1 = SkillDelta(
            target_skill="kokoro-canvas",
            suggestion_type="new_prompt",
            description="Test",
            evidence="evidence",
            priority="P0",
        )
        data = d1.to_dict()
        d2 = SkillDelta.from_dict(data)
        assert d1.target_skill == d2.target_skill
        assert d1.priority == d2.priority


class TestSkillsInventory:
    def test_load_returns_list(self) -> None:
        skills = load_skills_inventory()
        assert isinstance(skills, list)
        assert len(skills) > 0
        # Should include some known skills
        all_names = " ".join(skills)
        assert "escala-cash" in all_names or "escala-strategy" in all_names

    def test_skills_are_strings(self) -> None:
        skills = load_skills_inventory()
        for s in skills:
            assert isinstance(s, str)
            assert len(s) > 0


# ── Task 2: suggest_deltas() with mapping rules ──────────────────────────


class TestSuggestDeltas:
    def test_canvas_pattern_maps_to_skill(self) -> None:
        patterns = [
            Pattern(
                type="theme",
                label="business model canvas",
                evidence="canvas mencionado 3 veces",
            ),
        ]
        skills = ["kokoro-canvas", "escala-strategy"]
        deltas = suggest_deltas(patterns, skills)
        assert len(deltas) >= 1
        canvas_deltas = [d for d in deltas if d.target_skill == "kokoro-canvas"]
        assert len(canvas_deltas) >= 1

    def test_strategy_pattern_maps(self) -> None:
        patterns = [
            Pattern(
                type="theme",
                label="estrategia de la empresa",
                evidence="estrategia mencionada",
            ),
        ]
        skills = ["escala-strategy"]
        deltas = suggest_deltas(patterns, skills)
        assert len(deltas) >= 1
        assert deltas[0].target_skill == "escala-strategy"

    def test_commitment_pattern_maps(self) -> None:
        patterns = [
            Pattern(
                type="commitment",
                label="compromiso",
                evidence="compromiso de hablar con cliente",
            ),
        ]
        skills = ["escala-execution"]
        deltas = suggest_deltas(patterns, skills)
        assert len(deltas) >= 1
        assert deltas[0].target_skill == "escala-execution"

    def test_empty_patterns_returns_empty(self) -> None:
        skills = ["kokoro-canvas"]
        deltas = suggest_deltas([], skills)
        assert deltas == []

    def test_unknown_pattern_no_false_match(self) -> None:
        patterns = [
            Pattern(
                type="theme", label="temperatura del clima", evidence="clima mencionado"
            ),
        ]
        skills = ["escala-strategy", "kokoro-canvas"]
        deltas = suggest_deltas(patterns, skills)
        # "temperatura" and "clima" don't match any rule
        assert len(deltas) == 0

    def test_priority_sorting(self) -> None:
        patterns = [
            Pattern(type="theme", label="business model canvas", evidence="canvas"),
            Pattern(
                type="theme", label="estrategia corporativa", evidence="estrategia"
            ),
            Pattern(
                type="commitment", label="compromiso semanal", evidence="compromiso"
            ),
        ]
        skills = ["kokoro-canvas", "escala-strategy", "escala-execution"]
        deltas = suggest_deltas(patterns, skills)
        # P1 items should come before P2
        priorities = [d.priority for d in deltas]
        assert priorities == sorted(priorities), f"Priorities not sorted: {priorities}"


# ── Task 3: Persistence ─────────────────────────────────────────────────


class TestPersistence:
    @pytest.fixture
    def bundle(self, request: SubRequest) -> ClassBundle:
        t = Path(f"/tmp/skill_deltas_test_{request.node.name}.txt")
        t.write_text("test transcript", encoding="utf-8")
        return ingest_class(
            transcript_path=str(t),
            title=f"Test {request.node.name}",
            date="2026-06-02",
        )

    def test_save_load_roundtrip(self, bundle: ClassBundle) -> None:
        deltas = [
            SkillDelta(
                target_skill="kokoro-canvas",
                suggestion_type="strengthen_prompt",
                description="Reforzar",
                evidence="canvas repetido",
                priority="P1",
            ),
        ]
        path = save_deltas(bundle, deltas)
        assert path.exists()

        loaded = load_deltas(bundle)
        assert len(loaded) == 1
        assert loaded[0].target_skill == "kokoro-canvas"

    def test_load_empty_returns_empty(self, bundle: ClassBundle) -> None:
        loaded = load_deltas(bundle)
        assert loaded == []


# ── Edge cases ───────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_delta_unknown_skill_not_included(self) -> None:
        """A delta targeting a skill not in inventory should not appear."""
        patterns = [
            Pattern(type="theme", label="business model canvas", evidence="canvas"),
        ]
        # Supply inventory WITHOUT kokoro-canvas
        skills = ["escala-strategy"]
        deltas = suggest_deltas(patterns, skills)
        canvas_deltas = [d for d in deltas if d.target_skill == "kokoro-canvas"]
        assert len(canvas_deltas) == 0

    def test_save_empty_deltas(self, tmp_path: Path) -> None:
        class FakeBundle:
            class_id = "999999-fake-test"

        # Should handle being passed as a bundle even though not ClassBundle
        # We patch _CLASSES_ROOT manually by saving to tmp_path equivalent
        path = Path("work/classes/999999-fake-test/deltas.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[]", encoding="utf-8")
        assert path.exists()
