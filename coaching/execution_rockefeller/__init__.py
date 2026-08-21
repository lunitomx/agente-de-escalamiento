"""Rockefeller Habits module — persist, resume, score, and export.

Storage: `.escala/my-company/rockefeller.yaml`
Export: `.escala/my-company/rockefeller.md`
"""

from __future__ import annotations

from pathlib import Path

from ..core import read_yaml, write_yaml
from .engine import RockefellerAssessment, score, validate
from .formatter import render_markdown

ACTIONS = ("load", "save", "export")


def _rockefeller_yaml_path(base: Path) -> Path:
    return base / ".escala" / "my-company" / "rockefeller.yaml"


def _rockefeller_md_path(base: Path) -> Path:
    return base / ".escala" / "my-company" / "rockefeller.md"


def run(context: dict) -> dict:
    """Execute a Rockefeller Habits action.

    Context keys:
        - action: str ("load" | "save" | "export")
        - base_path: str (path to project root)
        - data: dict (required for "save" — assessment data)
        - company_name: str (optional, for "export" header)
        - action_plan: list[str] (optional, for "export")
    """
    action = context.get("action", "")
    base = Path(context.get("base_path", "."))
    yaml_path = _rockefeller_yaml_path(base)

    if action not in ACTIONS:
        return {
            "output": "",
            "artifacts": {},
            "errors": [
                f"Acción desconocida: {action!r}. Válidas: {', '.join(ACTIONS)}"
            ],
        }

    if action == "load":
        raw = read_yaml(yaml_path)
        assessment = RockefellerAssessment.from_dict(raw)
        return {
            "output": "",
            "artifacts": {
                "state": assessment.to_dict(),
                "resuming": any(s.score is not None for s in assessment.scores),
                "errors": validate(assessment),
                "score": score(assessment),
            },
            "errors": [],
        }

    if action == "save":
        raw = context.get("data", {})
        assessment = RockefellerAssessment.from_dict(raw)
        errors = validate(assessment)
        write_yaml(yaml_path, assessment.to_dict())
        return {
            "output": f"Guardado: {len(assessment.scores)} hábitos",
            "artifacts": {
                "state": assessment.to_dict(),
                "errors": errors,
                "score": score(assessment),
            },
            "errors": [],
        }

    # action == "export"
    raw = read_yaml(yaml_path)
    assessment = RockefellerAssessment.from_dict(raw)
    markdown = render_markdown(
        assessment,
        company_name=context.get("company_name", ""),
        action_plan=context.get("action_plan"),
    )
    md_path = _rockefeller_md_path(base)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(markdown, encoding="utf-8")
    return {
        "output": markdown,
        "artifacts": {
            "markdown": markdown,
            "errors": validate(assessment),
            "score": score(assessment),
            "export_path": str(md_path),
        },
        "errors": [],
    }


def _main() -> None:
    """Minimal module entry point for ``python -m coaching.execution_rockefeller``."""
    from ..core import load_context

    result = run(load_context())
    if result.get("output"):
        print(result["output"])
    for error in result.get("errors", []):
        print(error)
