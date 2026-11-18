# E88: Strategy 2026 — Retrospective

**Fechas:** 2026-11-18 → 2026-11-18 · **Jira:** ESCALA-119 · **Historias:** 7 de 7 (S88.1–S88.7, ESCALA-120 a ESCALA-126). Todas están fusionadas a main (31b8ccee) y en «Finalizada» en Jira. 25 puntos (24 planeados + S88.7 de 1).

Cierre fuera del pipeline, igual que E87. La corrida de la épica (b36b69d9) quedó en pausa en la fase `stories` por el defecto A62: no cuenta las corridas sueltas de historia. Retro, scope y Jira se hicieron a mano.

## Qué entrega

- Los 10 ejercicios del Workbook de Strategy 2026 tienen hoja en español y prompt 2026. Caben en 8 hojas: SWT y Resumen de visión llevan 2 ejercicios cada una.
- Motor: una hoja muestra varios prompts (`extra_prompts` en el inicio o el final). Al guardar, la hoja dice cuál sigue («Siguiente hoja»).
- Hojas nuevas: Propósito central, Meta grande (BHAG), Visión vívida, De clientes a fans y Tu propósito de vida.
- Prompts 2026: «Arranque con IA» en SWT, más los de Actividades diferenciadoras y Resumen de visión. Al empezar una hoja completada, la reabre y guarda un respaldo con fecha.
- Recorrido del Strategy Day en orden, de la SWT al Resumen de visión. Se prueba de punta a punta, incluso con la SWT ya completada.
- Mapa de cobertura 2026: 24 de 24 páginas y 10 de 10 ejercicios, con `pending: []`. Las páginas 1, 3, 21, 23 y 24 se leyeron del PDF del cuaderno en S88.8: la 21 es el compromiso del ejercicio 10 (va a Resumen de visión); 1, 3, 23 y 24 son portada, introducción, notas y derechos de autor.
- S88.7: el dueño ya no ve `/escala-worksheet` al guardar, al listar, en la vista ni en el aviso de hoja sin empezar.
- Instalado y verificado en la ESCALA de Eduardo el 2026-11-18 a las 18:11 UTC, con el hash dce86ea1 y luego 31b8ccee. La lista muestra 26 hojas y la SWT muestra «Arranque con IA».

## Métricas

| Dato | Valor |
|---|---|
| Historias | 7 de 7 cerradas (6 planeadas + 1 que salió de la retro de S88.6) |
| Puntos | 25 |
| Hojas en el registro | 21 → 26 |
| Mapa E6 | 88 → 93 entradas; 84 → 89 en espera de evidencia de dominio |
| Páginas 2026 mapeadas | 24 de 24 |
| Suite completa | 3906 pasan al cerrar, 5 omitidas; pyright 0 errores; ruff limpio |
| Funciones de prueba nuevas | 77 (`git diff` sobre `def test_`) |
| Commits de la épica | 69 |
| Duración | 1 día, con un reinicio de la Mac a la mitad |

## Qué salió bien

- **Paralelo con orden de fusión.** S88.1, S88.2 y S88.3 corrieron a la vez. S88.4 y S88.5 siguieron después, y S88.6 al final. Cada historia fusionó main antes de cerrar, sin conflictos de código.
- **Receta del mapa E6.** Se regeneró con `--repo . --output` en cada fusión. Ningún conflicto del json se resolvió a mano.
- **El motor ya tenía `next_sheet`.** S88.6 fue solo datos y pruebas.
- **Instalación probada en la Mac real**, no solo en el repo. Así salió que la copia instalada estaba 99 cambios atrás y con un cambio local en conflicto.
- **Cosas sin documentar quedaron marcadas, no inventadas** (5 páginas). Pero el PDF sí estaba en la Mac: S88.8 las leyó y la página 21 resultó ser ejercicio.

## Qué falló

- **Conteo de hojas contra ejercicios.** El criterio decía «9 hojas y 9 vistas», pero eran 8. Hay que contar hojas únicas al escribir los criterios.
- **El comando visible pasó las pruebas.** La prueba de S86.1 revisaba solo SKILL.md, no lo que imprime el motor. S88.1 metió el comando en «Siguiente hoja» y nada falló. S88.7 lo arregló y extendió la prueba.
- **La copia instalada no se actualizaba sola.** Estaba 99 cambios atrás, con un commit local en conflicto y 198 archivos que modificó RaiSE. `/escala-update` se habría detenido. Se respaldó en la rama `respaldo/instalada-2026-11-18` y se alineó con GitHub.
- **Defecto A68.** `pipeline start --token-file` no escribe el token en 3.1.7. Se usó la receta de registrar, restaurar y reemitir el token.
- **Defecto A62.** Es el mismo de E87: la épica se cierra fuera del pipeline.
- **Revisión sin retro.** La fase review pidió el artefacto retro (A12) cuando el agente no lo emitió.

## Patrones reforzados

| Patrón | Uso en E88 |
|---|---|
| PAT-221 | Las páginas solo viven en `tests/fixtures/`; los textos del dueño no las nombran |
| PAT-222 | Mapa E6 regenerado en cada fusión |
| PAT-227 | Recorrido del dueño de punta a punta, incluido el caso de reabrir |
| PAT-236 | Acentos en `name_es` de las 5 hojas nuevas |
| PAT-L-3635 | Sin comandos visibles, ahora también en las salidas del motor |

## Pendiente fuera de la épica

- `coaching/progress/` todavía sugiere `/escala-worksheet` en su resumen de avance. No está en el recorrido del Strategy Day.
- **Lección:** el brief de cada agente debe dar la ruta del PDF del cuaderno. El agente de S88.6 no la tenía y marcó 5 páginas como no documentadas.
