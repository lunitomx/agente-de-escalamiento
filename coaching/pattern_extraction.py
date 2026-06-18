"""
Pattern extraction from class transcripts and prompts.

Extracts themes, decisions, commitments, and contradictions
using simple heuristics (n-gram frequency, keyword matching, regex).
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path

from coaching.class_intake import ClassBundle, _CLASSES_ROOT


# ---------------------------------------------------------------------------
# Pattern dataclass
# ---------------------------------------------------------------------------


@dataclass
class Pattern:
    """A single extracted pattern from a class transcript."""

    type: str  # "theme", "decision", "commitment", "contradiction"
    label: str
    evidence: str
    occurrences: int = 1
    confidence: float = 0.5  # 0.0–1.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Pattern":
        return cls(**data)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "de",
    "la",
    "que",
    "el",
    "en",
    "y",
    "a",
    "los",
    "del",
    "se",
    "las",
    "por",
    "un",
    "una",
    "con",
    "no",
    "es",
    "lo",
    "al",
    "su",
    "le",
    "para",
    "más",
    "como",
    "pero",
    "sus",
    "este",
    "entre",
    "está",
    "todo",
    "esta",
    "muy",
    "qué",
    "porque",
    "eso",
    "hay",
    "tiene",
    "era",
    "son",
    "han",
    "fue",
    "ser",
    "sido",
    "cada",
    "también",
    "solo",
    "donde",
    "quien",
    "cómo",
    "tan",
    "años",
    "dos",
    "vez",
    "después",
    "así",
    "sí",
    "ni",
    "contra",
    "hasta",
    "puede",
    "hace",
    "tener",
    "tanto",
    "hoy",
    "voy",
    "va",
    "he",
}

_DECISION_KEYWORDS = [
    "compromiso",
    "acordamos",
    "les voy a pedir",
    "antes de la próxima clase",
    "su tarea es",
    "quiero que tengan",
    "necesito que",
    "vamos a hacer",
    "lo que quiero es que",
]

_COMMITMENT_PATTERNS = [
    r"\bvoy\s+a\b",
    r"\bme\s+comprometo\b",
    r"\besta\s+semana\b",
    r"\bantes\s+del?\s+próximo?\b",
]

_CONTRADICTION_MARKERS = [
    ("importante", "no es necesario"),
    ("obligatorio", "si pueden"),
    ("todos deben", "si quieren"),
]


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------


def _tokenize(text: str, keep_stopwords: bool = False) -> list[str]:
    """Lowercase, split on non-alpha, filter single-chars."""
    text = text.lower()
    tokens = re.findall(r"[a-záéíóúüñ]{2,}", text)
    if not keep_stopwords:
        tokens = [t for t in tokens if t not in _STOPWORDS]
    return tokens


def _extract_ngrams(tokens: list[str], n: int = 2) -> list[str]:
    """Generate n-grams as space-joined strings."""
    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def _extract_themes(text: str, top_n: int = 10) -> list[Pattern]:
    """Detect repeated themes via bigram and trigram frequency."""
    # Keep stopwords for n-gram adjacency, filter only for the final label
    tokens = _tokenize(text, keep_stopwords=True)

    patterns: list[Pattern] = []

    for n in (2, 3):
        ngrams = _extract_ngrams(tokens, n)
        if not ngrams:
            continue
        counts = Counter(ngrams)
        for ngram, count in counts.most_common(top_n * 2):
            if count < 2:
                continue
            # Skip n-grams that are entirely stopwords
            words = ngram.split()
            if all(w in _STOPWORDS for w in words):
                continue
            patterns.append(
                Pattern(
                    type="theme",
                    label=ngram,
                    evidence=f"Mencionado {count} veces",
                    occurrences=count,
                    confidence=min(count / 10, 0.95),
                )
            )

    # Deduplicate: longer n-grams that contain shorter ones → keep longer
    patterns.sort(key=lambda p: (-p.occurrences, -len(p.label)))
    deduped: list[Pattern] = []
    seen_labels: set[str] = set()
    for p in patterns:
        words = set(p.label.split())
        if any(words.issubset(set(d.label.split())) for d in deduped):
            continue
        deduped.append(p)
        seen_labels.add(p.label)
        if len(deduped) >= top_n:
            break

    return deduped


def _extract_decisions(text: str) -> list[Pattern]:
    """Detect decisions via keyword matching."""
    text_lower = text.lower()
    patterns: list[Pattern] = []

    for keyword in _DECISION_KEYWORDS:
        indices = [m.start() for m in re.finditer(re.escape(keyword), text_lower)]
        if not indices:
            continue
        # Grab context around first occurrence
        idx = indices[0]
        start = max(0, idx - 60)
        end = min(len(text), idx + len(keyword) + 120)
        evidence = text[start:end].strip()

        patterns.append(
            Pattern(
                type="decision",
                label=keyword,
                evidence=evidence,
                occurrences=len(indices),
                confidence=0.8,
            )
        )

    return patterns


def _extract_commitments(text: str) -> list[Pattern]:
    """Detect commitments via regex patterns."""
    patterns: list[Pattern] = []

    for regex in _COMMITMENT_PATTERNS:
        matches = list(re.finditer(regex, text, re.IGNORECASE))
        if not matches:
            continue
        m = matches[0]
        start = max(0, m.start() - 60)
        end = min(len(text), m.end() + 120)
        evidence = text[start:end].strip()

        patterns.append(
            Pattern(
                type="commitment",
                label=m.group(),
                evidence=evidence,
                occurrences=len(matches),
                confidence=0.7,
            )
        )

    return patterns


def extract_patterns(bundle: ClassBundle) -> list[Pattern]:
    """Extract all patterns from a ClassBundle's transcript.

    Args:
        bundle: A ClassBundle with a valid transcript_path.

    Returns:
        List of Pattern objects sorted by confidence descending.

    Raises:
        FileNotFoundError: If the bundle's transcript does not exist.
    """
    transcript_path = Path(bundle.transcript_path)
    if not transcript_path.exists():
        raise FileNotFoundError(f"transcript not found: {transcript_path}")

    text = transcript_path.read_text(encoding="utf-8")

    patterns: list[Pattern] = []
    patterns.extend(_extract_themes(text))
    patterns.extend(_extract_decisions(text))
    patterns.extend(_extract_commitments(text))

    # Sort by confidence descending
    patterns.sort(key=lambda p: -p.confidence)
    return patterns


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def save_patterns(bundle: ClassBundle, patterns: list[Pattern]) -> Path:
    """Save extracted patterns as JSON alongside the bundle."""
    bundle_dir = (_CLASSES_ROOT / bundle.class_id).resolve()
    bundle_dir.mkdir(parents=True, exist_ok=True)
    json_path = bundle_dir / "patterns.json"
    data = [p.to_dict() for p in patterns]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return json_path


def load_patterns(bundle: ClassBundle) -> list[Pattern]:
    """Load extracted patterns from JSON."""
    json_path = (_CLASSES_ROOT / bundle.class_id).resolve() / "patterns.json"
    if not json_path.exists():
        return []
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Pattern.from_dict(d) for d in data]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="pattern-extract", description="Extract patterns from class bundles"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    extract_parser = sub.add_parser(
        "extract", help="Extract patterns from a class bundle"
    )
    extract_parser.add_argument("class_id", help="Class ID")

    args = parser.parse_args()

    if args.command == "extract":
        from coaching.class_intake import load_bundle as lb

        bundle = lb(args.class_id)
        patterns = extract_patterns(bundle)
        save_patterns(bundle, patterns)
        print(f"✓ {len(patterns)} patterns extracted and saved")
        for p in patterns[:10]:
            print(
                f"  [{p.type:12s}] {p.label} (x{p.occurrences}, conf={p.confidence:.2f})"
            )


if __name__ == "__main__":
    main()
