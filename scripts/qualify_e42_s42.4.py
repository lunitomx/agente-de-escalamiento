#!/usr/bin/env python3
"""Build the E42 S42.4 functional catalog from S42.1-S42.3 evidence.

This script reads the evidence produced by S42.1, S42.2 and S42.3, builds a
unified skill inventory, and writes a Spanish markdown catalog plus a simple
PDF if a suitable PDF generation library is already installed.  When no PDF
generator is available it writes markdown only and reports the dependency gap.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EVIDENCE_DIR = ROOT / "work/epics/e42-product-qualification-and-functional-catalog/evidence"
SKILLS_DIR = ROOT / "escala-skills"
CATALOG_PATH = EVIDENCE_DIR / "catalog.md"
CATALOG_PDF_PATH = EVIDENCE_DIR / "catalog.pdf"

# Evidence files this catalog consumes.
EVIDENCE_FILES = {
    "S42.1": EVIDENCE_DIR / "s42.1-local-journey.json",
    "S42.2": EVIDENCE_DIR / "s42.2-skill-inventory.json",
    "S42.3": EVIDENCE_DIR / "s42.3-security-recovery.json",
}


@dataclass(frozen=True)
class SkillEntry:
    """A single skill as discovered from S42.2 evidence or escala-skills/."""

    id: str
    name: str
    description: str
    business_problem: str | None
    required_info: list[str]
    delivered_result: str | None
    positive_case: str | None
    negative_case: str | None
    demonstrated: bool
    demonstration_method: str


def main() -> int:
    source_commit = _source_commit()
    evidence = _load_evidence()

    # Determine overall qualification state from available evidence.
    s42_1 = evidence.get("S42.1")
    s42_2 = evidence.get("S42.2")
    s42_3 = evidence.get("S42.3")

    skills = _build_skill_inventory(s42_2)

    catalog = _render_catalog(
        source_commit=source_commit,
        s42_1=s42_1,
        s42_2=s42_2,
        s42_3=s42_3,
        skills=skills,
    )

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    CATALOG_PATH.write_text(catalog, encoding="utf-8")
    print(f"S42.4 catalog written: {CATALOG_PATH}")

    pdf_result = _maybe_generate_pdf(catalog)
    if pdf_result == "generated":
        print(f"S42.4 PDF written: {CATALOG_PDF_PATH}")
    else:
        print(f"S42.4 PDF not generated: {pdf_result}")

    receipt = {
        "schema_version": 1,
        "story": "S42.4",
        "epic": "E42",
        "source_commit": source_commit,
        "catalog_path": str(CATALOG_PATH.relative_to(ROOT)),
        "pdf_path": (
            str(CATALOG_PDF_PATH.relative_to(ROOT))
            if pdf_result == "generated"
            else None
        ),
        "pdf_status": pdf_result,
        "evidence_loaded": {k: v is not None for k, v in evidence.items()},
        "skill_count": len(skills),
        "overall_status": _overall_status(s42_1, s42_2, s42_3),
    }
    receipt_path = EVIDENCE_DIR / "s42.4-catalog-receipt.json"
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"S42.4 receipt written: {receipt_path}")
    return 0


def _load_evidence() -> dict[str, dict[str, object] | None]:
    """Load S42.1-S42.3 evidence where it exists; missing files return None."""
    loaded: dict[str, dict[str, object] | None] = {}
    for story, path in EVIDENCE_FILES.items():
        if path.exists():
            loaded[story] = json.loads(path.read_text(encoding="utf-8"))
        else:
            loaded[story] = None
    return loaded


def _build_skill_inventory(
    s42_2: dict[str, object] | None,
) -> list[SkillEntry]:
    """Return skill entries from S42.2 evidence, or fall back to escala-skills/."""
    inventory = _inventory_from_s42_2(s42_2)
    if inventory:
        return inventory
    return _inventory_from_filesystem()


def _inventory_from_s42_2(
    s42_2: dict[str, object] | None,
) -> list[SkillEntry]:
    """Parse the S42.2 inventory list when available."""
    if s42_2 is None:
        return []
    raw_inventory = s42_2.get("inventory")
    if not isinstance(raw_inventory, list):
        return []
    skills: list[SkillEntry] = []
    for raw in raw_inventory:
        if not isinstance(raw, dict):
            continue
        skill_id = str(raw.get("id", ""))
        if not skill_id:
            continue
        skills.append(
            SkillEntry(
                id=skill_id,
                name=str(raw.get("id", skill_id)),
                description=str(raw.get("description", "")),
                business_problem=_as_string_or_none(raw.get("business_problem")),
                required_info=_as_string_list(raw.get("required_info")),
                delivered_result=_as_string_or_none(raw.get("delivered_result")),
                positive_case=_as_string_or_none(raw.get("positive_case")),
                negative_case=_as_string_or_none(raw.get("negative_case")),
                demonstrated=bool(raw.get("demonstrated", False)),
                demonstration_method=str(raw.get("demonstration_method", "not-invoked")),
            )
        )
    return skills


def _inventory_from_filesystem() -> list[SkillEntry]:
    """Discover skills under escala-skills/ from SKILL.md front matter."""
    skills: list[SkillEntry] = []
    if not SKILLS_DIR.is_dir():
        return skills
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue
        text = skill_file.read_text(encoding="utf-8")
        description = _front_matter_value(text, "description") or _first_heading_paragraph(text) or "Skill descubierto"
        skills.append(
            SkillEntry(
                id=skill_dir.name,
                name=skill_dir.name,
                description=description,
                business_problem=None,
                required_info=[],
                delivered_result=None,
                positive_case=None,
                negative_case=None,
                demonstrated=False,
                demonstration_method="not-invoked",
            )
        )
    return skills


def _front_matter_value(text: str, key: str) -> str | None:
    """Return a simple `key: value` front-matter value, if present."""
    for line in text.splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def _first_heading_paragraph(text: str) -> str | None:
    """Return the first paragraph after the first markdown heading."""
    lines = text.splitlines()
    after_heading = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            after_heading = True
            continue
        if after_heading:
            if stripped == "":
                continue
            if stripped.startswith("#"):
                return None
            return stripped
    return None


def _as_string_or_none(value: object) -> str | None:
    """Coerce a JSON value to string or None."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _as_string_list(value: object) -> list[str]:
    """Coerce a JSON value to a list of strings."""
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]


