"""
Strategy OPSP module — persist, resume, and export the One-Page Strategic Plan.

Storage: `.escala/my-company/opsp.yaml` (same tree as escala-diagnose's
company-profile.yaml). Export: `.escala/my-company/opsp.md`, rendered from
templates/opsp.md's structure via formatter.render_markdown.
"""

from pathlib import Path

from ..core import read_yaml, write_yaml
from .engine import merge_section, missing_fields
from .formatter import render_markdown

ACTIONS = ("load", "save", "export")


def _opsp_yaml_path(base: Path) -> Path:
    return base / ".escala" / "my-company" / "opsp.yaml"


def _opsp_md_path(base: Path) -> Path:
    return base / ".escala" / "my-company" / "opsp.md"


def run(context: dict) -> dict:
    """
    Execute a strategy_opsp action.

    Context keys:
        - action: str ("load" | "save" | "export")
        - base_path: str (path to project root)
        - section: str (required for "save" — one of engine.SECTIONS)
        - data: Any (required for "save" — the value for that section)
        - company_name: str (optional, for "export" header)
        - date: str (optional, for "export" header)
    """
    action = context.get("action", "")
    base = Path(context.get("base_path", "."))
    yaml_path = _opsp_yaml_path(base)

    if action not in ACTIONS:
        return {
            "output": "",
            "artifacts": {},
            "errors": [f"Acción desconocida: {action!r}. Válidas: {', '.join(ACTIONS)}"],
        }

    if action == "load":
        state = read_yaml(yaml_path)
        return {
            "output": "",
            "artifacts": {
                "state": state,
                "resuming": bool(state),
                "missing": missing_fields(state),
            },
            "errors": [],
        }

    if action == "save":
        section = context.get("section", "")
        state = read_yaml(yaml_path)
        try:
            state = merge_section(state, section, context.get("data"))
        except ValueError as exc:
            return {"output": "", "artifacts": {}, "errors": [str(exc)]}
        write_yaml(yaml_path, state)
        return {
            "output": f"Guardado: {section}",
            "artifacts": {"state": state, "missing": missing_fields(state)},
            "errors": [],
        }

    # action == "export"
    state = read_yaml(yaml_path)
    markdown = render_markdown(
        state,
        company_name=context.get("company_name", ""),
        date=context.get("date", ""),
    )
    md_path = _opsp_md_path(base)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(markdown, encoding="utf-8")
    return {
        "output": markdown,
        "artifacts": {
            "markdown": markdown,
            "missing": missing_fields(state),
            "export_path": str(md_path),
        },
        "errors": [],
    }


def _main() -> None:
    """Minimal module entry point for ``python -m coaching.strategy_opsp``."""
    from ..core import load_context

    result = run(load_context())
    if result.get("output"):
        print(result["output"])
    for error in result.get("errors", []):
        print(error)
