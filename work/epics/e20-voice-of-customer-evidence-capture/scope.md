# Epic Scope: E20 — Voice of Customer & Evidence Capture

**Status:** Superseded/Discarded
**Closed as backlog:** 2026-06-18
**Terminal disposition:** Superseded by E34 Voice of Customer Evidence System

## Objective

Hacer que el agente Escala capture, ordene y reutilice voz real de clientes para fortalecer Core Customer, Brand Promise y posicionamiento.

## In Scope

- Captura de testimonios, audios o quotes de clientes reales
- Normalización de evidencia con fuente, contexto y fecha
- Reglas para convertir voz del cliente en inputs estratégicos
- Biblioteca reutilizable de pruebas y frases clave
- Conexión directa con Core Customer y Brand Promise

## Out of Scope

- CRM completo o pipeline comercial completo
- Análisis estadístico avanzado de sentimiento
- Automatización de reseñas externas
- Edición visual de testimonios

## Planned Stories

| ID | Story | Size | Depends |
|----|-------|------|---------|
| S20.1 | Evidence intake schema | M | — |
| S20.2 | Testimonial normalization | M | S20.1 |
| S20.3 | Voice-to-promise pattern extraction | M | S20.2 |
| S20.4 | Evidence library for other skills | S | S20.3 |

## Dependencies

- Skill de Core Customer y Brand Promise
- Fuentes reales de cliente (audio, texto, notas)
- Convenciones de trazabilidad y fuente

## Done Criteria

- [ ] La evidencia queda capturada con fuente y contexto
- [ ] Las quotes pueden reutilizarse en otros skills
- [ ] El agente no formula promesas sin evidencia suficiente
- [ ] Los inputs del cliente se vuelven una fuente estable de decisiones

## Backlog Closure Review

Verdict: **do not close as complete**. This folder contains only `brief.md` and
`scope.md`; `git ls-files` and `git log -- <path>` show no tracked
implementation, story artifacts, retrospective, or close commit for this draft.

Corrected disposition: **Superseded/Discarded; superseded by E34**. The idea
remains valuable and was renumbered as E34 Voice of Customer Evidence System.
E34 now carries the trusted implementation and closure evidence for this
direction.

Current backlog action: no active epic remains here. Do not count this folder as
pending product work unless a future scope deliberately reopens a new numbered
epic.

Tag action: no `complete` tag should be created for this draft.
