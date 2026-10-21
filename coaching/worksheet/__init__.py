"""
Worksheet module — load from ontology, guide step by step, validate, save.
"""

import sys
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..core import read_yaml, write_yaml, ensure_dir
from .guide import GuideStep, Tip, parse_guide, source_label
from .view import build_view, open_command, save_view


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_KNOWLEDGE = PACKAGE_ROOT / "conocimiento"
CLIENT_KNOWLEDGE = Path(".escala") / "knowledge"
REGISTRY_FILE = Path("registry") / "worksheets.yaml"
COMPLETED_DIR = Path(".escala/my-company/worksheets")


def knowledge_root(base_path: Path | None = None) -> Path:
    """Return the one knowledge root for registry and sheet content.

    The client's own ``.escala/knowledge`` wins only when its registry FILE
    exists; otherwise the package's ``conocimiento/`` is used.
    """
    base = base_path if base_path is not None else PACKAGE_ROOT
    client = base / CLIENT_KNOWLEDGE
    return client if (client / REGISTRY_FILE).is_file() else PACKAGE_KNOWLEDGE


def registry_path(base_path: Path | None = None) -> Path:
    """Return the worksheet registry file under :func:`knowledge_root`."""
    return knowledge_root(base_path) / REGISTRY_FILE


def list_worksheets(
    decision: str | None = None,
    base_path: Path | None = None,
) -> list[dict[str, Any]]:
    """List all worksheets, optionally filtered by decision."""
    registry = read_yaml(registry_path(base_path))
    worksheets = registry.get("worksheets", [])
    if decision:
        return [w for w in worksheets if w.get("decision") == decision]
    return worksheets


def find_worksheet(
    name_or_id: str,
    base_path: Path | None = None,
) -> dict[str, Any] | None:
    """Find a worksheet by name or ID (case-insensitive)."""
    registry = read_yaml(registry_path(base_path))
    name_lower = name_or_id.lower()
    for w in registry.get("worksheets", []):
        if w["id"].lower() == name_lower:
            return w
        if name_lower in w["name"].lower():
            return w
    return None


def get_completed_ids(base_path: Path | None = None) -> list[str]:
    """Get IDs of worksheets saved with ``status: completed``.

    An in-progress state file is not completed; counting it blocked ``resume``.
    """
    wdir = (
        (base_path / ".escala" / "my-company" / "worksheets")
        if base_path
        else COMPLETED_DIR
    )
    if not wdir.exists():
        return []
    completed: list[str] = []
    for f in sorted(wdir.glob("*.yaml")):
        data = read_yaml(f)
        sheet_id = str(data.get("worksheet_id") or f.stem)
        if data.get("status") == "completed" and sheet_id not in completed:
            completed.append(sheet_id)
    return completed


def load_worksheet_content(
    worksheet: dict[str, Any],
    base_path: Path | None = None,
) -> dict[str, Any]:
    """Load full worksheet content from its ontology node_path."""
    node_path = worksheet.get("node_path", "")
    if not node_path:
        return worksheet
    full_path = knowledge_root(base_path) / node_path
    content = read_yaml(full_path)
    return {**worksheet, **content}


class _GuideError(Exception):
    """The sheet carries a guide that breaks the ToolGuide contract."""


def _steps_and_tips(
    worksheet: dict[str, Any], content: dict[str, Any]
) -> tuple[list[GuideStep], list[Tip]]:
    """Guided steps and tips, or one plain step per legacy ``metadata.fields`` text."""
    try:
        guide = parse_guide(content)
    except ValidationError as exc:
        message = "; ".join(str(err["msg"]) for err in exc.errors())
        raise _GuideError(
            f"La hoja {worksheet['id']} no cumple el contrato: {message}"
        ) from exc
    if guide is not None:
        return list(guide.guide.steps), list(guide.tips)
    fields = content.get("metadata", {}).get("fields", [])
    steps = [
        GuideStep.model_construct(id=str(f), question=str(f), how="", example="")
        for f in fields
    ]
    return steps, []


def _step_lines(
    steps: list[GuideStep], tips: list[Tip], index: int, plain_hint: str
) -> list[str]:
    """Markdown for step ``index`` (0-based), shown as ``Paso index+2``."""
    step = steps[index]
    lines = [f"### Paso {index + 2}: {step.question}", ""]
    if not step.how:
        return [*lines, plain_hint]
    lines += [f"**Cómo llenarlo:** {step.how}", f"**Ejemplo:** {step.example}"]
    shown = [t for t in tips if t.step == step.id or (t.step is None and index == 0)]
    if shown:
        lines += ["**Tips:**"]
        lines += [f"- {t.text} (fuente: {source_label(t.source)})" for t in shown]
    return lines


