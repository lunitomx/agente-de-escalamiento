---
epic_id: "E44"
title: "Outcome Learning and Accountability"
status: "in_progress"
depends_on: ["E43"]
release_gate: ["E42"]
created: "2026-07-23"
---

# E44 — Aprendizaje a partir de resultados

## Objetivo

Hacer que ESCALA convierta una recomendación confiable en un ciclo empresarial
completo: decisión, acción, responsable, fecha, resultado, aprendizaje y
siguiente paso.

**Valor:** el dueño ya no necesita reconstruir de memoria por qué se decidió
algo ni si la recomendación funcionó.

## Historias

| ID | Historia | Tamaño | Estado | Demostración de valor |
|---|---|:---:|:---:|---|
| S44.1 | Registrar la decisión | M | Implemented; acceptance pending | Una recomendación puede aceptarse, rechazarse o quedar pendiente con su motivo. |
| S44.2 | Convertir decisión en acción | M | Implemented; acceptance pending | Cada acción relevante tiene responsable, plazo, métrica esperada y revisión. |
| S44.3 | Preguntar en el ritmo correcto | M | Implemented; acceptance pending | Daily, weekly, mensual o trimestral recuperan solo lo que toca revisar. |
| S44.4 | Comparar resultado con expectativa | M | Implemented; acceptance pending | ESCALA diferencia cambio observado, duda y posible explicación. |
| S44.5 | Confirmar aprendizaje y confianza | M | Implemented; acceptance pending | El dueño confirma, corrige o rechaza una lección antes de reutilizarla. |
| S44.6 | Mostrar el tablero de aprendizaje | S | Implemented; acceptance pending | Vista clara de decisiones, acciones, resultados y aprendizajes por confirmar. |

## S44.1 — Registrar la decisión

Toda recomendación que el empresario considere relevante termina en un estado:
aceptada, rechazada, aplazada o necesita más información. Se conserva el motivo,
la evidencia usada y la persona que tomó la decisión.

**Termina cuando:** una conversación posterior puede recuperar qué se decidió
sin volver a preguntarlo ni confundir recomendación con decisión.

## S44.2 — Convertir decisión en acción

Una decisión aceptada puede crear una acción concreta con responsable, fecha de
revisión, resultado esperado y métrica asociada cuando aplique.

**Termina cuando:** el sistema evita tanto acciones sin dueño como tareas
innecesarias; el empresario puede editar o cancelar una acción.

## S44.3 — Preguntar en el ritmo correcto

ESCALA revisará resultados en la daily, weekly, mensual o trimestral indicada
por el tipo de decisión. No debe tratar todas las acciones como urgentes.

**Termina cuando:** la pregunta de seguimiento es oportuna, explica qué se está
revisando y permite responder "todavía no hay resultado".

## S44.4 — Comparar resultado con expectativa

El sistema comparará la expectativa declarada con el resultado disponible y
mostrará: qué cambió, qué no cambió, qué evidencia falta y qué conviene revisar.

**Termina cuando:** la salida nunca llama causalidad a una coincidencia temporal.

## S44.5 — Confirmar aprendizaje y confianza

Un aprendizaje solo se vuelve reutilizable cuando está confirmado o revisado por
el empresario. Puede vencer, corregirse o rechazarse; no se vuelve permanente
por repetirse en una conversación.

**Termina cuando:** el sistema conserva procedencia, fecha, confianza y estado
de revisión sin almacenar conclusiones sensibles sobre personas sin permiso.

## S44.6 — Mostrar el tablero de aprendizaje

El cockpit mostrará decisiones abiertas, acciones vencidas, revisiones próximas,
resultados observados y aprendizajes pendientes.

**Termina cuando:** el dueño puede identificar la siguiente conversación o
acción importante sin navegar la memoria técnica.

## Dentro

- Cadena decisión → acción → resultado → aprendizaje.
- Cadencias de seguimiento y la opción "sin resultado todavía".
- Corrección humana y vigencia de aprendizaje.
- Vista ejecutiva de progreso.
- Casos de Cash, People, Strategy y Execution.

## Fuera

- Inferencias de desempeño, ánimo o personalidad de empleados.
- Rankings entre personas o empresas.
- Automatización de cambios al producto → E46.
- Colaboración de especialistas → E45.
- Sincronización de memoria entre instalaciones.

## Criterios de terminación

- [x] Una recomendación puede ligarse a una decisión explícita.
- [x] Una decisión aceptada puede llevar una acción con responsable y fecha.
- [x] La revisión respeta la cadencia y puede registrar falta de resultado.
- [x] Resultado observado, interpretación y causalidad se muestran separados.
- [x] El empresario puede confirmar, corregir o rechazar un aprendizaje.
- [x] La memoria conserva origen, fecha, confianza y vigencia.
- [x] El tablero ejecutivo no expone tecnicismos ni datos de otra empresa.
- [x] Los cuatro pilares tienen al menos un ciclo calificado.
- [ ] Retrospectiva y evidencia de aceptación completadas.

