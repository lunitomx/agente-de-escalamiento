"""FACChart module — persist, resume, validate, and export.

Storage: `.escala/my-company/facchart.yaml`
Export: `.escala/my-company/facchart.md`
"""

from __future__ import annotations

from pathlib import Path

from ..core import read_yaml, write_yaml
from .engine import FACChart, score, validate
from .formatter import render_markdown

ACTIONS = ("load", "save", "export")


def _facchart_yaml_path(base: Path) -> Path:
    return base / ".escala" / "my-company" / "facchart.yaml"


def _facchart_md_path(base: Path) -> Path:
    return base / ".escala" / "my-company" / "facchart.md"


def run(context: dict) -> dict:
    """Execute a FACChart action.

    Context keys:
        - action: str ("load" | "save" | "export")
        - base_path: str (path to project root)
        - data: dict (required for "save" — chart data)
        - company_name: str (optional, for "export" header)
    """
    action = context.get("action", "")
    base = Path(context.get("base_path", "."))
    yaml_path = _facchart_yaml_path(base)

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
        chart = FACChart.from_dict(raw)
        return {
            "output": "",
            "artifacts": {
                "state": chart.to_dict(),
                "resuming": bool(chart.functions),
                "errors": validate(chart),
                "score": score(chart),
            },
            "errors": [],
        }

    if action == "save":
        raw = context.get("data", {})
        chart = FACChart.from_dict(raw)
        errors = validate(chart)
        # Save even if there are validation errors so the user can iterate.
        write_yaml(yaml_path, chart.to_dict())
        return {
            "output": f"Guardado: {len(chart.functions)} funciones",
            "artifacts": {
                "state": chart.to_dict(),
                "errors": errors,
                "score": score(chart),
            },
            "errors": [],
        }

    # action == "export"
    raw = read_yaml(yaml_path)
    chart = FACChart.from_dict(raw)
    markdown = render_markdown(
        chart,
        company_name=context.get("company_name", ""),
    )
    md_path = _facchart_md_path(base)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(markdown, encoding="utf-8")
    return {
        "output": markdown,
        "artifacts": {
            "markdown": markdown,
            "errors": validate(chart),
            "score": score(chart),
            "export_path": str(md_path),
        },
        "errors": [],
    }


def _main() -> None:
    """Minimal module entry point for ``python -m coaching.people_facchart``."""
    from ..core import load_context

    result = run(load_context())
    if result.get("output"):
        print(result["output"])
    for error in result.get("errors", []):
        print(error)
