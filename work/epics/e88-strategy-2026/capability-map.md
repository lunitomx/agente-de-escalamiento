# E88 Strategy 2026: mapa de capacidades (ESCALA-119)

Commit base: 1da25f40. Método: lectura directa (el grafo no indexa `coaching/worksheet`).

## Parte 1. Hallazgos del gemba

| Capacidad | Estado | Disposición |
|---|---|---|
| Motor de hojas (`coaching/worksheet/`) | `ai_prompt` es un solo objeto con solo `text`. Se usa en `__init__.py` (revisión final, 2 sitios) y `view.py` (HTML y MD) | extender (S88.1) |
| Hoja guiada completa | `differentiating-activities` y `vision-summary` ya lo son. `swt` no tiene `guide`: no muestra prompt | reusar; SWT migrar |
| 5 hojas nuevas | Borradores en scratchpad: los 5 pasan `parse_guide` (core-purpose 8 pasos, bhag 7, vivid-vision 17, life-purpose 4, fanocracy 7) | reusar borradores |
| Conceptos | `strategy/concepts/core-purpose.yaml` y `bhag.yaml` existen; sin hoja. Fanocracy, Vivid Vision y Personal Why no existen | extender / nuevo |
| Encadenar hojas | `GuideStep.next_sheet` y `derived_from` ya existen. `coaching/journey` es otro concepto (viaje del cliente) | extender |
| Mapa de cobertura | `tests/fixtures/e87-workbook-coverage.yaml` (38 p., 2025). No hay mapa 2026 | extender |
| Registro y migración E6 | `total_worksheets: 21` pasa a 26. `test_e6_migration` pide 88 entradas (84 await-domain-evidence): pasa a 93 y 89. Regenerar con `scripts/build_e6_migration_map.py` | extender |
| AI Setup | No existe | nuevo (depende del motor) |

Código muerto / pendientes: no se corrió vulture (no instalado). Sin TODO/FIXME en `coaching/worksheet/`.

## Parte 2. Backlog (Jira, ESCALA)

- ESCALA-108 (S87.1, cobertura 38 páginas) y ESCALA-115 (S87.8, Vision Summary): Finalizadas. Base de reuso.
- ESCALA-120..125: Tareas por hacer. Sin trabajo en curso que duplique E88.

## Parte 3. Validación del alcance

- Dentro de alcance y correcto: cambio mínimo del motor, 5 hojas, prompts 2026, mapa de 24 páginas.
- Riesgo 1: el id `worksheet-bhag` lleva la palabra que el Resumen de visión prohíbe en texto público. Confirmar si aplica a ids; si sí, renombrar (p. ej. `worksheet-meta-grande`).
- Riesgo 2: no hay texto 2026 en el repo; la prueba anticopia compara con el texto 2025.
- Riesgo 3: cada yaml nuevo bajo `conocimiento/` rompe el conteo de `test_e6_migration`; regenerar el mapa en S88.3 y S88.4.
- Nota: `ontology/v2/` sin nodos nuevos (alcance); la migración E6 solo añade entradas await-domain-evidence.
