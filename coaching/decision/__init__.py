"""
Decision module — clarify an open question into a concrete decision sheet.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..core import read_yaml, write_yaml
from .engine import (
    apply_correction,
    build_clarification,
    build_draft,
    needs_clarification,
    validate_draft,
)
from .formatter import format_clarification, format_confirmed, format_draft

PROFILE_REL_PATH = Path(".escala") / "agent" / "memory" / "company-profile.yaml"

VALID_ACTIONS = ["question", "confirm", "correct"]


def _profile_path(base: Path) -> Path:
    return base / PROFILE_REL_PATH


def _persist_decision(base: Path, draft: dict[str, Any]) -> str:
    """Persist a confirmed decision sheet to the company profile."""
    profile_path = _profile_path(base)
    profile = read_yaml(profile_path)

    profile["focus"] = profile.get("focus", {})
    profile["focus"]["current_decision"] = {
        "decision": draft["decision"],
        "area": draft["area"],
        "horizon": draft["horizon"],
        "outcome": draft["outcome"],
        "confirmed": str(__import__("datetime").datetime.now().date()),
    }
    write_yaml(profile_path, profile)
    return str(profile_path)


def run(context: dict) -> dict:
    """
    Execute the decision clarification flow.

    Context keys:
        - action: 'question' | 'confirm' | 'correct' (default: 'question')
        - question: str (required for action='question')
        - draft: dict (required for action='confirm' or 'correct')
        - corrections: dict (required for action='correct')
        - base_path: str (default: '.')

    Returns:
        dict with output, artifacts, errors
    """
    action = context.get("action", "question")
    base = Path(context.get("base_path", "."))

    if action not in VALID_ACTIONS:
        return {
            "output": "",
            "artifacts": {},
            "errors": [f"Invalid action: {action}. Must be one of {VALID_ACTIONS}"],
        }

    if action == "question":
        question = context.get("question", "").strip()
        if not question:
            return {
                "output": "",
                "artifacts": {},
                "errors": ["question es requerida para action='question'"],
            }

        draft = build_draft(question)
        if needs_clarification(draft):
            return {
                "output": format_clarification(build_clarification(draft)),
                "artifacts": {"action": "clarify", "draft": draft},
                "errors": [],
            }

        return {
            "output": format_draft(draft),
            "artifacts": {"action": "propose", "draft": draft},
            "errors": [],
        }

    # action == 'confirm' or 'correct'
    draft = context.get("draft", {})
    errors = validate_draft(draft)
    if errors:
        return {"output": "", "artifacts": {}, "errors": errors}

    if action == "correct":
        corrections = context.get("corrections", {})
        updated = apply_correction(draft, corrections)
        return {
            "output": format_draft(updated),
            "artifacts": {"action": "propose", "draft": updated},
            "errors": [],
        }

    # action == 'confirm'
    profile_path = _persist_decision(base, draft)
    return {
        "output": format_confirmed(draft),
        "artifacts": {
            "action": "confirmed",
            "draft": draft,
            "profile_path": profile_path,
        },
        "errors": [],
    }


def _main() -> None:
    """Minimal module entry point for ``python -m coaching.decision``."""
    import json
    import sys

    from ..core import load_context

    context = load_context()
    result = run(context)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(1 if result.get("errors") else 0)
