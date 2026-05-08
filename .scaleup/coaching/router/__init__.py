"""coaching.router — deterministic routing to sub-agent skills.

Public API:
    run(context: dict) -> dict

Standalone:
    python3 -m coaching.router --context '{"profile_path": ".scaleup/my-company/profile.yaml"}'
    python3 -m coaching.router --context '{"people": 3, "strategy": 2, "execution": 4, "cash": 1}'
    python3 -m coaching.router --context '{"explicit": "cash"}'
"""
from __future__ import annotations

import json
import pathlib
import sys

try:
    import yaml
except ImportError as e:
    raise ImportError("PyYAML required: pip install pyyaml") from e

from coaching.router.engine import route


def run(context: dict) -> dict:
    scores = {}

    profile_path = context.get("profile_path")
    if profile_path:
        path = pathlib.Path(profile_path)
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            scores = {k: v for k, v in data.get("scores", {}).items() if isinstance(v, int)}

    for dec in ["people", "strategy", "execution", "cash"]:
        if dec in context and isinstance(context[dec], int):
            scores[dec] = context[dec]

    routing = route(scores, context.get("explicit"))

    return {
        "output": f"Route to `/{ routing['skill']}` — {routing['label']} ({routing['reason']})",
        "artifacts": routing,
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
