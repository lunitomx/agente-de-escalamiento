"""Quality gate validators for task board."""

from __future__ import annotations

import pathlib
import re
from datetime import date, datetime


_TASK_RE = re.compile(r"^- \[[ x]\] (.+?)(?:\s*<!--\s*(.+?)\s*-->)?$")
_META_RE = re.compile(r"(\w+):(\S+)")
_VALID_DECISIONS = {"people", "strategy", "execution", "cash"}
_SECTIONS = {"En Progreso", "Próximo", "Completado"}


def parse_tasks(board_path: pathlib.Path) -> dict[str, list[dict]]:
    """Parse tasks.md into structured data. Returns {section: [task_dict]}."""
    result: dict[str, list[dict]] = {s: [] for s in _SECTIONS}
    current_section = ""

    if not board_path.exists():
        return result

    for line in board_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section_name = line[3:].strip()
            if section_name in _SECTIONS:
                current_section = section_name

        if not current_section:
            continue

        match = _TASK_RE.match(line.strip())
        if match:
            desc = match.group(1).strip()
            meta_str = match.group(2) or ""
            meta = dict(_META_RE.findall(meta_str))
            done = line.strip().startswith("- [x]")
            result[current_section].append(
                {
                    "description": desc,
                    "done": done,
                    "decision": meta.get("decision", ""),
                    "node": meta.get("node", ""),
                    "due": meta.get("due", ""),
                    "completed": meta.get("completed", ""),
                }
            )

    return result


def validate_task_board(board_path: pathlib.Path) -> list[str]:
    """Validate task board structure. Returns list of errors (empty = valid)."""
    errors: list[str] = []

    if not board_path.exists():
        return [f"Task board not found: {board_path}"]

    text = board_path.read_text(encoding="utf-8")

    for section in _SECTIONS:
        if f"## {section}" not in text:
            errors.append(f"Missing section: ## {section}")

    tasks = parse_tasks(board_path)
    for section, items in tasks.items():
        for task in items:
            if task["decision"] and task["decision"] not in _VALID_DECISIONS:
                errors.append(
                    f"Task '{task['description'][:30]}...' has invalid decision: {task['decision']}"
                )
            if task["due"]:
                try:
                    datetime.strptime(task["due"], "%Y-%m-%d")
                except ValueError:
                    errors.append(
                        f"Task '{task['description'][:30]}...' has invalid due date: {task['due']}"
                    )

    return errors


def find_overdue(board_path: pathlib.Path) -> list[dict]:
    """Return list of overdue tasks (due date < today)."""
    tasks = parse_tasks(board_path)
    today = date.today()
    overdue = []

    for task in tasks.get("En Progreso", []):
        if task["due"]:
            try:
                due = datetime.strptime(task["due"], "%Y-%m-%d").date()
                if due < today:
                    overdue.append(task)
            except ValueError:
                pass

    return overdue
