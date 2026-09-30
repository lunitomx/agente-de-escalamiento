# Capability map E84 (ESCALA-50)

Gemba por lectura directa en `8978f79`. Sin consultas al grafo ni herramientas `pipeline_*` (motor de pipeline roto, defecto A53) y sin leer Jira (las historias ESCALA-63..66 ya existen). Las rutas se probaron corriendo `route_request`, también sobre una copia del catálogo en memoria (no se cambió ningún archivo).

## Part 1 - Gemba findings
| Capability | State | Where | Disposition |
|---|---|---|---|
| Tablero de progreso actual | Funciona: markdown de sólo lectura con 4 secciones (scores 1-5, historial de pulsos, victorias, atención). En inglés y le dice al dueño "Run /escala-diagnose" | `coaching/dashboard/__init__.py`, `escala-skills/escala-dashboard/SKILL.md`, 23 tests | extend: se conserva tal cual como acción por defecto; se añaden `recommend` y `render` |
| Tablero de evidencia sin score (conocido / no comparable / pendiente) | Funciona | `coaching/evidence/dashboard.py`, acción `facts_dashboard` | reuse: es el corazón de "lo que falta se muestra como falta" |
| Facts con periodo, fuente local y confianza | Funciona | `coaching/evidence/facts.py` | reuse: fuente de los números del tablero |
| Reporte local autocontenido HTML + MD + JSON, determinista y escapado | Funciona (E38 S38.4) | `escala_server/financial/report.py` | reuse: patrón del generador |
| Tableros del servidor local (`/api/worksheets`) | Funcionan sólo con `escala_server` corriendo | `escala_server/static/dashboards/**`, `escala_server/dashboard.py` | no se usan; su reparación es de E80 S80.2 |
| HTML con Chart.js desde CDN | Legacy, fuera del catálogo | `escala-agent/skills/escala-dashboard-generado/SKILL.md` | rechazado: pide internet y llama a un tercero |
| Conteos del embudo en el diagnóstico | Funciona; campos ausentes quedan ausentes | `coaching/diagnose/models.py` `FunnelMetrics` | reuse: etapas con número |
| Diagnóstico sólo con evidencia local `fact`; `assumptions`, `open_questions` | Funciona | `coaching/diagnose/primary_constraint.py` | reuse (S84.2) |
| Especialista de strategy con "journey" en su trigger | Funciona | `escala_server/specialist_team.py:63`, `adapters/specialists/contract.json` | reuse; trigger sin cambio |
| Ruta de pedidos de journey | Parcial: "cliente" llega a Strategy; "pocos compran", "no vendo lo suficiente", "marketing" caen en welcome | `catalog.yaml` routes | extend (S84.1) |
| Ruta de pedidos de tablero | No existe: "dashboard", "gráfica", "indicadores" caen en welcome; "tablero de mis ventas" cae en Cash | `catalog.yaml` routes | extend (S84.3) |
| Catálogo cerrado (64 procedimientos, 65 capacidades) | Funciona; el 64 está fijo en 3 sitios | `catalog.yaml`, `tests/test_capability_catalog.py:26-27`, `escala_server/capabilities.py:192` | +1 procedimiento interno |
| Contrato de research y reporte local (E83 S83.1) | Funciona | `coaching/research/` | reuse: forma de modelos, acciones por stdin, guardar sólo con el sí |
| Journey como hipótesis (E71 S71.5) | Diseñado, sin código | `work/epics/e71-.../design.md` `JourneyHypothesis` | extend: se pliega en S84.1/S84.2 |
| Asesor de tableros (E73) | Planeado, sin código | `work/epics/e73-adaptive-dashboard-advisor/` | extend: se absorbe su núcleo (decisión propuesta) |
| Carpeta local ignorada | `.escala/my-company/` sí; `.escala/agent/memory/` no | `.gitignore:78`, `git check-ignore` | reuse `.escala/my-company/`; lo otro va como hallazgo a E79 |
| Mismo formato local en Claude, Codex y ChatGPT Work | No verificado | - | new (matriz en S84.4) |

Gaps: G1 sin modelo, entrevista ni disparador de journey; G2 sin memoria de "después"/"no"; G3 pedidos de ventas/marketing y de tablero caen en welcome; G4 sin recomendador (qué medir, por qué, de dónde, cada cuánto); G5 sin archivo de tablero portátil; G6 E73 se solapa; G7 el tablero de progreso habla inglés y muestra comandos (E80); G8 `facts.yaml` vive en ruta no ignorada (E79).

## Part 2 - Backlog scan
Local únicamente (no se tocó Jira). E71 (ESCALA-35) absorbida por E83; su S71.5 (journey) llega aquí por decisión del dueño. E73 (ESCALA-37, planned, sin commits) es casi el mismo alcance que S84.3 + S84.4. E80 (ESCALA-43) es dueño de reparar el tablero y los scores actuales. E75 (ESCALA-39, in_progress) nombra a E71/E73 como destinos del hand-off; ahora serían E83/E84. E85 (ESCALA-51) decide si ESCALA corre en ChatGPT Work.

## Part 3 - Scope validation
- `coaching/dashboard` se **extiende**, no se reemplaza: su salida de progreso queda como acción por defecto (los 23 tests no cambian) y no se toca su cálculo de scores (E80).
- "Un dato faltante se muestra como faltante" ya existe como regla y como código (`build_evidence_dashboard`); E84 lo reutiliza en vez de reescribirlo.
- El journey cabe en un solo procedimiento interno; los tableros caben en `escala-dashboard`, que ya está en el catálogo.
- El formato portátil no puede depender de un servidor, de internet ni de JavaScript: HTML autocontenido más su gemelo Markdown.
