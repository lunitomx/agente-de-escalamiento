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

## Legacy sweep

No hay un V1 de inteligencia de reuniones en `escala_server`; los skills textuales históricos de `escala-skills` permanecen como interfaz de coaching y no se reemplazan en esta épica. E39 añade un seam local verificable, no duplica el ledger de E37.
