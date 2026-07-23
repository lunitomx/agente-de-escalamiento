---
epic_id: "E40"
title: "Executive Cockpit and Coaching"
status: "in_progress"
created: "2026-07-22"
mission: "escala-local-v2-plan-maestro-2607202112"
---

# Epic Scope: E40 — Executive Cockpit and Coaching

## Objective

Permitir que un empresario construya un perfil de compañía mediante preguntas, vea un diagnóstico visual 0–100 de People, Strategy, Execution y Cash, profundice en el dolor principal con evidencia y preguntas pendientes, y convierta la recomendación en estrategia y ejecución persistente en su máquina local.

**Value:** El director obtiene una vista accionable de su empresa, no solo una colección de skills: puede entender qué se sabe, qué se infiere, qué falta y cuál es el siguiente paso sin ceder datos a un servicio hospedado.

## Architectural invariants

1. Runtime, estado canónico y SQLite viven únicamente en la máquina instaladora; `WorkspaceConfig` se valida antes de escribir.
2. Google Drive, OneDrive o una carpeta ordinaria son solo intercambio de documentos; no hay APIs cloud, OAuth, workers remotos ni SQLite sincronizada.
3. E40 compone contratos y source IDs de E37–E39, no duplica ingestión ni copia transcripts/workbooks a receipts.
4. Toda recomendación conserva evidencia, frescura y estado (`fact`, `inference`, `unknown`, `evidence_limited`); lo ambiguo permanece pendiente.
5. El cockpit es un artefacto HTML/JSON local y determinista; no requiere una UI hospedada.

## Stories (8 requirements)

| ID | Story | Size | Status | Master requirements | Description |
|---|---|:---:|:---:|---|---|
| S40.1 | Guided Onboarding and Diagnostic | L | Done | REQ-E40-001, REQ-E40-002 | Construir perfil validado y scores 0–100 separados a partir de respuestas y evidencia suministrada. |
| S40.2 | Visual Cockpit and Pain Drill-Down | L | Pending | REQ-E40-003, REQ-E40-007 | Mostrar scores, tendencias, frescura, bloqueadores y drill-down local hacia evidencia, preguntas y acción. |
| S40.3 | Strategy and Four-Decision Coaching | L | Pending | REQ-E40-004, REQ-E40-005 | Producir visión/OPSP con pendientes y enrutar People, Strategy, Execution o Cash sin sobreafirmar. |
| S40.4 | Persistent Execution and Honest Guidance | M | Pending | REQ-E40-006, REQ-E40-008 | Persistir objetivos, prioridades, tareas y continuidad local; hacer preguntas materiales y separar hechos de inferencias. |

## Scope

**In scope (MUST):**

- Modelos Pydantic cerrados para onboarding, diagnóstico, cockpit, estrategia, rutas y ejecución.
- Persistencia JSON derivada bajo `data_root` y autoridad local validada; no estado en exchange.
- Qualification sintética y ocho gates exactos de aceptación.
- Tests TDD focalizados, lint, formato, tipos y readiness del ledger maestro.

**In scope (SHOULD):**

- Render de cockpit HTML con barras accesibles, JSON redacted y reportes legibles en español.

**Out of scope:**

- DISC/correlación personal → parking lot; requiere consentimiento y decisión ética explícita.
- Instalación/actualización nativa → E41.
- Qualification end-to-end y catálogo PDF comercial → E42.

## Done Criteria

**Per story:**

- [ ] Código con anotaciones de tipo y modelos Pydantic cerrados.
- [ ] Tests focalizados y negative cases pasan.
- [ ] `gate-format`, `gate-lint`, `gate-tests`, `gate-types` pasan.
- [ ] Retrospectiva de story y commit de cierre existen.

**Epic complete:**

- [ ] S40.1–S40.4 completas y sus ocho requirements tienen JSON + receipt exactos.
- [ ] Fixture sintético demuestra onboarding, diagnóstico, cockpit, estrategia, routing, persistencia y guidance honesto.
- [ ] El cockpit se escribe solo bajo `data_root`, es determinista y no expone rutas, endpoints o texto privado en receipts.
- [ ] Readiness del ledger: 8/8 E40 proved; suite completa y gates de cierre pasan.
- [ ] Retrospectiva y tag local `epic/e40-complete`; sin push/publicación sin autorización.

## Dependencies

```
E37/E38/E39 contracts
        ↓
S40.1 onboarding + diagnostic
        ↓
S40.2 cockpit + drill-down ──┐
        ↓                    │
S40.3 strategy + routing ────┤
        ↓                    │
S40.4 persistence + guidance ◄┘
```

**External:** Ninguna; la qualification usa una empresa sintética y filesystem temporal local.

