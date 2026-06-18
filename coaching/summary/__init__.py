"""coaching.summary — session summary generator.

Public API:
    run(context: dict) -> dict
        Builds and appends a Session Summary section to the session log file.
        Returns {"output": str, "artifacts": dict, "errors": list[str]}.

Standalone (stdin JSON or --context arg):
    python3 -m coaching.summary                         # reads JSON from stdin
    python3 -m coaching.summary --context '{"...": ...}'  # reads JSON from arg
"""

from __future__ import annotations

import json
import pathlib
import sys

from coaching.summary.engine import build_summary
from coaching.summary.formatter import format_summary


def run(context: dict) -> dict:
    """Build a session summary and append it to the session log file.

    Args:
        context: Dict with session data and operational metadata:
            - log_file_path (str | None): path to the session log file
            - date (str): YYYY-MM-DD
            - duration_minutes (int): session length in minutes
            - decision_focus (str): one of people/strategy/execution/cash
            - worksheets_completed (list[str]): worksheets covered
            - tasks_created (list[str]): new tasks created
            - tasks_completed (list[str]): tasks completed
            - notes (list[str]): key points from the session
            - scores_before (dict | None): optional score snapshot

    Returns:
        {"output": str, "artifacts": dict, "errors": list[str]}
    """
    errors: list[str] = []

    log_file_path = context.get("log_file_path")
    if not log_file_path:
        errors.append("Missing required field: log_file_path")
        return {"output": "", "artifacts": {}, "errors": errors}

    log_path = pathlib.Path(log_file_path)
    if not log_path.exists():
        errors.append(f"File not found: {log_file_path}")
        return {"output": "", "artifacts": {}, "errors": errors}

    # Build and format summary
    summary = build_summary(context)
    summary_text = format_summary(summary)

    # Append to session log
    existing = log_path.read_text(encoding="utf-8")
    separator = "\n" if existing.endswith("\n") else "\n\n"
    log_path.write_text(existing + separator + summary_text, encoding="utf-8")

    # Determine which sections were included
    sections_included = ["decision_focus"]
    if summary.get("worksheets_completed"):
        sections_included.append("worksheets")
    if summary.get("tasks_created") or summary.get("tasks_completed"):
        sections_included.append("tasks")
    if summary.get("notes"):
        sections_included.append("notes")

    return {
        "output": f"Summary appended: {log_file_path}",
        "artifacts": {
            "log_file_path": log_file_path,
            "summary_appended": True,
            "sections": sections_included,
        },
        "errors": [],
    }


def _main() -> None:
    """Entry point for `python3 -m coaching.summary`."""
    # Support both --context arg and stdin
    context_json: str | None = None

    args = sys.argv[1:]
    if "--context" in args:
        idx = args.index("--context")
        if idx + 1 < len(args):
            context_json = args[idx + 1]
        else:
            print(
                json.dumps(
                    {
                        "output": "",
                        "artifacts": {},
                        "errors": ["--context requires a JSON argument"],
                    }
                )
            )
            sys.exit(1)
    else:
        context_json = sys.stdin.read().strip()

    if not context_json:
        print(
            json.dumps(
                {
                    "output": "",
                    "artifacts": {},
                    "errors": ["No context provided (use stdin or --context)"],
                }
            )
        )
        sys.exit(1)

    try:
        context = json.loads(context_json)
    except json.JSONDecodeError as exc:
        print(
            json.dumps(
                {"output": "", "artifacts": {}, "errors": [f"Invalid JSON: {exc}"]}
            )
        )
        sys.exit(1)

    result = run(context)

    print(json.dumps(result))

    if result["errors"]:
        sys.exit(1)
    else:
        sys.exit(0)
