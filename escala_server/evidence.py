"""Local, consent-first evidence capture for ScaleUp methodologies.

Raw files and connector responses are used only to construct a local preview.
They are never stored in the business memory. A value becomes usable only after
the person accepts that individual field.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
from xml.etree import ElementTree

from .project_memory import ProjectMemoryRuntime

DECISIONS = ("people", "strategy", "execution", "cash")
_SECRET = re.compile(
    r"(?i)\b(?:api[_-]?key|token|password|secret|private key)\b|\bsk-[A-Za-z0-9_-]+"
)
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PERSONAL_ID = re.compile(
    r"(?i)\b(?:rfc|curp|nss|ssn|passport|account number|cuenta bancaria)\b"
)


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    methodology: str
    question: str
    numeric: bool = False
    aliases: tuple[str, ...] = ()


FIELDS: dict[str, tuple[FieldSpec, ...]] = {
    "cash": (
        FieldSpec(
            "price",
            "precio por unidad",
            "power-of-one",
            "¿Cuál es el precio promedio por unidad o venta?",
            True,
            ("precio", "precio promedio", "precio unitario", "price", "unit price"),
        ),
        FieldSpec(
            "volume",
            "volumen",
            "power-of-one",
            "¿Cuál fue el volumen de unidades o ventas en el periodo?",
            True,
            ("volumen", "unidades", "ventas unidades", "volume", "units"),
        ),
        FieldSpec(
            "cogs",
            "COGS (%)",
            "power-of-one",
            "¿Cuál es el costo de ventas como porcentaje de ingresos?",
            True,
            (
                "cogs",
                "costo de ventas",
                "costo ventas",
                "cost of goods",
                "gross margin",
            ),
        ),
        FieldSpec(
            "overheads",
            "gastos operativos",
            "power-of-one",
            "¿Cuáles son los gastos operativos del periodo?",
            True,
            ("gastos", "gastos operativos", "overheads", "opex", "operating expenses"),
        ),
        FieldSpec(
            "ar_days",
            "días de cobranza (A/R)",
            "cash-conversion-cycle",
            "¿Cuántos días tardan en cobrar, en promedio?",
            True,
            (
                "dias cobranza",
                "dias de cobro",
                "ar days",
                "dso",
                "accounts receivable days",
            ),
        ),
        FieldSpec(
            "inv_days",
            "días de inventario",
            "cash-conversion-cycle",
            "¿Cuántos días permanece el inventario antes de venderse?",
            True,
            ("dias inventario", "inventory days", "dio"),
        ),
        FieldSpec(
            "ap_days",
            "días de pago (A/P)",
            "cash-conversion-cycle",
            "¿En cuántos días pagan a proveedores, en promedio?",
            True,
            ("dias pago", "ap days", "dpo", "accounts payable days"),
        ),
    ),
    "people": (
        FieldSpec(
            "role_coverage",
            "roles críticos cubiertos",
            "team-capacity",
            "¿Qué roles críticos están cubiertos y cuál sigue sin dueño claro?",
        ),
        FieldSpec(
            "capacity_constraint",
            "restricción de capacidad",
            "team-capacity",
            "¿Cuál es la restricción de capacidad más concreta hoy?",
        ),
        FieldSpec(
            "face_practice",
            "práctica FACe",
            "face",
            "¿Qué práctica concreta usan para dar feedback, rendir cuentas o desarrollar al equipo?",
        ),
    ),
    "strategy": (
        FieldSpec(
            "core_customer",
            "cliente principal",
            "core-customer",
            "¿Cuál es el cliente principal que eligieron servir?",
        ),
        FieldSpec(
            "brand_promise",
            "promesa de marca",
            "brand-promise",
            "¿Cuál es la promesa que hacen y cómo sabrán si la cumplieron?",
        ),
        FieldSpec(
            "strategic_choice",
            "decisión estratégica",
            "opsp",
            "¿Qué decisión estratégica concreta necesitan aclarar ahora?",
        ),
    ),
    "execution": (
        FieldSpec(
            "quarterly_priority",
            "prioridad trimestral",
            "priorities",
            "¿Cuál es la prioridad trimestral con un resultado observable?",
        ),
        FieldSpec(
            "kpi",
            "indicador",
            "balanced-kpis",
            "¿Qué indicador mostrará avance y con qué frecuencia lo revisarán?",
        ),
        FieldSpec(
            "meeting_rhythm",
            "ritmo de reuniones",
            "meeting-rhythms",
            "¿Qué reunión o revisión sostiene esa prioridad y cada cuándo ocurre?",
        ),
    ),
}


@dataclass(frozen=True)
class Preview:
    ready: bool
    headers: tuple[str, ...] = ()
    rows: tuple[dict[str, str], ...] = ()
    proposed: dict[str, Any] | None = None
    ambiguous: tuple[str, ...] = ()
    sensitivity: str | None = None
    reason: str | None = None
    source_ref: str | None = None
    content_sha256: str | None = None


@dataclass(frozen=True)
class CaptureResult:
    ready: bool
    source_id: str | None = None
    value_id: str | None = None
    reason: str | None = None


def field_specs(decision: str) -> tuple[FieldSpec, ...]:
    return FIELDS.get(decision, ())


def _normalise(value: str) -> str:
    import unicodedata

    return " ".join(
        "".join(
            char
            for char in unicodedata.normalize("NFD", value.casefold())
            if unicodedata.category(char) != "Mn"
        ).split()
    )


def sensitivity_of(value: object) -> str | None:
    text = str(value or "")
    if _SECRET.search(text):
        return "secret"
    if _EMAIL.search(text) or _PERSONAL_ID.search(text):
        return "personal_data"
    return None


def _header_sensitivity(header: str) -> str | None:
    normalized = _normalise(header)
    if _SECRET.search(header):
        return "secret"
    if any(
        token in normalized
        for token in (
            "correo",
            "email",
            "nombre cliente",
            "cliente",
            "proveedor",
            "rfc",
            "curp",
            "nss",
            "cuenta bancaria",
        )
    ):
        return "personal_data"
    return None


def _safe_source_ref(value: str) -> str:
    return Path(value).name[:180] or "fuente local"


def _as_number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip().replace(" ", "")
    raw = re.sub(r"(?i)(mxn|usd|\$|%|d[ií]as?)", "", raw)
    if raw.count(",") == 1 and raw.count(".") == 0:
        raw = raw.replace(",", ".")
    else:
        raw = raw.replace(",", "")
    try:
        return float(raw)
    except ValueError:
        return None


class EvidenceStore:
    """Store accepted methodology facts in local SQLite with full provenance."""

    def __init__(self, project_root: str | Path) -> None:
        self.runtime = ProjectMemoryRuntime(project_root)

    def preview_file(self, path: str | Path, decision: str) -> Preview:
        candidate = Path(path).expanduser()
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            return Preview(False, reason="No encontré ese archivo local.")
        if not resolved.is_file() or resolved.suffix.casefold() not in {
            ".csv",
            ".xlsx",
        }:
            return Preview(
                False, reason="Sólo puedo previsualizar archivos CSV o XLSX."
            )
        if resolved.stat().st_size > 5 * 1024 * 1024:
            return Preview(
                False,
                reason="El archivo supera 5 MB; comparte sólo una exportación con las columnas necesarias.",
            )
        try:
            headers, rows = (
                _read_csv(resolved)
                if resolved.suffix.casefold() == ".csv"
                else _read_xlsx(resolved)
            )
        except (
            OSError,
            UnicodeDecodeError,
            ValueError,
            zipfile.BadZipFile,
            ElementTree.ParseError,
        ) as error:
            return Preview(
                False, reason=f"No pude leer el archivo con seguridad: {error}"
            )
        return self._preview(
            headers,
            rows,
            decision,
            _safe_source_ref(str(resolved)),
            hashlib.sha256(resolved.read_bytes()).hexdigest(),
        )

    def preview_host_content(
        self,
        content: str,
        decision: str,
        *,
        source_ref: str = "contenido autorizado por el host",
    ) -> Preview:
        """Preview explicitly supplied host content; this never opens a connector."""
        if not isinstance(content, str) or not content.strip():
            return Preview(False, reason="No recibí contenido para previsualizar.")
        if len(content.encode("utf-8")) > 1_000_000:
            return Preview(
                False,
                reason="El contenido es demasiado grande; comparte sólo las columnas necesarias.",
            )
        try:
            reader = csv.DictReader(content.splitlines())
            headers = tuple(reader.fieldnames or ())
            rows = tuple(
                {str(k): str(v or "") for k, v in row.items()}
                for row in list(reader)[:20]
            )
            if not headers:
                raise ValueError("necesito encabezados CSV")
        except (csv.Error, ValueError) as error:
            return Preview(
                False,
                reason=f"Para contenido del host comparte una tabla CSV con encabezados: {error}.",
            )
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return self._preview(
            headers, rows, decision, _safe_source_ref(source_ref), digest
        )

    def preview_values(
        self,
        decision: str,
        values: dict[str, object],
        *,
        source_ref: str = "captura manual",
    ) -> Preview:
        specs = {spec.key: spec for spec in field_specs(decision)}
        proposed: dict[str, Any] = {}
        for key, value in values.items():
            if key not in specs or value in (None, ""):
                continue
            risk = sensitivity_of(value)
            if risk:
                return Preview(
                    False,
                    sensitivity=risk,
                    reason="Ese dato parece delicado. No lo guardaré ni lo usaré como propuesta.",
                )
            parsed = _as_number(value) if specs[key].numeric else str(value).strip()
            if parsed is None or parsed == "":
                return Preview(
                    False, reason=f"No pude interpretar el valor de {specs[key].label}."
                )
            proposed[key] = parsed
        if not proposed:
            return Preview(
                False, reason="No encontré datos útiles para esta metodología."
            )
        raw = json.dumps(proposed, ensure_ascii=False, sort_keys=True)
        return Preview(
            True,
            proposed=proposed,
            source_ref=_safe_source_ref(source_ref),
            content_sha256=hashlib.sha256(raw.encode()).hexdigest(),
        )

    def _preview(
        self,
        headers: tuple[str, ...],
        rows: tuple[dict[str, str], ...],
        decision: str,
        source_ref: str,
        digest: str,
    ) -> Preview:
        header_risk = next(
            (
                _header_sensitivity(header)
                for header in headers
                if _header_sensitivity(header)
            ),
            None,
        )
        value_risk = next(
            (
                sensitivity_of(value)
                for row in rows
                for value in row.values()
                if sensitivity_of(value)
            ),
            None,
        )
        if header_risk or value_risk:
            return Preview(
                False,
                sensitivity=header_risk or value_risk,
                reason="El archivo declara o contiene datos delicados. Retíralos antes de continuar; no guardaré ni indexaré el archivo.",
            )
        proposed: dict[str, Any] = {}
        ambiguous: list[str] = []
        normal_headers = {_normalise(header): header for header in headers}
        for spec in field_specs(decision):
            matches = [
                original
                for alias in (spec.key, *spec.aliases)
                if (original := normal_headers.get(_normalise(alias)))
            ]
            matches = list(dict.fromkeys(matches))
            if len(matches) > 1:
                ambiguous.append(spec.key)
                continue
            if not matches or not rows:
                continue
            value = rows[0].get(matches[0], "")
            risk = sensitivity_of(value)
            if risk:
                continue
            parsed = _as_number(value) if spec.numeric else value.strip()
            if parsed not in (None, ""):
                proposed[spec.key] = parsed
        return Preview(
            True,
            headers=headers,
            rows=rows[:5],
            proposed=proposed,
            ambiguous=tuple(ambiguous),
            source_ref=source_ref,
            content_sha256=digest,
        )

    def confirm_value(
        self,
        *,
        decision: str,
        field: str,
        value: object,
        source_type: str,
        source_ref: str,
        observed_at: str | None = None,
        content_sha256: str | None = None,
        source_id: str | None = None,
    ) -> CaptureResult:
        """Persist one explicitly confirmed value and supersede only that field."""
        spec = next((item for item in field_specs(decision) if item.key == field), None)
        if spec is None or source_type not in {
            "manual",
            "file_preview",
            "host_connector",
        }:
            return CaptureResult(False, reason="El campo o la fuente no son válidos.")
        risk = sensitivity_of(value)
        if risk:
            return CaptureResult(
                False, reason="Ese dato parece delicado; no lo guardaré."
            )
        parsed = _as_number(value) if spec.numeric else str(value).strip()
        if parsed in (None, ""):
            return CaptureResult(False, reason="No pude interpretar ese valor.")
        ready = self.runtime.ensure_memory()
        if not ready.ready:
            return CaptureResult(
                False, reason=ready.reason or "No pude preparar la memoria local."
            )
        observed = observed_at or datetime.now(timezone.utc).date().isoformat()
        try:
            with sqlite3.connect(ready.db_path) as db:
                if source_id is None:
                    source_id = str(uuid4())
                    db.execute(
                        "INSERT INTO evidence_sources (id, source_type, source_ref, observed_at, allowed_scope, content_sha256) VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            source_id,
                            source_type,
                            _safe_source_ref(source_ref),
                            observed,
                            decision,
                            content_sha256,
                        ),
                    )
                prior = db.execute(
                    "SELECT id FROM methodology_values WHERE methodology=? AND field=? AND status='active'",
                    (spec.methodology, spec.key),
                ).fetchall()
                for (old_id,) in prior:
                    db.execute(
                        "UPDATE methodology_values SET status='superseded' WHERE id=?",
                        (old_id,),
                    )
                version = db.execute(
                    "SELECT COALESCE(MAX(version), 0) + 1 FROM methodology_values WHERE methodology=? AND field=?",
                    (spec.methodology, spec.key),
                ).fetchone()[0]
                value_id = str(uuid4())
                encoded = json.dumps(parsed, ensure_ascii=False)
                db.execute(
                    "INSERT INTO methodology_values (id, methodology, field, value_json, source_id, observed_at, confidence, version, status) VALUES (?, ?, ?, ?, ?, ?, 1.0, ?, 'active')",
                    (
                        value_id,
                        spec.methodology,
                        spec.key,
                        encoded,
                        source_id,
                        observed,
                        version,
                    ),
                )
                db.execute(
                    "INSERT INTO evidence_proposals (id, source_id, methodology, field, value_json, sensitivity, state, decided_at) VALUES (?, ?, ?, ?, ?, 'none', 'accepted', CURRENT_TIMESTAMP)",
                    (str(uuid4()), source_id, spec.methodology, spec.key, encoded),
                )
                db.commit()
            self._write_methodology_snapshot(ready.db_path, decision)
            return CaptureResult(True, source_id=source_id, value_id=value_id)
        except (sqlite3.Error, TypeError, ValueError) as error:
            return CaptureResult(False, reason=str(error))

    def reject_value(
        self, *, decision: str, field: str, source_type: str, source_ref: str
    ) -> bool:
        """Keep a rejection audit without storing the rejected raw value."""
        spec = next((item for item in field_specs(decision) if item.key == field), None)
        ready = self.runtime.ensure_memory()
        if spec is None or not ready.ready:
            return False
        try:
            with sqlite3.connect(ready.db_path) as db:
                source_id = str(uuid4())
                db.execute(
                    "INSERT INTO evidence_sources (id, source_type, source_ref, observed_at, allowed_scope) VALUES (?, ?, ?, ?, ?)",
                    (
                        source_id,
                        source_type,
                        _safe_source_ref(source_ref),
                        datetime.now(timezone.utc).date().isoformat(),
                        decision,
                    ),
                )
                db.execute(
                    "INSERT INTO evidence_proposals (id, source_id, methodology, field, value_json, sensitivity, state, decided_at) VALUES (?, ?, ?, ?, NULL, 'none', 'rejected', CURRENT_TIMESTAMP)",
                    (str(uuid4()), source_id, spec.methodology, spec.key),
                )
                db.commit()
            return True
        except sqlite3.Error:
            return False

    def snapshot(self, decision: str) -> dict[str, Any]:
        specs = field_specs(decision)
        result = {
            spec.key: {
                "label": spec.label,
                "methodology": spec.methodology,
                "state": "pending",
                "value": None,
                "source": None,
                "observed_at": None,
            }
            for spec in specs
        }
        ready = self.runtime.ensure_memory()
        if not ready.ready:
            return {"decision": decision, "fields": result, "ready": False}
        methodologies = tuple(dict.fromkeys(spec.methodology for spec in specs))
        placeholders = ",".join("?" for _ in methodologies)
        with sqlite3.connect(ready.db_path) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                f"SELECT values_.field, values_.value_json, values_.observed_at, values_.confidence, sources.source_type, sources.source_ref FROM methodology_values AS values_ JOIN evidence_sources AS sources ON sources.id=values_.source_id WHERE values_.methodology IN ({placeholders}) AND values_.status='active'",
                methodologies,
            ).fetchall()
        for row in rows:
            if row["field"] in result:
                try:
                    stale = (
                        datetime.now(timezone.utc).date()
                        - date.fromisoformat(str(row["observed_at"])[:10])
                    ).days > 180
                except ValueError:
                    stale = True
                result[row["field"]].update(
                    {
                        "state": "stale" if stale else "confirmed",
                        "value": json.loads(row["value_json"]),
                        "source": {
                            "type": row["source_type"],
                            "label": row["source_ref"],
                        },
                        "observed_at": row["observed_at"],
                        "confidence": row["confidence"],
                    }
                )
        return {"decision": decision, "fields": result, "ready": True}

    def _write_methodology_snapshot(self, db_path: Path, decision: str) -> None:
        """Expose accepted values to existing local dashboards without raw files."""
        snapshot = self.snapshot(decision)
        values = snapshot["fields"]
        if decision == "cash":
            variables = {
                key: {"current": item["value"], "adjusted": item["value"]}
                for key, item in values.items()
                if item["state"] == "confirmed"
            }
            payload: dict[str, Any] = {"variables": variables, "evidence": snapshot}
            tool, category = "power-of-one", "cash"
        else:
            payload = {"evidence": snapshot}
            tool, category = "evidence", decision
        with sqlite3.connect(db_path) as db:
            version = db.execute(
                "SELECT COALESCE(MAX(version), 0) + 1 FROM worksheets WHERE category=? AND tool=?",
                (category, tool),
            ).fetchone()[0]
            db.execute(
                "INSERT INTO worksheets (category, tool, data, version) VALUES (?, ?, ?, ?)",
                (category, tool, json.dumps(payload, ensure_ascii=False), version),
            )
            db.commit()


def _read_csv(path: Path) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = tuple(reader.fieldnames or ())
        if not headers:
            raise ValueError("el CSV no tiene encabezados")
        rows = tuple(
            {str(key): str(value or "") for key, value in row.items()}
            for row in list(reader)[:20]
        )
    return headers, rows


def _read_xlsx(path: Path) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(node.itertext()) for node in root.findall(f"{ns}si")]
        sheets = sorted(
            name
            for name in archive.namelist()
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
        )
        if not sheets:
            raise ValueError("el XLSX no contiene hojas")
        root = ElementTree.fromstring(archive.read(sheets[0]))
    matrix: list[list[str]] = []
    for row in root.findall(f".//{ns}sheetData/{ns}row"):
        cells: list[str] = []
        for cell in row.findall(f"{ns}c"):
            value = cell.find(f"{ns}v")
            raw = value.text if value is not None and value.text is not None else ""
            if cell.attrib.get("t") == "inlineStr":
                inline = cell.find(f"{ns}is")
                raw = "".join(inline.itertext()) if inline is not None else ""
            elif (
                cell.attrib.get("t") == "s" and raw.isdigit() and int(raw) < len(shared)
            ):
                raw = shared[int(raw)]
            cells.append(raw)
        matrix.append(cells)
        if len(matrix) >= 21:
            break
    if not matrix or not matrix[0]:
        raise ValueError("la primera hoja está vacía")
    headers = tuple(str(value).strip() for value in matrix[0])
    rows = tuple(
        {
            header: row[index] if index < len(row) else ""
            for index, header in enumerate(headers)
        }
        for row in matrix[1:]
    )
    return headers, rows
