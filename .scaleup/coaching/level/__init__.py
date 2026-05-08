"""coaching.level — coaching level detection and adaptation (Shu/Ha/Ri).

Public API:
    run(context: dict) -> dict

Standalone:
    python3 -m coaching.level --context '{"average_score": 3.0, "worksheets_completed": 5, "sessions_count": 8}'
    python3 -m coaching.level --context '{"override": "ri"}'
"""
from __future__ import annotations

import json
import pathlib
import sys

try:
    import yaml
except ImportError as e:
    raise ImportError("PyYAML required: pip install pyyaml") from e

from coaching.level.engine import build_level_assessment
from coaching.level.formatter import format_level


def run(context: dict) -> dict:
    profile_path = context.get("profile_path")
    avg_score = context.get("average_score", 0)
    ws_completed = context.get("worksheets_completed", 0)
    sessions = context.get("sessions_count", 0)
    override = context.get("override")

    if profile_path:
        path = pathlib.Path(profile_path)
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            scores = data.get("scores", {})
            valid = [v for v in scores.values() if isinstance(v, int)]
            if valid and not avg_score:
                avg_score = sum(valid) / len(valid)

    assessment = build_level_assessment({
        "average_score": avg_score,
        "worksheets_completed": ws_completed,
        "sessions_count": sessions,
        "override": override,
    })
    output = format_level(assessment)

    if override and profile_path:
        path = pathlib.Path(profile_path)
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            data["coaching_level"] = override
            path.write_text(
                yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

    return {
        "output": output,
        "artifacts": {
            "level": assessment["level"],
            "label": assessment["label"],
            "override": override,
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
