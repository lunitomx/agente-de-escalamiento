# Mapa de historias E56

## Secuencia

| Orden | Historia | Resultado | No se avanza sin |
|---:|---|---|---|
| 1 | S56.1 Inventario y decisiones Bitter Pill | Registro de línea base y disposición de cada capacidad. | Caso de regresión y dueño por cada retiro/fusión. |
| 2 | S56.2 Contrato del orquestador `escala` | Una entrada pública que enruta intención y explica límites. | Casos naturales y contrato de salida. |
| 3 | S56.3 Fuente única y distribución | Artefactos reproducibles para Claude, Codex y Hermes. | Prueba de instalación limpia y control de deriva. |
| 4 | S56.4 Compatibilidad y migración `scaleup-*` | Adaptadores temporales sin lógica duplicada. | Mapa de aliases, aviso y rollback. |
| 5 | S56.5 Internalización y retiro seguro | Catálogo reducido según decisiones aprobadas. | Reemplazo probado y recibo de retiro. |
| 6 | S56.6 Calificación empresarial y cierre | Evidencia de que un no técnico obtiene valor sin comandos. | Recorrido completo y documentación de migración. |

## S56.1 — Inventario y decisiones Bitter Pill

**Como** dueño de producto, **quiero** saber qué capacidad existe realmente y
por qué se conserva o cambia, **para** que una consolidación no pierda valor.

**Incluye:** escaneo reproducible de las 62 capacidades `escala-*`, 39
`scaleup-*` y espejos; normalización por intención; excepción Rockefeller;
registro inicial, dueño, consumidor, pruebas y disposición.

**Aceptación:** toda entrada tiene `keep`, `internalize`, `merge` o `retire`;
una decisión de retirar/fusionar cita reemplazo y regresión; no hay duplicado
sin decisión explícita.

## S56.2 — Contrato del orquestador `escala`

**Como** empresario no técnico, **quiero** contarle mi necesidad a ESCALA sin
aprender comandos, **para** llegar al siguiente paso útil.

**Incluye:** intención inicial/retomar/diagnosticar/ayuda, carga de contexto
permitido, enrutamiento por registro, respuesta con evidencia y límites, y
casos negativos cuando falte información.

**Aceptación:** cinco recorridos naturales alcanzan una capacidad o límite
correcto; ningún recorrido requiere escoger una carpeta, skill o slash-command.

## S56.3 — Fuente única y distribución determinista

**Como** mantenedor, **quiero** que cada plataforma reciba el mismo contrato
desde una sola fuente, **para** que no haya espejos editables que se contradigan.

**Incluye:** formato/validador del manifest, generador o empaquetador elegido,
integridad de artefactos y pruebas de instalación limpia en Claude, Codex y
Hermes.

**Aceptación:** una alteración no declarada en un artefacto soportado falla; el
instalador reporta qué instaló y sólo toma fuentes declaradas.

## S56.4 — Compatibilidad `scaleup-*`

**Como** usuario de una instalación anterior, **quiero** que mis accesos
legados tengan una transición comprensible, **para** no perder continuidad.

**Incluye:** tabla alias→canónico, adaptadores sin segunda lógica, aviso de
migración, condición de caducidad, rollback y resolución explícita de
`scaleup-execution-rockefeller`.

**Aceptación:** cada alias conservado resuelve exactamente el contrato
canónico; un alias sin reemplazo falla con ayuda accionable, nunca en silencio.

## S56.5 — Internalización y retiro seguro

**Como** producto, **quiero** exponer sólo capacidades que aportan valor
reconocible, **para** que el catálogo no sea una carga para el empresario.

**Incluye:** mover helpers a módulos internos cuando corresponda, retirar sólo
entradas aprobadas y actualizar referencias, documentación y pruebas.

**Aceptación:** no quedan referencias rotas ni dos implementaciones para una
misma capacidad; cada retiro tiene recibo, reemplazo y prueba regresiva.

## S56.6 — Calificación empresarial y cierre

**Como** empresario nuevo, **quiero** instalar y obtener una siguiente acción
útil con mis propias palabras, **para** adoptar ESCALA sin entrenamiento técnico.

**Incluye:** recorrido de instalación limpia, primera conversación, retomar,
diagnóstico y ayuda; documentación en español y catálogo empresarial derivado
de la evidencia, no de directorios.

**Aceptación:** el recorrido produce recibos de plataforma, resultado,
limitaciones y siguiente acción; cualquier brecha abre reparación y se repite
el caso antes de cerrar E56.
