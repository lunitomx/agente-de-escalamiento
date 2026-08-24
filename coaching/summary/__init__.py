"""Generate and append an idempotent summary to a ScaleUp session log."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .engine import build_summary
from .formatter import format_summary


_SUMMARY_RE = re.compile(r"^## Session Summary\s*$", re.MULTILINE)


def _sections(summary: dict) -> list[str]:
    sections = ["decision_focus"]
    if summary.get("worksheets_completed"):
        sections.append("worksheets")
    if summary.get("tasks_created") or summary.get("tasks_completed"):
        sections.append("tasks")
    if summary.get("notes"):
        sections.append("notes")
    return sections


def run(context: dict) -> dict:
    """Append a formatted summary to the requested session log once."""
    log_file_path = context.get("log_file_path")
    if not log_file_path:
        return {
            "output": "",
            "artifacts": {},
            "errors": ["Missing required field: log_file_path"],
        }

    log_path = Path(log_file_path)
    if not log_path.is_absolute() and context.get("base_path"):
        log_path = Path(context["base_path"]) / log_path
    if not log_path.is_file():
        return {
            "output": "",
            "artifacts": {},
            "errors": [f"File not found: {log_file_path}"],
        }

    summary = build_summary(context)
    existing = log_path.read_text(encoding="utf-8")
    already_present = bool(_SUMMARY_RE.search(existing))
    if not already_present:
        separator = "" if existing.endswith("\n") else "\n"
        log_path.write_text(
            existing + separator + "\n" + format_summary(summary),
            encoding="utf-8",
        )

    return {
        "output": (
            f"Summary already present: {log_file_path}"
            if already_present
            else f"Summary appended: {log_file_path}"
        ),
        "artifacts": {
            "log_file_path": log_file_path,
            "summary_appended": not already_present,
            "summary_present": True,
            "sections": _sections(summary),
        },
        "errors": [],
    }


def _main() -> None:
    """CLI entry point supporting stdin JSON or `--context` JSON."""
    context_json = None
    args = sys.argv[1:]
    if "--context" in args:
        index = args.index("--context")
        if index + 1 < len(args):
            context_json = args[index + 1]
        else:
            _exit_with_error("--context requires a JSON argument")
    else:
        context_json = sys.stdin.read().strip()

    if not context_json:
        _exit_with_error("No context provided (use stdin or --context)")

    try:
        context = json.loads(context_json)
    except json.JSONDecodeError as exc:
        _exit_with_error(f"Invalid JSON: {exc}")

    result = run(context)
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(1 if result["errors"] else 0)


def _exit_with_error(message: str) -> None:
    print(json.dumps({"output": "", "artifacts": {}, "errors": [message]}))
    raise SystemExit(1)
