---
epic_id: "E16"
title: "People Dashboards"
status: "complete"
completed: "2026-05-28"
stories:
  total: 6
  done: 6
---

# Epic Retrospective: E16 — People Dashboards

## Summary
Epic completado en una sesión continua. Se construyeron 6 dashboards visuales para la decisión People del sistema Escala.

## Stories

| Story | Status | Component |
|:------|:------:|:----------|
| S16.1 — Core Values | ✅ | `components/core-values-board/index.html` |
| S16.2 — FACe | ✅ | `components/face-board/index.html` |
| S16.3 — Team Growth | ✅ | `components/team-growth-board/index.html` |
| S16.4 — DISC | ✅ | `components/disc-board/index.html` |
| S16.5 — Love/Loathe | ✅ | `components/love-loathe-board/index.html` |
| S16.6 — Hiring Pipeline | ✅ | `components/hiring-pipeline-board/index.html` |

## What was built
- **Core Values**: Mission to Mars con tripulación, selección de atributos, extracción de valores + 3 pruebas de fuego
- **FACe**: Matriz funciones × persona × KPIs × resultados, detección de vacantes y duplicados
- **Team Growth**: Radar chart Chart.js (Onboarding, Coaching, Desarrollo) con sliders Company vs Personal
- **DISC**: 4 cuadrantes interactivos, barras de composición, selector por clic cíclico
- **Love/Loathe**: Kanban dual love/loathe con plan de acción delegar/automatizar/abdicar/eliminar
- **Hiring Pipeline**: Pipeline 7 pasos con movimiento de candidatos entre etapas

## Next
E17 — Execution Dashboards (7 historias: Rockefeller, WWW, Priorities, KPIs, Meetings, Influencers, Vision)

## Pipeline / Skills / Gates

- Pipeline pattern: reuse E14/E15 visual framework, implement one dashboard per people tool.
- Skills/components involved: Core Values, FACe, Team Growth, DISC, Love/Loathe, Hiring Pipeline dashboards.
- Core modules: self-contained HTML dashboards with shared visual framework.
- Quality gates: scope tracking, component existence, manual visual/interaction verification. No automated test gate is documented for this epic.
- Verification evidence: close commit `e008ea4`, retrospective story table, completed scope tracking.
- Canonical tag: `epic/e16-people-dashboards-complete`.
