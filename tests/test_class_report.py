"""Tests for class_report — generate_report, sections, evidence."""

from __future__ import annotations

from pathlib import Path

from coaching.class_intake import ingest_class
from coaching.pattern_extraction import Pattern, save_patterns
from coaching.skill_deltas import SkillDelta, save_deltas
from coaching.class_report import generate_report, _render_header, _render_patterns


class TestGenerateReport:
    def test_report_created(self) -> None:
        # Create a bundle
        t = Path("/tmp/test_report_create.txt")
        t.write_text("test transcript", encoding="utf-8")
        bundle = ingest_class(
            transcript_path=str(t),
            title="Report Test Class",
            date="2026-06-02",
        )

        # Save some patterns and deltas
        patterns = [
            Pattern(
                type="theme",
                label="estrategia corporativa",
                evidence="estrategia mencionada 5 veces",
            ),
            Pattern(
                type="decision",
                label="compromiso",
                evidence="compromiso de hablar con cliente",
            ),
        ]
        save_patterns(bundle, patterns)

        deltas = [
            SkillDelta(
                target_skill="escala-strategy",
                suggestion_type="new_prompt",
                description="Añadir prompt de estrategia",
                evidence="estrategia repetida en clase",
                priority="P1",
            ),
        ]
        save_deltas(bundle, deltas)

        # Generate report
        path = generate_report(bundle)
        assert path.exists()
        assert path.name == "report.md"

        # Read and verify content
        content = path.read_text(encoding="utf-8")
        assert "Report Test Class" in content
        assert "## 2. Extracted Patterns" in content
        assert "## 3. Skill Deltas" in content

    def test_header_has_class_info(self) -> None:
        t = Path("/tmp/test_header_info.txt")
        t.write_text("transcript", encoding="utf-8")
        bundle = ingest_class(
            transcript_path=str(t), title="Header Test", date="2026-06-02"
        )
        header = _render_header(bundle)
        assert "Header Test" in header
        assert "Class ID" in header
        assert "2026-06-02" in header

    def test_empty_patterns_shows_no_patterns(self) -> None:
        t = Path("/tmp/test_empty_patterns.txt")
        t.write_text("transcript", encoding="utf-8")
        bundle = ingest_class(
            transcript_path=str(t), title="Empty Patterns", date="2026-06-02"
        )
        patterns_section = _render_patterns(bundle)
        assert "Total patterns:" in patterns_section
        assert (
            "No patterns extracted" in patterns_section
            or "0" in patterns_section.split("Total patterns:")[1][:5]
        )

    def test_report_three_sections(self) -> None:
        t = Path("/tmp/test_three_sections.txt")
        t.write_text("transcript", encoding="utf-8")
        bundle = ingest_class(
            transcript_path=str(t), title="Three Sections", date="2026-06-02"
        )

        patterns = [Pattern(type="theme", label="tema de prueba", evidence="prueba")]
        save_patterns(bundle, patterns)

        deltas = [
            SkillDelta(
                target_skill="escala-cash",
                suggestion_type="new_prompt",
                description="Test delta",
                evidence="evidence",
            ),
        ]
        save_deltas(bundle, deltas)

        content = generate_report(bundle).read_text(encoding="utf-8")
        assert "## 1. Class Summary" in content
        assert "## 2. Extracted Patterns" in content
        assert "## 3. Skill Deltas" in content

    def test_delta_shows_priority_and_skill(self) -> None:
        t = Path("/tmp/test_delta_shows.txt")
        t.write_text("transcript", encoding="utf-8")
        bundle = ingest_class(
            transcript_path=str(t), title="Delta Show", date="2026-06-02"
        )

        deltas = [
            SkillDelta(
                target_skill="escala-strategy",
                suggestion_type="new_prompt",
                description="Improve strategy prompt",
                evidence="strategy mentioned",
                priority="P1",
            ),
        ]
        save_deltas(bundle, deltas)

        content = generate_report(bundle).read_text(encoding="utf-8")
        assert "escala-strategy" in content
        assert "P1" in content or "High" in content
