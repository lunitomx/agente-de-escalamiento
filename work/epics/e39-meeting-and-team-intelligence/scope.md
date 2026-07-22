---
epic_id: "E39"
title: "Meeting and Team Intelligence"
status: "in_progress"
created: "2026-07-22"
mission: "escala-local-v2-plan-maestro-2607202112"
---

# Epic Scope: E39 — Meeting and Team Intelligence

## Objective

Permitir que el empresario deje transcripts diarios y semanales en una carpeta local o sincronizada como intercambio, y que ESCALA los ingiera idempotentemente en la máquina instaladora, extraiga hechos trazables, detecte señales a través del tiempo y genere una revisión ejecutiva local sin inventar conclusiones.

## Value

El director obtiene visibilidad diaria del ritmo y salud de su equipo basada en evidencia real, con preguntas explícitas cuando falta contexto, sin adaptar sus transcripts a una plantilla ni ceder la autoridad de datos a Drive, OneDrive, un servidor o una SQLite compartida.

## Architectural invariants

1. Runtime, estado canónico, ledger y reportes viven en la máquina del instalador.
2. Drive/OneDrive solo actúa como carpeta ordinaria de intercambio; no hay APIs cloud, OAuth, worker hospedado ni SQLite sincronizada.
3. E39 reutiliza la identidad y autoridad de E37; no duplica ni modifica el transcript original.
4. Cada hecho conserva `source_id`, ruta relativa, rango de líneas, hash de evidencia y confianza; lo ambiguo queda explícitamente unresolved.
5. Ausencia de transcript o campo no es una falta de desempeño personal: se reporta como evidencia faltante o pregunta.
6. Los reportes son deterministas, locales, con rutas relativas y sin contenido sensible en receipts.

## In scope

- Ingestión idempotente de `.txt`, `.md` y `.transcript` desde manual input o inbox local.
- Identificación de tipo de reunión, fecha, equipo, participantes mencionados y procedencia.
- Extracción de decisiones, acciones, owners, fechas límite, blockers, riesgos y compromisos con evidencia y confianza.
- Evaluación declarativa de ritmo diario/semanal sin penalizar evidencia ausente.
- Detección temporal de blockers repetidos, compromisos vencidos/repetidos, decisiones sin resolver y tendencias entre reuniones.
- Revisión ejecutiva diaria con salud del equipo, cambios materiales, preguntas y evidencia.
- Agenda local determinista y exportación de reportes a archivos ordinarios.

## Out of scope

- Audio/video, OCR, transcripción automática y comprensión lingüística universal.
- Integraciones OAuth, calendarios, Slack, Teams, correo, Jira o APIs cloud.
- Diagnóstico 0–100/cockpit ejecutivo y correlación DISC (E40).
- Instalador nativo, actualización y rollback (E41).
- Aceptación humana, catálogo funcional y PDF comercial (E42).
- Evaluación psicológica, ranking individual o inferencias sobre intención.

## Planned stories

| ID | Story | Size | Depends on | Master requirements | Outcome |
|---|---|:---:|---|---|---|
| S39.1 | Transcript Intake and Context | M | E37 | REQ-E39-001, REQ-E39-002 | Los transcripts se aceptan idempotentemente y su contexto queda identificado o unresolved con procedencia. |
| S39.2 | Evidence Extraction and Rhythm | L | S39.1 | REQ-E39-003, REQ-E39-004 | Decisiones, acciones y calidad del ritmo se extraen con evidencia, confianza y reglas declarativas. |
| S39.3 | Temporal Team Signals and Executive Review | L | S39.2 | REQ-E39-005, REQ-E39-006 | El sistema detecta patrones entre reuniones y genera una revisión ejecutiva diaria sin inventar negativos. |
| S39.4 | Local Scheduling and Report Exchange | M | S39.3 | REQ-E39-007 | La agenda local y el intercambio de reportes usan solo la máquina instaladora y archivos ordinarios. |

## Story closure checklist

- [x] S39.1 Transcript Intake and Context — merged `a124bd3` / `30d857c`; focused tests, lint, format and types PASS.
- [x] S39.2 Evidence Extraction and Rhythm — merged `8642e6c` / `c5aa559`; focused tests, lint, format and types PASS.
- [x] S39.3 Temporal Team Signals and Executive Review — merged `6e112ad` / `bcca359`; focused tests, lint, format and types PASS.
- [ ] S39.4 Local Scheduling and Report Exchange

## Done criteria

- [ ] Las cuatro stories completan start → design → plan → implement → review → close, con commits y retrospectivas.
- [ ] Los siete requisitos E39 tienen evidencia JSON y receipts exactos que prueban comportamiento, no solo presencia de código.
- [ ] Un fixture sintético con reuniones diarias/semanales demuestra ingestión idempotente, contexto, hechos, ritmo, tendencias y reporte ejecutivo.
- [ ] Un caso negativo demuestra ambigüedad, evidencia faltante y ausencia de datos sin acusar a una persona ni inventar hallazgos.
- [ ] El almacenamiento canónico y los reportes quedan bajo `data_root`; el intercambio no contiene SQLite ni estado autoritativo.
- [ ] Gates exactos E39, tests focalizados, lint, formato, tipos y suite completa pasan.
- [ ] Retrospectiva de épica, señal de cierre y tag local `epic/e39-complete` quedan registrados; no se hace push sin autorización.