## Dependencias

```text
E43 recomendación confiable
           ↓
S44.1 decisión → S44.2 acción → S44.3 seguimiento
                                      ↓
                           S44.4 resultado → S44.5 aprendizaje
                                                     ↓
                                            S44.6 tablero ejecutivo
```

- E43 cerrada con recomendaciones trazables.
- E42 sigue siendo gate de release/hardware/aceptación humana, no bloqueo para
  construir el ciclo local con fixtures y decisiones sintéticas.
- Sesiones, tareas, memoria, grafo y cockpit locales existentes.
- Una empresa de prueba dispuesta a revisar al menos un resultado por cadencia.

## Plan de implementación

### Secuencia

| Orden | Historia | Razonamiento | Habilita |
|---:|---|---|---|
| 1 | S44.1 | Sin decisión explícita no hay aprendizaje que atribuir. | S44.2-S44.5 |
| 2 | S44.2 | Define dueño, plazo y expectativa antes de cualquier recordatorio. | S44.3-S44.4 |
| 3 | S44.3 | Prueba que el seguimiento puede ser útil sin ser invasivo. | S44.4 |
| 4 | S44.4 | El riesgo mayor es confundir resultado con causalidad. | S44.5-S44.6 |
| 5 | S44.5 | Solo se actualiza la memoria después de revisión humana. | S44.6 |
| 6 | S44.6 | Hace visible el ciclo completo para el dueño. | Gate hacia E45 |

### Hitos

| Hito | Historias | Criterio de éxito |
|---|---|---|
| M1 — Un compromiso útil | S44.1-S44.2 | Una recomendación aceptada tiene dueño, plazo y expectativa. |
| M2 — Seguimiento honesto | S44.3-S44.4 | El sistema registra un resultado o reconoce que todavía no existe. |
| M3 — Memoria con criterio | S44.5-S44.6 | El dueño aprueba un aprendizaje y lo consulta desde el cockpit. |
| M4 — Gate E45 | — | Existe historial suficiente para evaluar si un equipo de especialistas agrega valor. |

### Trabajo en paralelo

S44.6 puede preparar su vista a partir del contrato de S44.1 y S44.2, pero se
integra después de S44.5 para no mostrar aprendizajes no revisados.

### Seguimiento

| Story | Estado | Evidencia esperada |
|---|---|---|
| S44.1 | Implemented; owner acceptance pending | Registro de decisión aceptada, rechazada y aplazada. |
| S44.2 | Implemented; owner acceptance pending | Acción con responsable, fecha y expectativa. |
| S44.3 | Implemented; owner acceptance pending | Seguimientos por daily, weekly y trimestre. |
| S44.4 | Implemented; owner acceptance pending | Comparaciones sin causalidad inventada. |
| S44.5 | Implemented; owner acceptance pending | Aprendizaje confirmado, corregido y rechazado. |
| S44.6 | Implemented; owner acceptance pending | Vista ejecutiva y prueba de lectura empresarial. |

## Evidencia local (2026-08-27)

- Módulo local: `escala_server/outcome_learning.py`.
- API: decisiones, acciones, resultados, aprendizajes y cockpit por empresa.
- Cobertura: Cash, People, Strategy y Execution; People requiere consentimiento explícito.
- Calificación técnica reproducible: `scripts/qualify_e44_e45.py`, con cuatro ciclos sintéticos confirmados, consentimiento People, `no_result_yet`, causalidad no reclamada y cockpit sin IDs internos.
- Gates locales: `tests/test_outcome_learning.py`, `tests/test_escala_server.py`, `tests/test_qualify_e44_e45.py`, Ruff y Pyright.
- Pendiente de cierre: una aceptación real de empresario y retrospectiva; la calificación sintética no las sustituye.

## Riesgos

| Riesgo | L/I | Mitigación |
|---|:---:|---|
| Cargar al empresario con seguimiento excesivo | M/H | Cadencia explícita, opción de aplazar y solo acciones relevantes. |
| Llamar causa a una coincidencia | M/H | Separar hecho, interpretación y causalidad; requerir confirmación. |
| Guardar información delicada sobre personas | M/H | Consentimiento, límites de People y revisión humana antes de promover. |
| La memoria se vuelve una lista de notas sin decisiones | M/M | Solo promover registros que tengan fuente, estado y siguiente revisión. |

## Parking lot

- Alertas automáticas fuera de la conversación → evaluar solo después de probar
  las cadencias dentro de ESCALA y sin añadir servicios hospedados.
