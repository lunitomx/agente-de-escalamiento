# E87: Strategy workbook completo — brief

Jira: ESCALA-107 · Fecha: 2026-10-20 · Estado: activa

## Problema

El workbook de Strategy (EOA Strategy 2025 Participant Workbook, 38 páginas) es la fuente de la metodología de Strategy de ESCALA. Hoy ESCALA no cubre todas sus herramientas.

La historia S6.3 (2026-04-20) pobló la ontología de Strategy desde una lista cerrada de 18 nodos escrita antes de leer el workbook. El criterio de terminado contó nodos, no cobertura. La épica E6 prometió 34 hojas de trabajo y cerró con 15. Esta épica corrige eso con una prueba de cobertura página por página.

## Hipótesis

Si ESCALA trae todas las herramientas del workbook de Strategy, con guía de llenado, tips profesionales y una vista visual al terminar, el dueño puede llenar su estrategia sin un consultor al lado.

## Alcance

Solo el workbook de Strategy. People, Execution y Cash quedan fuera.

Herramientas que faltan y se agregan:

- Business Model Canvas (9 bloques, p. 7-11, checklist de Strategyzer en p. 11).
- Puente BMC → Scaling Up (p. 8): Segmentos de clientes = Cliente central; Propuesta de valor = Promesa de marca («empieza aquí»); Actividades clave = Actividades diferenciadoras; Canales = Caja de arena.
- Strategy Canvas (p. 7, 12): una sola hoja que une Cliente central, Promesa de marca, Actividades diferenciadoras y Caja de arena.
- Vision Summary (p. 7, 35, 36).
- Promesa de marca completa (p. 16-21): promesa principal y dos promesas de apoyo, cada una con una medida; Count On / Expect / Unique; tres pruebas (llena una necesidad, diferencia, es medible); antipromesas y compensaciones (p. 19).
- Preguntas del Cliente central (p. 20): mejor en / diferente / raro o malo.
- Hoja de Actividades diferenciadoras con competidores principales y diferencias en Personas, Producto, Operaciones y Términos (p. 25).
- Pronóstico de Caja de arena a 3-5 años (p. 28).
- Los prompts de IA de cada ejercicio (p. 9, 16, 20, 26, 29, 33, 34).

Cada herramienta debe tener:

1. Una guía de llenado paso a paso.
2. Tips profesionales, con investigación permitida vía `rai-research`.
3. Al terminar el llenado, un resultado visual que se abre como artefacto de Claude o como página HTML, además de guardarse en markdown o yaml.

## Restricciones

- No copiar imágenes del workbook al repo (derechos de Gazelles, p. 38).
- Las tarjetas de conocimiento citan número de página.
- Para E87, la prueba de cobertura página por página es obligatoria: cada página del workbook mapea a una tarjeta de conocimiento o se marca como contenido que no es herramienta.

## Piezas existentes

- Conocimiento: `conocimiento/strategy/` y `.scaleup/knowledge/strategy/`.
- Registro de hojas: `conocimiento/registry/worksheets.yaml` (15 hojas).
- Skills: `escala-skills/escala-strategy*`, `escala-skills/escala-worksheet`.
- Motor de hojas: `coaching/worksheet/`.
- Tablero de solo lectura: `escala_server/static/dashboards/strategy/bmc-board.html`.

## Apetito y riesgos

- Apetito: 8 historias tentativas (ver scope.md). Se decide el número final en diseño.
- Riesgo: repetir S6.3 si las historias se diseñan antes de leer el workbook. Mitigación: S87.1 es el inventario y la prueba de cobertura, y va primero.
- Riesgo: copiar material con derechos. Mitigación: solo texto y paráfrasis con cita de página.
