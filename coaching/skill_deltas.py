"""
Skill delta suggestions for Escala coaching.

Maps extracted patterns to specific Escala skills and generates
suggested improvements (deltas) with evidence.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from coaching.class_intake import ClassBundle, _CLASSES_ROOT


# ---------------------------------------------------------------------------
# SkillDelta dataclass
# ---------------------------------------------------------------------------


@dataclass
class SkillDelta:
    """A suggested improvement for an Escala skill, grounded in class evidence."""

    target_skill: str
    suggestion_type: str  # "new_prompt", "strengthen_prompt", "fix_contradiction", "new_heuristic"
    description: str
    evidence: str
    priority: str = "P2"  # P0 (critical), P1 (high), P2 (medium), P3 (low)
    pattern_label: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SkillDelta":
        return cls(**data)


# ---------------------------------------------------------------------------
# Mapping rules
# ---------------------------------------------------------------------------

# Pattern keyword → target skill areas + suggestion type
_MAP_RULES: list[tuple[re.Pattern, str, str, str, str]] = [
    # (pattern_regex, target_skill, suggestion_type, description_template, priority)

    # Canvas / business model
    (re.compile(r"canvas", re.I), "kokoro-canvas", "strengthen_prompt",
     "Reforzar prompt del canvas con el tema detectado", "P1"),

    # Strategy
    (re.compile(r"estrategi|strategi", re.I), "escala-strategy", "new_prompt",
     "Añadir prompt basado en el tema de estrategia observado en clase", "P1"),

    # Core customer / buyer persona
    (re.compile(r"cliente|core.?customer|buyer.?person|a quién", re.I), "escala-people", "strengthen_prompt",
     "Reforzar prompt de definición de cliente ideal con hallazgo de clase", "P2"),

    # Brand promise
    (re.compile(r"promesa|brand.?promise|marca", re.I), "kokoro-luxury-communication", "new_prompt",
     "Añadir prompt para brand promise basado en la clase", "P1"),

    # Commitment / homework
    (re.compile(r"compromiso|antes de la próxima clase|tarea", re.I), "escala-execution", "new_heuristic",
     "Añadir heurística de seguimiento de compromisos post-clase", "P2"),

    # Execution / habits
    (re.compile(r"ejecución|hábito|ritmo|reunión", re.I), "escala-execution-habits", "new_heuristic",
     "Añadir heurística basada en tema de ejecución", "P3"),

    # Cash / finances
    (re.compile(r"cash|efectivo|ingreso|rentabil", re.I), "escala-cash", "new_prompt",
     "Añadir prompt financiero basado en el tema de clase", "P2"),
]


def _match_pattern_to_skill(pattern_label: str, pattern_evidence: str) -> Optional[SkillDelta]:
    """Match a single pattern label against mapping rules."""
    for regex, skill, sug_type, desc_template, priority in _MAP_RULES:
        if regex.search(pattern_label):
            return SkillDelta(
                target_skill=skill,
                suggestion_type=sug_type,
                description=desc_template,
                evidence=pattern_evidence[:200],
                priority=priority,
                pattern_label=pattern_label,
            )
    return None


# ---------------------------------------------------------------------------
# Skills inventory
# ---------------------------------------------------------------------------


def load_skills_inventory() -> list[str]:
    """Scan the escala-skills/ directory for available skill names.

    Looks at subdirectory names under escala-skills/ and optionally
    the kokoro skills directory.
    """
    skills: list[str] = []

    # Local escala-skills
    escala_skills = Path("escala-skills")
    if escala_skills.exists():
        for d in sorted(escala_skills.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                skills.append(d.name)

    # Also check Hermes kokoro skills
    hermes_skills = Path.home() / ".hermes" / "skills" / "kokoro"
    if hermes_skills.exists():
        for d in sorted(hermes_skills.iterdir()):
            if d.is_dir() and d.name not in skills:
                skills.append(f"kokoro-{d.name}")

    return sorted(skills)


# ---------------------------------------------------------------------------
# Suggestion engine
# ---------------------------------------------------------------------------


def suggest_deltas(
    patterns: list,
    skills: Optional[list[str]] = None,
) -> list[SkillDelta]:
    """Generate SkillDelta suggestions from extracted patterns.

    Args:
        patterns: List of Pattern objects (from pattern_extraction).
        skills: Optional list of available skill names. If None, loads from disk.

    Returns:
        List of SkillDelta suggestions sorted by priority.
    """
    if skills is None:
        skills = load_skills_inventory()

    deltas: list[SkillDelta] = []

    for pattern in patterns:
        label = str(getattr(pattern, "label", ""))
        evidence = str(getattr(pattern, "evidence", ""))

        if not label:
            continue

        delta = _match_pattern_to_skill(str(label), str(evidence))
        if delta and delta.target_skill in skills:
            deltas.append(delta)

    # Deduplicate: same skill + same suggestion_type
    seen = set()
    unique: list[SkillDelta] = []
    for d in deltas:
        key = (d.target_skill, d.suggestion_type)
        if key not in seen:
            seen.add(key)
            unique.append(d)

    # Sort by priority
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    unique.sort(key=lambda d: priority_order.get(d.priority, 99))

    return unique


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def save_deltas(bundle: ClassBundle, deltas: list[SkillDelta]) -> Path:
    """Save skill deltas as JSON alongside the bundle."""
    bundle_dir = (_CLASSES_ROOT / bundle.class_id).resolve()
    bundle_dir.mkdir(parents=True, exist_ok=True)
    json_path = bundle_dir / "deltas.json"
    data = [d.to_dict() for d in deltas]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return json_path


def load_deltas(bundle: ClassBundle) -> list[SkillDelta]:
    """Load skill deltas from JSON."""
    json_path = (_CLASSES_ROOT / bundle.class_id).resolve() / "deltas.json"
    if not json_path.exists():
        return []
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [SkillDelta.from_dict(d) for d in data]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="skill-deltas", description="Suggest skill deltas from class patterns")
    sub = parser.add_subparsers(dest="command", required=True)

    suggest_parser = sub.add_parser("suggest", help="Generate deltas from class bundle patterns")
    suggest_parser.add_argument("class_id", help="Class ID")

    skills_parser = sub.add_parser("skills", help="List available skills in inventory")

    args = parser.parse_args()

    if args.command == "suggest":
        from coaching.class_intake import load_bundle as lb
        from coaching.pattern_extraction import load_patterns

        bundle = lb(args.class_id)
        patterns = load_patterns(bundle)
        skills = load_skills_inventory()
        deltas = suggest_deltas(patterns, skills)
        save_deltas(bundle, deltas)
        print(f"✓ {len(deltas)} deltas suggested and saved")
        for d in deltas:
            print(f"  [{d.priority}] {d.target_skill}: {d.description[:60]}...")

    elif args.command == "skills":
        skills = load_skills_inventory()
        print(f"{len(skills)} skills in inventory:")
        for s in skills:
            print(f"  - {s}")


if __name__ == "__main__":
    main()
