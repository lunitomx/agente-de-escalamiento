#!/usr/bin/env python3
"""Run the E42 S42.2 skill inventory and real-invocation qualification.

This script scans ``escala-skills/``, builds a structured inventory, and
invokes a representative sample of skills through their Python core modules.
It does NOT replace a full manual audit or human acceptance; those are
recorded separately.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from coaching.dashboard import run as dashboard_run  # noqa: E402
from coaching.diagnose import run as diagnose_run  # noqa: E402
from coaching.diagnose import DIAGNOSE_QUESTIONS  # noqa: E402
from coaching.level import run as level_run  # noqa: E402
from coaching.progress import run as progress_run  # noqa: E402
from coaching.pulse import run as pulse_run  # noqa: E402
from coaching.welcome import run as welcome_run  # noqa: E402


SKILLS_DIR = ROOT / "escala-skills"
EVIDENCE_DIR = (
    ROOT / "work/epics/e42-product-qualification-and-functional-catalog/evidence"
)
EVIDENCE_PATH = EVIDENCE_DIR / "s42.2-skill-inventory.json"


def main() -> int:
    source_commit = _source_commit()
    skills = _scan_skills()
    inventory = [_analyze_skill(skill) for skill in skills]
    duplicates = _detect_duplicates(inventory)
    obsolete = _detect_obsolete(inventory)

    with tempfile.TemporaryDirectory(prefix="e42-s42.2-") as temporary:
        base = Path(temporary)
        _seed_workspace(base)

        invocation_results: dict[str, object] = {}

        # Positive case: welcome creates a company profile.
        welcome_ok = welcome_run(
            {
                "base_path": str(base),
                "company_name": "Nopal Foods S.A. de C.V.",
                "industry": "Alimentos",
                "employees": 35,
                "entry_methodology": "bmc",
            }
        )
        invocation_results["escala-welcome-positive"] = {
            "status": "pass" if not welcome_ok.get("errors") else "fail",
            "errors": welcome_ok.get("errors", []),
        }

        # Negative case: welcome rejects missing required fields.
        welcome_bad = welcome_run(
            {
                "base_path": str(base),
                "company_name": "",
                "industry": "",
                "employees": 0,
            }
        )
        invocation_results["escala-welcome-negative"] = {
            "status": "pass" if welcome_bad.get("errors") else "fail",
            "errors": welcome_bad.get("errors", []),
        }

        # Positive case: full diagnose with all answers.
        answers = _full_answers()
        diagnose_ok = diagnose_run(
            {
                "base_path": str(base),
                "answers": answers,
                "mode": "full",
            }
        )
        invocation_results["escala-diagnose-positive"] = {
            "status": "pass" if not diagnose_ok.get("errors") else "fail",
            "priority": diagnose_ok.get("artifacts", {}).get("priority"),
            "errors": diagnose_ok.get("errors", []),
        }

        # Negative case: diagnose rejects missing answers.
        diagnose_bad = diagnose_run(
            {
                "base_path": str(base),
                "answers": {},
                "mode": "full",
            }
        )
        invocation_results["escala-diagnose-negative"] = {
            "status": "pass" if diagnose_bad.get("errors") else "fail",
            "errors": diagnose_bad.get("errors", []),
        }

        # Positive case: level detection with valid scores.
        level_ok = level_run(
            {
                "base_path": str(base),
                "action": "detect",
            }
        )
        invocation_results["escala-level-positive"] = {
            "status": "pass" if not level_ok.get("errors") else "fail",
            "level": level_ok.get("artifacts", {}).get("level"),
            "errors": level_ok.get("errors", []),
        }

        # Negative case: level rejects invalid level name.
        level_bad = level_run(
            {
                "base_path": str(base),
                "action": "set",
                "level": "invalid",
            }
        )
        invocation_results["escala-level-negative"] = {
            "status": "pass" if level_bad.get("errors") else "fail",
            "errors": level_bad.get("errors", []),
        }

        # Positive case: progress dashboard with scores and worksheets.
        progress_ok = progress_run(
            {
                "base_path": str(base),
            }
        )
        invocation_results["escala-progress-positive"] = {
            "status": "pass" if not progress_ok.get("errors") else "fail",
            "completion_pct": progress_ok.get("artifacts", {}).get("completion_pct"),
            "errors": progress_ok.get("errors", []),
        }

        # Positive case: pulse check with all decisions answered.
        pulse_ok = pulse_run(
            {
                "base_path": str(base),
                "answers": {
                    "people": 1,
                    "strategy": 0,
                    "execution": 1,
                    "cash": -1,
                    "overall": 0,
                },
            }
        )
        invocation_results["escala-pulse-positive"] = {
            "status": "pass" if not pulse_ok.get("errors") else "fail",
            "trends": pulse_ok.get("artifacts", {}).get("trends"),
            "errors": pulse_ok.get("errors", []),
        }

        # Negative case: pulse rejects missing answers.
        pulse_bad = pulse_run(
            {
                "base_path": str(base),
                "answers": {"people": 1},
            }
        )
        invocation_results["escala-pulse-negative"] = {
            "status": "pass" if pulse_bad.get("errors") else "fail",
            "errors": pulse_bad.get("errors", []),
        }

        # Positive case: dashboard renders after data exists.
        dashboard_ok = dashboard_run({"base_path": str(base)})
        invocation_results["escala-dashboard-positive"] = {
            "status": "pass" if not dashboard_ok.get("errors") else "fail",
            "errors": dashboard_ok.get("errors", []),
        }

    all_pass = all(
        isinstance(result, dict) and result.get("status") == "pass"
        for result in invocation_results.values()
    )

    evidence: dict[str, Any] = {
        "schema_version": 1,
        "story": "S42.2",
        "epic": "E42",
        "source_commit": source_commit,
        "environment": "local-synthetic",
        "requirement": "REQ-E42-002",
        "platform_matrix": ["macos", "windows"],
        "notes": [
            "Inventory is built from escala-skills/ SKILL.md files.",
            "Invocation exercises Python core modules only; pure markdown skills are listed as not-demonstrated.",
            "Clean hardware and human acceptance are recorded separately.",
        ],
        "inventory": inventory,
        "inventory_summary": {
            "total_skills": len(inventory),
            "demonstrated": sum(1 for s in inventory if s["demonstrated"]),
            "not_demonstrated": sum(1 for s in inventory if not s["demonstrated"]),
            "duplicates_flagged": len(duplicates),
            "obsolete_flagged": len(obsolete),
        },
        "duplicates": duplicates,
        "obsolete": obsolete,
        "invocation_results": invocation_results,
        "overall_status": "pass" if all_pass else "fail",
    }

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    status = evidence["overall_status"]
    print(f"S42.2 skill inventory qualification: {status.upper()}")
    print(f"Evidence: {EVIDENCE_PATH}")
    print(f"Skills inventoried: {len(inventory)}")
    print(f"Demonstrated: {evidence['inventory_summary']['demonstrated']}")
    print(f"Not demonstrated: {evidence['inventory_summary']['not_demonstrated']}")
    print(f"Duplicates flagged: {len(duplicates)}")
    for result in invocation_results.values():
        if isinstance(result, dict) and result.get("status") != "pass":
            print(f"FAILED invocation: {result}")
    return 0 if status == "pass" else 1


def _scan_skills() -> list[Path]:
    """Return sorted list of skill directories that contain a SKILL.md file."""
    skills: list[Path] = []
    if not SKILLS_DIR.exists():
        return skills
    for directory in sorted(SKILLS_DIR.iterdir()):
        skill_file = directory / "SKILL.md"
        if directory.is_dir() and skill_file.exists():
            skills.append(directory)
    return skills


def _analyze_skill(skill_dir: Path) -> dict[str, Any]:
    """Parse a skill directory into a structured inventory entry."""
    skill_file = skill_dir / "SKILL.md"
    text = skill_file.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(text)
    meta = yaml.safe_load(frontmatter) if frontmatter else {}

    name = meta.get("name") or skill_dir.name
    description = meta.get("description") or ""
    purpose = _extract_purpose(body) or description
    required_info = _extract_required_info(body)
    delivered_result = _extract_delivered_result(body)
    positive_case = _build_positive_case(name, purpose, required_info)
    negative_case = _build_negative_case(name, required_info)
    demonstrated = _has_python_core(name)

    return {
        "id": name,
        "directory": str(skill_dir.relative_to(ROOT)),
        "description": description,
        "business_problem": purpose,
        "required_info": required_info,
        "delivered_result": delivered_result,
        "positive_case": positive_case,
        "negative_case": negative_case,
        "demonstrated": demonstrated,
        "demonstration_method": "python-core" if demonstrated else "not-invoked",
    }


def _split_frontmatter(text: str) -> tuple[str, str]:
    """Split YAML frontmatter from markdown body."""
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) >= 3:
        return parts[1], parts[2]
    return "", text


def _extract_purpose(body: str) -> str:
    """Extract the first paragraph under a Purpose heading."""
    match = re.search(
        r"##?\s*Purpose\s*\n+(.+?)(?:\n\n|\n##|\Z)", body, re.IGNORECASE | re.DOTALL
    )
    if match:
        return " ".join(match.group(1).strip().split())
    return ""


def _extract_required_info(body: str) -> list[str]:
    """Heuristically list inputs/context the skill needs."""
    required: list[str] = []
    if re.search(r"company.?profile|perfil.*empresa", body, re.IGNORECASE):
        required.append("company profile")
    if re.search(r"diagnos|scores|score", body, re.IGNORECASE):
        required.append("diagnosis scores")
    if re.search(r"worksheet|worksheets", body, re.IGNORECASE):
        required.append("worksheets registry")
    if re.search(r"cash|efectivo|CCC|Power of One", body, re.IGNORECASE):
        required.append("cash flow data")
    if re.search(r"reunión|meeting|daily|weekly|huddle", body, re.IGNORECASE):
        required.append("meeting notes or rhythm context")
    if re.search(r"prioridad|priority|critical number", body, re.IGNORECASE):
        required.append("quarterly priorities")
    if re.search(r"people|equipo|values|topgrading|FAC", body, re.IGNORECASE):
        required.append("people/team data")
    if re.search(r"strategy|OPSP|SWOT|7 strata|BHAG", body, re.IGNORECASE):
        required.append("strategy context")
    if not required:
        required.append("user intent / conversation context")
    return required


def _extract_delivered_result(body: str) -> str:
    """Extract output/destination from the skill body."""
    match = re.search(
        r"##?\s*Output\s*\n+(.*?)(?:\n\n|\n##|\Z)", body, re.IGNORECASE | re.DOTALL
    )
    if match:
        return " ".join(match.group(1).strip().split())
    match = re.search(
        r"##?\s*Result\s*\n+(.*?)(?:\n\n|\n##|\Z)", body, re.IGNORECASE | re.DOTALL
    )
    if match:
        return " ".join(match.group(1).strip().split())
    return "Guided recommendation or artifact stored in work/"


def _build_positive_case(name: str, purpose: str, required_info: list[str]) -> str:
    info = required_info[0] if required_info else "required context"
    return (
        f"When {info} is available, {name} guides the user through "
        f"{purpose.lower() if purpose else 'its workflow'} and produces a concrete next step."
    )


def _build_negative_case(name: str, required_info: list[str]) -> str:
    info = required_info[0] if required_info else "required context"
    return (
        f"When {info} is missing or incomplete, {name} asks clarifying questions "
        "instead of fabricating a recommendation."
    )


def _has_python_core(name: str) -> bool:
    """Return True if the skill has a runnable Python core module in this script."""
    return name in {
        "escala-diagnose",
        "escala-progress",
        "escala-level",
        "escala-dashboard",
        "escala-pulse",
        "escala-welcome",
    }


def _detect_duplicates(inventory: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Flag skills whose names suggest overlapping responsibility."""
    flagged: list[dict[str, str]] = []
    by_stem: dict[str, list[str]] = {}
    for item in inventory:
        name = item["id"]
        # Group by base decision + action (e.g. execution-priorities / execution-prioridad)
        normalized = re.sub(r"s$|es$", "", name.replace("escala-", "").lower())
        normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
        by_stem.setdefault(normalized, []).append(name)

    known_overlaps = {
        "execution-prioriti": [
            "escala-execution-priorities",
            "escala-execution-prioridad",
        ],
        "execution-rhythm": ["escala-execution-rhythms", "escala-rhythm-weekly"],
        "people-organigram": ["escala-people-organigrama", "escala-people-fac"],
    }

    for stem, names in by_stem.items():
        if stem in known_overlaps:
            flagged.append(
                {
                    "stem": stem,
                    "skills": ", ".join(known_overlaps[stem]),
                    "reason": "similar scope; verify which is canonical",
                }
            )
        elif len(names) > 1:
            flagged.append(
                {
                    "stem": stem,
                    "skills": ", ".join(names),
                    "reason": "names normalize to same stem",
                }
            )
    return flagged


