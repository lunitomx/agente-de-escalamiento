"""
Worksheet module — load from ontology, guide step by step, validate, save.
"""
from pathlib import Path
from ..core import read_yaml, write_yaml, ensure_dir


REGISTRY_PATH = Path(__file__).parent.parent.parent / ".scaleup" / "knowledge" / "registry" / "worksheets.yaml"
COMPLETED_DIR = Path(".scaleup/my-company/worksheets")


def list_worksheets(decision: str = None, base_path: Path = None) -> list[dict]:
    """List all worksheets, optionally filtered by decision."""
    registry_path = (base_path / ".scaleup" / "knowledge" / "registry" / "worksheets.yaml") if base_path else REGISTRY_PATH
    registry = read_yaml(registry_path)
    worksheets = registry.get("worksheets", [])
    if decision:
        return [w for w in worksheets if w.get("decision") == decision]
    return worksheets


def find_worksheet(name_or_id: str, base_path: Path = None) -> dict | None:
    """Find a worksheet by name or ID (case-insensitive)."""
    registry_path = (base_path / ".scaleup" / "knowledge" / "registry" / "worksheets.yaml") if base_path else REGISTRY_PATH
    registry = read_yaml(registry_path)
    name_lower = name_or_id.lower()
    for w in registry.get("worksheets", []):
        if w["id"].lower() == name_lower:
            return w
        if name_lower in w["name"].lower():
            return w
    return None


def get_completed_ids(base_path: Path = None) -> list[str]:
    """Get list of completed worksheet IDs from saved files."""
    wdir = (base_path / ".scaleup" / "my-company" / "worksheets") if base_path else COMPLETED_DIR
    if not wdir.exists():
        return []
    completed = []
    for f in wdir.glob("*.yaml"):
        data = read_yaml(f)
        wid = data.get("worksheet_id") if data else f.stem
        if wid:
            completed.append(wid)
        else:
            completed.append(f.stem)
    return completed


def load_worksheet_content(worksheet: dict, base_path: Path = None) -> dict:
    """Load full worksheet content from its ontology node_path."""
    node_path = worksheet.get("node_path", "")
    if not node_path:
        return worksheet
    base = base_path or Path(__file__).parent.parent.parent
    full_path = base / ".scaleup" / "knowledge" / node_path
    content = read_yaml(full_path)
    return {**worksheet, **content}