def _overall_status(
    s42_1: dict[str, object] | None,
    s42_2: dict[str, object] | None,
    s42_3: dict[str, object] | None,
) -> str:
    """Best-effort status: pass only when all three evidence files pass."""
    statuses: list[str] = []
    for evidence in (s42_1, s42_2, s42_3):
        if evidence is None:
            statuses.append("missing")
        else:
            statuses.append(str(evidence.get("overall_status", "unknown")))
    if all(status == "pass" for status in statuses):
        return "pass"
    if "missing" in statuses:
        return "incomplete"
    return "fail"


def _platform_text(platform_matrix: object) -> str:
    """Render platform matrix as a readable string (dict keys or list items)."""
    if isinstance(platform_matrix, dict):
        names = sorted(platform_matrix.keys())
        return ", ".join(str(name) for name in names) if names else "pendiente"
    if isinstance(platform_matrix, list):
        return ", ".join(str(p) for p in platform_matrix) if platform_matrix else "pendiente"
    return "pendiente"


def _render_catalog(
    source_commit: str,
    s42_1: dict[str, object] | None,
    s42_2: dict[str, object] | None,
    s42_3: dict[str, object] | None,
    skills: list[SkillEntry],
) -> str:
    """Render the Spanish markdown catalog."""
    lines: list[str] = [
        "# Catálogo funcional de ESCALA",
        "",
        f"- **Épica:** E42 — Producto probado y catálogo verdadero",
        f"- **Historia:** S42.4 — Catálogo, PDF y aceptación humana",
        f"- **Commit fuente:** `{source_commit}`",
        f"- **Generado:** automáticamente desde la evidencia de S42.1, S42.2 y S42.3",
        "",
        "> Este documento traduce la evidencia técnica a lenguaje de negocio. Cada afirmación enlaza con el recibo de evidencia que la respalda. La aceptación humana requisito por requisito se registra aparte.",
        "",
        "---",
        "",
        "## 1. ¿Qué hace ESCALA?",
        "",
    ]

    # Summary from S42.1.
    if s42_1:
        overall = s42_1.get("overall_status", "unknown")
        environment = s42_1.get("environment", "desconocido")
        platform_text = _platform_text(s42_1.get("platform_matrix"))
        lines.extend(
            [
                "ESCALA guía a una empresa a través de ocho pasos locales: instalación, creación del espacio de trabajo, ingreso de documentos, análisis de reuniones, análisis Cash, preguntas de Strategy, cockpit ejecutivo y acción con seguimiento.",
                "",
                f"- **Estado del recorrido (S42.1):** {overall}",
                f"- **Entorno de la prueba:** {environment}",
                f"- **Matriz de plataforma:** {platform_text}",
                "",
                "**Evidencia:** `evidence/s42.1-local-journey.json`",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "El recorrido completo aún no ha sido cualificado. La evidencia de S42.1 es necesaria para completar esta sección.",
                "",
                "**Evidencia:** pendiente (`evidence/s42.1-local-journey.json`)",
                "",
            ]
        )

    lines.extend(
        [
            "## 2. Catálogo de funcionalidades",
            "",
            "| Funcionalidad | ¿Qué resuelve? | Evidencia | Estado |",
            "|---|---|---|---|",
        ]
    )

    rows: list[str] = []

    # Functional rows derived from S42.1 journey_steps.
    journey_steps = s42_1.get("journey_steps") if s42_1 else None
    if isinstance(journey_steps, list):
        for step in journey_steps:
            if isinstance(step, dict):
                step_id = step.get("id", "paso")
                description = step.get("description", "Paso del recorrido")
                status = step.get("status", "unknown")
                rows.append(
                    f"| {step_id} | {description} | S42.1 | {status} |"
                )

    # Skill rows derived from S42.2 or the live inventory.
    skill_source = "S42.2" if s42_2 else "inventario local"
    for skill in skills:
        problem = skill.business_problem or skill.description
        # Keep table cells compact; replace newlines.
        problem_inline = " ".join(str(problem).split())
        demonstrated = "demostrado" if skill.demonstrated else "pendiente"
        rows.append(
            f"| `{skill.id}` | {problem_inline} | {skill_source} | {demonstrated} |"
        )

    if not rows:
        rows.append("| — | — | — | pendiente |")

    lines.extend(rows)
    lines.append("")

    # Negative cases from S42.1.
    negative_cases = s42_1.get("negative_cases") if s42_1 else None
    if isinstance(negative_cases, list) and negative_cases:
        lines.extend(
            [
                "### Casos negativos verificados",
                "",
                "| Caso | Resultado esperado | Estado |",
                "|---|---|---|",
            ]
        )
        for case in negative_cases:
            if isinstance(case, dict):
                case_id = case.get("id", "caso")
                expected = case.get("expected", "—")
                status = case.get("status", "unknown")
                lines.append(f"| {case_id} | {expected} | {status} |")
        lines.append("")

    # Security / recovery rows from S42.3.
    lines.extend(
        [
            "## 3. Seguridad y recuperación",
            "",
            "| Escenario | Mensaje de negocio | Estado |",
            "|---|---|---|",
        ]
    )
    scenarios = s42_3.get("scenarios") if s42_3 else None
    if isinstance(scenarios, list):
        for scenario in scenarios:
            if isinstance(scenario, dict):
                scenario_id = scenario.get("id", "escenario")
                message = scenario.get("business_message", scenario.get("expected", "—"))
                status = scenario.get("status", "unknown")
                lines.append(f"| {scenario_id} | {message} | {status} |")
    else:
        lines.append("| Escenarios de seguridad y recuperación | Resultado comprensible y recuperable, sin pérdida de datos locales | pendiente |")
    lines.append("")

    # Requirements mapping.
    requirements = s42_1.get("requirements") if s42_1 else None
    if isinstance(requirements, list) and requirements:
        lines.extend(
            [
                "## 4. Cumplimiento de requisitos",
                "",
                "| Requisito | Descripción | Estado | Evidencia |",
                "|---|---|---|---|",
            ]
        )
        for req in requirements:
            if isinstance(req, dict):
                req_id = req.get("id", "REQ-?")
                description = req.get("description", "—")
                status = req.get("status", "unknown")
                evidence = req.get("evidence", "—")
                lines.append(f"| {req_id} | {description} | {status} | {evidence} |")
        lines.append("")

    lines.extend(
        [
            "## 5. ¿Qué archivos necesita?",
            "",
            "ESCALA trabaja con archivos locales y opcionalmente con una carpeta de intercambio de documentos:",
            "",
            "- **Documentos de la empresa:** workbooks, actas, datos financieros (se ingresan en la carpeta de intercambio o se cargan localmente).",
            "- **Estado local:** base de datos SQLite y archivos de configuración en el directorio de datos elegido por el usuario.",
            "- **Artefactos de evidencia:** los recibos de S42.1, S42.2 y S42.3 en `work/epics/e42-product-qualification-and-functional-catalog/evidence/`.",
            "",
            "> La carpeta compartida solo puede contener documentos; nunca se convierte en autoridad de datos.",
            "",
            "## 6. Limitaciones conocidas",
            "",
        ]
    )

    limitations: list[str] = []
    if s42_1 is None:
        limitations.append("El recorrido completo aún no ha sido registrado (falta evidencia S42.1).")
    if s42_2 is None:
        limitations.append("El inventario de skills aún no ha sido probado con invocaciones reales (falta evidencia S42.2).")
    if s42_3 is None:
        limitations.append("Los escenarios de seguridad y recuperación aún no han sido ejecutados (falta evidencia S42.3).")
    if not skills:
        limitations.append("No se encontró ningún skill en `escala-skills/`.")

    # Surface S42.1 blockers as limitations.
    blockers = s42_1.get("blockers") if s42_1 else None
    if isinstance(blockers, list) and blockers:
        for blocker in blockers:
            limitations.append(f"Bloqueo en S42.1: {blocker}")

    # Surface S42.2 duplicates as limitations.
    duplicates = s42_2.get("duplicates") if s42_2 else None
    if isinstance(duplicates, list) and duplicates:
        for dup in duplicates:
            if isinstance(dup, dict):
                skills_dup = dup.get("skills", "")
                reason = dup.get("reason", "")
                limitations.append(f"Skill posiblemente duplicado: {skills_dup} ({reason}).")

    if not limitations:
        limitations.append("Ninguna limitación registrada en la evidencia disponible.")

    for limitation in limitations:
        lines.append(f"- {limitation}")
    lines.append("")

    # External validation note.
    external = s42_1.get("external_validation") if s42_1 else None
    if isinstance(external, dict):
        lines.extend(
            [
                "## 7. Validación externa pendiente",
                "",
                "Las siguientes validaciones no pueden completarse con pruebas automáticas:",
                "",
            ]
        )
        for key, value in external.items():
            if key == "reason":
                continue
            lines.append(f"- **{key}:** {value}")
        reason = external.get("reason")
        if reason:
            lines.extend(["", f"*Razón: {reason}*"])
        lines.append("")

    lines.extend(
        [
            "## 8. Privacidad y datos locales",
            "",
            "- Toda la información de la empresa permanece en la máquina local.",
            "- No se sincroniza la base de datos SQLite como autoridad compartida.",
            "- El catálogo y el PDF no incluyen datos reales de empresa ni materiales protegidos.",
            "- Las pruebas usan datos sintéticos o redactados.",
            "",
            "## 9. Checklist de aceptación humana",
            "",
            "El dueño del producto debe revisar y aceptar o registrar reservas para cada requisito:",
            "",
            "- [ ] REQ-E42-005: El catálogo coincide con la evidencia y el inventario.",
            "- [ ] REQ-E42-005: El PDF (cuando se genere) no menciona fuentes privadas o materiales prohibidos.",
            "- [ ] REQ-E42-005: Las limitaciones se explican sin lenguaje técnico innecesario.",
            "- [ ] REQ-E42-006: Auditoría final completada.",
            "- [ ] REQ-E42-006: Aceptación explícita requisito por requisito registrada.",
            "",
            "---",
            "",
            "*Este catálogo fue generado automáticamente. No sustituye la aceptación humana.*",
        ]
    )

    return "\n".join(lines)


