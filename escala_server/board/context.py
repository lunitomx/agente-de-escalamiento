"""Build bounded, deterministic evidence packets from local E19 knowledge."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import CATEGORIES, CompanyFact, EvidencePacket, EvidenceRef

_TERMS = {
    "cash": ("cash", "cobro", "margen", "liquidez", "inventario", "precio"),
    "strategy": ("estrateg", "cliente", "marca", "swt", "swot", "prioridad"),
    "people": ("persona", "equipo", "talento", "rol", "cultura", "contratar"),
    "execution": ("ejec", "daily", "huddle", "reunion", "reunión", "kpi", "bloque"),
}


class PortableKnowledgeHandler:
    """Read the packaged YAML ontology through the same narrow context contract."""

    def __init__(self, knowledge_dir: str | None = None) -> None:
        root = Path(__file__).resolve().parents[2]
        candidates = [
            Path(knowledge_dir) if knowledge_dir else None,
            root / ".scaleup" / "knowledge",
            root / "knowledge",
        ]
        self.knowledge_dir = next((path for path in candidates if path is not None and path.is_dir()), root / "knowledge")

    def get_context(self, *, category: str) -> dict[str, object]:
        try:
            import yaml
        except ImportError:
            return {"status": "error", "message": "PyYAML no disponible"}
        entities: list[dict[str, object]] = []
        for path in sorted(self.knowledge_dir.rglob("*.yaml")):
            try:
                raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(raw, dict) or raw.get("decision") != category:
                continue
            source = raw.get("source") if isinstance(raw.get("source"), dict) else {}
            line = source.get("file_line") or source.get("workbook_line")
            line_refs = [line] if isinstance(line, int) else []
            entities.append({
                "name": str(raw.get("name") or raw.get("id") or ""),
                "type": str(raw.get("type") or "concept"),
                "properties": {
                    "description": str(raw.get("summary") or ""),
                    "line_refs": line_refs,
                    "chapter_ids": [],
                },
            })
        return {"status": "ok", "category": category, "entities": entities}


class BoardContextBuilder:
    """Uses only the injected local KnowledgeHandler; it never executes input."""

    def __init__(self, knowledge_handler: Any, *, evidence_limit: int = 6) -> None:
        if evidence_limit < 1:
            raise ValueError("evidence_limit must be positive")
        self.handler = knowledge_handler
        self.evidence_limit = evidence_limit

    def classify(self, text: str, category: str | None = None) -> str:
        if category is not None:
            if category not in CATEGORIES:
                raise ValueError("unknown board category")
            return category
        lower = text.casefold()
        scores = {name: sum(token in lower for token in tokens) for name, tokens in _TERMS.items()}
        return max(CATEGORIES, key=lambda name: (scores[name], name))

    def build(
        self,
        text: str,
        *,
        category: str | None = None,
        company_facts: list[CompanyFact] | None = None,
    ) -> EvidencePacket:
        selected = self.classify(text, category)
        facts = tuple(company_facts or [CompanyFact("company:input:0", text or "Sin dato empresarial.", selected)])
        gaps: list[str] = []
        warnings: list[str] = []
        evidence: list[EvidenceRef] = []
        try:
            result = self.handler.get_context(category=selected)
        except Exception:
            result = {"status": "error"}
            warnings.append("No se pudo consultar la evidencia local.")
        if result.get("status") != "ok":
            gaps.append("No hay evidencia local disponible para esta categoría.")
        else:
            seen: set[str] = set()
            for entity in result.get("entities", []):
                if not isinstance(entity, dict):
                    continue
                name = str(entity.get("name", "")).strip()
                props = entity.get("properties") or {}
                lines = tuple(int(value) for value in props.get("line_refs", []) if isinstance(value, int))
                chapters = tuple(int(value) for value in props.get("chapter_ids", []) if isinstance(value, int))
                if not name or name in seen or not lines:
                    continue
                seen.add(name)
                evidence.append(EvidenceRef(
                    id=f"e19:{name}",
                    entity_name=name,
                    entity_type=str(entity.get("type", "concept")),
                    description=str(props.get("description", ""))[:320],
                    line_refs=lines,
                    chapter_ids=chapters,
                    retrieved_by=f"category:{selected}",
                ))
                if len(evidence) >= self.evidence_limit:
                    break
        if not evidence:
            gaps.append("Falta evidencia trazable del conocimiento local; se limitarán las recomendaciones.")
        return EvidencePacket(
            schema_version="evidence-packet-v1",
            category=selected,
            company_facts=facts,
            source_evidence=tuple(evidence),
            gaps=tuple(dict.fromkeys(gaps)),
            warnings=tuple(dict.fromkeys(warnings)),
        )