def _review_lines(steps: list[GuideStep], answers: dict[str, Any]) -> list[str]:
    """Final review: each question with its answer, then ask to confirm.

    Nothing is completed here; only ``save`` marks the sheet and writes the view.
    """
    lines = [
        "### Revisión Final",
        "",
        "Revisa tus respuestas antes de guardar:",
        "",
    ]
    for step in steps:
        answer = answers.get(step.id)
        shown = str(answer).strip() if answer not in (None, "", []) else ""
        lines.append(f"- **{step.question}:** {shown or '(sin respuesta)'}")
    lines += [
        "",
        "Responde 'confirmar' para guardar la hoja y abrir tu vista.",
    ]
    return lines


def _contract_error(message: str) -> dict[str, Any]:
    return {"output": "", "artifacts": {}, "errors": [message]}


def run(context: dict[str, Any]) -> dict[str, Any]:
    """
    Execute worksheet guidance.

    Context keys:
        - action: 'list' | 'start' | 'step' | 'save' | 'resume'
        - worksheet_name: str (for start/resume)
        - decision: str (for list)
        - step_id: str (for step)
        - fields: dict of {field_name: value} (for step/save)
        - base_path: str (project root)

    Returns:
        dict with output, artifacts, errors
    """
    base = Path(context.get("base_path", "."))
    action = context.get("action", "list")

    if action == "list":
        decision = context.get("decision")
        if decision is not None and not isinstance(decision, str):
            decision = str(decision)
        all_ws = list_worksheets(decision, base)
        completed = get_completed_ids(base)

        lines = [
            "## Worksheets Disponibles",
            "",
            "| Worksheet | Decisión | Dificultad | Tiempo | Estado |",
            "|-----------|----------|-----------|--------|--------|",
        ]
        for w in all_ws:
            status = "✅" if w["id"] in completed else "⬜"
            lines.append(
                f"| {w['name']} (`{w['id']}`) | "
                f"{w.get('decision', '—')} | "
                f"{w.get('difficulty', '—')} | "
                f"{w.get('time_estimate', '—')} | {status} |"
            )
        lines.extend(
            [
                "",
                "Para empezar: `/escala-worksheet [nombre]`",
                "Para reanudar: mismo comando si ya empezaste",
            ]
        )

        return {
            "output": "\n".join(lines),
            "artifacts": {"worksheets": all_ws, "completed": completed},
            "errors": [],
        }

    elif action in ("start", "resume"):
        ws_name = str(context.get("worksheet_name", ""))
        worksheet = find_worksheet(ws_name, base)
        if not worksheet:
            available = [
                w["name"] for w in list_worksheets(decision=None, base_path=base)
            ]
            return {
                "output": "",
                "artifacts": {},
                "errors": [
                    f"Worksheet '{ws_name}' no encontrado. Disponibles: {', '.join(available[:5])}..."
                ],
            }

        completed = get_completed_ids(base)
        if worksheet["id"] in completed:
            return {
                "output": f"Worksheet **{worksheet['name']}** ya está completado. Usa `/escala-worksheet list` para ver otros.",
                "artifacts": {"worksheet": worksheet, "status": "completed"},
                "errors": [],
            }

        state_path = (
            base / ".escala" / "my-company" / "worksheets" / f"{worksheet['id']}.yaml"
        )
        state = read_yaml(state_path)
        if state and action == "resume":
            current_step = state.get("current_step", 0)
            saved_fields = state.get("fields", {})
        else:
            current_step = 0
            saved_fields = {}

        content = load_worksheet_content(worksheet, base)
        try:
            steps, tips = _steps_and_tips(worksheet, content)
        except _GuideError as exc:
            return _contract_error(str(exc))
        total_steps = len(steps) + 2  # information + steps + final review

        lines = [
            f"## {worksheet['name']}",
            "",
            f"**Decisión:** {worksheet.get('decision', '—')}",
            f"**Dificultad:** {worksheet.get('difficulty', '—')}",
            f"**Tiempo estimado:** {worksheet.get('time_estimate', '—')}",
            "",
            f"{content.get('summary', '')}",
            "",
        ]

        if current_step == 0:
            lines.extend(
                [
                    "### Paso 1: Información General",
                    "",
                    "Antes de empezar, confirma que tienes:",
                ]
            )
            if worksheet.get("prerequisites"):
                lines.append(
                    "- [ ] Prerrequisitos completados: "
                    + ", ".join(worksheet["prerequisites"])
                )
            lines.extend(
                [
                    "- [ ] Datos actualizados de tu empresa",
                    "- [ ] 1-2 horas sin interrupciones",
                    "",
                    "Responde con 'listo' para empezar.",
                ]
            )
        else:
            step_idx = current_step - 1
            if step_idx < len(steps):
                lines.extend(
                    _step_lines(
                        steps,
                        tips,
                        step_idx,
                        "Completa este campo. Responde con tu información.",
                    )
                )
            else:
                lines.extend(_review_lines(steps, saved_fields))

        write_yaml(
            state_path,
            {
                "worksheet_id": worksheet["id"],
                "worksheet_name": worksheet["name"],
                "decision": worksheet.get("decision"),
                "current_step": current_step,
                "total_steps": total_steps,
                "fields": saved_fields,
                "status": "in_progress",
            },
        )

        return {
            "output": "\n".join(lines),
            "artifacts": {
                "worksheet": worksheet,
                "current_step": current_step,
                "total_steps": total_steps,
                "state_path": str(state_path),
            },
            "errors": [],
        }

    elif action == "step":
        ws_name = str(context.get("worksheet_name", ""))
        worksheet = find_worksheet(ws_name, base)
        if not worksheet:
            return {
                "output": "",
                "artifacts": {},
                "errors": [f"Worksheet '{ws_name}' no encontrado"],
            }

        state_path = (
            base / ".escala" / "my-company" / "worksheets" / f"{worksheet['id']}.yaml"
        )
        state = read_yaml(state_path)
        if not state:
            return {
                "output": "",
                "artifacts": {},
                "errors": [
                    f"Worksheet '{ws_name}' no iniciado. Usa /escala-worksheet {ws_name} primero"
                ],
            }

        current_step = state.get("current_step", 0)
        saved_fields = state.get("fields", {})

        step_fields = context.get("fields", {})
        saved_fields.update(step_fields)
        current_step += 1

        content = load_worksheet_content(worksheet, base)
        try:
            steps, tips = _steps_and_tips(worksheet, content)
        except _GuideError as exc:
            return _contract_error(str(exc))

        review_step = len(steps) + 1
        current_step = min(current_step, review_step)
        write_yaml(
            state_path,
            {
                **state,
                "current_step": current_step,
                "total_steps": len(steps) + 2,
                "fields": saved_fields,
                "status": "in_progress",
            },
        )

        if current_step < review_step:
            lines = _step_lines(
                steps,
                tips,
                current_step - 1,
                "Completa este campo con tu información.",
            )
        else:
            lines = _review_lines(steps, saved_fields)

        return {
            "output": "\n".join(lines),
            "artifacts": {
                "worksheet": worksheet,
                "current_step": current_step,
                "total_steps": len(steps) + 2,
                "state_path": str(state_path),
            },
            "errors": [],
        }

    elif action == "save":
        ws_name = context.get("worksheet_name", "")
        worksheet = find_worksheet(ws_name, base)
        if not worksheet:
            return {
                "output": "",
                "artifacts": {},
                "errors": [f"Worksheet '{ws_name}' no encontrado"],
            }

        state_path = (
            base / ".escala" / "my-company" / "worksheets" / f"{worksheet['id']}.yaml"
        )
        content = load_worksheet_content(worksheet, base)
        try:
            _steps_and_tips(worksheet, content)
        except _GuideError as exc:
            return _contract_error(str(exc))

        state = read_yaml(state_path)
        fields = state.get("fields", {})

        completed_data = {
            "worksheet_id": worksheet["id"],
            "worksheet_name": worksheet["name"],
            "decision": worksheet.get("decision"),
            "fields": fields,
            "completed": str(__import__("datetime").datetime.now().date()),
            "status": "completed",
        }
        ensure_dir(state_path.parent)

        # Back up a previously completed worksheet before overwriting it.
        backup_path: Path | None = None
        if state_path.exists():
            existing = read_yaml(state_path)
            if existing and existing.get("status") == "completed":
                timestamp = (
                    __import__("datetime").datetime.now().strftime("%Y%m%d-%H%M%S")
                )
                backup_path = (
                    state_path.parent
                    / f"{state_path.stem}-{timestamp}{state_path.suffix}"
                )
                state_path.rename(backup_path)

        write_yaml(state_path, completed_data)

        view = build_view(content, fields, made_on=date.today())
        html_path, md_path = save_view(base, view)

        return {
            "output": (
                f"✅ **{worksheet['name']}** guardado como completado.\n"
                f"Vista lista: {html_path}"
            ),
            "artifacts": {
                "worksheet": worksheet,
                "completed_data": completed_data,
                "state_path": str(state_path),
                "backup_path": str(backup_path) if backup_path else None,
                "view": {
                    "html": str(html_path),
                    "md": str(md_path),
                    "open_cmd": open_command(html_path, sys.platform),
                },
            },
            "errors": [],
        }

    return {"output": "", "artifacts": {}, "errors": [f"Unknown action: {action}"]}


def _main() -> None:
    """Minimal module entry point for ``python -m coaching.worksheet``."""
    result = run({})
    if result.get("output"):
        print(result["output"])
    for error in result.get("errors", []):
        print(error)
