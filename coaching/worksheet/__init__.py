"""coaching.worksheet — worksheet loading, guidance, and completion.

Public API:
    run(context: dict) -> dict
        Lists worksheets, loads a specific one, or saves completed data.
        Returns {"output": str, "artifacts": dict, "errors": list[str]}.

Standalone:
    python3 -m coaching.worksheet --context '{"action": "list", "decision": "people"}'
    python3 -m coaching.worksheet --context '{"action": "load", "worksheet_id": "worksheet-face"}'
"""
from __future__ import annotations

import datetime
import json
import pathlib
import sys

try:
    import yaml
except ImportError as e:
    raise ImportError("PyYAML required: pip install pyyaml") from e

from coaching.worksheet.engine import (
    build_worksheet_session,
    check_prerequisites,
    find_worksheet,
    list_worksheets,
)
from coaching.worksheet.formatter import (
    format_completed,
    format_worksheet_guide,
    format_worksheet_list,
)

_DEFAULT_REGISTRY = pathlib.Path(__file__).parent.parent.parent / "knowledge" / "registry" / "worksheets.yaml"
_DEFAULT_KNOWLEDGE = pathlib.Path(__file__).parent.parent.parent / "knowledge"


def _load_registry(registry_path: str | None = None) -> list[dict]:
    path = pathlib.Path(registry_path) if registry_path else _DEFAULT_REGISTRY
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data.get("worksheets", []) if isinstance(data, dict) else []


def _load_worksheet_content(knowledge_dir: str | None, node_path: str) -> dict:
    base = pathlib.Path(knowledge_dir) if knowledge_dir else _DEFAULT_KNOWLEDGE
    path = base / node_path
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _resolve_worksheets_dir(context: dict) -> pathlib.Path:
    """Resolve the directory holding worksheet state.

    Companies are isolated by directory: callers pass ``base_path`` (the
    company's project root). An explicit ``worksheets_dir`` overrides everything.
    We must NOT fall back to a bare relative ``.scaleup/my-company`` that ignores
    ``base_path`` — doing so makes every company write to the same CWD folder and
    silently clobber each other's worksheets.
    """
    explicit = context.get("worksheets_dir")
    if explicit:
        return pathlib.Path(explicit)
    base = pathlib.Path(context.get("base_path", "."))
    return base / ".scaleup" / "my-company" / "worksheets"


def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%dT%H%M%S%f")


def _get_completed_ids(worksheets_dir: str | pathlib.Path | None) -> set[str]:
    if not worksheets_dir:
        return set()
    path = pathlib.Path(worksheets_dir)
    if not path.exists():
        return set()
    completed = set()
    for f in path.glob("*.yaml"):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("status") == "completed":
            completed.add(data.get("worksheet_id", f.stem))
    return completed


def run(context: dict) -> dict:
    action = context.get("action", "list")
    registry = _load_registry(context.get("registry_path"))

    if not registry:
        return {"output": "", "artifacts": {}, "errors": ["Worksheet registry not found or empty"]}

    if action == "list":
        decision = context.get("decision")
        worksheets = list_worksheets(registry, decision)
        output = format_worksheet_list(worksheets, decision)
        return {
            "output": output,
            "artifacts": {"count": len(worksheets), "decision": decision},
            "errors": [],
        }

    elif action == "load":
        worksheet_id = context.get("worksheet_id")
        if not worksheet_id:
            return {"output": "", "artifacts": {}, "errors": ["worksheet_id required for load action"]}

        meta = find_worksheet(registry, worksheet_id)
        if not meta:
            return {"output": "", "artifacts": {}, "errors": [f"Worksheet not found: {worksheet_id}"]}

        completed = _get_completed_ids(_resolve_worksheets_dir(context))
        missing = check_prerequisites(registry, worksheet_id, completed)

        content = _load_worksheet_content(context.get("knowledge_dir"), meta.get("node_path", ""))
        session = build_worksheet_session(meta, content)
        output = format_worksheet_guide(session)

        if missing:
            prereq_note = f"\n**Prerequisites not met:** {', '.join(missing)}\n"
            output = prereq_note + output

        return {
            "output": output,
            "artifacts": {
                "worksheet_id": worksheet_id,
                "decision": meta.get("decision", ""),
                "prerequisites_met": len(missing) == 0,
                "missing_prerequisites": missing,
            },
            "errors": [],
        }

    elif action == "save":
        worksheet_data = context.get("data", {})
        path = _resolve_worksheets_dir(context)
        path.mkdir(parents=True, exist_ok=True)

        wid = worksheet_data.get("worksheet_id", "unknown")
        file_path = path / f"{wid}.yaml"
        new_content = yaml.dump(
            worksheet_data, default_flow_style=False, allow_unicode=True, sort_keys=False
        )

        backup_path = None
        if file_path.exists():
            existing = file_path.read_text(encoding="utf-8")
            if existing != new_content and not context.get("overwrite"):
                # Never lose data silently: snapshot the prior version before
                # overwriting, so a re-save or a different company can't clobber it.
                backup_path = file_path.with_name(f"{wid}.{_timestamp()}.bak.yaml")
                backup_path.write_text(existing, encoding="utf-8")

        file_path.write_text(new_content, encoding="utf-8")
        output = format_completed(worksheet_data)
        artifacts = {"saved_path": str(file_path), "worksheet_id": wid}
        if backup_path is not None:
            artifacts["backup_path"] = str(backup_path)
        return {
            "output": output,
            "artifacts": artifacts,
            "errors": [],
        }

    return {"output": "", "artifacts": {}, "errors": [f"Unknown action: {action}"]}


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
