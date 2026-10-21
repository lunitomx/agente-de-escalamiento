# E87: Strategy workbook completo — Retrospective

**Fechas:** 2026-10-20 → 2026-10-21 · **Jira:** ESCALA-107 · **Historias:** 9 de 9 (S87.1–S87.9, ESCALA-108 a ESCALA-116), todas fusionadas a main y «Finalizada» en Jira. 40 puntos.

Cierre fuera del pipeline: la corrida de la épica quedó en pausa porque su conteo de historias no vio las 9 corridas sueltas de historia (defecto A62 en raise-conocido). Retro, scope y Jira se hicieron a mano.

## Qué entrega

- Las 38 páginas del workbook de Strategy quedan mapeadas: 9 sin herramienta (con razón) y 29 con nodo. La lista de pendientes quedó vacía (`pending: []`).
- La prueba de cobertura falla si una página vuelve a pendiente (`FROZEN_PENDING = frozenset()`, S87.8).
- Contrato de hoja guiada (`ToolGuide`): pasos con pregunta, cómo y ejemplo real; 3 tips o más con fuente; vista `cards` o `canvas`.
- Al guardar, el motor escribe yaml + HTML + `.md` y devuelve `open_cmd`; el skill `escala-worksheet` abre la vista.
- Hojas nuevas o extendidas: Cliente central, Lienzo de modelo de negocio, Promesa de marca, Actividades diferenciadoras, Caja de arena, Lienzo de estrategia (lee 5 hojas origen), Resumen de visión, Plan Personal de Una Página con tableros de visión.
- Motor en español: búsqueda sin acentos, paso 1 y lista en español, `name_es`, `summary_es` y `time_es` en todo el registro.

## Métricas

| Dato | Valor |
|---|---|
| Historias | 9 de 9 cerradas |
| Puntos | 40 de 40 |
| Hojas en el registro | 15 → 21 |
| Mapa E6 | 82 → 88 entradas; 78 → 84 en espera de evidencia de dominio |
| Páginas pendientes del workbook | 29 → 0 |
| Suite completa | 3661 (primera medición, S87.2) → 3801 pasan al cerrar |
| Funciones de prueba nuevas desde el inicio de la épica | 172 (`git diff` sobre `def test_`) |
| Commits de la épica | 145 |
| Tips investigados | 42 hallazgos; triangulados por familia independiente |

## Resultado por historia

1. **S87.1** — Mapa de 38 páginas y prueba de cobertura que solo encoge. Una ronda de corrección por la frontera pública.
2. **S87.2** — Raíz única del conocimiento, contrato `ToolGuide` y vista HTML + MD. Verify con 1 crítico; reintento lo cerró.
3. **S87.3** — 8 archivos de investigación, 42 hallazgos. La regla de familia bajó los triangulados de 35 a 24.
4. **S87.4** — Lienzo de modelo de negocio con puentes a otras hojas. Verify pasó a la primera.
5. **S87.5** — Promesa de marca. Verify FAIL: respuestas de varias líneas salían pegadas. Arreglo en la vista compartida.
6. **S87.6** — Cliente central completo y Actividades diferenciadoras. Verify pasó a la primera.
7. **S87.7** — Caja de arena y Lienzo de estrategia. Verify FAIL: resumen y tiempo en inglés en 17 de 20 hojas. Reintento.
8. **S87.8** — Resumen de visión atado a la ontología. Pendientes en cero. Verify pasó a la primera.
9. **S87.9** — Plan Personal de 8 áreas × 4 filas y tableros de visión. Verify con 3 arreglos; re-verify PASS.

## Qué salió bien

- **Olas en paralelo con orden de fusión.** La ola 3 corrió 4 historias a la vez (S87.4, S87.5, S87.6, S87.9). Cada historia dejó instrucciones de fusión para la siguiente; S87.8 fusionó S87.7 primero (T0) y no tuvo conflictos.
- **Receta de S87.2.** El contrato `ToolGuide` y su receta escrita permitieron agregar hojas sin tocar el motor (S87.4, S87.6, S87.8).
- **Investigación triangulada con 3 fuentes o más.** S87.3 definió la triangulación por familia (autor o escuela), no por dominio. S87.8 y S87.9 buscaron fuentes fuera de esas familias hasta llegar a 3; S87.9 subió de 2 a 5 de 5 con meta-análisis.
- **Recorrido del dueño por todas las hojas.** Desde S87.7 se recorre la salida de las 21 hojas del registro (paso 1, Revisión Final, `.md` y HTML). S87.8 lo hizo desde implementación y pasó el verify a la primera.
- **Mutaciones en verify.** Cada verify probó que las pruebas muerden (S87.7: 5 de 5; S87.8: 10 de 10).

## Qué falló

