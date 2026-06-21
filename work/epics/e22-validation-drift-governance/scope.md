# Epic Scope: E22 — Validation, Drift Control & Governance

**Status:** Superseded/Discarded
**Closed as backlog:** 2026-06-18
**Terminal disposition:** Superseded by E35 Skill Golden Cases & Drift Gates

## Objective

Crear un sistema de validación y gobierno para los skills del agente Escala que detecte drift, proteja la metodología y haga trazables las mejoras.

## In Scope

- Casos de prueba y golden outputs para skills núcleo
- Validación estructural de prompts y salidas
- Registro de versiones y cambios relevantes
- Señales de drift metodológico o de comportamiento
- Gate de publicación antes de promover cambios

## Out of Scope

- Entrenamiento de modelos
- Infraestructura externa compleja
- UI nueva para observabilidad
- Automatización de despliegue sin revisión

## Planned Stories

| ID | Story | Size | Depends |
|----|-------|------|---------|
| S22.1 | Golden cases for strategy skills | M | — |
| S22.2 | Output validation rules | M | S22.1 |
| S22.3 | Drift detection signals | M | S22.2 |
| S22.4 | Prompt/version changelog | M | S22.2 |
| S22.5 | Release gate checklist | S | S22.3, S22.4 |

## Dependencies

- Skills núcleo ya definidos
- Outputs esperados de clases/transcripts
- Convenciones de versión y release del proyecto

## Done Criteria

- [ ] Cada skill núcleo tiene casos de validación
- [ ] El drift metodológico se puede detectar antes de publicar
- [ ] Las versiones quedan rastreables
- [ ] El release gate bloquea cambios débiles o inconsistentes

## Backlog Closure Review

Verdict: **do not close as complete**. This folder contains only `brief.md` and
`scope.md`; `git ls-files` and `git log -- <path>` show no tracked
implementation, story artifacts, retrospective, or close commit for this draft.

Corrected disposition: **Superseded/Discarded; superseded by E35**. Parts of
this direction were later addressed by E30/E31 pipeline validation and E32
closure governance. The remaining valuable gap was renumbered and narrowed as
E35 Skill Golden Cases & Drift Gates: golden cases for core skills plus a
deterministic release check.

Current backlog action: no active epic remains here. Do not count this folder as
pending product work unless a future scope deliberately reopens a new numbered
epic.

Tag action: no `complete` tag should be created for this draft.
