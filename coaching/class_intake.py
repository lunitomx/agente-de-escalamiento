"""
Class intake + source bundling for Escala coaching.

Captures a class transcript, metadata, and optional lesson artifacts
into a structured, traceable bundle persisted as YAML.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class ClassBundle:
    """Structured bundle tying together class transcript, audio, and lesson materials."""

    class_id: str
    title: str
    date: str
    source_type: str  # "bbb", "file", "upload", etc.
    transcript_path: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # optional
    audio_path: Optional[str] = None
    source_url: Optional[str] = None
    artifact_paths: list[str] = field(default_factory=list)

    provenance: dict = field(default_factory=lambda: {"source": "unknown", "original_location": None})

    def to_dict(self) -> dict:
        """Convert to YAML-serializable dict."""
        return {
            "class_id": self.class_id,
            "title": self.title,
            "date": self.date,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "created_at": self.created_at,
            "transcript_path": self._abs(self.transcript_path),
            "audio_path": self._abs(self.audio_path) if self.audio_path else None,
            "artifact_paths": [self._abs(p) for p in self.artifact_paths],
            "provenance": self.provenance,
        }

    @staticmethod
    def _abs(path: str) -> str:
        return str(Path(path).resolve())

    @classmethod
    def from_dict(cls, data: dict) -> "ClassBundle":
        return cls(
            class_id=data["class_id"],
            title=data["title"],
            date=data["date"],
            source_type=data.get("source_type", "unknown"),
            transcript_path=data["transcript_path"],
            created_at=data.get("created_at", ""),
            audio_path=data.get("audio_path"),
            source_url=data.get("source_url"),
            artifact_paths=data.get("artifact_paths", []),
            provenance=data.get("provenance", {}),
        )


def _generate_class_id(date: str, title: str) -> str:
    """Generate YYMMDD-slug from date and title.

    Examples:
        >>> _generate_class_id("2026-05-26", "ELN Sesión 2 — Estrategia I")
        '260526-eln-sesion-2-estrategia-i'
    """
    # Parse date to YYMMDD
    try:
        dt = datetime.strptime(date.strip(), "%Y-%m-%d")
        yymmdd = dt.strftime("%y%m%d")
    except ValueError:
        # fallback: strip dashes
        yymmdd = date.replace("-", "")[-6:]

    # Slugify title — normalize accents to ASCII, then strip everything non-alphanumeric
    import unicodedata as _ud

    slug = _ud.normalize("NFKD", title.lower())
    slug = slug.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug).strip("-")

    return f"{yymmdd}-{slug}"


_CLASSES_ROOT = Path("work/classes")


def ingest_class(
    transcript_path: str,
    title: str,
    date: str,
    source_type: str = "file",
    source_url: Optional[str] = None,
    audio_path: Optional[str] = None,
    artifact_paths: Optional[list[str]] = None,
) -> ClassBundle:
    """Create a ClassBundle from a transcript and metadata.

    Args:
        transcript_path: Path to the transcript file (must exist).
        title: Class title.
        date: Class date (YYYY-MM-DD).
        source_type: Origin type ("bbb", "file", "upload").
        source_url: Optional URL of original recording.
        audio_path: Optional path to audio file.
        artifact_paths: Optional list of paths to supplementary materials.

    Returns:
        A ClassBundle with generated class_id and persisted YAML.

    Raises:
        FileNotFoundError: If transcript_path does not exist.
    """
    transcript_resolved = Path(transcript_path).resolve()
    if not transcript_resolved.exists():
        raise FileNotFoundError(f"transcript path does not exist: {transcript_path}")

    # Resolve optional paths
    audio_resolved = str(Path(audio_path).resolve()) if audio_path else None
    artifacts_resolved = [str(Path(p).resolve()) for p in (artifact_paths or [])]

    class_id = _generate_class_id(date, title)

    bundle = ClassBundle(
        class_id=class_id,
        title=title,
        date=date,
        source_type=source_type,
        transcript_path=str(transcript_resolved),
        audio_path=audio_resolved,
        source_url=source_url,
        artifact_paths=artifacts_resolved,
        provenance={
            "source": source_type,
            "original_location": source_url or str(transcript_resolved),
        },
    )

    _persist_bundle(bundle)
    return bundle


def _persist_bundle(bundle: ClassBundle) -> Path:
    """Write bundle as YAML to work/classes/{class_id}/bundle.yaml."""
    bundle_dir = (_CLASSES_ROOT / bundle.class_id).resolve()
    bundle_dir.mkdir(parents=True, exist_ok=True)

    yaml_path = bundle_dir / "bundle.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(bundle.to_dict(), f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    return yaml_path


def load_bundle(class_id_or_path: str) -> ClassBundle:
    """Load a ClassBundle from disk.

    Args:
        class_id_or_path: Either a class_id (e.g. "260526-eln-sesion2")
                          or a direct path to a bundle.yaml file.

    Returns:
        The deserialized ClassBundle.
    """
    candidate = Path(class_id_or_path)
    if candidate.suffix == ".yaml" and candidate.exists():
        yaml_path = candidate
    elif (_CLASSES_ROOT / class_id_or_path / "bundle.yaml").exists():
        yaml_path = _CLASSES_ROOT / class_id_or_path / "bundle.yaml"
    else:
        raise FileNotFoundError(f"no bundle found for: {class_id_or_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return ClassBundle.from_dict(data)


def summary(bundle: ClassBundle) -> str:
    """Return a human-readable summary of a ClassBundle."""
    lines = [
        f"class_id: {bundle.class_id}",
        f"title: {bundle.title}",
        f"date: {bundle.date}",
        f"transcript: {bundle.transcript_path}",
    ]
    if bundle.audio_path:
        lines.append(f"audio: {bundle.audio_path}")
    if bundle.artifact_paths:
        lines.append(f"artifacts: {len(bundle.artifact_paths)} file(s)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(prog="class-intake", description="Class intake and bundling")
    sub = parser.add_subparsers(dest="command", required=True)

    # ingest
    ingest_parser = sub.add_parser("ingest", help="Create a class bundle from transcript + metadata")
    ingest_parser.add_argument("--transcript", required=True, help="Path to transcript file")
    ingest_parser.add_argument("--title", required=True, help="Class title")
    ingest_parser.add_argument("--date", default="", help="Class date (YYYY-MM-DD, defaults to today)")
    ingest_parser.add_argument("--source-type", default="file", choices=["bbb", "file", "upload"], help="Source type")
    ingest_parser.add_argument("--source-url", default=None, help="Original recording URL")
    ingest_parser.add_argument("--audio", default=None, help="Path to audio file")
    ingest_parser.add_argument("--artifact", action="append", default=[], help="Path to lesson artifact")

    # load
    load_parser = sub.add_parser("load", help="Load and show a class bundle")
    load_parser.add_argument("class_id", help="Class ID or path to bundle.yaml")

    args = parser.parse_args()

    if args.command == "ingest":
        date = args.date or datetime.now().strftime("%Y-%m-%d")
        bundle = ingest_class(
            transcript_path=args.transcript,
            title=args.title,
            date=date,
            source_type=args.source_type,
            source_url=args.source_url,
            audio_path=args.audio,
            artifact_paths=args.artifact or None,
        )
        yaml_path = _CLASSES_ROOT / bundle.class_id / "bundle.yaml"
        print(f"✓ Bundle created: {yaml_path.resolve()}")

    elif args.command == "load":
        bundle = load_bundle(args.class_id)
        print(summary(bundle))


if __name__ == "__main__":
    main()
