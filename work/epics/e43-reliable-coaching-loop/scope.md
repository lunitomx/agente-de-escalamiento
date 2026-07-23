---
epic_id: "E43"
title: "Reliable Coaching Loop"
status: "planned"
depends_on: ["E42"]
created: "2026-07-23"
---

# E43 — Respuestas confiables antes de recomendar

## Objetivo

Hacer que ESCALA responda preguntas empresariales importantes con un ciclo
visible de objetivo, evidencia, revisión y recomendación; si falta información,
debe preguntar antes de concluir.

**Valor:** el empresario deja de recibir una respuesta que "suena bien" y
recibe una recomendación que puede verificar, entender y convertir en acción.

## Historias

| ID | Historia | Tamaño | Estado | Demostración de valor |
|---|---|:---:|:---:|---|
| S43.1 | Aclarar la decisión | S | Pending | ESCALA confirma qué se quiere decidir, área afectada y resultado esperado. |
| S43.2 | Armar el paquete de evidencia | M | Pending | Muestra documentos usados, periodo, datos faltantes y nivel de certeza. |
| S43.3 | Elegir la herramienta adecuada | M | Pending | Usa el análisis local de workbook, reuniones, contexto o tareas según la necesidad. |
| S43.4 | Revisar antes de responder | M | Pending | Detecta contradicciones, cálculos dudosos y afirmaciones sin fuente. |
| S43.5 | Entregar la respuesta ejecutiva | S | Pending | Presenta qué veo, por qué importa, qué no sé, acción y pregunta siguiente. |
| S43.6 | Calificar las cuatro decisiones | M | Pending | Demuestra el ciclo con casos de People, Strategy, Execution y Cash. |

## S43.1 — Aclarar la decisión

ESCALA convertirá una pregunta abierta en una ficha breve: la decisión a tomar,
el área principal, el horizonte temporal y el resultado que el empresario
espera. Si la pregunta es sencilla, lo hará en una sola interacción.

**Termina cuando:** una pregunta ambigua no dispara análisis ni recomendación
hasta que el objetivo sea entendible; una pregunta clara no recibe fricción
innecesaria.

## S43.2 — Armar el paquete de evidencia

ESCALA identificará los archivos locales, sesiones, métricas, tareas o
worksheet relevantes. Separará evidencia disponible, evidencia ausente y
evidencia que no se puede confiar todavía.

**Termina cuando:** el empresario puede ver qué fuentes influyeron en la
recomendación sin revelar rutas internas, datos innecesarios ni información de
otra empresa.

## S43.3 — Elegir la herramienta adecuada

Con la evidencia seleccionada, ESCALA elegirá el análisis que corresponde: Cash
para un workbook financiero, reuniones para una weekly, estrategia para una
decisión de mercado o ejecución para prioridades y ritmos.

**Termina cuando:** el sistema deja de pedir formatos artificiales y no usa una
herramienta cuando el dato mínimo no existe.

## S43.4 — Revisar antes de responder

Antes de entregar una recomendación, ESCALA realizará una revisión breve:

- ¿cada afirmación importante es un hecho, una inferencia o un desconocido?
- ¿los números corresponden al periodo correcto?
- ¿dos fuentes se contradicen?
- ¿falta una pregunta que cambia la decisión?
- ¿la acción propuesta sí responde al objetivo inicial?

**Termina cuando:** una contradicción sembrada y un cálculo financiero dudoso
se bloquean o se presentan como duda, nunca como certeza.

## S43.5 — Entregar la respuesta ejecutiva

La respuesta al empresario tendrá siempre cinco bloques breves:

1. qué veo;
2. por qué importa;
3. evidencia relevante;
4. qué no sé todavía;
5. acción recomendada o siguiente pregunta.

**Termina cuando:** un empresario puede leerla en menos de cinco minutos y
explicar cuál es la decisión siguiente sin que alguien le traduzca el sistema.

## S43.6 — Calificar las cuatro decisiones

Se crearán escenarios positivos y negativos para People, Strategy, Execution y
Cash. Los negativos incluyen evidencia faltante, contradicción o información
dañada.

**Termina cuando:** el ciclo no solo funciona con Cash; conserva las mismas
reglas de evidencia y honestidad en las cuatro decisiones.

## Dentro

- Un plan corto por análisis importante.
- Evidencia local trazable y preguntas de aclaración.
- Revisión de hechos, inferencias, números y contradicciones.
- Respuesta ejecutiva consistente.
- Casos de calificación y comparación contra la línea base E42.

