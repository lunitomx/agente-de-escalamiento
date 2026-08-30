---
epic_id: E64
title: Consolidación ontológica y release de cobertura
status: in_progress
depends_on: [E59, E60, E61, E62, E63]
---

# Scope E64

## Objetivo

Promover únicamente conocimiento aprobado de las cinco pasadas a una versión canónica coherente y publicable internamente, con una matriz de cobertura que pruebe qué unidad fuente llega a qué nodo.

## Dentro

- Normalización canónica sin borrar evidencia ni conflictos.
- Consolidación de aliases, referencias externas y relaciones tipadas.
- Validadores de huérfanos, enlaces rotos, herramientas sin decisión, reglas sin evidencia y métricas sin unidad/definición.
- Matriz `source_id → node_id → status`, reportes de cobertura/fidelidad y release interno.
- Revisión de estructuras mínimas: 4D, decisiones, barreras, disciplinas, hábitos, estratos, palancas, ritmos y campos de herramientas.

## Fuera

- Crear procedimientos o cambiar el catálogo de E56.
- Ocultar ambigüedad para mejorar indicadores de cobertura.
- Distribuir material derivado fuera de la frontera de E57/E36.

## Historias y secuencia

| Orden | Historia | Entrega verificable |
|---:|---|---|
| 1 | S64.1 Normalización | Nodos canónicos con mapa de aliases/evidencias. |
| 2 | S64.2 Integridad | Gates automatizados contra relaciones inválidas. |
| 3 | S64.3 Cobertura | Matriz fuente→nodo con exclusiones. |
| 4 | S64.4 Fidelidad | Reporte y bloqueo de críticos. |

## Criterios de terminación

- Todas las estructuras nombradas están representadas o justificadamente excluidas.
- Cero nodo/relación roto u huérfano.
- Cero distorsión crítica abierta.
- Todo concepto apto para compilación tiene procedencia y estado de revisión.

## Handoff y riesgos

E65 sólo consume esta release. No se acepta una salida "verde" si la cola de revisión contiene hallazgos críticos.

## Implementation Plan

> Added by `/rai-epic-plan` on 2026-08-30. No `design.md` or `ux-design.md`
> exists for this legacy governed scope, so the plan preserves its approved
> scope and records hard source gates rather than bypassing them.

### Story Sequence

| Order | Story | Size | Dependencies | Milestone | Rationale |
|:-----:|-------|:----:|--------------|-----------|-----------|
| 1 | S64.1 — Normalización | M | E59; E60–E63 validated candidate receipts | M1 | Canonical IDs, aliases and explicit exclusions must exist before any integrity or coverage statement. |
| 2 | S64.2 — Integridad | M | S64.1 | M2 | Checks orphan nodes, invalid relations and provenance after the canonical set is stable. |
| 3 | S64.3 — Cobertura | M | S64.1 | M2 | Builds the source→node matrix independently of integrity checks, so omissions remain visible. |
| 4 | S64.4 — Fidelidad | M | S64.2, S64.3 | M3 | Audits critical findings and creates the internal release only when both gates agree. |

### Milestones

| Milestone | Stories | Target | Success Criteria |
|-----------|---------|--------|------------------|
| **M0: Upstream source gate** | E60–E63 | Before S64.1 | E60–E62 have authorized visual-layout receipts; E63 remains source-bounded with its independent review. |
| **M1: Canonical skeleton** | S64.1 | After M0 | A versioned candidate set has aliases, evidence and explicit exclusions, with no raw source text. |
| **M2: Measurable release** | S64.2, S64.3 | After M1 | Integrity and coverage validators pass independently and report all exclusions. |
| **M3: Epic complete** | S64.4 | After M2 | No critical fidelity finding remains; internal release is ready for E65 and retrospective is complete. |

### Parallel Work Streams

```text
Hard source gate: E60–E63 ──► S64.1 ─┬─► S64.2 ─┐
                                     └─► S64.3 ─┴─► S64.4
```

**Merge point:** S64.4 accepts only the intersection of an integrity-passing
canonical set and a coverage-passing matrix. A blocked candidate or an
unreviewed form is an exclusion, never a green result.

### Progress Tracking

| Story | Size | Status | Actual | Velocity | Notes |
|-------|:----:|:------:|:------:|:--------:|-------|
| S64.1 | M | Done | 2026-08-30 | — | Source-safe canonical release: 76 nodes and 3 explicit exclusions from 79 authorized candidates. Independent review passed with one documented nonblocking semantic-label limitation. |
| S64.2 | M | Done | 2026-08-30 | — | Integrity gate is `not-assessed` without an authorized relationship manifest; it passes only with a valid manifest, never by inference. |
| S64.3 | M | Done | 2026-08-30 | — | Deterministic safe matrix has 76 mapped records and 3 Cash review-required records; no percentage conceals them. |
| S64.4 | M | Pending | — | — | Starts only when S64.2 and S64.3 pass without critical findings. |

### Sequencing Risks

| Risk | L/I | Mitigation |
|------|:---:|------------|
| Text extraction hides a form-layout defect | M/H | Require the private visual-layout receipts before S64.1; do not infer topology from text. |
| Blocked Cash formula leaks into canonical knowledge | M/H | Retain E63 dependency receipt and exclude blocked/needs-revision candidates from the release. |
| A coverage percentage obscures an exclusion | M/M | Matrix must label every source unit as mapped, excluded or review-required with reason. |
