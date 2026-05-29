# Epic Scope: E16 — People Dashboards

## Objective
Crear dashboards visuales para las herramientas de la decisión People del sistema Escala. Visualizar personas, cultura, roles y desarrollo del equipo.

## In Scope
- S16.1 — Core Values: Mission to Mars visual + tarjetas de valores vivos
- S16.2 — FACe: Matriz visual completa (Funciones × Persona × KPIs × Resultados P&L/BS)
- S16.3 — Team Growth: Radar chart (Onboarding, Coaching, Desarrollo) con ranking Company vs Personal
- S16.4 — DISC: Composición visual del equipo (Dominance, Influence, Steadiness, Conscientiousness)
- S16.5 — Love/Loathe: Balance board visual (top 5 tareas amadas/odiadas + plan delegar)
- S16.6 — Hiring Pipeline: Proceso visual de 7 pasos

## Out of Scope
- Integración con HRIS/ATS
- Evaluaciones DISC automatizadas
- Multi-idioma

## Dependencies
- Sistema Escala base funcional (skills people existentes)
- Framework de visualización compartido con E14/E15/E17

## Design Decisions
- **DD1:** Todos los dashboards de E16 se ubicarán en `work/epics/e16-people-dashboards/components/{dashboard-name}/index.html`
- **DD2:** Reutilizan el framework visual de E14 (Chart.js + dashboard-base.css) con ruta relativa `../../e14-cash-dashboards/components/shared/`
- **DD3:** Cada dashboard es single-file HTML, sin build step

## Status: complete

### Progress Tracking

| Story | Size | Status | Started | Completed | Notes |
|:------|:----:|:------:|:-------:|:---------:|:------|
| S16.1 — Core Values | M | Done | 2026-05-28 | 2026-05-28 | Mission to Mars + tarjetas |
| S16.2 — FACe | L | Done | 2026-05-28 | 2026-05-28 | Matriz funciones × persona |
| S16.3 — Team Growth | S | Done | 2026-05-28 | 2026-05-28 | Radar chart 3 áreas |
| S16.4 — DISC | M | Done | 2026-05-28 | 2026-05-28 | Composición 4 cuadrantes |
| S16.5 — Love/Loathe | S | Done | 2026-05-28 | 2026-05-28 | Balance board tareas |
| S16.6 — Hiring Pipeline | S | Done | 2026-05-28 | 2026-05-28 | Pipeline 7 pasos |
