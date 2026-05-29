# E18: Escala Server & Interactive Dashboards

## Hypothesis

Los dashboards visuales de Escala (E14-E17) son estáticos — muestran datos de ejemplo pero no se conectan con los datos reales que el usuario ingresa en los worksheets. Si construimos un mini servidor local que sirva los dashboards con datos en vivo y permita interacción (sliders, barras editables), el usuario podrá visualizar y manipular su propio negocio en tiempo real, y los cambios persistirán.

## Success Metrics

- Power of One interactivo funcional con sliders + persistencia a YAML
- Home page con navegación jerárquica: Decisiones → Herramientas → Dashboard
- Mínimo 3 herramientas completamente interactivas (Power of One + 2 más)
- Todos los 22 dashboards servidos desde el server con datos reales
- `escala-server start` arranca el servidor

## Appetite

Épica completa — 8 historias. Prioridad: piloto Power of One primero.

## Rabbit Holes

- No sobreingeniería — server minimalista con http.server, sin flask/fastapi
- No tocar los HTML existentes más de lo necesario — inyectar interactividad con fetch() + sliders
- Los dashboards de Strategy/People/Execution son más de visualización que de edición — priorizar los editables (Power of One, CCC, Priorities)
- La navegación debe funcionar sin server (los HTML estáticos deben seguir viéndose solos)

## No-Go

- NO base de datos externa (SQLite/Postgres) — solo YAML plano
- NO autenticación — es local
- NO despliegue cloud — solo local
