"""Explicit-consent, local-only collaboration context for a ScaleUp leader."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from uuid import uuid4

from .project_memory import ProjectMemoryRuntime

HumanField = Literal[
    "role", "responsibilities", "communication_style", "language",
    "detail_level", "pace", "availability", "horizon", "capacity",
    "professional_goal",
]
Consumer = Literal["coaching", "cadence", "board"]

_FIELDS: dict[str, dict[str, object]] = {
    "role": {"label": "rol", "purpose": "adaptar las preguntas a las decisiones que puedes tomar", "consumers": frozenset(("coaching", "cadence", "board"))},
    "responsibilities": {"label": "responsabilidades", "purpose": "no pedirte información que no te corresponde decidir", "consumers": frozenset(("coaching", "board"))},
    "communication_style": {"label": "estilo de comunicación", "purpose": "presentar recomendaciones de una forma más útil para ti", "consumers": frozenset(("coaching", "cadence", "board"))},
    "language": {"label": "idioma", "purpose": "responderte en el idioma que prefieres", "consumers": frozenset(("coaching", "cadence", "board"))},
    "detail_level": {"label": "nivel de detalle", "purpose": "calibrar la extensión de planes y explicaciones", "consumers": frozenset(("coaching", "cadence", "board"))},
    "pace": {"label": "ritmo de trabajo", "purpose": "proponer pasos que quepan en tu ritmo", "consumers": frozenset(("coaching", "cadence"))},
    "availability": {"label": "disponibilidad", "purpose": "sugerir revisiones en un horizonte realista", "consumers": frozenset(("coaching", "cadence"))},
    "horizon": {"label": "horizonte de planificación", "purpose": "ordenar decisiones por el plazo que te sirve", "consumers": frozenset(("coaching", "cadence", "board"))},
    "capacity": {"label": "capacidad disponible", "purpose": "evitar comprometer más acciones de las que caben", "consumers": frozenset(("coaching", "cadence"))},
    "professional_goal": {"label": "objetivo profesional ligado a la empresa", "purpose": "conectar el acompañamiento empresarial con el resultado que buscas", "consumers": frozenset(("coaching", "board"))},
}
_SENSITIVE = re.compile(
    r"\b(?:salud|diagnostico|diagnóstico|terapia|m[eé]dic\w*|medicaci[oó]n|embaraz|religion|religión|"
    r"politic|orientaci[oó]n|sexual|raza|etnia|discapacidad|pasaporte|curp|ine|"
    r"contrase(?:ñ|n)a|password|token|api[ _-]?key|clave privada|n[uú]mero de tarjeta)\b",
    re.IGNORECASE,
)
_SECRET = re.compile(r"(?:api[_-]?key|password|secret|token|private[_-]?key)\s*[:=]", re.I)
_PHONE_OR_CARD = re.compile(r"(?:\+?\d[\s-]?){10,}")


@dataclass(frozen=True)
class HumanContextEntry:
    """A user-confirmed, local collaboration preference."""

    id: str
    field: HumanField
    value: str
    purpose: str
    consented_at: str


@dataclass(frozen=True)
class HumanContextResult:
    """Safe result for the natural-language adapter."""

    ready: bool
    entry: HumanContextEntry | None = None
    entries: tuple[HumanContextEntry, ...] = ()
    reason: str | None = None
    suggested_generalization: str | None = None


class HumanContextStore:
    """Manage the minimal leader profile using the project's local SQLite DB."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        self.runtime = ProjectMemoryRuntime(self.project_root)

    @staticmethod
    def fields() -> tuple[str, ...]:
        return tuple(_FIELDS)

    @staticmethod
    def describe(field: str) -> tuple[str, str]:
        spec = _field_spec(field)
        return str(spec["label"]), str(spec["purpose"])

    def validate(self, field: str, value: object) -> HumanContextResult:
        """Validate a possible value without recording it anywhere."""
        try:
            _field_spec(field)
            clean = _clean_value(value)
            if _looks_sensitive(clean):
                return HumanContextResult(
                    False,
                    reason="sensitive personal data must not be stored",
                    suggested_generalization=_generalization(field),
                )
            return HumanContextResult(True)
        except ValueError as error:
            return HumanContextResult(False, reason=str(error))

    def confirm(
        self, field: str, value: object, *, explicit_confirmation: bool
    ) -> HumanContextResult:
        """Persist exactly one approved field, superseding its old active value."""
        if not explicit_confirmation:
            return HumanContextResult(False, reason="explicit confirmation is required")
        valid = self.validate(field, value)
        if not valid.ready:
            return valid
        try:
            clean = _clean_value(value)
            spec = _field_spec(field)
            memory = self.runtime.ensure_memory()
            if not memory.ready:
                return HumanContextResult(False, reason=memory.reason)
            entry_id = str(uuid4())
            with sqlite3.connect(memory.db_path) as db:
                db.execute("BEGIN IMMEDIATE")
                previous = db.execute(
                    "SELECT id FROM human_context_entries WHERE field=? AND status='active' "
                    "ORDER BY consented_at DESC, id DESC LIMIT 1",
                    (field,),
                ).fetchone()
                if previous is not None:
                    db.execute(
                        "UPDATE human_context_entries SET status='superseded' WHERE id=?",
                        (previous[0],),
                    )
                db.execute(
                    """INSERT INTO human_context_entries
                       (id, field, value, purpose, source, status, replaces_entry_id)
                       VALUES (?, ?, ?, ?, 'explicit_user_statement', 'active', ?)""",
                    (entry_id, field, clean, spec["purpose"], previous[0] if previous else None),
                )
                row = db.execute(
                    "SELECT id, field, value, purpose, consented_at "
                    "FROM human_context_entries WHERE id=?",
                    (entry_id,),
                ).fetchone()
                db.commit()
            assert row is not None
            return HumanContextResult(True, entry=_row_to_entry(row))
        except (OSError, sqlite3.Error, ValueError) as error:
            return HumanContextResult(False, reason=str(error))

    def list(self) -> HumanContextResult:
        """Return active context only; deleted and superseded values are hidden."""
        try:
            memory = self.runtime.ensure_memory()
            if not memory.ready:
                return HumanContextResult(False, reason=memory.reason)
            with sqlite3.connect(memory.db_path) as db:
                rows = db.execute(
                    """SELECT id, field, value, purpose, consented_at
                       FROM human_context_entries WHERE status='active'
                       ORDER BY field, consented_at, id"""
                ).fetchall()
            return HumanContextResult(True, entries=tuple(_row_to_entry(row) for row in rows))
        except (OSError, sqlite3.Error, ValueError) as error:
            return HumanContextResult(False, reason=str(error))

    def delete(self, field: str | None = None) -> HumanContextResult:
        """Idempotently remove one field or the complete personal profile."""
        try:
            if field is not None:
                _field_spec(field)
            memory = self.runtime.ensure_memory()
            if not memory.ready:
                return HumanContextResult(False, reason=memory.reason)
            with sqlite3.connect(memory.db_path) as db:
                if field is None:
                    db.execute(
                        "UPDATE human_context_entries SET status='deleted', deleted_at=datetime('now') "
                        "WHERE status='active'"
                    )
                else:
                    db.execute(
                        "UPDATE human_context_entries SET status='deleted', deleted_at=datetime('now') "
                        "WHERE field=? AND status='active'",
                        (field,),
                    )
                db.commit()
            return HumanContextResult(True)
        except (OSError, sqlite3.Error, ValueError) as error:
            return HumanContextResult(False, reason=str(error))

    def project(self, consumer: Consumer) -> HumanContextResult:
        """Return only fields needed by one consumer and log local use."""
        if consumer not in {"coaching", "cadence", "board"}:
            return HumanContextResult(False, reason="unknown context consumer")
        try:
            memory = self.runtime.ensure_memory()
            if not memory.ready:
                return HumanContextResult(False, reason=memory.reason)
            with sqlite3.connect(memory.db_path) as db:
                rows = db.execute(
                    """SELECT id, field, value, purpose, consented_at
                       FROM human_context_entries WHERE status='active'
                       ORDER BY field, consented_at, id"""
                ).fetchall()
                entries = tuple(
                    _row_to_entry(row)
                    for row in rows
                    if consumer in _field_spec(str(row[1]))["consumers"]
                )
                for entry in entries:
                    db.execute(
                        "INSERT INTO human_context_accesses (entry_id, consumer, purpose) VALUES (?, ?, ?)",
                        (entry.id, consumer, _field_spec(entry.field)["purpose"]),
                    )
                db.commit()
            return HumanContextResult(True, entries=entries)
        except (OSError, sqlite3.Error, ValueError) as error:
            return HumanContextResult(False, reason=str(error))


def _field_spec(field: str) -> dict[str, object]:
    if field not in _FIELDS:
        raise ValueError("unsupported human-context field")
    return _FIELDS[field]


def _clean_value(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("context value must be text")
    clean = " ".join(value.strip().split())
    if not 1 <= len(clean) <= 240:
        raise ValueError("context value must contain 1 to 240 characters")
    if "\x00" in clean:
        raise ValueError("context value contains unsafe characters")
    return clean


def _looks_sensitive(value: str) -> bool:
    return bool(_SENSITIVE.search(value) or _SECRET.search(value) or _PHONE_OR_CARD.search(value))


def _generalization(field: str) -> str:
    label, purpose = HumanContextStore.describe(field)
    return f"Puedes expresarlo de forma general como una restricción de trabajo relacionada con tu {label}; así puedo {purpose}."


def _row_to_entry(row: tuple[object, ...]) -> HumanContextEntry:
    entry_id, field, value, purpose, consented_at = row
    if not all(isinstance(item, str) and item for item in row):
        raise ValueError("invalid local human-context entry")
    _field_spec(field)
    return HumanContextEntry(entry_id, field, value, purpose, consented_at)
