# Epic Scope: E19 — Strategy Core Skills

**Status:** Backlog/Not Completed
**Closed as backlog:** 2026-06-18

## Objective

Alinear y fortalecer los skills de estrategia central para que el agente Escala guíe mejor la construcción de estrategia en una frase, Business Model Canvas, Core Customer, Brand Promise y Strategy Canvas.

## In Scope

- Refinar Prompt 0 a 4 con lenguaje más concreto
- Mantener la lógica de una sola pregunta por turno
- Homologar salidas HTML autocontenidas
- Conectar los prompts entre sí como una secuencia de trabajo
- Asegurar que el Strategy Canvas se actualice conforme avanzan los ejercicios

## Out of Scope

- Reescritura completa del curso
- Cambios de layout en la presentación
- Integraciones externas de automatización
- Nuevas herramientas fuera del núcleo estratégico

## Planned Stories

| ID | Story | Size | Depends |
|----|-------|------|---------|
| S19.1 | Strategy-in-a-sentence prompt hardening | M | — |
| S19.2 | Business Model Canvas prompt hardening | M | S19.1 |
| S19.3 | Core Customer prompt hardening | M | S19.2 |
| S19.4 | Brand Promise prompt hardening | M | S19.3 |
| S19.5 | Strategy Canvas update flow | S | S19.3, S19.4 |

## Dependencies

- Clase de Strategy I y sus materiales fuente
- HTML/markdown de prompts 0-4
- Convenciones de salida de los skills actuales

## Done Criteria

- [ ] Los cinco prompts siguen una secuencia clara y consistente
- [ ] Cada skill produce una salida usable por el usuario final
- [ ] El Strategy Canvas se actualiza sin romper navegación
- [ ] El vocabulario y las reglas quedan homogéneas

## Backlog Closure Review

Verdict: **do not close as complete**. This folder contains only `brief.md` and
`scope.md`; `git ls-files` and `git log -- <path>` show no tracked
implementation, story artifacts, retrospective, or close commit for this draft.

Corrected disposition: **Backlog/Not Completed**. The idea remains valid as a
future strategy-skill hardening epic, but it must be renumbered and restarted
with fresh story artifacts before implementation.

Tag action: no `complete` tag should be created for this draft.
