"""Tests for pattern_extraction — Pattern dataclass, extraction, persistence."""

from __future__ import annotations

from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from coaching.class_intake import (
    ClassBundle,
    ingest_class,
    load_bundle,
)
from coaching.pattern_extraction import (
    Pattern,
    extract_patterns,
    load_patterns,
    save_patterns,
)


@pytest.fixture
def short_transcript(tmp_path: Path) -> Path:
    """A short transcript with clear repeated themes and decisions."""
    text = (
        "Hoy vamos a hablar de estrategia. "
        "La estrategia es importante porque define el rumbo. "
        "El compromiso de esta semana es hablar con un cliente. "
        "Les voy a pedir que tengan listo su Business Model Canvas. "
        "La estrategia debe ser clara. "
        "A quién sí, a quién sí es el filtro más importante. "
        "Usen a quién sí para decidir. "
        "El compromiso es tenerlo listo antes de la próxima clase. "
        "Voy a hablar con mi mejor cliente esta semana. "
        "Me comprometo a terminar el canvas."
    )
    f = tmp_path / "transcript.txt"
    f.write_text(text, encoding="utf-8")
    return f


@pytest.fixture
def bundle(short_transcript: Path, request: SubRequest) -> ClassBundle:
    """Create a real bundle with a unique title per test to prevent class_id collisions."""
    b = ingest_class(
        transcript_path=str(short_transcript),
        title=f"Test {request.node.name}",
        date="2026-06-02",
        source_type="file",
    )
    return b


# ── Task 1: Pattern dataclass ────────────────────────────────────────────


class TestPatternDataclass:
    def test_pattern_minimal(self) -> None:
        p = Pattern(type="theme", label="a quién sí", evidence="usen a quién sí")
        assert p.type == "theme"
        assert p.label == "a quién sí"
        assert p.occurrences == 1
        assert p.confidence == 0.5

    def test_pattern_full(self) -> None:
        p = Pattern(
            type="decision",
            label="compromiso",
            evidence="el compromiso es...",
            occurrences=3,
            confidence=0.9,
        )
        assert p.type == "decision"
        assert p.occurrences == 3

    def test_pattern_roundtrip(self) -> None:
        p1 = Pattern(type="theme", label="estrategia", evidence="texto", occurrences=5, confidence=0.8)
        d = p1.to_dict()
        p2 = Pattern.from_dict(d)
        assert p1.type == p2.type
        assert p1.label == p2.label
        assert p1.occurrences == p2.occurrences


# ── Task 2: Theme extraction ─────────────────────────────────────────────


class TestThemeExtraction:
    def test_extract_returns_list(self, bundle: ClassBundle) -> None:
        b = bundle
        patterns = extract_patterns(b)
        assert isinstance(patterns, list)
        assert len(patterns) > 0

    def test_themes_detected(self, bundle: ClassBundle) -> None:
        b = bundle
        patterns = extract_patterns(b)
        themes = [p for p in patterns if p.type == "theme"]
        assert len(themes) >= 1
        # "a quién sí" should appear as a theme
        theme_labels = [t.label for t in themes]
        any_si = any("quién" in label or "a quién" in label for label in theme_labels)
        assert any_si, f"Expected 'a quién sí' theme, got: {theme_labels}"

    def test_theme_has_occurrences(self, bundle: ClassBundle) -> None:
        b = bundle
        patterns = extract_patterns(b)
        themes = [p for p in patterns if p.type == "theme"]
        for t in themes:
            assert t.occurrences >= 2, f"Theme '{t.label}' only {t.occurrences} occurrences"


# ── Task 3: Decision + commitment extraction ─────────────────────────────


class TestDecisionExtraction:
    def test_decisions_detected(self, bundle: ClassBundle) -> None:
        b = bundle
        patterns = extract_patterns(b)
        decisions = [p for p in patterns if p.type == "decision"]
        assert len(decisions) >= 1, "Expected at least 1 decision"

    def test_commitments_detected(self, bundle: ClassBundle) -> None:
        b = bundle
        patterns = extract_patterns(b)
        commitments = [p for p in patterns if p.type == "commitment"]
        assert len(commitments) >= 1, "Expected at least 1 commitment"


# ── Task 4: Persistence ──────────────────────────────────────────────────


class TestPersistence:
    def test_load_empty_returns_empty_list(self, bundle: ClassBundle) -> None:
        b = bundle
        # Before saving, load should return empty
        patterns = load_patterns(b)
        assert patterns == []

    def test_save_load_roundtrip(self, bundle: ClassBundle) -> None:
        b = bundle
        patterns = extract_patterns(b)
        path = save_patterns(b, patterns)
        assert path.exists()

        loaded = load_patterns(b)
        assert len(loaded) == len(patterns)
        assert loaded[0].type == patterns[0].type


# ── Edge cases ───────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_missing_transcript_raises(self, tmp_path: Path) -> None:
        """Bundle with non-existent transcript path."""
        from coaching.class_intake import ClassBundle

        bad_bundle = ClassBundle(
            class_id="999999-bogus",
            title="Bogus",
            date="2026-06-02",
            source_type="file",
            transcript_path=str(tmp_path / "nonexistent.txt"),
        )
        with pytest.raises(FileNotFoundError, match="transcript not found"):
            extract_patterns(bad_bundle)
