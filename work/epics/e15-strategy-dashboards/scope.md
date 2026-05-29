# Epic Scope: E15 — Strategy Dashboards

## Objective
Crear dashboards visuales para las herramientas de la decisión Strategy del sistema Escala. Visualizar cada herramienta estratégica como tableros interactivos.

## In Scope
- S15.1 — Business Model Canvas: Grid visual de 9 bloques interactivo
- S15.2 — Core Customer: Tarjetas visuales de clientes + atributos + descripción
- S15.3 — Brand Promises: 3 promesas visuales con medidores de cumplimiento
- S15.4 — Differentiating Activities: Matriz competitiva visual vs competidores
- S15.5 — Sandbox: Mapa visual (geografía, productos, canales, tendencias)

## Out of Scope
- Integración con CRM para datos en vivo
- Exportación a PDF/PPT
- Multi-idioma

## Dependencies
- Sistema Escala base funcional (skills strategy existentes)
- Framework de visualización compartido con E14/E16/E17
  - Chart.js v4 vendored en `e14-cash-dashboards/components/shared/vendor/chart.umd.min.js`
  - `dashboard-base.css` en `e14-cash-dashboards/components/shared/styles/`
  - Cada dashboard será self-contained HTML con ruta relativa al shared

## Design Decisions
- **DD1:** Todos los dashboards de E15 se ubicarán en `work/epics/e15-strategy-dashboards/components/{dashboard-name}/index.html`
- **DD2:** Reutilizan el framework visual de E14 (Chart.js + dashboard-base.css) con ruta relativa `../../e14-cash-dashboards/components/shared/`
- **DD3:** Cada dashboard es single-file HTML, sin build step

## Status: active

### Progress Tracking

| Story | Size | Status | Started | Completed | Notes |
|:------|:----:|:------:|:-------:|:---------:|:------|
| S15.1 — BMC Visual | M | Done | 2026-05-28 | 2026-05-28 | Grid 9 bloques + ejemplos |
| S15.2 — Core Customer | S | Done | 2026-05-28 | 2026-05-28 | Tarjetas cliente + atributos |
| S15.3 — Brand Promises | S | Pending | — | — | 3 promesas + medidores |
| S15.4 — Diff Activities | M | Pending | — | — | Matriz competitiva |
| S15.5 — Sandbox | S | Pending | — | — | Mapa 4 cuadrantes |
