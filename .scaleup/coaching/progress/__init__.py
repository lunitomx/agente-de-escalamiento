"""coaching.progress — progress dashboard and next action suggestion.

Public API:
    run(context: dict) -> dict

Standalone:
    python3 -m coaching.progress --context '{"profile_path": "...", "worksheets_dir": "..."}'
"""
from __future__ import annotations

import json
import pathlib
import sys

try:
    import yaml
except ImportError as e:
    raise ImportError("PyYAML required: pip install pyyaml") from e

from coaching.progress.engine import calculate_progress, suggest_next_action
from coaching.progress.formatter import format_progress

_DEFAULT_REGISTRY = pathlib.Path(__file__).parent.parent.parent / "knowledge" / "registry" / "worksheets.yaml"


def run(context: dict) -> dict:
    profile_path = context.get("profile_path")
    scores = {}

    if profile_path:
        path = pathlib.Path(profile_path)
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            scores = data.get("scores", {})

    scores = {k: v for k, v in scores.items() if isinstance(v, int)}

    registry_path = context.get("registry_path") or str(_DEFAULT_REGISTRY)
    rpath = pathlib.Path(registry_path)
    registry = []
    if rpath.exists():
        reg_data = yaml.safe_load(rpath.read_text(encoding="utf-8"))
        registry = reg_data.get("worksheets", []) if isinstance(reg_data, dict) else []

    worksheets_dir = context.get("worksheets_dir", ".scaleup/my-company/worksheets")
    completed_ids: set[str] = set()
    wdir = pathlib.Path(worksheets_dir)
    if wdir.exists():
        for f in wdir.glob("*.yaml"):
            d = yaml.safe_load(f.read_text(encoding="utf-8"))
            if isinstance(d, dict) and d.get("status") == "completed":
                completed_ids.add(d.get("worksheet_id", f.stem))

    progress = calculate_progress(scores, list(completed_ids), len(registry))
    suggestion = suggest_next_action(scores, completed_ids, registry)
    output = format_progress(progress, suggestion)

    return {
        "output": output,
        "artifacts": {
            "average_score": progress["average_score"],
            "completion_pct": progress["completion_pct"],
            "focus": progress["focus"],
            "next_action": suggestion.get("action") if suggestion else None,
        },
        "errors": [],
    }


def _main() -> None:
    context_json: str | None = None
    args = sys.argv[1:]
    if "--context" in args:
        idx = args.index("--context")
        if idx + 1 < len(args):
            context_json = args[idx + 1]
        else:
            print(json.dumps({"output": "", "artifacts": {}, "errors": ["--context requires a JSON argument"]}))
            sys.exit(1)
    else:
        context_json = sys.stdin.read().strip()

    if not context_json:
        print(json.dumps({"output": "", "artifacts": {}, "errors": ["No context provided"]}))
        sys.exit(1)

    try:
        context = json.loads(context_json)
    except json.JSONDecodeError as exc:
        print(json.dumps({"output": "", "artifacts": {}, "errors": [f"Invalid JSON: {exc}"]}))
        sys.exit(1)

    result = run(context)
    print(json.dumps(result))
    sys.exit(1 if result["errors"] else 0)