## Master requirements owned

| Requirement | Acceptance proof |
|---|---|
| REQ-E39-001 | Dos escaneos del mismo inbox producen un único source identity y no duplican el ledger local. |
| REQ-E39-002 | Parser identifica meeting type/date/team/participants o emite preguntas unresolved, conservando source provenance. |
| REQ-E39-003 | Hechos de decisiones, acciones, owners, due dates, blockers, risks y commitments incluyen evidencia y confianza. |
| REQ-E39-004 | Reglas de ritmo declaran qué evidencia existe, qué falta y cómo se evalúa sin tratar ausencia como fallo humano. |
| REQ-E39-005 | Fixture multi-reunión detecta blockers repetidos, compromisos vencidos/repetidos, decisiones unresolved y tendencias. |
| REQ-E39-006 | Reporte diario muestra salud, cambios materiales, preguntas y evidencia únicamente sustentada. |
| REQ-E39-007 | Agenda/reporte usan carpetas locales relativas y validan que SQLite/configuración autoritativa no esté en el intercambio. |

## Risks and mitigations

| Risk | Likelihood/impact | Mitigation |
|---|---|---|
| Transcripts heterogéneos generan falsos positivos | High/High | Heurísticas acotadas, evidencia por línea, confianza y unresolved fail-closed. |
| Se confunde ausencia de transcript con mal desempeño | Medium/High | Estado `evidence_missing`, reglas declarativas y lenguaje no punitivo. |
| Carpeta sincronizada termina conteniendo autoridad | Medium/High | Reutilizar `validate_workspace`, receipts de autoridad y gate negativo explícito. |

## Implementation Plan

### Sequence and rationale

1. **S39.1 — Transcript Intake and Context (M)**: risk-first walking skeleton. Proves the E37 seam, idempotency and unresolved context before any extraction can create facts.
2. **S39.2 — Evidence Extraction and Rhythm (L)**: depends on stable context/provenance. Adds the smallest useful facts and declarative rhythm assessment.
3. **S39.3 — Temporal Team Signals and Executive Review (L)**: consumes persisted facts and produces the executive outcome; trend rules remain deterministic and fail-closed.
4. **S39.4 — Local Scheduling and Report Exchange (M)**: finalizes the local delivery seam and validates the no-SQLite-in-exchange invariant around the complete pipeline.

The critical path is S39.1 → S39.2 → S39.3 → S39.4. Parallel work is intentionally avoided: every later story consumes contracts and evidence from the previous story, and splitting the parser/report seams would increase drift without reducing risk.

### Milestones

#### M1 — Walking Skeleton (S39.1)

- Success: the same transcript scanned twice yields one stable source identity; metadata is ready or asks bounded questions; original file and exchange remain unchanged.
- Demo: local `WorkspaceConfig` + `daily-2026-07-21.transcript` → intake receipt.

#### M2 — Core MVP (S39.2)

- Success: a synthetic daily/weekly pair yields traceable actions, decisions and commitments plus rhythm states `supported`/`evidence_missing`/`unresolved`.
- Demo: evidence spans point to source IDs and line ranges; confidence is visible without copying transcript text.

#### M3 — Feature Complete (S39.3)

- Success: three meetings surface one repeated blocker, one overdue commitment, one unresolved decision and a material trend; no unsupported negative claim appears.
- Demo: daily executive review has health, material changes, questions and evidence.

#### M4 — Epic Complete (S39.4)

- Success: local schedule and report exchange write only beneath `data_root`; a deliberate exchange SQLite is rejected; all seven exact gates and quality checks pass.
- Demo: `run_daily_review` + report artifacts are deterministic and redacted.

### Progress Tracking

| Story | Size | Status | Actual | Velocity | Notes |
|---|:---:|---|---|---|---|
| S39.1 Transcript Intake and Context | M | Done | one focused cycle | — | Depends on E37; merged `a124bd3` / `30d857c` |
| S39.2 Evidence Extraction and Rhythm | L | Done | one focused cycle | — | Depends on S39.1; merged `8642e6c` / `c5aa559` |
| S39.3 Temporal Team Signals and Executive Review | L | Done | one focused cycle | — | Depends on S39.2; merged `6e112ad` / `bcca359` |
| S39.4 Local Scheduling and Report Exchange | M | Pending | — | — | Depends on S39.3 |

### Sequencing risks

- **Heuristic drift**: use line-level evidence and confidence; no model claims without a matching rule.
- **Cross-meeting identity mismatch**: source IDs and normalized meeting dates are the only join keys; ambiguous people/team stay unresolved.
- **Delivery boundary drift**: S39.4 owns the negative authority test before closure; no report path may point into exchange.

## Legacy sweep

No hay un V1 de inteligencia de reuniones en `escala_server`; los skills textuales históricos de `escala-skills` permanecen como interfaz de coaching y no se reemplazan en esta épica. E39 añade un seam local verificable, no duplica el ledger de E37.
