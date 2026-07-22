"""Fail-closed local workbook profiling for E38 S38.1.

Only structural/semantic metadata is exposed by receipts. Raw cells remain in
the in-memory profile so later E38 stories can derive figures without reading
the source a second time, but the receipt functions deliberately project them
out.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from escala_server.workspace.authority import WorkspaceConfig, validate_workspace
from escala_server.workspace.ingestion import (
    SourceIdentity,
    SourceIngestionError,
    SourceRegistry,
    build_source_identity,
)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


MappingTarget = Literal[
    "revenue",
    "cogs",
    "opex",
    "net_profit",
    "cash",
    "accounts_receivable",
    "inventory",
    "accounts_payable",
    "assets",
    "liabilities",
    "operating_cash_flow",
    "investing_cash_flow",
    "financing_cash_flow",
    "opening_cash",
    "closing_cash",
]
ProfileStatus = Literal[
    "ready", "needs_clarification", "unsupported", "provider_unavailable", "corrupt"
]
MappingStatus = Literal["resolved", "unresolved"]


class RawCell(_StrictModel):
    address: str = Field(min_length=1, max_length=32)
    value: str = ""
    formula: str | None = None
    cached_value: str | None = None


class RawSheet(_StrictModel):
    name: str = Field(min_length=1, max_length=120)
    rows: tuple[tuple[RawCell, ...], ...] = ()


class FinancialSheetProfile(_StrictModel):
    name: str = Field(min_length=1, max_length=120)
    table_range: str = Field(min_length=1, max_length=80)
    header_row: int = Field(ge=0)
    headers: tuple[str, ...] = ()
    row_count: int = Field(ge=0)
    column_count: int = Field(ge=0)
    periods: tuple[str, ...] = ()
    currencies: tuple[str, ...] = ()
    units: tuple[str, ...] = ()
    formula_count: int = Field(ge=0)
    formula_without_cached_value_count: int = Field(ge=0)


class MappingCandidate(_StrictModel):
    candidate_id: str = Field(pattern=r"^cand-[0-9a-f]{16}$")
    target: MappingTarget
    sheet: str = Field(min_length=1, max_length=120)
    row_index: int = Field(ge=0)
    label: str = Field(min_length=1, max_length=120)
    cell_range: str = Field(min_length=1, max_length=80)
    value_columns: tuple[int, ...] = ()
    score: float = Field(ge=0, le=1)
    confidence: Literal["high", "medium", "low"]


class MappingQuestion(_StrictModel):
    code: Literal["mapping_ambiguous", "mapping_missing"]
    target: MappingTarget
    prompt: str = Field(min_length=1, max_length=240)
    options: tuple[str, ...] = Field(min_length=2, max_length=5)


class MappingAnswer(_StrictModel):
    target: MappingTarget
    candidate_id: str = Field(pattern=r"^cand-[0-9a-f]{16}$")


class FinancialWorkbookProfile(_StrictModel):
    schema_version: Literal[1] = 1
    identity: SourceIdentity
    status: ProfileStatus
    mapping_status: MappingStatus
    sheets: tuple[FinancialSheetProfile, ...] = ()
    mapping_candidates: tuple[MappingCandidate, ...] = ()
    questions: tuple[MappingQuestion, ...] = ()
    findings: tuple[str, ...] = ()
    raw_sheets: tuple[RawSheet, ...] = ()


_PERIOD_RE = re.compile(r"^(?:20\d{2}[-/]\d{1,2}|20\d{2}[-/]\d{1,2}[-/]\d{1,2})$")
_CURRENCY_ALIASES = {"mxn", "usd", "eur", "gbp", "cad", "m$", "$", "€", "£"}
_UNIT_ALIASES = {
    "pesos",
    "peso",
    "miles",
    "millones",
    "units",
    "unidad",
    "%",
    "porcentaje",
}
_REQUIRED_TARGETS: tuple[MappingTarget, ...] = (
    "revenue",
    "cogs",
    "opex",
    "net_profit",
    "cash",
    "accounts_receivable",
    "inventory",
    "accounts_payable",
)
_ALIASES: dict[MappingTarget, tuple[str, ...]] = {
    "revenue": ("ventas netas", "ventas", "ingresos", "revenue", "sales"),
    "cogs": ("costo de ventas", "costo de venta", "cogs", "cost of goods sold"),
    "opex": ("gastos operativos", "gastos de operacion", "opex", "overheads", "gastos"),
    "net_profit": (
        "utilidad neta",
        "utilidad",
        "net profit",
        "net income",
        "ganancia neta",
    ),
    "cash": ("caja", "efectivo", "cash", "cash balance", "bancos"),
    "accounts_receivable": (
        "cuentas por cobrar",
        "clientes",
        "accounts receivable",
        "ar",
    ),
    "inventory": ("inventario", "inventory", "existencias"),
    "accounts_payable": ("cuentas por pagar", "proveedores", "accounts payable", "ap"),
    "assets": ("activos", "total assets", "assets"),
    "liabilities": ("pasivos", "total liabilities", "liabilities"),
    "operating_cash_flow": ("flujo operativo", "operating cash flow", "cfo"),
    "investing_cash_flow": ("flujo de inversion", "investing cash flow", "cfi"),
    "financing_cash_flow": ("flujo de financiamiento", "financing cash flow", "cff"),
    "opening_cash": ("caja inicial", "opening cash", "saldo inicial"),
    "closing_cash": ("caja final", "closing cash", "saldo final"),
}


def profile_financial_workbook(
    config: WorkspaceConfig,
    source_path: Path,
) -> FinancialWorkbookProfile:
    """Profile a local workbook and expose questions before calculations."""

    if validate_workspace(config).status != "pass":
        raise SourceIngestionError("workspace_invalid")
    registry = SourceRegistry.default()
    identity = build_source_identity(
        source_path, config.exchange_root, registry=registry
    )
    capability = registry.capability_for(source_path)
    if capability.status == "unsupported":
        return _empty_profile(identity, "unsupported", ("format_unsupported",))
    if capability.status == "provider_unavailable":
        return _empty_profile(
            identity, "provider_unavailable", ("provider_unavailable",)
        )
    try:
        sheets = _read_sheets(source_path, capability.format)
    except (
        OSError,
        UnicodeDecodeError,
        csv.Error,
        BadZipFile,
        ET.ParseError,
        KeyError,
        ValueError,
    ):
        return _empty_profile(identity, "corrupt", ("source_unreadable",))
    if not sheets or all(not sheet.rows for sheet in sheets):
        return _empty_profile(identity, "corrupt", ("source_empty",))

    profiles = tuple(_profile_sheet(sheet) for sheet in sheets)
    candidates = tuple(
        candidate
        for sheet in sheets
        for candidate in _mapping_candidates(identity, sheet)
    )
    questions = _mapping_questions(candidates)
    findings: set[str] = set()
    if any(
        sheet.formula and sheet.cached_value is None
        for raw in sheets
        for row in raw.rows
        for sheet in row
    ):
        findings.add("formula_without_cached_value")
    if any(profile.formula_without_cached_value_count for profile in profiles):
        findings.add("formula_without_cached_value")
    status: ProfileStatus = "needs_clarification" if questions else "ready"
    return FinancialWorkbookProfile(
        identity=identity,
        status=status,
        mapping_status="unresolved" if questions else "resolved",
        sheets=profiles,
        mapping_candidates=candidates,
        questions=questions,
        findings=tuple(sorted(findings)),
        raw_sheets=tuple(sheets),
    )


def resolve_mapping_answers(
    profile: FinancialWorkbookProfile,
    answers: tuple[MappingAnswer, ...],
) -> FinancialWorkbookProfile:
    """Apply only owner-selected candidate IDs and return an immutable profile."""

    answer_by_target = {answer.target: answer.candidate_id for answer in answers}
    valid_ids = {candidate.candidate_id for candidate in profile.mapping_candidates}
    if any(candidate_id not in valid_ids for candidate_id in answer_by_target.values()):
        raise ValueError("mapping_answer_candidate_unknown")
    remaining: list[MappingQuestion] = []
    for question in profile.questions:
        selected = answer_by_target.get(question.target)
        if selected is None or selected not in question.options:
            remaining.append(question)
    status: ProfileStatus = "needs_clarification" if remaining else "ready"
    return profile.model_copy(
        update={
            "status": status,
            "mapping_status": "unresolved" if remaining else "resolved",
            "questions": tuple(remaining),
        }
    )


def render_profile_receipt_json(profile: FinancialWorkbookProfile) -> str:
    """Render deterministic metadata only; never raw cell values or paths."""

    return json.dumps(
        _receipt_payload(profile),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def render_profile_receipt_markdown(profile: FinancialWorkbookProfile) -> str:
    """Render a human-readable redacted profile receipt."""

    lines = [
        "# Financial Workbook Profile Receipt",
        "",
        f"- status: {profile.status}",
        f"- mapping_status: {profile.mapping_status}",
        f"- relative_path: {profile.identity.relative_path}",
        f"- source_id: {profile.identity.source_id}",
        "",
        "## Findings",
    ]
    lines.extend(f"- {finding}" for finding in profile.findings) or lines.append(
        "- none"
    )
    lines.extend(["", "## Questions"])
    if profile.questions:
        lines.extend(
            f"- {question.target}: {question.code} ({', '.join(question.options)})"
            for question in profile.questions
        )
    else:
        lines.append("- none")
    lines.extend(["", "## Sheets"])
    for sheet in profile.sheets:
        lines.append(
            f"- {sheet.name}: rows={sheet.row_count}, columns={sheet.column_count}, "
            f"periods={','.join(sheet.periods) or 'unknown'}, currencies={','.join(sheet.currencies) or 'unknown'}, "
            f"units={','.join(sheet.units) or 'unknown'}, formulas={sheet.formula_count}"
        )
    return "\n".join(lines) + "\n"


def _empty_profile(
    identity: SourceIdentity, status: ProfileStatus, findings: tuple[str, ...]
) -> FinancialWorkbookProfile:
    return FinancialWorkbookProfile(
        identity=identity, status=status, mapping_status="unresolved", findings=findings
    )


def _read_sheets(source_path: Path, format_name: str) -> list[RawSheet]:
    if format_name in {"csv", "tsv"}:
        raw = source_path.read_bytes().decode("utf-8-sig")
        delimiter = "\t" if format_name == "tsv" else ","
        rows = list(csv.reader(io.StringIO(raw), delimiter=delimiter))
        return [_raw_sheet(source_path.stem, rows)]
    if format_name == "xlsx":
        return _read_xlsx(source_path)
    raise ValueError("format_not_supported")


def _raw_sheet(name: str, rows: list[list[str]]) -> RawSheet:
    converted: list[tuple[RawCell, ...]] = []
    for row_index, row in enumerate(rows, start=1):
        cells: list[RawCell] = []
        for column_index, value in enumerate(row):
            address = f"{_column_name(column_index)}{row_index}"
            if value.startswith("="):
                cells.append(RawCell(address=address, formula=value[1:], value=""))
            else:
                cells.append(RawCell(address=address, value=value, cached_value=value))
        converted.append(tuple(cells))
    return RawSheet(name=name, rows=tuple(converted))


def _read_xlsx(source_path: Path) -> list[RawSheet]:
    with ZipFile(source_path) as archive:
        shared = _shared_strings(archive)
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        relation_targets = {
            relation.attrib["Id"]: relation.attrib["Target"]
            for relation in rels
            for _ in [0]
        }
        result: list[RawSheet] = []
        for sheet in workbook.iter():
            if _xml_local(sheet.tag) != "sheet":
                continue
            name = sheet.attrib.get("name", "Sheet")
            relation_id = next(
                (
                    value
                    for key, value in sheet.attrib.items()
                    if key.rsplit("}", 1)[-1] == "id"
                ),
                "",
            )
            target = relation_targets.get(relation_id, "")
            sheet_path = "xl/" + target.lstrip("/")
            result.append(_xlsx_sheet(name, archive.read(sheet_path), shared))
        if not result:
            raise ValueError("xlsx_no_sheets")
        return result


def _shared_strings(archive: ZipFile) -> tuple[str, ...]:
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return ()
    values: list[str] = []
    for item in root.iter():
        if _xml_local(item.tag) == "si":
            values.append(
                "".join(
                    (child.text or "")
                    for child in item.iter()
                    if _xml_local(child.tag) == "t"
                )
            )
    return tuple(values)


def _xlsx_sheet(name: str, payload: bytes, shared: tuple[str, ...]) -> RawSheet:
    root = ET.fromstring(payload)
    rows: list[list[str]] = []
    formula_cells: dict[str, tuple[str, str | None]] = {}
    for row_element in root.iter():
        if _xml_local(row_element.tag) != "row":
            continue
        cells: dict[int, str] = {}
        for cell in row_element:
            if _xml_local(cell.tag) != "c":
                continue
            coordinate = cell.attrib.get("r", "")
            match = re.match(r"([A-Za-z]+)", coordinate)
            if not match:
                continue
            index = _column_index(match.group(1))
            value_element = next(
                (child for child in cell if _xml_local(child.tag) == "v"), None
            )
            raw_value = value_element.text if value_element is not None else None
            if cell.attrib.get("t") == "s" and raw_value is not None:
                value = shared[int(raw_value)] if int(raw_value) < len(shared) else ""
            elif cell.attrib.get("t") == "inlineStr":
                value = "".join(
                    (child.text or "")
                    for child in cell.iter()
                    if _xml_local(child.tag) == "t"
                )
            else:
                value = raw_value or ""
            formula_element = next(
                (child for child in cell if _xml_local(child.tag) == "f"), None
            )
            if formula_element is not None:
                formula = formula_element.text or ""
                formula_cells[coordinate] = (formula, raw_value)
            cells[index] = value
        if cells:
            rows.append([cells.get(index, "") for index in range(max(cells) + 1)])
    raw_sheet = _raw_sheet(name, rows)
    updated_rows: list[tuple[RawCell, ...]] = []
    for row in raw_sheet.rows:
        updated: list[RawCell] = []
        for cell in row:
            formula_data = formula_cells.get(cell.address)
            if formula_data is None:
                updated.append(cell)
            else:
                formula, cached = formula_data
                updated.append(
                    RawCell(
                        address=cell.address,
                        value=cached or "",
                        formula=formula,
                        cached_value=cached,
                    )
                )
        updated_rows.append(tuple(updated))
    return raw_sheet.model_copy(update={"rows": tuple(updated_rows)})


def _profile_sheet(sheet: RawSheet) -> FinancialSheetProfile:
    row_values = [[cell.value for cell in row] for row in sheet.rows]
    header_index = _header_index(row_values)
    headers = tuple(
        value.strip() for value in (row_values[header_index] if row_values else [])
    )
    periods = _unique_tokens(
        value
        for row in row_values
        for value in row
        if _PERIOD_RE.fullmatch(value.strip())
    )
    currencies = _unique_tokens(
        value.upper()
        for row in row_values
        for value in row
        if _normalize(value) in _CURRENCY_ALIASES
    )
    units = _unique_tokens(
        value.casefold()
        for row_index, row in enumerate(row_values)
        if row_index != header_index
        for value in row
        if _normalize(value) in {_normalize(token) for token in _UNIT_ALIASES}
    )
    formula_count = sum(1 for row in sheet.rows for cell in row if cell.formula)
    missing = sum(
        1
        for row in sheet.rows
        for cell in row
        if cell.formula and cell.cached_value is None
    )
    column_count = max((len(row) for row in sheet.rows), default=0)
    end = f"{_column_name(max(column_count - 1, 0))}{len(sheet.rows)}"
    return FinancialSheetProfile(
        name=sheet.name,
        table_range=f"A1:{end}",
        header_row=header_index,
        headers=headers,
        row_count=len(sheet.rows),
        column_count=column_count,
        periods=periods,
        currencies=currencies,
        units=units,
        formula_count=formula_count,
        formula_without_cached_value_count=missing,
    )


def _mapping_candidates(
    identity: SourceIdentity, sheet: RawSheet
) -> list[MappingCandidate]:
    candidates: list[MappingCandidate] = []
    for row_index, row in enumerate(sheet.rows):
        if not row or not row[0].value.strip():
            continue
        label = row[0].value.strip()
        normalized = _normalize(label)
        for target, aliases in _ALIASES.items():
            score = _alias_score(normalized, aliases)
            if score <= 0:
                continue
            candidate_id = (
                "cand-"
                + hashlib.sha256(
                    f"{identity.source_id}\0{sheet.name}\0{row_index}\0{target}".encode(
                        "utf-8"
                    )
                ).hexdigest()[:16]
            )
            candidates.append(
                MappingCandidate(
                    candidate_id=candidate_id,
                    target=target,
                    sheet=sheet.name,
                    row_index=row_index,
                    label=label,
                    cell_range=f"{sheet.name}!A{row_index + 1}:{_column_name(max(len(row) - 1, 1))}{row_index + 1}",
                    value_columns=tuple(
                        index
                        for index, cell in enumerate(row[1:], start=1)
                        if cell.value or cell.formula
                    ),
                    score=score,
                    confidence="high"
                    if score >= 0.95
                    else "medium"
                    if score >= 0.75
                    else "low",
                )
            )
    return candidates


def _mapping_questions(
    candidates: tuple[MappingCandidate, ...],
) -> tuple[MappingQuestion, ...]:
    questions: list[MappingQuestion] = []
    for target in _REQUIRED_TARGETS:
        options = tuple(
            candidate.candidate_id
            for candidate in candidates
            if candidate.target == target
        )
        ranked = sorted(
            (candidate for candidate in candidates if candidate.target == target),
            key=lambda candidate: (-candidate.score, candidate.candidate_id),
        )
        if len(ranked) > 1 and ranked[0].score == ranked[1].score:
            questions.append(
                MappingQuestion(
                    code="mapping_ambiguous",
                    target=target,
                    prompt=f"¿Cuál fila representa {target}?",
                    options=tuple(candidate.candidate_id for candidate in ranked[:5]),
                )
            )
        elif options and ranked[0].score < 0.75:
            questions.append(
                MappingQuestion(
                    code="mapping_ambiguous",
                    target=target,
                    prompt=f"Confirma la fila para {target}.",
                    options=options[:5],
                )
            )
    return tuple(questions)


def _alias_score(normalized: str, aliases: tuple[str, ...]) -> float:
    normalized_aliases = tuple(_normalize(alias) for alias in aliases)
    if normalized in normalized_aliases:
        return 1.0
    if any(
        alias in normalized or normalized in alias
        for alias in normalized_aliases
        if len(alias) > 3
    ):
        return 0.75
    return 0.0


def _header_index(rows: list[list[str]]) -> int:
    if not rows:
        return 0
    scored = [
        (
            index,
            sum(
                1
                for value in row
                if _PERIOD_RE.fullmatch(value.strip())
                or _normalize(value) in _ALIASES["revenue"]
            ),
        )
        for index, row in enumerate(rows[:10])
    ]
    return max(scored, key=lambda item: (item[1], -item[0]))[0]


def _receipt_payload(profile: FinancialWorkbookProfile) -> dict[str, object]:
    return {
        "schema_version": profile.schema_version,
        "status": profile.status,
        "mapping_status": profile.mapping_status,
        "identity": profile.identity.model_dump(mode="json"),
        "findings": profile.findings,
        "questions": tuple(
            question.model_dump(mode="json") for question in profile.questions
        ),
        "sheets": tuple(sheet.model_dump(mode="json") for sheet in profile.sheets),
        "mapping_candidates": tuple(
            candidate.model_dump(mode="json")
            for candidate in profile.mapping_candidates
        ),
    }


def _unique_tokens(values: object) -> tuple[str, ...]:
    seen: list[str] = []
    for value in values:  # type: ignore[union-attr]
        if value and value not in seen:
            seen.append(value)
    return tuple(seen)


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(
        char for char in normalized if not unicodedata.combining(char)
    ).strip()


def _column_name(index: int) -> str:
    value = index + 1
    result = ""
    while value:
        value, remainder = divmod(value - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def _column_index(letters: str) -> int:
    index = 0
    for letter in letters.upper():
        index = index * 26 + ord(letter) - ord("A") + 1
    return index - 1


def _xml_local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
