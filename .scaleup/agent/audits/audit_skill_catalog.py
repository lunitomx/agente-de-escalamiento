#!/usr/bin/env python3
"""
Skill catalog inventory and duplication analysis.

Scans ESCALA/ScaleUp product skills and produces a Markdown report with:
- Count by source directory
- Skill list with decision area and description
- Duplicate / near-duplicate pairs
- Bitter Pill recommendations (keep / merge / delete)
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SOURCE_DIRS = [
    REPO_ROOT / "escala-skills",
    REPO_ROOT / ".agents" / "skills",
    REPO_ROOT / ".claude" / "skills",
]

DECISION_AREAS = {
    "people": ["people", "fac", "topgrading", "values", "hiring", "equipo"],
    "strategy": ["strategy", "opsp", "7strata", "swot", "bhag", "estrategia"],
    "execution": ["execution", "rhythms", "priorities", "habits", "rockefeller", "huddle"],
    "cash": ["cash", "ccc", "power1", "power-of-one", "finanzas", "acceleration"],
    "session": ["welcome", "start", "close", "diagnose", "progress", "pulse", "dashboard", "export", "task"],
}


def infer_decision_area(name: str, text: str) -> str:
    """Infer which of the 4 Decisions a skill belongs to."""
    lowered = f"{name} {text[:500]}".lower()
    scores: dict[str, int] = defaultdict(int)
    for area, keywords in DECISION_AREAS.items():
        for kw in keywords:
            scores[area] += lowered.count(kw)
    if not scores or max(scores.values()) == 0:
        return "other"
    return max(scores, key=lambda k: scores[k])


def parse_frontmatter(text: str) -> dict[str, str]:
    """Extract simple YAML frontmatter key/value pairs."""
    meta: dict[str, str] = {}
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            for line in text[3:end].strip().splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta


def extract_purpose(text: str) -> str:
    """First paragraph after frontmatter or first H1/H2."""
    body = re.sub(r"^---.*?---", "", text, flags=re.DOTALL).strip()
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    for line in lines[:10]:
        if line.startswith("#"):
            return line.lstrip("#").strip()
    for line in lines[:10]:
        if len(line) > 20:
            return line
    return ""


def scan_skills() -> list[dict]:
    """Scan configured source directories for product skills."""
    skills: list[dict] = []
    for source in SOURCE_DIRS:
        if not source.exists():
            continue
        for skill_dir in sorted(source.iterdir()):
            if not skill_dir.is_dir():
                continue
            name = skill_dir.name
            if not name.startswith(("escala-", "scaleup-")):
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            text = skill_file.read_text(encoding="utf-8")
            meta = parse_frontmatter(text)
            purpose = extract_purpose(text)
            skills.append(
                {
                    "name": name,
                    "display_name": meta.get("name", name),
                    "description": meta.get("description", ""),
                    "purpose": purpose,
                    "source": str(skill_dir.relative_to(REPO_ROOT)),
                    "source_dir": str(source.relative_to(REPO_ROOT)),
                    "decision_area": infer_decision_area(name, text),
                    "word_count": len(text.split()),
                }
            )
    return skills


def find_duplicates(skills: list[dict]) -> list[dict]:
    """Find duplicate / near-duplicate skills by normalized name."""
    by_norm: dict[str, list[dict]] = defaultdict(list)
    for skill in skills:
        # Normalize escala-* and scaleup-* to a common root.
        norm = skill["name"].removeprefix("escala-").removeprefix("scaleup-")
        by_norm[norm].append(skill)

    duplicates: list[dict] = []
    for norm, group in sorted(by_norm.items()):
        if len(group) > 1:
            duplicates.append({"norm": norm, "skills": group})
    return duplicates


def recommend(norm: str, group: list[dict]) -> str:
    """Bitter Pill recommendation for a duplicate group."""
    names = {s["name"] for s in group}
    has_escala = any(n.startswith("escala-") for n in names)
    has_scaleup = any(n.startswith("scaleup-") for n in names)

    # Session lifecycle skills are likely needed as orchestrators.
    if norm in {"welcome", "start", "close", "diagnose", "progress", "pulse", "dashboard", "export"}:
        return "keep-escala | deprecate-scaleup | migrate to core Python when memory is real"

    if has_escala and has_scaleup:
        return "merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic"

    return "review manually"


def generate_report(skills: list[dict], duplicates: list[dict]) -> str:
    """Generate Markdown report."""
    lines: list[str] = [
        "# Skill Catalog Inventory",
        "",
        f"Generated from {len(skills)} product skills.",
        "",
        "## Count by source directory",
        "",
        "| Source | Count |",
        "|--------|-------|",
    ]

    counts: dict[str, int] = defaultdict(int)
    for skill in skills:
        counts[skill["source_dir"]] += 1
    for source, count in sorted(counts.items()):
        lines.append(f"| {source} | {count} |")

    lines.extend(
        [
            "",
            "## Count by decision area",
            "",
            "| Area | Count |",
            "|------|-------|",
        ]
    )
    area_counts: dict[str, int] = defaultdict(int)
    for skill in skills:
        area_counts[skill["decision_area"]] += 1
    for area, count in sorted(area_counts.items()):
        lines.append(f"| {area} | {count} |")

    lines.extend(
        [
            "",
            "## Duplicate / near-duplicate groups",
            "",
            f"Found {len(duplicates)} groups with more than one skill.",
            "",
        ]
    )
    for dup in duplicates:
        lines.append(f"### {dup['norm']}")
        lines.append("")
        lines.append(f"**Recommendation:** {recommend(dup['norm'], dup['skills'])}")
        lines.append("")
        lines.append("| Skill | Source | Area | Words | Description |")
        lines.append("|-------|--------|------|-------|-------------|")
        for skill in dup["skills"]:
            desc = skill["description"][:80].replace("|", "\\|")
            lines.append(
                f"| {skill['name']} | {skill['source_dir']} | {skill['decision_area']} | "
                f"{skill['word_count']} | {desc} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Full catalog",
            "",
            "| Skill | Source | Area | Words | Purpose |",
            "|-------|--------|------|-------|---------|",
        ]
    )
    for skill in sorted(skills, key=lambda s: (s["decision_area"], s["name"])):
        purpose = skill["purpose"][:80].replace("|", "\\|")
        lines.append(
            f"| {skill['name']} | {skill['source_dir']} | {skill['decision_area']} | "
            f"{skill['word_count']} | {purpose} |"
        )

    return "\n".join(lines)


def main() -> None:
    skills = scan_skills()
    duplicates = find_duplicates(skills)
    report = generate_report(skills, duplicates)

    output_path = REPO_ROOT / "work" / "debug" / "escala-gap-analysis" / "skill-catalog-inventory.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Wrote inventory to {output_path}")
    print(f"Skills: {len(skills)} | Duplicate groups: {len(duplicates)}")


if __name__ == "__main__":
    main()
