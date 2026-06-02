"""
Reviewable learning report for class bundles.

Generates a human-readable markdown report that summarizes a class,
its extracted patterns, and the suggested skill deltas.
"""

from __future__ import annotations

from pathlib import Path

from coaching.class_intake import ClassBundle, _CLASSES_ROOT
from coaching.pattern_extraction import load_patterns
from coaching.skill_deltas import load_deltas


def _render_header(bundle: ClassBundle) -> str:
    lines = [
        f"# Class Learning Report: {bundle.title}",
        "",
        f"**Class ID:** {bundle.class_id}  ",
        f"**Date:** {bundle.date}  ",
        f"**Source:** {bundle.source_type}  ",
        f"**Generated:** {bundle.created_at}  ",
        "",
        "---",
        "",
        "## 1. Class Summary",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Title | {bundle.title} |",
        f"| Date | {bundle.date} |",
        f"| Source | {bundle.source_type} |",
        f"| Transcript | `{bundle.transcript_path}` |",
    ]
    if bundle.audio_path:
        lines.append(f"| Audio | `{bundle.audio_path}` |")
    if bundle.source_url:
        lines.append(f"| Recording URL | {bundle.source_url} |")
    if bundle.artifact_paths:
        lines.append(f"| Artifacts | {len(bundle.artifact_paths)} file(s) |")

    lines.extend([
        "",
        "---",
        "",
    ])
    return "\n".join(lines)


def _render_patterns(bundle: ClassBundle) -> str:
    patterns = load_patterns(bundle)

    lines = [
        "## 2. Extracted Patterns",
        "",
        f"**Total patterns:** {len(patterns)}",
        "",
    ]

    if not patterns:
        lines.append("_No patterns extracted._")
        lines.append("")
        return "\n".join(lines)

    # Group by type
    by_type: dict[str, list] = {}
    for p in patterns:
        by_type.setdefault(p.type, []).append(p)

    type_labels = {
        "theme": "Themes (repeated topics)",
        "decision": "Decisions (explicit commitments from teacher)",
        "commitment": "Commitments (student action promises)",
        "contradiction": "Contradictions (prompt vs teaching mismatch)",
    }

    for ptype, label in type_labels.items():
        group = by_type.get(ptype, [])
        if not group:
            continue

        lines.append(f"### {label}")
        lines.append("")

        for p in group:
            lines.append(f"- **{p.label}** (x{p.occurrences}, confidence: {p.confidence:.0%})")
            lines.append(f"  - Evidence: _{p.evidence}_")
            lines.append("")

    return "\n".join(lines)


def _render_deltas(bundle: ClassBundle) -> str:
    deltas = load_deltas(bundle)

    lines = [
        "---",
        "",
        "## 3. Skill Deltas (Suggested Improvements)",
        "",
        f"**Total suggestions:** {len(deltas)}",
        "",
    ]

    if not deltas:
        lines.append("_No skill deltas generated._")
        lines.append("")
        return "\n".join(lines)

    for d in deltas:
        priority_label = {"P0": "🔴 Critical", "P1": "🟠 High", "P2": "🟡 Medium", "P3": "🟢 Low"}
        prio = priority_label.get(d.priority, d.priority)

        lines.append(f"### [{prio}] {d.target_skill}")
        lines.append("")
        lines.append(f"**Type:** `{d.suggestion_type}`  ")
        lines.append(f"**Description:** {d.description}  ")
        lines.append(f"**Evidence:** _{d.evidence}_  ")
        if d.pattern_label:
            lines.append(f"**From pattern:** `{d.pattern_label}`  ")
        lines.append("")

    return "\n".join(lines)


def generate_report(bundle: ClassBundle) -> Path:
    """Generate a markdown learning report for a class bundle.

    Reads patterns and deltas from disk, writes report.md
    alongside the bundle files.

    Returns:
        Path to the generated report.
    """
    sections = [
        _render_header(bundle),
        _render_patterns(bundle),
        _render_deltas(bundle),
    ]

    report = "\n".join(sections)

    bundle_dir = (_CLASSES_ROOT / bundle.class_id).resolve()
    bundle_dir.mkdir(parents=True, exist_ok=True)
    report_path = bundle_dir / "report.md"
    report_path.write_text(report, encoding="utf-8")

    return report_path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="class-report", description="Generate learning report for a class bundle")
    parser.add_argument("class_id", help="Class ID")
    args = parser.parse_args()

    from coaching.class_intake import load_bundle as lb

    bundle = lb(args.class_id)
    path = generate_report(bundle)
    print(f"✓ Report generated: {path}")


if __name__ == "__main__":
    main()
