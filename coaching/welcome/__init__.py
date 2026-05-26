"""coaching.welcome — company onboarding profile generator.

Public API:
    run(context: dict) -> dict
        Validates intake data, builds profile, writes to disk.
        Returns {"output": str, "artifacts": dict, "errors": list[str]}.

Standalone:
    python3 -m coaching.welcome --context '{"name": "Acme", "industry": "SaaS", "employees": 25}'
"""
from __future__ import annotations

import json
import pathlib
import sys

try:
    import yaml
except ImportError as e:
    raise ImportError("PyYAML required: pip install pyyaml") from e

from coaching.welcome.engine import build_profile, validate_intake
from coaching.welcome.formatter import format_profile, format_summary


def run(context: dict) -> dict:
    errors = validate_intake(context)
    if errors:
        return {"output": "", "artifacts": {}, "errors": errors}

    profile = build_profile(context)
    profile_yaml = format_profile(profile)
    summary_md = format_summary(profile)

    profile_path = context.get("profile_path", ".scaleup/my-company/profile.yaml")
    path = pathlib.Path(profile_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(profile_yaml, encoding="utf-8")

    return {
        "output": summary_md,
        "artifacts": {
            "profile_path": str(path),
            "growth_stage": profile["company"]["growth_stage"],
            "has_scores": any(v is not None for v in profile.get("scores", {}).values()),
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