## Fuera

- Seguimiento de resultados y ajuste de confianza → E44.
- Roles de especialistas y desacuerdos entre ellos → E45.
- Cambios a skills basados en señales de uso → E46.
- Cualquier ejecución hospedada, API externa o base de datos compartida.

## Criterios de terminación

- [ ] Toda recomendación relevante nombra evidencia o declara el hueco de
      información.
- [ ] Los cálculos pueden verificarse contra sus fuentes.
- [ ] Una contradicción conocida se presenta como contradicción.
- [ ] Una pregunta ausente bloquea la conclusión cuando altera la decisión.
- [ ] La respuesta no expone tecnicismos innecesarios al empresario.
- [ ] Los cuatro pilares tienen casos positivos y negativos aprobados.
- [ ] Las métricas de claridad, confianza y utilidad superan o explican la
      línea base E42.
- [ ] La autoridad local y la prohibición de sincronizar SQLite se mantienen.
- [ ] Retrospectiva y evidencia de calificación completadas.

## Dependencias

```text
E42 línea base y recorrido probado
             ↓
S43.1 objetivo claro → S43.2 evidencia → S43.3 herramienta
                                         ↓
                         S43.4 revisión → S43.5 respuesta
                                                   ↓
                                           S43.6 cuatro decisiones
```

- E42 terminada con línea base y aceptación humana.
- Ingesta local, Cash, reuniones, cockpit y pipelines existentes.
- Casos redactados que no contengan información identificable de empresarios.

## Plan de implementación

### Secuencia

| Orden | Historia | Razonamiento | Habilita |
|---:|---|---|---|
| 1 | S43.1 | Sin una decisión clara, el resto puede analizar lo equivocado. | S43.2-S43.5 |
| 2 | S43.2 | La evidencia debe existir antes de elegir o interpretar herramientas. | S43.3-S43.4 |
| 3 | S43.3 | Prueba el primer recorrido real sin crear una plataforma nueva. | S43.4-S43.5 |
| 4 | S43.4 | El riesgo principal es recomendar sin revisar contradicciones. | S43.5 |
| 5 | S43.5 | Convierte el comportamiento interno en valor visible para el dueño. | S43.6 |
| 6 | S43.6 | Extiende el patrón solo después de probar Cash y Weekly. | Gate hacia E44 |

### Hitos

| Hito | Historias | Criterio de éxito |
|---|---|---|
| M1 — Primer recorrido confiable | S43.1-S43.3 | Cash o Weekly llega de pregunta a evidencia y análisis sin dato inventado. |
| M2 — Revisión visible | S43.4-S43.5 | Una contradicción se detecta y la respuesta ejecutiva explica su límite. |
| M3 — Cuatro decisiones | S43.6 | Los cuatro pilares pasan casos positivos y negativos. |
| M4 — Gate E44 | — | E42/E43 muestran mejor confianza y trazabilidad que la línea base. |

### Trabajo en paralelo

Después de S43.2, la preparación de casos de S43.6 puede avanzar en paralelo;
no se integra hasta que S43.5 defina el formato final de respuesta.

### Seguimiento

| Story | Estado | Evidencia esperada |
|---|---|---|
| S43.1 | Pending | Fichas de decisión y casos de aclaración. |
| S43.2 | Pending | Paquetes de evidencia y rechazos seguros. |
| S43.3 | Pending | Recibos de elección de análisis. |
| S43.4 | Pending | Casos de contradicción, cálculo y pregunta faltante. |
| S43.5 | Pending | Respuestas ejecutivas aprobadas por empresarios. |
| S43.6 | Pending | Matriz People/Strategy/Execution/Cash. |

## Riesgos

| Riesgo | L/I | Mitigación |
|---|:---:|---|
| Convertir la revisión en preguntas interminables | M/H | Una pregunta a la vez y detenerse cuando no cambie la decisión. |
| Confundir fuente disponible con fuente confiable | M/H | Marcar procedencia, periodo y certeza por separado. |
| Añadir una capa paralela a los flujos existentes | M/M | Reutilizar pipelines, ingesta, Cash, reuniones y coaching actuales. |
| Mostrar un reporte técnico en vez de una decisión | M/M | Pruebas de lectura con empresarios y formato ejecutivo fijo. |

## Parking lot

- Explicación visual del camino de evidencia → evaluar después de aceptación de
  S43.5; no es necesaria para probar el valor.
