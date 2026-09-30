# Capability map E83 (ESCALA-49)

Gemba por lectura directa en `6b13dd2`. Sin consultas al grafo (motor de pipeline roto, defecto A53) y sin leer Jira (las historias ESCALA-57..61 ya existen).

## Part 1 - Gemba findings
| Capability | State | Where | Disposition |
|---|---|---|---|
| Puerta única y catálogo cerrado (63 procedimientos, 64 capacidades) | Works | `escala-skills/escala/SKILL.md`, `escala-skills/catalog.yaml`, `tests/test_capability_catalog.py:26-27` | reuse; +1 procedimiento interno |
| Ruta a Strategy por palabra clave | Works only for `competencia`, `cliente`, `estrategia`, `opsp`, `rumbo`; "mi mercado", "mis competidores", "tendencias" caen en welcome (probado con `route_request`) | `catalog.yaml` routes, `escala_server/capabilities.py:199` | extend (S83.1) |
| Especialista privado de strategy con regla "nunca afirmar mercado sin fuente y fecha" | Works | `adapters/specialists/contract.json`, `adapters/*/agents/escala-strategy.*`, `validators/specialist_agents.py` | reuse; trigger ya cubre market/competition |
| Quinto especialista "research" | Rechazado por test (`choose_team({"areas": ["research"]})` falla) | `tests/test_specialist_team.py:96-98` | no se crea |
| SWT canónico (sólo datos internos) | Works | `escala-skills/escala-strategy-swt/SKILL.md` | extend (S83.4) |
| Paquete de evidencia y facts con procedencia; fuentes deben ser locales, sin URL | Works | `coaching/evidence/models.py`, `coaching/evidence/facts.py`, `coaching/core/__init__.py:34` | extend (el reporte local es la fuente) |
| Diagnóstico con evidencia `fact` de fuentes narrativas; `assumptions` y `open_questions` | Works | `coaching/diagnose/models.py`, `coaching/diagnose/primary_constraint.py` | reuse (S83.5) |
| Contrato de research, TAM/SAM/SOM, competidores | Planned, sin código | `work/epics/e71-market-intelligence-research/` | absorber en E83 (decisión propuesta) |
| Hand-off del diagnóstico a máximo dos deep dives elegidos por el usuario | Diseñado; S75.1-S75.2 hechas | `work/epics/e75-.../design.md` | reuse |
| Carpeta local ignorada | Works | `.gitignore:78` (`.escala/my-company/`) | reuse |
| Búsqueda web disponible en Claude, Codex, ChatGPT Work | No verificado en este repo | - | new (verificar en S83.5) |

Gaps: G1 sin módulo de research; G2 rutas de mercado/tendencias; G3 SWT sin evidencia externa; G4 diagnóstico sin vía documentada para afirmaciones externas; G5 búsqueda web por plataforma sin verificar; G6 E71 se solapa y no tiene disposición.

## Part 2 - Backlog scan
Local únicamente (no se tocó Jira): E71 (ESCALA-35, planned, sin commits) se solapa en encuadre, fuentes, mercado y competidores; su customer journey (S71.5) se solapa con E84 (ESCALA-50). E75 (ESCALA-39) ya prevé el hand-off a "research/market". E85 (ESCALA-51) decide si ESCALA corre en ChatGPT Work.

## Part 3 - Scope validation
- Los tres módulos caben en un solo procedimiento interno con tres modos; ninguno necesita comando público ni especialista nuevo.
- El módulo 3 no debe producir un segundo SWT: alimenta a `escala-strategy-swt`.
- "Enlace a la evidencia del diagnóstico" no puede ser un `Fact` con URL (el validador lo rechaza); el enlace es el reporte local más la decisión confirmada.
- El comportamiento sin búsqueda web es el caso común no verificado; va en el contrato (S83.1), no al final.