- **Dos verify FAIL.**
  - S87.5: ninguna prueba usaba una respuesta de varias líneas; el `.html` y el `.md` las pegaban en una línea.
  - S87.7: el implement revisó una hoja de muestra; el cambio del motor dejó texto en inglés en 17 de 20 hojas. El journal ya lo anotaba como «observación».
- **Recuentos en cada fusión.** El registro (`total_worksheets`), el mapa E6, el subtotal de espera y los conteos en `test_root.py`, `test_guide.py`, `test_view.py` y `test_e6_migration.py` chocaban al fusionar. La receta nombraba 3 conteos; había 5. Se resolvió regenerando y con `grep` del número viejo, nunca a mano.
- **Transiciones de Jira del motor.** Siempre fallaban con los nombres de estado en español («Finalizada»). Se transicionó a mano con `rai backlog transition --adapter jira`.
- **`raise_task_complete`.** No puede preparar `work/` porque está en `.gitignore`; y con `gate_scope` en `tests/` busca un `coaching/worksheet/src` que no existe. Commits a mano con chequeo de rama.
- **`raise_story_open`** no sirve si la rama ya existe (`branch-exists`); story y scope se escribieron a mano en S87.4–S87.7.
- **`rai signal emit-work`** rechaza la fase `verify` (raise-cli 3.1.2); se emitió `quality-review`.
- **Defecto A62 del pipeline.** El fan-out de historias de la corrida de la épica no cuenta corridas de historia sueltas. La épica quedó en pausa y se cerró fuera del pipeline.
- **Entorno.** Disco al 100 % en el verify de S87.6: 11 pruebas fallaron por espacio y pasaron al repetir.

## Patrones agregados en E87

| Patrón | Regla |
|---|---|
| PAT-221 | Revisar la frontera pública antes de agregar campos a contenido público |
| PAT-222 | Regenerar el mapa E6 al tocar yaml de `conocimiento/` |
| PAT-223 | Correr gates acotados también sobre archivos nuevos sin rastrear |
| PAT-226 | Contar triangulación por familia independiente, no por dominio |
| PAT-227 | Prueba de punta a punta del flujo del dueño desde el diseño |
| PAT-228 | Un off-by-one arreglado puede borrar la pantalla que usaba el índice extra |
| PAT-229 | Contrato `ToolGuide` para hojas guiadas |
| PAT-230 | Puente entre hojas como campo opcional que valida solo la forma |
| PAT-231 | Buscar el número viejo en las pruebas antes de confiar en la receta de conteos |
| PAT-232 | El estado guardado es por posición: pasos nuevos al final |
| PAT-233 | Una lista `pending` congelada no detecta que una página cubierta regrese |
| PAT-234 | Respuestas en lista por `answer_text` en toda superficie |
| PAT-235 | Leer la Revisión Final, no solo la vista guardada |
| PAT-236 | Acentos en `name_es`, con prueba |
| PAT-237 | Recorrido del dueño con al menos una respuesta de varias líneas |
| PAT-238 | La primera hoja con un tipo nuevo de respuesta destapa huecos de la vista; arreglar en `view.py` |
| PAT-239 | `check_coverage` no fallaba con páginas en `pending`; la prueba general debe atrapar la regresión |
| PAT-241 | Cambio de superficie del motor: recorrer todas las hojas del registro |
| PAT-242 | Buscar literales del motor que dupliquen un campo del registro |
| PAT-243 | El generador del mapa E6 no sobreescribe; generar a ruta temporal |
| PAT-244 | Vaciar la lista congelada al sacar el último elemento |
| PAT-245 | `raise_task_complete`: `git add -f` para `work/`; `gate_scope` en el paquete |

## Seguimiento

- **ESCALA-117:** 13 hojas antiguas sin guía muestran sus preguntas en inglés; la hoja de ciclo de conversión de efectivo muestra un dict crudo.
- Motor: guardar respuestas por id de paso, no por posición (PAT-232).
- Casilla de tiempo larga en el paso 1; mensajes de error en spanglish; guarda de idioma más fuerte que `_ENGLISH_MARKERS`.
- Fuentes complemento de tips sin verificar en línea (S87.7).

## Heutagogical Checkpoint

1. **¿Qué aprendí?** Una forma nueva de respuesta (varias líneas, lista) o un cambio del motor toca todas las hojas a la vez. Revisar una muestra no basta.
2. **¿Qué cambiaría del proceso?** En el diseño de la épica: cruzar cada contrato de datos con la frontera pública y listar todos los conteos con `grep` antes de la ola paralela.
3. **¿Mejoras al framework?** A62 (fan-out de la épica), transiciones con estados en español, `raise_task_complete` con `work/` y `src/`, `raise_story_open` con rama existente.
4. **¿Qué puedo hacer ahora?** Convertir una herramienta del workbook en hoja guiada con tips triangulados, recorrido del dueño probado y vista abierta, en una historia de 3 a 5 puntos.