def _detect_obsolete(inventory: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Flag skills that mention deprecated or obsolete artifacts."""
    flagged: list[dict[str, str]] = []
    obsolete_markers = [
        "deprecado",
        "deprecated",
        "obsoleto",
        "obsolete",
        "old command",
    ]
    for item in inventory:
        text = " ".join(
            [item["description"], item["business_problem"], item["delivered_result"]]
        ).lower()
        for marker in obsolete_markers:
            if marker in text:
                flagged.append(
                    {
                        "skill": item["id"],
                        "reason": f"contains marker: {marker}",
                    }
                )
                break
    return flagged


def _seed_workspace(base: Path) -> None:
    """Create a minimal .escala workspace so core modules can run."""
    memory = base / ".escala" / "agent" / "memory"
    memory.mkdir(parents=True, exist_ok=True)
    registry = base / ".escala" / "knowledge" / "registry"
    registry.mkdir(parents=True, exist_ok=True)
    my_company = base / ".escala" / "my-company"
    my_company.mkdir(parents=True, exist_ok=True)

    profile = {
        "company": {
            "name": "Nopal Foods S.A. de C.V.",
            "industry": "Alimentos",
            "employees": 35,
            "growth_stage": "growth",
            "entry_methodology": "bmc",
        },
        "scores": {},
        "focus": {"current_decision": None, "last_session": None},
        "coaching": {"level": "shu", "level_source": "auto"},
    }
    (memory / "company-profile.yaml").write_text(
        yaml.dump(
            profile, default_flow_style=False, allow_unicode=True, sort_keys=False
        ),
        encoding="utf-8",
    )

    worksheets = {
        "worksheets": [
            {
                "id": "people-1",
                "name": "Core Values",
                "decision": "people",
                "difficulty": "easy",
                "time_estimate": "30m",
            },
            {
                "id": "strategy-1",
                "name": "OPSP",
                "decision": "strategy",
                "difficulty": "hard",
                "time_estimate": "2h",
            },
            {
                "id": "execution-1",
                "name": "Quarterly Priorities",
                "decision": "execution",
                "difficulty": "medium",
                "time_estimate": "1h",
            },
            {
                "id": "cash-1",
                "name": "CCC Analysis",
                "decision": "cash",
                "difficulty": "medium",
                "time_estimate": "1h",
            },
        ]
    }
    (registry / "worksheets.yaml").write_text(
        yaml.dump(
            worksheets, default_flow_style=False, allow_unicode=True, sort_keys=False
        ),
        encoding="utf-8",
    )

    (my_company / "pulse-history.yaml").write_text(
        yaml.dump({"history": []}, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )


def _full_answers() -> dict[str, int]:
    """Return a complete set of valid diagnosis answers."""
    answers: dict[str, int] = {}
    for decision, data in DIAGNOSE_QUESTIONS.items():
        for index, question in enumerate(data["questions"]):
            answers[question["id"]] = (index % 3) + 2  # values 2, 3, 4
    return answers


def _source_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
