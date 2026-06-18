# Epic Scope: E21 — Transcript Intelligence for Escala

**Status:** Backlog/Not Completed
**Closed as backlog:** 2026-06-18

## Objective

Transformar transcripts de clases y sesiones en inteligencia accionable para el agente Escala: decisiones, compromisos, bloqueos, quotes y oportunidades de mejora.

## In Scope

- Procesamiento de transcripts crudos
- Extracción de decisiones, hipótesis y compromisos
- Detección de bloqueos y frases clave
- Enlaces entre transcript, clase y skill afectado
- Salida lista para revisión humana y mejora del agente

## Out of Scope

- Transcripción automática desde cero si no existe fuente
- Edición de video/audio
- Sincronización con servicios externos de manera automática
- Reescritura del contenido sin trazabilidad

## Planned Stories

| ID | Story | Size | Depends |
|----|-------|------|---------|
| S21.1 | Transcript intake + validation | M | — |
| S21.2 | Decision and commitment extraction | M | S21.1 |
| S21.3 | Blocker and quote classification | M | S21.2 |
| S21.4 | Skill-impact mapping | M | S21.3 |
| S21.5 | Reviewable intelligence report | S | S21.4 |

## Dependencies

- Flujo de transcript local o exportado
- Convención de métricas y trazabilidad
- Skills estratégicos núcleo para mapear impactos

## Done Criteria

- [ ] Cada transcript produce decisiones y compromisos detectables
- [ ] Las quotes y bloqueos se separan correctamente
- [ ] La salida indica qué skill debe mejorar
- [ ] Nada se inventa: la ambigüedad se conserva

## Backlog Closure Review

Verdict: **do not close as complete**. This folder contains only `brief.md` and
`scope.md`; `git ls-files` and `git log -- <path>` show no tracked
implementation, story artifacts, retrospective, or close commit for this draft.

Corrected disposition: **Backlog/Not Completed**. The idea overlaps with the
completed E18 class-to-skill learning loop but is broader. Any future work
should start as a new numbered epic and explicitly reuse or extend E18 rather
than pretending this draft was implemented.

Tag action: no `complete` tag should be created for this draft.