def run(context: dict) -> dict:
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
    errors = []

    if action == "list":
        decision = context.get("decision")
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
        lines.extend([
            "",
            "Para empezar: `/escala-worksheet [nombre]`",
            "Para reanudar: mismo comando si ya empezaste",
        ])

        return {"output": "\n".join(lines), "artifacts": {"worksheets": all_ws, "completed": completed}, "errors": []}

    elif action in ("start", "resume"):
        ws_name = context.get("worksheet_name", "")
        worksheet = find_worksheet(ws_name, base)
        if not worksheet:
            available = [w["name"] for w in list_worksheets(decision=None, base_path=base)]
            return {
                "output": "",
                "artifacts": {},
                "errors": [f"Worksheet '{ws_name}' no encontrado. Disponibles: {', '.join(available[:5])}..."],
            }

        completed = get_completed_ids(base)
        if worksheet["id"] in completed:
            return {
                "output": f"Worksheet **{worksheet['name']}** ya está completado. Usa `/escala-worksheet list` para ver otros.",
                "artifacts": {"worksheet": worksheet, "status": "completed"},
                "errors": [],
            }

        state_path = base / ".scaleup" / "my-company" / "worksheets" / f"{worksheet['id']}.yaml"
        state = read_yaml(state_path)
        if state and action == "resume":
            current_step = state.get("current_step", 0)
            saved_fields = state.get("fields", {})
        else:
            current_step = 0
            saved_fields = {}

        content = load_worksheet_content(worksheet, base)
        fields = content.get("metadata", {}).get("fields", [])
        total_steps = len(fields) + 1  # fields + confirmation step

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
            lines.extend([
                "### Paso 1: Información General",
                "",
                "Antes de empezar, confirma que tienes:",
            ])
            if worksheet.get("prerequisites"):
                lines.append("- [ ] Prerrequisitos completados: " + ", ".join(worksheet["prerequisites"]))
            lines.extend([
                "- [ ] Datos actualizados de tu empresa",
                "- [ ] 1-2 horas sin interrupciones",
                "",
                "Responde con 'listo' para empezar.",
            ])
        else:
            step_idx = current_step - 1
            if step_idx < len(fields):
                lines.extend([
                    f"### Paso {current_step + 1}: {fields[step_idx]}",
                    "",
                    "Completa este campo. Responde con tu información.",
                ])
            else:
                lines.extend([
                    "### Revisión Final",
                    "",
                    "Has completado todos los pasos. Revisa tus respuestas y confirma para guardar.",
                ])

        write_yaml(state_path, {
            "worksheet_id": worksheet["id"],
            "worksheet_name": worksheet["name"],
            "decision": worksheet.get("decision"),
            "current_step": current_step,
            "total_steps": total_steps,
            "fields": saved_fields,
            "status": "in_progress",
        })

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
        ws_name = context.get("worksheet_name", "")
        worksheet = find_worksheet(ws_name, base)
        if not worksheet:
            return {"output": "", "artifacts": {}, "errors": [f"Worksheet '{ws_name}' no encontrado"]}

        state_path = base / ".scaleup" / "my-company" / "worksheets" / f"{worksheet['id']}.yaml"
        state = read_yaml(state_path)
        if not state:
            return {"output": "", "artifacts": {}, "errors": [f"Worksheet '{ws_name}' no iniciado. Usa /escala-worksheet {ws_name} primero"]}

        current_step = state.get("current_step", 0)
        total_steps = state.get("total_steps", 0)
        saved_fields = state.get("fields", {})

        step_fields = context.get("fields", {})
        saved_fields.update(step_fields)
        current_step += 1

        content = load_worksheet_content(worksheet, base)
        fields = content.get("metadata", {}).get("fields", [])

        if current_step >= total_steps:
            completed_data = {
                "worksheet_id": worksheet["id"],
                "worksheet_name": worksheet["name"],
                "decision": worksheet.get("decision"),
                "fields": saved_fields,
                "completed": str(__import__("datetime").datetime.now().date()),
                "status": "completed",
            }
            ensure_dir(state_path.parent)
            write_yaml(state_path, completed_data)

            lines = [
                f"## ✅ {worksheet['name']} — Completado",
                "",
                "¡Excelente! Has completado este worksheet.",
                "",
                "### Resumen de tus respuestas:",
                "",
            ]
            for field_name, value in saved_fields.items():
                lines.append(f"- **{field_name}:** {value}")
            lines.extend([
                "",
                "Próximos pasos sugeridos:",
                f"- `/escala-progress` para ver tu avance general",
                f"- `/escala-worksheet list` para ver otros worksheets",
            ])

            return {
                "output": "\n".join(lines),
                "artifacts": {"worksheet": worksheet, "completed_data": completed_data, "state_path": str(state_path)},
                "errors": [],
            }
        else:
            write_yaml(state_path, {**state, "current_step": current_step, "fields": saved_fields, "status": "in_progress"})

            if current_step < len(fields):
                next_field = fields[current_step]
                lines = [f"### Paso {current_step + 1}: {next_field}", "", "Completa este campo con tu información."]
            else:
                lines = ["### Revisión Final", "", "Has completado todos los campos. Revisa y confirma:", ""]
                for field_name, value in saved_fields.items():
                    lines.append(f"- **{field_name}:** {value}")
                lines.append("")
                lines.append("Responde 'confirmar' para guardar el worksheet como completado.")

            return {
                "output": "\n".join(lines),
                "artifacts": {"worksheet": worksheet, "current_step": current_step, "total_steps": total_steps, "state_path": str(state_path)},
                "errors": [],
            }

    elif action == "save":
        ws_name = context.get("worksheet_name", "")
        worksheet = find_worksheet(ws_name, base)
        if not worksheet:
            return {"output": "", "artifacts": {}, "errors": [f"Worksheet '{ws_name}' no encontrado"]}

        state_path = base / ".scaleup" / "my-company" / "worksheets" / f"{worksheet['id']}.yaml"
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

        # Anti-overwrite silencioso: si vamos a pisar un worksheet YA finalizado,
        # respaldamos la versión previa con timestamp en vez de borrarla sin rastro.
        # El flujo normal step→save (status in_progress) no genera respaldos.
        backup_path = None
        if state_path.exists() and state.get("status") == "completed":
            import datetime
            import shutil
            ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_path = state_path.with_name(f"{worksheet['id']}.{ts}.bak.yaml")
            shutil.copy2(state_path, backup_path)

        write_yaml(state_path, completed_data)

        output = f"✅ **{worksheet['name']}** guardado como completado."
        if backup_path is not None:
            output += f"\n\n♻️ Se respaldó la versión previa en `{backup_path.name}` antes de sobrescribir."
        artifacts = {"worksheet": worksheet, "completed_data": completed_data, "state_path": str(state_path)}
        if backup_path is not None:
            artifacts["backup_path"] = str(backup_path)
        return {"output": output, "artifacts": artifacts, "errors": []}

    return {"output": "", "artifacts": {}, "errors": [f"Unknown action: {action}"]}