def _maybe_generate_pdf(markdown_text: str) -> str:
    """Generate a simple PDF if a suitable library is available.

    Returns a short status string: "generated" or the reason PDF was skipped.
    """
    # pypdfium2 is read-only; skip it.  Accept only well-known generators.
    candidates = ["fpdf", "reportlab", "fpdf2"]
    available: str | None = None
    for name in candidates:
        try:
            __import__(name)
            available = name
            break
        except ImportError:
            continue
    if available is None:
        return "no pdf generation library installed (fpdf/reportlab/fpdf2)"

    if available in {"fpdf", "fpdf2"}:
        try:
            from fpdf import FPDF  # type: ignore[import-untyped]
        except ImportError:
            return "fpdf import failed"
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in markdown_text.splitlines():
            # FPDF's cell/encoding can choke on some characters; replace common ones.
            safe_line = line.encode("latin-1", "replace").decode("latin-1")
            pdf.cell(0, 6, safe_line, ln=True)
        pdf.output(str(CATALOG_PDF_PATH))
        return "generated"

    if available == "reportlab":
        try:
            from reportlab.lib.pagesizes import letter  # type: ignore[import-untyped]
            from reportlab.pdfgen import canvas  # type: ignore[import-untyped]
        except ImportError:
            return "reportlab import failed"
        c = canvas.Canvas(str(CATALOG_PDF_PATH), pagesize=letter)
        width, height = letter
        y = height - 40
        for line in markdown_text.splitlines():
            c.drawString(40, y, line[:120])
            y -= 14
            if y < 40:
                c.showPage()
                y = height - 40
        c.save()
        return "generated"

    return f"unsupported pdf library: {available}"


def _source_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