## Architecture

| Decision | ADR | Summary |
|----------|-----|---------|
| Derivados ejecutivos bajo `data_root` | D1 (design.md) | JSON atómico y HTML local; la autoridad SQLite/exchange sigue siendo E37. |
| Evidencia explícita y estados fail-closed | D2 (design.md) | Cada score/ruta conserva source IDs y preguntas; unknown no se convierte en dato. |
| Cockpit como artefacto local | D3 (design.md) | HTML/JSON deterministas, sin servidor hospedado ni endpoints remotos. |

## Risks

| Risk | L/I | Mitigation |
|------|:---:|------------|
| Score decorativo sin evidencia | H/H | Requerir source IDs/owner answers, freshness y status en cada assessment; gate negativo sin evidencia. |
| Persistencia deriva hacia el exchange | M/H | Reutilizar `validate_workspace`, escribir atómicamente bajo `data_root` y probar SQLite/paths compartidos. |
| Coaching sobreafirma estrategia | M/H | `unknown`/unresolved explícitos, preguntas materiales y routing soportado por decision/score. |

## Parking Lot

- DISC consentido y correlación longitudinal → `dev/parking-lot.md`, promoción solo con consentimiento, retención y qualification local.
- UI interactiva hospedada → E41+ y nueva decisión de producto; no bloquea el cockpit HTML local.
@@
 ## Risks
 | Coaching sobreafirma estrategia | M/H | `unknown`/unresolved explícitos, preguntas materiales y routing soportado por decision/score. |

## Implementation Plan

> Added by `/rai-epic-plan` — 2026-07-22

### Story Sequence

| Order | Story | Size | Dependencies | Milestone | Rationale |
|:-----:|-------|:----:|--------------|-----------|-----------|
| 1 | S40.1 | L | E37/E38/E39 contracts | M1 | Risk-first walking skeleton: profile + four scores establish the evidence contract before presentation. |
| 2 | S40.2 | L | S40.1 | M1/M2 | The visual cockpit proves the user-visible outcome and the pain drill-down before coaching is layered on. |
| 3 | S40.3 | L | S40.1, S40.2 | M2 | Strategy and routing consume the diagnostic and make the next decision executable. |
| 4 | S40.4 | M | S40.1–S40.3 | M3/M4 | Persistence and honest guidance close the loop and protect continuity across sessions. |

Critical path: `S40.1 → S40.2 → S40.3 → S40.4`. Parallel work is intentionally avoided because each story consumes the previous typed contracts; splitting would increase drift without reducing risk.

### Milestones

| Milestone | Stories | Target | Success Criteria |
|-----------|---------|--------|------------------|
| **M1: Walking Skeleton** | S40.1, S40.2 | 2026-07-22 | Synthetic owner answers yield a validated profile, four evidence-backed 0–100 scores and a local cockpit with a pain drill-down. |
| **M2: Coaching MVP** | +S40.3 | 2026-07-22 | A partial OPSP/vision keeps unresolved decisions visible and routes the lowest decision to an existing skill with a bounded explanation. |
| **M3: Feature Complete** | +S40.4 | 2026-07-22 | Goals/priorities/tasks/session continuity persist locally and every recommendation distinguishes fact, inference and unknown. |
| **M4: Epic Complete** | — | 2026-07-22 | Eight exact requirements proved, focused/full gates pass, retrospective and local tag exist; no push. |

### Parallel Work Streams

```text
Stream critical: S40.1 ─► S40.2 ─► S40.3 ─► S40.4
Evidence/gates:  tests ───────────────► qualification ─► closure
```

### Progress Tracking

| Story | Size | Status | Actual | Velocity | Notes |
|-------|:----:|:------:|:------:|:--------:|-------|
| S40.1 Guided Onboarding and Diagnostic | L | Pending | — | — | Foundation; REQ-E40-001/002 |
| S40.2 Visual Cockpit and Pain Drill-Down | L | Pending | — | — | REQ-E40-003/007 |
| S40.3 Strategy and Four-Decision Coaching | L | Pending | — | — | REQ-E40-004/005 |
| S40.4 Persistent Execution and Honest Guidance | M | Pending | — | — | REQ-E40-006/008 |

### Sequencing Risks

| Risk | L/I | Mitigation |
|------|:---:|------------|
| Legacy 1–5 scores leak into the new 0–100 contract | M/H | Keep E40 models separate, test scale bounds and use explicit conversion only in adapters. |
| HTML becomes a hidden hosted product | M/H | Assert filesystem-only artifact paths, no endpoints and no server dependency. |
| Persistence silently accepts unverified claims | M/H | Require status/provenance in models and negative tests for missing evidence. |
