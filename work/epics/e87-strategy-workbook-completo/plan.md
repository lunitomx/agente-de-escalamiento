# E87 · Plan — Strategy workbook completo

Jira: ESCALA-107 · Fecha: 2026-10-20 · Entradas: scope.md, design.md (9fc6d537), adversarial-review.md.
Total: 9 historias, 40 puntos, 5 olas, 4 hitos. Se conservan las olas del diseño; no hay conflicto real de dependencias.

## Olas y dependencias

| Ola | Historias (Jira) | Puntos | Depende de |
|---|---|---|---|
| 1 | S87.1 (ESCALA-108) en paralelo con S87.3 (ESCALA-110) | 3 + 5 | nada |
| 2 | S87.2 (ESCALA-109) | 8 | S87.1 |
| 3 | S87.4 (111) ∥ S87.5 (112) ∥ S87.6 (113) ∥ S87.9 (116) | 5+3+5+3 | S87.2 y S87.3 |
| 4 | S87.7 (114) | 5 | S87.4, S87.5, S87.6 |
| 5 | S87.8 (115) | 3 | S87.7 |

Notas:
- S87.3 (solo investigación, escribe en `work/research/e87-tips/`) no toca código: corre durante toda la ola 2 si tarda más que S87.1.
- S87.2 es el cuello de botella (8 pts). Si no cabe en una sesión, se parte en "raíz + contrato" (3) y "vista + skill" (5). Las historias de la ola 3 solo necesitan ambas mitades terminadas.
- S87.9 no depende de S87.7: puede cerrar en la ola 3 sin esperar al Strategy Canvas.
- S87.8 podría empezar su investigación junto a la ola 4, pero su prueba de `derived_from` exige que S87.7 ya esté fusionada. Se mantiene en la ola 5.

## Hitos

1. **M1 Cimiento (olas 1-2):** mapa de cobertura con `pending`, tips de las 8 herramientas, motor con raíz única + `ToolGuide` + vista + skill. Salida: `list_worksheets()` desde el repo da 15 (hoy 0).
2. **M2 Hojas base (ola 3):** BMC, Promesa de marca, Cliente central + Actividades diferenciadoras, Plan Personal.
3. **M3 Lienzo (ola 4):** Caja de arena + Strategy Canvas con `derived_from`.
4. **M4 Cierre (ola 5):** Vision Summary; `pending` vacío; `rai gate check --all`.

## Un worktree por historia

Cada historia en su propio worktree y su rama `story/s87.N/<nombre>`, creada desde main actualizado después de fusionar la ola anterior (`git fetch` primero; main local puede estar atrasado). Verificar la rama en el mismo comando del commit.

## Archivos compartidos (puntos calientes)

| Archivo | Quién lo toca | Riesgo | Cómo se evita |
|---|---|---|---|
| `conocimiento/registry/worksheets.yaml` (línea `total_worksheets: 15`, texto "all 15 worksheets" y lista) | S87.4 (+bmc), S87.6 (+differentiating-activities), S87.7 (+sandbox, +strategy-canvas), S87.8 (+vision-summary); S87.5 y S87.9 solo editan entradas existentes | Alto en ola 3: S87.4 y S87.6 cambian la misma línea del contador y añaden al final de la lista | Cada historia añade su entrada y recalcula `total_worksheets` al hacer rebase; la prueba de S87.1 o S87.2 exige `total == len(lista)`, así que un conflicto mal resuelto falla visible. Añadir entradas en bloque propio por decisión (strategy) para no chocar con el final del archivo |
| `conocimiento/strategy/workbook-coverage.yaml` (lista `pending`) y la lista congelada en `tests/test_e87_workbook_coverage.py` | Todas las historias de herramienta S87.4 a S87.9 quitan sus páginas de `pending` | Medio: líneas vecinas en una lista de una línea (`pending: [7, 8, ...]`) conflictúan siempre | S87.1 escribe `pending` en **una página por línea** (formato de lista en bloque) para que cada historia borre solo sus líneas y las fusiones sean limpias. La lista congelada de la prueba no se edita (solo puede encoger el archivo, no la prueba). Entradas `pages:` de cada historia: bloques separados por página |
| `conocimiento/strategy/worksheets/worksheet-core-customer.yaml` | S87.2 (la usa de validación), luego S87.6 | Bajo: son olas distintas | S87.6 parte de main con S87.2 ya fusionada |
| `coaching/worksheet/__init__.py`, `guide.py`, `view.py`, `escala-skills/escala-worksheet/SKILL.md`, `boards/render.py` | Solo S87.2 | Bajo en olas 3+: las historias de herramienta no deben tocarlos | Regla: si una historia de ola 3+ necesita cambiar el motor, se parkea y se avisa; cambios de motor en una historia aparte |
| `conocimiento/strategy/tools/sandbox.yaml` | S87.1 (corrige tarjeta) y S87.7 (hoja) | Bajo | Distintas olas |
| `conocimiento/people/worksheets/oppp.yaml`, `people/tools/oppp.yaml` | Solo S87.9 | Ninguno | — |
| `conocimiento/strategy/concepts/brand-promise.yaml` | Solo S87.5 | Ninguno | — |
| `.scaleup/` | Nadie | Prueba lo prohíbe | Lista congelada de S87.1 |
| `work/epics/e87-.../` (scope, retros) y Jira | Cada historia | Bajo | Cada una en su subcarpeta `stories/s87.N/` |

## Orden de fusión (minimiza conflictos)

1. Ola 1: **S87.1** primero (define el formato de `pending` y las pruebas), luego **S87.3** (solo `work/research/`, sin conflicto posible).
2. Ola 2: **S87.2** (rebase sobre S87.1).
3. Ola 3, de menos a más puntos de contacto con el registro: **S87.9** (no agrega hoja, solo edita `oppp`), **S87.5** (edita entradas, no suma hoja), **S87.6** (+1 hoja), **S87.4** (+1 hoja, el último; quien fusiona al final recalcula `total_worksheets`). Cada una hace `git fetch` + rebase sobre main justo antes de fusionar y vuelve a correr sus pruebas y la de cobertura. Las 4 ramas pueden implementarse a la vez; solo la fusión es en serie.
4. Ola 4: **S87.7**. Ola 5: **S87.8**.

Regla de rebase para los dos puntos calientes: tras un conflicto, recontar `total_worksheets` con la lista real y confirmar que la prueba de cobertura sigue con `pending` ⊆ lista congelada.

## Riesgos de la secuencia

- PRECAUCIÓN: S87.2 retrasa a 4 historias. Mitigación: partirla en dos si pasa de una sesión; S87.3 corre en paralelo para no perder tiempo.
- PRECAUCIÓN: la instalación debe seguir en modo editable (`install.sh:229`); la prueba de S87.2 lo fija.
- S87.7 es la única con dependencia triple; si S87.4 se atrasa, S87.7 puede empezar con `worksheet-bmc` marcado `required: false`, pero entonces la validación de `sheet` lo exigirá en el registro: no se adelanta, se espera.

## Machine
```yaml
waves: [[S87.1, S87.3], [S87.2], [S87.4, S87.5, S87.6, S87.9], [S87.7], [S87.8]]
merge_order: [S87.1, S87.3, S87.2, S87.9, S87.5, S87.6, S87.4, S87.7, S87.8]
milestones: {M1: [S87.1, S87.2, S87.3], M2: [S87.4, S87.5, S87.6, S87.9], M3: [S87.7], M4: [S87.8]}
hotspots:
  - conocimiento/registry/worksheets.yaml
  - conocimiento/strategy/workbook-coverage.yaml
```
