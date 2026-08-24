"""
Progress module — completion dashboard per decision.
"""
from pathlib import Path
from ..core import read_yaml

DECISIONS = ["people", "strategy", "execution", "cash"]

DECISION_LABELS = {
    "people": "People — Personas",
    "strategy": "Strategy — Estrategia",
    "execution": "Execution — Ejecución",
    "cash": "Cash — Efectivo",
}

DECISION_ORDER = ["people", "strategy", "execution", "cash"]


def _get_worksheets(base_path: Path) -> tuple[list[dict], dict[str, dict]]:
    """Load all worksheets and completed ones."""
    runtime_root = Path(__file__).resolve().parents[2]
    registry_paths = (
        base_path / ".scaleup" / "knowledge" / "registry" / "worksheets.yaml",
        runtime_root / ".scaleup" / "knowledge" / "registry" / "worksheets.yaml",
        runtime_root / "knowledge" / "registry" / "worksheets.yaml",
    )
    registry_path = next(
        (path for path in registry_paths if path.is_file()), registry_paths[0]
    )
    registry = read_yaml(registry_path)
    all_ws = registry.get("worksheets", [])

    wdir = base_path / ".scaleup" / "my-company" / "worksheets"
    completed = {}
    if wdir.exists():
        for f in wdir.glob("*.yaml"):
            data = read_yaml(f)
            wid = data.get("worksheet_id") if data else f.stem
            if data and data.get("status") == "completed":
                completed[wid] = data

    return all_ws, completed


def run(context: dict) -> dict:
    """
    Generate progress dashboard.

    Context keys:
        - base_path: str
        - scores: dict (optional, will read from profile if not provided)

    Returns:
        dict with output, artifacts, errors
    """
    base = Path(context.get("base_path", "."))
    profile_path = base / ".scaleup" / "agent" / "memory" / "company-profile.yaml"
    profile = read_yaml(profile_path)
    scores = context.get("scores", profile.get("scores", {}))

    all_ws, completed = _get_worksheets(base)

    if not scores:
        name = profile.get("company", {}).get("name") or "tu empresa"
        return {"output": f"Ya tengo el perfil de {name}. Para saber dónde conviene empezar, revisemos cuatro áreas de tu empresa con preguntas sencillas. ¿Te parece si empezamos?", "artifacts": {"company_name": name, "next_step": "diagnosis"}, "errors": []}

    if not all_ws:
        return {"output": "No puedo cargar las guías de seguimiento en esta instalación. Reinstala ScaleUp y vuelve a intentarlo; tus datos de empresa se conservarán.", "artifacts": {}, "errors": ["Empty worksheet registry"]}

    lines = ["## 📊 Dashboard de Progreso", "", "### Scores por Decisión", "", "| Decisión | Score | Nivel |", "|----------|-------|-------|"]
    level_labels = {1: "🔴 No iniciado", 2: "🟠 Ad hoc", 3: "🟡 Emergente", 4: "🟢 Establecido", 5: "⭐ Optimizado"}

    for dec_key in DECISION_ORDER:
        score = scores.get(dec_key, 0)
        lines.append(f"| {DECISION_LABELS.get(dec_key, dec_key)} | {score} | {level_labels.get(score, '—')} |")

    lines.extend(["", "### Worksheets por Decisión", ""])

    for dec_key in DECISION_ORDER:
        dec_ws = [w for w in all_ws if w.get("decision") == dec_key]
        total = len(dec_ws)
        done = sum(1 for w in dec_ws if w["id"] in completed)
        pct = round((done / total * 100)) if total > 0 else 0
        lines.append(f"**{DECISION_LABELS.get(dec_key, dec_key)}:** {done}/{total} ({pct}%)")
        lines.append("")
        for w in dec_ws:
            lines.append(f"- {'✅' if w['id'] in completed else '⬜'} {w['name']}")
        lines.append("")

    lowest_decision = min([d for d in DECISION_ORDER if scores.get(d, 0) > 0], key=lambda d: scores.get(d, 0), default=None)

    if lowest_decision:
        dec_ws = [w for w in all_ws if w.get("decision") == lowest_decision and w["id"] not in completed]
        if dec_ws:
            next_ws = dec_ws[0]
            lines.extend(["### Siguiente Sugerido", f"- {next_ws['name']} en {DECISION_LABELS.get(lowest_decision, lowest_decision)}", f"- Dificultad: {next_ws.get('difficulty', '—')} | Tiempo: {next_ws.get('time_estimate', '—')}", "- Podemos empezar con este siguiente paso cuando quieras.", ""])

    lines.append("> Puedes revisar de nuevo las cuatro áreas cuando cambie tu situación.")

    total_all = sum(len([w for w in all_ws if w.get("decision") == d]) for d in DECISION_ORDER)
    done_all = sum(1 for w in all_ws if w["id"] in completed)
    overall_pct = round((done_all / total_all * 100)) if total_all > 0 else 0

    return {
        "output": "\n".join(lines),
        "artifacts": {
            "total_worksheets": total_all,
            "completed_worksheets": done_all,
            "completion_pct": overall_pct,
            "per_decision": {d: {"score": scores.get(d, 0), "total": len([w for w in all_ws if w.get("decision") == d]), "completed": sum(1 for w in all_ws if w.get("decision") == d and w["id"] in completed)} for d in DECISION_ORDER},
        },
        "errors": [],
    }
