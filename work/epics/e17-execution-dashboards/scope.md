# Epic Scope: E17 — Execution Dashboards

## Objective
Crear dashboards visuales para las herramientas de la decisión Execution del sistema Escala. Visualizar hábitos, métricas, reuniones, prioridades y visión.

## In Scope
- S17.1 — Rockefeller Habits: Scoreboard visual de 10 hábitos (score, top/bottom, 1 THING)
- S17.2 — WWW (Who What When): Task tracker visual con fechas y responsables
- S17.3 — SMART Priorities + Thematic Goal: Tablero anual (Título, 5 Capítulos, 2 Rocks trimestrales)
- S17.4 — Balanced KPIs: Leading/Lagging con traffic lights (6 áreas A-F)
- S17.5 — Meeting Rhythms: Calendario visual de 5 reuniones + Agendas diarias/semanales
- S17.6 — Top 25 Influencers: Board visual de relaciones estratégicas
- S17.7 — Vision Summary: Panel central unificado (Core Values, Purpose, Brand Promises, BHAG, KPIs, Critical Numbers, Priorities)

## Out of Scope
- Integración con calendarios reales (Google/Outlook)
- Notificaciones automáticas
- Multi-idioma

## Dependencies
- Sistema Escala base funcional (skills execution existentes)
- Framework de visualización compartido con E14/E15/E16

## Design Decisions
- **DD1:** Todos los dashboards de E17 se ubicarán en `work/epics/e17-execution-dashboards/components/{dashboard-name}/index.html`
- **DD2:** Reutilizan el framework visual de E14 (Chart.js + dashboard-base.css)
- **DD3:** Cada dashboard es single-file HTML, sin build step

## Status: active

### Progress Tracking

| Story | Size | Status | Started | Completed | Notes |
|:------|:----:|:------:|:-------:|:---------:|:------|
| S17.1 — Rockefeller Habits | M | Done | 2026-05-28 | 2026-05-28 | Scoreboard 10 hábitos |
| S17.2 — WWW | S | Done | 2026-05-28 | 2026-05-28 | Task tracker |
| S17.3 — SMART Priorities | M | Done | 2026-05-28 | 2026-05-28 | Tablero anual + rocks |
| S17.4 — Balanced KPIs | M | Pending | — | — | Leading/Lagging + semáforos |
| S17.5 — Meeting Rhythms | S | Pending | — | — | Calendario + agendas |
| S17.6 — Top 25 Influencers | S | Pending | — | — | Board relaciones |
| S17.7 — Vision Summary | L | Pending | — | — | Panel unificado |
