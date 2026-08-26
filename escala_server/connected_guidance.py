"""Conservative external-context guidance; ScaleUp never invokes a connector."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal
from uuid import uuid4

from .project_memory import ProjectMemoryRuntime

Host = Literal["claude", "codex", "none"]
Need = Literal["documents", "calendar", "market_research"]

_SECRET = re.compile(r"(?i)\b(?:api[_-]?key|token|password|secret|private key)\b|sk-[A-Za-z0-9_-]+")
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_MONEY = re.compile(r"(?<!\w)(?:MXN|USD|\$)\s?[\d,.]+")
_LONG_ID = re.compile(r"\b\d{8,}\b")


@dataclass(frozen=True)
class HostCapabilities:
    host: Host
    drive: bool = False
    calendar: bool = False
    deep_research: bool = False
    scheduled_tasks: bool = False


@dataclass(frozen=True)
class Guidance:
    need: Need
    purpose: str
    data_minimum: str
    risk: str
    manual_alternative: str
    connector: str | None
    host_message: str


def capabilities(host: Host, declared: dict[str, bool] | None = None) -> HostCapabilities:
    """Capabilities are supplied by the host/fixture, never guessed."""
    values = declared or {}
    if host not in {"claude", "codex", "none"}:
        host = "none"
    return HostCapabilities(host, *(bool(values.get(key, False)) for key in ("drive", "calendar", "deep_research", "scheduled_tasks")))


def recommend(need: Need, host: HostCapabilities) -> Guidance:
    catalog = {
        "documents": ("Contrastar una decisión con documentos ya autorizados", "Sólo los campos necesarios, sin nombres de clientes ni credenciales", "Los documentos pueden contener contratos, importes o información de terceros", "Resume localmente los datos mínimos y comparte sólo una versión anonimizada", "Drive", host.drive),
        "calendar": ("Ver si un compromiso cabe en la agenda", "Sólo ventanas de disponibilidad, sin títulos, invitados ni enlaces", "El calendario revela personas, reuniones y ubicaciones", "Define aquí un bloque semanal sin conectar ningún calendario", "Calendar", host.calendar),
        "market_research": ("Comprobar si un SWT sigue vigente", "Pregunta sectorial anonimizda, sin empresa, clientes ni importes", "La investigación externa puede revelar estrategia o contexto identificable", "Revisa SWT manualmente al abrir ScaleUp", "Deep Research", host.deep_research),
    }
    purpose, minimum, risk, manual, connector, available = catalog[need]
    if not available:
        return Guidance(need, purpose, minimum, risk, manual, None, "Este host no declaró esa capacidad. Puedes usar la alternativa manual; ScaleUp no instalará ni conectará nada.")
    return Guidance(need, purpose, minimum, risk, manual, connector, f"Tu host declaró {connector}. Si decides usarlo, la autorización ocurre en el host, fuera de ScaleUp.")


def anonymize_preview(text: str) -> str | None:
    """Return a shareable preview, or None for secrets that must stop the flow."""
    if not isinstance(text, str) or not text.strip() or _SECRET.search(text):
        return None
    value = _EMAIL.sub("[PERSONA]", text)
    value = _MONEY.sub("[IMPORTE]", value)
    value = _LONG_ID.sub("[IDENTIFICADOR]", value)
    value = re.sub(r"(?i)\b(?:cliente|proveedor)\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ-]*", "[TERCERO]", value)
    return value


def swt_recipe(host: HostCapabilities, months: int = 3) -> Guidance:
    if not 1 <= months <= 12:
        raise ValueError("frequency must be between 1 and 12 months")
    base = recommend("market_research", host)
    return Guidance(base.need, f"Revisar SWT cada {months} meses con evidencia reciente", base.data_minimum, base.risk, base.manual_alternative, base.connector, base.host_message + " Es una sugerencia; aceptarla localmente no programa una tarea.")


def record_decision(project_root: str, *, need: Need, state: str, explicit_confirmation: bool) -> bool:
    """Record only an explicit local choice, never a token, account or payload."""
    if not explicit_confirmation or state not in {"accepted", "rejected", "paused"}:
        return False
    runtime = ProjectMemoryRuntime(project_root)
    ready = runtime.ensure_memory()
    if not ready.ready:
        return False
    import sqlite3
    value = json.dumps({"need": need, "state": state, "external_content": None}, sort_keys=True)
    with sqlite3.connect(ready.db_path) as db:
        db.execute("INSERT INTO memory_facts (key, value) VALUES (?, ?)", (f"connected_guidance.decision.{uuid4()}", value))
        db.commit()
    return True
