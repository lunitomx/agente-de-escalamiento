"""Persistent One-Page Strategic Plan core shared by Claude and Codex."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from .core import ensure_dir, read_yaml

KNOWLEDGE_PATH = Path(".scaleup/knowledge/strategy/tools/opsp.yaml")
ARTIFACT_PATH = Path("work/strategy/opsp.md")


def load_opsp_knowledge(base_path: str | Path = ".") -> dict[str, Any]:
    """Read the repository's canonical OPSP tool record."""
    base = Path(base_path)
    candidates = [base / KNOWLEDGE_PATH, Path(__file__).resolve().parents[1] / KNOWLEDGE_PATH, Path(__file__).resolve().parents[1] / "knowledge" / "strategy" / "tools" / "opsp.yaml"]
    path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    data = read_yaml(path)
    if data.get("id") != "tool-opsp":
        raise ValueError(f"Canonical OPSP knowledge is missing or invalid: {path}")
    return data


def _merge(original: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(original)
    for key, value in changes.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        elif value is not None:
            result[key] = value
    return result


def _metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    raw, separator, _ = text[4:].partition("\n---\n")
    if not separator:
        return {}
    data = yaml.safe_load(raw) or {}
    return data if isinstance(data, dict) else {}


def _text(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ").strip()


def _rows(rows: Any, keys: tuple[str, ...], width: int = 5) -> list[str]:
    rows = rows if isinstance(rows, list) else []
    output = []
    for index in range(width):
        item = rows[index] if index < len(rows) and isinstance(rows[index], dict) else {}
        output.append("| " + " | ".join([str(index + 1)] + [_text(item.get(key)) for key in keys]) + " |")
    return output


def render_opsp(data: dict[str, Any]) -> str:
    """Render structured, resumable plan data into its canonical Markdown file."""
    values = data.get("core_values") if isinstance(data.get("core_values"), list) else []
    sandbox = data.get("sandbox") if isinstance(data.get("sandbox"), dict) else {}
    brand = data.get("brand_promise") if isinstance(data.get("brand_promise"), dict) else {}
    meta = {
        "schema": "tool-opsp",
        "status": data.get("status", "in_progress"),
        "updated_at": data.get("updated_at"),
        "data": data,
    }
    lines = ["---", yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).strip(), "---", "", "# One-Page Strategic Plan (OPSP)", "", f"> Empresa: {_text(data.get('company_name')) or 'Tu empresa'} | Actualizado: {_text(data.get('updated_at'))}", "", "## CORE VALUES / Valores Fundamentales", "", "| # | Core Value | Descripción |", "|---|---|---|"]
    for index in range(5):
        item = values[index] if index < len(values) else {}
        item = {"name": item} if isinstance(item, str) else item if isinstance(item, dict) else {}
        lines.append(f"| {index + 1} | {_text(item.get('name'))} | {_text(item.get('description'))} |")
    lines += ["", "## PURPOSE / Propósito", "", f"> {_text(data.get('purpose')) or 'Pendiente'}", "", "## BHAG — Meta 10-25 años", "", f"> {_text(data.get('bhag')) or 'Pendiente'}", f"\n**Fecha objetivo:** {_text(data.get('bhag_date')) or 'Pendiente'}", "", "## SANDBOX / Arena Competitiva (3-5 años)", "", "| Elemento | Definición |", "|---|---|"]
    for key, label in (("revenue_target", "Revenue target"), ("profit_target", "Profit target"), ("market", "Market/Geography"), ("customer_segment", "Customer segment"), ("product_focus", "Product/Service focus")):
        lines.append(f"| {label} | {_text(sandbox.get(key)) or 'Pendiente'} |")
    lines += ["", "## BRAND PROMISE / Promesa de Marca", "", "| Elemento | Definición |", "|---|---|", f"| Brand Promise | {_text(brand.get('promise')) or 'Pendiente'} |", f"| KPI que la mide | {_text(brand.get('kpi')) or 'Pendiente'} |", "", "## QUARTERLY PLAN / Plan Trimestral", "", f"**Trimestre:** {_text(data.get('quarter')) or 'Pendiente'}", f"**Critical Number:** {_text(data.get('critical_number')) or 'Pendiente'}", "", "### Prioridades de la Empresa", "", "| # | Prioridad | Owner | KPI | Status |", "|---|---|---|---|---|", *_rows(data.get("quarterly_priorities"), ("priority", "owner", "kpi", "status")), "", "## ANNUAL GOALS / Metas Anuales", "", f"**Año:** {_text(data.get('year')) or 'Pendiente'}", f"**Revenue target:** {_text(data.get('annual_revenue')) or 'Pendiente'}", f"**Profit target:** {_text(data.get('annual_profit')) or 'Pendiente'}", "", "### Prioridades Anuales", "", "| # | Prioridad | Owner | KPI |", "|---|---|---|---|", *_rows(data.get("annual_priorities"), ("priority", "owner", "kpi")), ""]
    return "\n".join(lines)


def validate_opsp(path: Path) -> list[str]:
    """Validate an OPSP without rejecting an honest partial plan."""
    if not path.exists():
        return [f"OPSP not found: {path}"]
    meta = _metadata(path)
    data = meta.get("data") if isinstance(meta.get("data"), dict) else {}
    errors = []
    if meta.get("schema") != "tool-opsp":
        errors.append("OPSP schema must be 'tool-opsp'")
    if meta.get("status") not in {"in_progress", "completed"}:
        errors.append("OPSP status must be 'in_progress' or 'completed'")
    if not meta.get("updated_at"):
        errors.append("OPSP updated_at is required")
    if meta.get("status") == "completed":
        errors.extend(_completion_errors(data))
    return errors


def update_opsp(context: dict[str, Any]) -> dict[str, Any]:
    """Merge partial data, preserving prior answers, and save the canonical artifact."""
    base = Path(context.get("base_path", "."))
    knowledge = load_opsp_knowledge(base)
    artifact = base / ARTIFACT_PATH
    supplied = context.get("data", context.get("opsp", {}))
    if not isinstance(supplied, dict):
        return {"output": "Necesito los datos del plan en un formato válido.", "artifacts": {}, "errors": ["OPSP data must be a mapping"]}
    existing = _metadata(artifact).get("data", {})
    profile = read_yaml(base / ".scaleup/agent/memory/company-profile.yaml")
    defaults = {"company_name": profile.get("company", {}).get("name", ""), "status": "in_progress"}
    data = _merge(_merge(defaults, existing if isinstance(existing, dict) else {}), supplied)
    data["updated_at"] = str(context.get("updated_at") or date.today().isoformat())
    completion_errors = _completion_errors(data)
    if context.get("complete") and not completion_errors:
        data["status"] = "completed"
    elif context.get("complete"):
        # Keep the draft and all answers; the caller asked to finish too early.
        data["status"] = "in_progress"
    ensure_dir(artifact.parent)
    artifact.write_text(render_opsp(data), encoding="utf-8")
    errors = validate_opsp(artifact)
    if context.get("complete") and data["status"] != "completed":
        errors = completion_errors
    if data["status"] == "completed":
        output = "Tu plan en una hoja se guardó y puedes retomarlo cuando quieras."
    elif context.get("complete"):
        output = "Guardé tu avance; aún faltan datos antes de marcar el plan como completo. " + _next_question(completion_errors)
    else:
        output = "Guardé este avance de tu plan en una hoja. ¿Cuál es el propósito de tu empresa más allá de hacer dinero?"
    return {"output": output, "artifacts": {"opsp": str(ARTIFACT_PATH), "knowledge_id": knowledge["id"], "status": data["status"], "data": data}, "errors": errors}


def run(context: dict[str, Any]) -> dict[str, Any]:
    base = Path(context.get("base_path", "."))
    artifact = base / ARTIFACT_PATH
    if context.get("action") in {"status", "validate"}:
        errors = validate_opsp(artifact)
        return {"output": "OPSP válido." if not errors else "OPSP requiere correcciones.", "artifacts": {"opsp": str(ARTIFACT_PATH), "status": _metadata(artifact).get("status")}, "errors": errors}
    return update_opsp(context)
def _has_text(value: Any) -> bool:
    return bool(_text(value))


def _valid_values(values: Any) -> bool:
    if not isinstance(values, list) or len(values) < 3:
        return False
    return all(_has_text(item.get("name") if isinstance(item, dict) else item) for item in values[:3])


def _actionable_priorities(rows: Any, label: str) -> list[str]:
    """Return completion errors for a priority list, without rejecting drafts."""
    if not isinstance(rows, list) or not rows:
        return [f"Completed OPSP needs at least one {label} priority"]
    for index, item in enumerate(rows, start=1):
        if not isinstance(item, dict):
            return [f"Completed OPSP {label} priority {index} must include priority, owner, and KPI"]
        missing = [key for key in ("priority", "owner", "kpi") if not _has_text(item.get(key))]
        if missing:
            return [f"Completed OPSP {label} priority {index} missing: {', '.join(missing)}"]
    return []


def _completion_errors(data: dict[str, Any]) -> list[str]:
    """Minimum user-meaningful content required before calling an OPSP complete."""
    errors: list[str] = []
    for key in ("company_name", "purpose", "bhag", "bhag_date", "quarter", "critical_number", "year", "annual_revenue", "annual_profit"):
        if not _has_text(data.get(key)):
            errors.append(f"Completed OPSP missing: {key}")
    if not _valid_values(data.get("core_values")):
        errors.append("Completed OPSP needs at least three named core values")
    sandbox = data.get("sandbox") if isinstance(data.get("sandbox"), dict) else {}
    if not _has_text(sandbox.get("market")):
        errors.append("Completed OPSP missing: sandbox.market")
    brand = data.get("brand_promise") if isinstance(data.get("brand_promise"), dict) else {}
    for key in ("promise", "kpi"):
        if not _has_text(brand.get(key)):
            errors.append(f"Completed OPSP missing: brand_promise.{key}")
    errors.extend(_actionable_priorities(data.get("annual_priorities"), "annual"))
    errors.extend(_actionable_priorities(data.get("quarterly_priorities"), "quarterly"))
    return errors


def _next_question(errors: list[str]) -> str:
    """Give a nontechnical person one concrete next answer after an incomplete finish."""
    prompts = {
        "company_name": "¿Cómo se llama tu empresa?",
        "core_values": "¿Cuáles son tres valores que guían las decisiones de tu empresa?",
        "purpose": "¿Cuál es el propósito de tu empresa más allá de hacer dinero?",
        "bhag": "¿Qué meta ambiciosa quieren alcanzar en 10 a 25 años?",
        "bhag_date": "¿Para qué fecha quieren alcanzar esa meta ambiciosa?",
        "sandbox.market": "¿En qué mercado o geografía competirán?",
        "brand_promise": "¿Qué promesa concreta hacen siempre a sus clientes y cómo la medirán?",
        "quarter": "¿Qué trimestre estás planificando?",
        "critical_number": "¿Cuál es el número crítico que enfocará este trimestre?",
        "year": "¿Qué año cubrirán estas metas?",
        "annual_revenue": "¿Cuál es su meta anual de ingresos?",
        "annual_profit": "¿Cuál es su meta anual de utilidad?",
        "annual priority": "¿Cuál es una prioridad anual, quién la lidera y cómo medirán el resultado?",
        "quarterly priority": "¿Cuál es una prioridad de este trimestre, quién la lidera y qué indicador la medirá?",
    }
    first = errors[0] if errors else ""
    for marker, prompt in prompts.items():
        if marker in first:
            return prompt
    return "¿Qué dato falta para que este plan sea accionable?"
