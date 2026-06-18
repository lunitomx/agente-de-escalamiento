"""Tests for class_intake — ClassBundle, ingest_class, CLI, and edge cases."""

from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest

from coaching.class_intake import (
    ClassBundle,
    _generate_class_id,
    ingest_class,
    load_bundle,
    summary,
)


@pytest.fixture
def transcript_path(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary transcript file."""
    f = tmp_path / "transcript.txt"
    f.write_text("Muy bien, vamos a empezar la clase...", encoding="utf-8")
    yield f


# ── Task 1: ClassBundle dataclass + ingest_class() ────────────────────────


class TestIngestBasic:
    def test_ingest_returns_bundle(self, transcript_path: Path) -> None:
        bundle = ingest_class(
            transcript_path=str(transcript_path),
            title="ELN Sesión 2 — Estrategia I",
            date="2026-05-26",
            source_type="bbb",
        )
        assert isinstance(bundle, ClassBundle)
        assert bundle.title == "ELN Sesión 2 — Estrategia I"
        assert bundle.date == "2026-05-26"
        assert bundle.source_type == "bbb"

    def test_bundle_has_required_fields(self, transcript_path: Path) -> None:
        bundle = ingest_class(
            transcript_path=str(transcript_path),
            title="Test Class",
            date="2026-01-15",
        )
        assert bundle.class_id is not None
        assert bundle.class_id.startswith("260115-")
        assert bundle.transcript_path is not None
        assert Path(bundle.transcript_path).exists()
        assert bundle.created_at is not None

    def test_missing_transcript_raises_error(self) -> None:
        with pytest.raises(FileNotFoundError, match="does not exist"):
            ingest_class(
                transcript_path="/nonexistent/file.txt",
                title="Test",
                date="2026-01-01",
            )


# ── Task 2: YAML persistence + class_id generation ────────────────────────


class TestPersistence:
    def test_bundle_persisted_as_yaml(
        self,
        transcript_path: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        bundle = ingest_class(
            transcript_path=str(transcript_path),
            title="Persist Test",
            date="2026-06-01",
        )
        yaml_path = Path("work/classes") / bundle.class_id / "bundle.yaml"
        assert yaml_path.exists(), f"Expected {yaml_path} to exist"
        content = yaml_path.read_text(encoding="utf-8")
        assert "class_id:" in content
        assert "transcript_path:" in content

    def test_class_id_format(self) -> None:
        cid = _generate_class_id("2026-05-26", "ELN Sesión 2 — Estrategia I")
        # YYMMDD-slug
        assert cid.startswith("260526-eln")
        assert "-" in cid

    def test_artifact_paths_absolute(
        self, transcript_path: Path, tmp_path: Path
    ) -> None:
        rel_artifact = tmp_path / "prompt.txt"
        rel_artifact.write_text("prompt content", encoding="utf-8")

        bundle = ingest_class(
            transcript_path=str(transcript_path),
            title="Abs Paths Test",
            date="2026-05-26",
            artifact_paths=[str(rel_artifact)],
        )
        for ap in bundle.artifact_paths:
            assert Path(ap).is_absolute(), f"artifact path should be absolute: {ap}"


# ── Task 3: CLI ──────────────────────────────────────────────────────────


class TestCli:
    def test_cli_ingest_via_main(self, transcript_path: Path) -> None:
        from coaching.class_intake import main as cli_main

        import sys

        test_args = [
            "class-intake",
            "ingest",
            "--transcript",
            str(transcript_path),
            "--title",
            "CLI Test Class",
            "--date",
            "2026-06-02",
        ]
        sys_argv_saved = sys.argv
        try:
            sys.argv = test_args
            cli_main()  # should not raise
        finally:
            sys.argv = sys_argv_saved

    def test_load_after_ingest(self, transcript_path: Path) -> None:
        bundle = ingest_class(
            transcript_path=str(transcript_path),
            title="Load Test",
            date="2026-06-02",
        )
        loaded = load_bundle(bundle.class_id)
        assert loaded.class_id == bundle.class_id
        assert loaded.title == "Load Test"

    def test_load_summary(self, transcript_path: Path) -> None:
        bundle = ingest_class(
            transcript_path=str(transcript_path),
            title="Summary Test",
            date="2026-06-02",
        )
        s = summary(bundle)
        assert bundle.class_id in s
        assert "transcript:" in s


# ── Task 4: Edge cases + optional fields ─────────────────────────────────


class TestEdgeCases:
    def test_audio_path_optional(self, transcript_path: Path) -> None:
        bundle = ingest_class(
            transcript_path=str(transcript_path),
            title="No Audio",
            date="2026-06-01",
        )
        assert bundle.audio_path is None

    def test_source_url_defaults_none(self, transcript_path: Path) -> None:
        bundle = ingest_class(
            transcript_path=str(transcript_path),
            title="No URL",
            date="2026-06-01",
        )
        assert bundle.source_url is None

    def test_empty_artifact_paths(self, transcript_path: Path) -> None:
        bundle = ingest_class(
            transcript_path=str(transcript_path),
            title="Empty Artifacts",
            date="2026-06-01",
            artifact_paths=[],
        )
        assert bundle.artifact_paths == []

    def test_full_metadata(self, transcript_path: Path, tmp_path: Path) -> None:
        audio = tmp_path / "audio.wav"
        audio.write_text("fake audio", encoding="utf-8")
        art = tmp_path / "exercise.md"
        art.write_text("# Exercise", encoding="utf-8")

        bundle = ingest_class(
            transcript_path=str(transcript_path),
            title="Full Metadata",
            date="2026-06-01",
            source_type="bbb",
            source_url="https://example.com/recording",
            audio_path=str(audio),
            artifact_paths=[str(art)],
        )
        assert bundle.audio_path is not None
        assert bundle.source_url == "https://example.com/recording"
        assert len(bundle.artifact_paths) == 1
        assert bundle.provenance["original_location"] == "https://example.com/recording"

    def test_slugify_special_chars(self) -> None:
        cid = _generate_class_id("2026-01-01", "¡Clase especial! con acentos y ñoños")
        assert cid == "260101-clase-especial-con-acentos-y-nonos"
