"""
Evidence module — build a privacy-safe evidence package for a confirmed decision.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..core import read_yaml
from .engine import discover_sources
from .formatter import format_package, package_summary
from .models import DecisionRef

PROFILE_REL_PATH = Path(".escala") / "agent" / "memory" / "company-profile.yaml"
SESSIONS_REL_PATH = Path(".escala") / "my-company" / "sessions"
TASKS_REL_PATH = Path(".escala") / "my-company" / "tasks.md"
WORKSHEETS_REL_PATH = Path(".escala") / "my-company" / "worksheets"
METRICS_REL_PATH = Path(".escala") / "my-company" / "context" / "metrics.yaml"
REGISTRY_REL_PATH = Path(".escala") / "knowledge" / "registry" / "worksheets.yaml"

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.+?)\n---", re.DOTALL)


def _profile_path(base: Path) -> Path:
    return base / PROFILE_REL_PATH


def _load_decision(base: Path) -> DecisionRef | None:
    """Load the confirmed decision from the company profile."""
    profile = read_yaml(_profile_path(base))
    focus = profile.get("focus") or {}
    current = focus.get("current_decision")
    if not isinstance(current, dict) or not current.get("decision"):
        return None
    try:
        return DecisionRef(
            decision=current["decision"],
            area=current["area"],
            horizon=current["horizon"],
            outcome=current["outcome"],
        )
    except Exception:
        return None


def _parse_session(path: Path) -> dict[str, Any] | None:
    """Parse a session log markdown file with YAML frontmatter."""
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None
    try:
        import yaml

        frontmatter: dict[str, Any] = yaml.safe_load(match.group(1))
    except Exception:
        return None
    if not isinstance(frontmatter, dict):
        return None
    return {
        "id": f"session-{frontmatter.get('date', path.stem)}",
        "date": str(frontmatter.get("date", "")),
        "decision_focus": frontmatter.get("decision_focus", ""),
        "worksheets_completed": frontmatter.get("worksheets_completed", []),
        "locator": f".escala/my-company/sessions/{path.name}",
    }


def _load_sessions(base: Path) -> list[dict[str, Any]]:
    """Load all session logs from the local memory path."""
    sessions_dir = base / SESSIONS_REL_PATH
    if not sessions_dir.exists():
        return []
    sessions: list[dict[str, Any]] = []
    for path in sorted(sessions_dir.glob("*.md")):
        session = _parse_session(path)
        if session:
            sessions.append(session)
    return sessions


def _load_tasks(base: Path) -> list[dict[str, Any]]:
    """Load tasks from the local task board."""
    from validators.tasks import parse_tasks

    tasks_path = base / TASKS_REL_PATH
    if not tasks_path.exists():
        return []
    parsed = parse_tasks(tasks_path)
    tasks: list[dict[str, Any]] = []
    for section, items in parsed.items():
        for idx, task in enumerate(items):
            tasks.append(
                {
                    "id": f"task-{section}-{idx}",
                    "title": task.get("description", "Tarea vinculada"),
                    "decision": task.get("decision", ""),
                    "completed": task.get("done", False),
                    "date": task.get("completed", ""),
                    "locator": ".escala/my-company/tasks.md",
                }
            )
    return tasks


def _load_worksheets(base: Path) -> list[dict[str, Any]]:
    """Load completed worksheets from the local memory path."""
    worksheets_dir = base / WORKSHEETS_REL_PATH
    if not worksheets_dir.exists():
        return []
    worksheets: list[dict[str, Any]] = []
    for path in sorted(worksheets_dir.glob("*.yaml")):
        data = read_yaml(path)
        if not isinstance(data, dict):
            continue
        worksheets.append(
            {
                "id": data.get("worksheet_id", path.stem),
                "name": data.get("worksheet_name", path.stem),
                "decision": data.get("decision", ""),
                "completed": data.get("status") == "completed",
                "date": str(data.get("completed", "")),
                "locator": f".escala/my-company/worksheets/{path.name}",
            }
        )
    return worksheets


def _load_metrics(base: Path) -> list[dict[str, Any]]:
    """Load metrics from the local context file."""
    metrics_path = base / METRICS_REL_PATH
    data = read_yaml(metrics_path)
    if not isinstance(data, dict):
        return []
    metrics: list[dict[str, Any]] = []
    for idx, (key, value) in enumerate(data.get("metrics", {}).items()):
        metric = value if isinstance(value, dict) else {"value": value}
        metrics.append(
            {
                "id": f"metric-{idx}-{key}",
                "name": metric.get("name", key),
                "decision": metric.get("decision", ""),
                "value": str(metric.get("value", "")),
                "date": str(metric.get("date", "")),
                "locator": ".escala/my-company/context/metrics.yaml",
            }
        )
    return metrics


def _load_registry(base: Path) -> dict[str, Any]:
    """Load the worksheet registry."""
    registry_path = base / REGISTRY_REL_PATH
    return read_yaml(registry_path)


def _load_local_sources(base: Path) -> dict[str, Any]:
    """Load all local sources for evidence discovery."""
    return {
        "sessions": _load_sessions(base),
        "tasks": _load_tasks(base),
        "worksheets": _load_worksheets(base),
        "metrics": _load_metrics(base),
        "registry": _load_registry(base),
    }


def run(context: dict[str, Any]) -> dict[str, Any]:
    """
    Build an evidence package for the current confirmed decision.

    Context keys:
        - base_path: str (default: '.')
        - freshness_days: int (default: 90)

    Returns:
        dict with output, artifacts, errors
    """
    base = Path(context.get("base_path", "."))
    freshness_days = context.get("freshness_days", 90)

    decision = _load_decision(base)
    if decision is None:
        return {
            "output": "",
            "artifacts": {},
            "errors": [
                "No hay una decisión confirmada. "
                "Ejecuta /escala-decision primero para aclarar la decisión."
            ],
        }

    local_sources = _load_local_sources(base)
    package = discover_sources(decision, local_sources, freshness_days=freshness_days)

    return {
        "output": format_package(package),
        "artifacts": {
            "action": "evidence_package",
            "decision_ref": package.decision_ref.model_dump(),
            "package": package.model_dump(),
            "summary": package_summary(package),
        },
        "errors": [],
    }


def _main() -> None:
    """Minimal module entry point for ``python -m coaching.evidence``."""
    import json
    import sys

    from ..core import load_context

    context = load_context()
    result = run(context)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(1 if result.get("errors") else 0)
