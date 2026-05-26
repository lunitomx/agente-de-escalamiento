"""coaching.diagnose — company diagnosis across 4 decisions.

Public API:
    run(context: dict) -> dict
        Scores the 4 decisions, determines focus, updates profile.
        Returns {"output": str, "artifacts": dict, "errors": list[str]}.

Standalone:
    python3 -m coaching.diagnose --context '{"people": 3, "strategy": 2, "execution": 4, "cash": 1, "date": "2026-05-07"}'
"""
from __future__ import annotations

import json
import pathlib
import sys

try:
    import yaml
except ImportError as e:
    raise ImportError("PyYAML required: pip install pyyaml") from e

from coaching.diagnose.engine import build_diagnosis, validate_scores
from coaching.diagnose.formatter import format_diagnosis


def run(context: dict) -> dict:
    scores_input = {
        k: context[k] for k in ["people", "strategy", "execution", "cash"]
        if k in context
    }

    errors = validate_scores(scores_input)
    if errors:
        return {"output": "", "artifacts": {}, "errors": errors}

    diagnosis = build_diagnosis({**scores_input, "date": context.get("date", "")})
    output = format_diagnosis(diagnosis)

    profile_path = context.get("profile_path")
    if profile_path:
        path = pathlib.Path(profile_path)
        if path.exists():
            profile = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            profile["scores"] = diagnosis["scores"]
            profile["focus"] = diagnosis["focus"]
            path.write_text(
                yaml.dump(profile, default_flow_style=False, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

    return {
        "output": output,
        "artifacts": {
            "scores": diagnosis["scores"],
            "focus": diagnosis["focus"]["decision"],
            "average": diagnosis["summary"]["average"],
            "profile_updated": bool(profile_path),
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
