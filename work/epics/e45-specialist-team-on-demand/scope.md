---
epic_id: "E45"
title: "Specialist Team on Demand"
status: "planned"
depends_on: ["E42", "E43", "E44"]
created: "2026-07-23"
---

# E45 — Especialistas bajo demanda

## Objetivo

Resolver problemas empresariales complejos con los especialistas necesarios,
una crítica independiente y una verificación de evidencia, entregando una sola
respuesta clara al dueño.

**Valor:** una caída de caja, por ejemplo, puede requerir Cash, Execution,
Strategy y People. E45 evita que ESCALA responda desde una sola perspectiva o
simule certeza cuando las áreas discrepan.

## Historias

| ID | Historia | Tamaño | Estado | Demostración de valor |
|---|---|:---:|:---:|---|
| S45.1 | Decidir cuándo se necesita un equipo | S | Pending | Preguntas simples siguen rápidas; casos complejos explican por qué requieren revisión. |
| S45.2 | Dar a cada especialista el contexto mínimo | M | Pending | Cash, People, Strategy o Execution reciben solo evidencia pertinente. |
| S45.3 | Incorporar al crítico y verificador | M | Pending | Un rol desafía supuestos y otro confirma cifras, periodo y fuentes. |
| S45.4 | Resolver desacuerdos con evidencia | M | Pending | El sistema distingue acuerdo, desacuerdo y pregunta que falta resolver. |
| S45.5 | Entregar una sola recomendación | M | Pending | El dueño recibe alternativas, riesgo, decisión sugerida, acción y seguimiento. |
| S45.6 | Calificar casos transversales | M | Pending | Casos de tres o cuatro decisiones prueban valor frente a un solo coach. |

## S45.1 — Decidir cuándo se necesita un equipo

El router considerará complejidad solo cuando haya impacto importante, más de
una decisión afectada, evidencia contradictoria o un riesgo que no se puede
resolver con una pregunta simple.

**Termina cuando:** un caso simple no activa al equipo y un caso transversal
explica qué especialistas participan y por qué.

## S45.2 — Dar a cada especialista el contexto mínimo

Cada especialista recibe su objetivo, evidencia relevante, huecos conocidos y
la pregunta que debe responder. No recibe archivos ni memoria que no necesita.

**Termina cuando:** la separación de contexto se puede revisar y permanece
local; una carpeta compartida no se convierte en canal de autoridad.

## S45.3 — Incorporar al crítico y verificador

El crítico busca riesgos, supuestos débiles y contradicciones. El verificador
comprueba fuentes, periodos y cálculos. Ambos pueden devolver el caso a una
pregunta, en vez de aceptar una recomendación incompleta.

**Termina cuando:** una afirmación sin evidencia y un número de periodo
equivocado quedan bloqueados antes de la síntesis.

## S45.4 — Resolver desacuerdos con evidencia

Cuando especialistas no coinciden, ESCALA no elige por mayoría. Presenta qué
está acordado, qué está en disputa y qué información resolvería la diferencia.

**Termina cuando:** el dueño puede tomar una decisión informada incluso si el
sistema no tiene suficiente evidencia para una conclusión única.

## S45.5 — Entregar una sola recomendación

La síntesis final incluye decisión, alternativas, evidencia, desacuerdo
relevante, riesgo, acción, responsable sugerido y siguiente revisión.

**Termina cuando:** el empresario nunca lee mensajes internos de los
especialistas ni tiene que decidir cuál de ellos creer.

## S45.6 — Calificar casos transversales

Se probarán al menos dos problemas: caída de caja con causas operativas y un
problema de crecimiento con tensión entre estrategia, personas y ejecución.

**Termina cuando:** el equipo encuentra un riesgo omitido por el análisis simple
o se demuestra honestamente que no agrega valor y se reduce el diseño.

## Dentro

- Router simple/complejo.
- Roles de especialista, crítico, verificador y síntesis.
- Contexto mínimo y límites de trabajo.
- Desacuerdos visibles y una respuesta ejecutiva.
- Comparación frente a una respuesta de un solo coach.

## Fuera

- Personas ficticias o "consejeros" basados en figuras reales.
- Ejecución permanente de varios agentes.
- Decisiones autónomas sobre personas, presupuesto o publicación.
- Datos compartidos entre instalaciones.
- Mejora automática del producto → E46.

## Criterios de terminación

- [ ] El router deja casos simples con un solo coach.
- [ ] Los roles reciben contexto mínimo y verificable.
- [ ] El crítico encuentra un supuesto o riesgo sembrado.
- [ ] El verificador bloquea una fuente, cálculo o periodo inválido.
- [ ] Los desacuerdos muestran evidencia y la pregunta para resolverlos.
- [ ] La síntesis es una sola respuesta ejecutiva para el empresario.
- [ ] La calificación demuestra valor frente a un solo análisis o reduce el
      equipo si no lo demuestra.
- [ ] Los límites de rondas, tiempo y privacidad se cumplen.
- [ ] Retrospectiva y aceptación empresarial completadas.

## Dependencias

```text
E43 evidencia y revisión
          ↓
E44 decisiones y resultados
          ↓
S45.1 router → S45.2 contexto → S45.3 crítico/verificador
                                      ↓
                           S45.4 desacuerdos → S45.5 síntesis
                                                        ↓
                                              S45.6 casos transversales
```

- E43 debe aportar evidencia y límites confiables.
- E44 debe aportar decisiones y resultados para valorar el impacto.
- Los sub-skills People, Strategy, Execution y Cash ya existentes.
- Casos redactados que crucen decisiones sin exponer empresa real.

## Plan de implementación

### Secuencia

| Orden | Historia | Razonamiento | Habilita |
|---:|---|---|---|
| 1 | S45.1 | El primer riesgo es convertir todo en trabajo multi-agente. | S45.2-S45.6 |
| 2 | S45.2 | Define límites de información antes de sumar roles. | S45.3-S45.5 |
| 3 | S45.3 | Prueba la diferencia entre producir más texto y revisar mejor. | S45.4-S45.5 |
| 4 | S45.4 | Los desacuerdos deben resolverse antes de diseñar la síntesis. | S45.5 |
| 5 | S45.5 | Convierte los roles en valor comprensible para el dueño. | S45.6 |
| 6 | S45.6 | Mide si el equipo merece existir antes de pasar a E46. | Gate hacia E46 |

### Hitos

| Hito | Historias | Criterio de éxito |
|---|---|---|
| M1 — Router útil | S45.1 | Casos simples y complejos siguen rutas diferentes correctamente. |
| M2 — Equipo con control | S45.2-S45.3 | Contexto mínimo y una falla sembrada son manejados correctamente. |
| M3 — Síntesis de negocio | S45.4-S45.5 | Un desacuerdo llega a una sola recomendación honesta. |
| M4 — Gate E46 | S45.6 | El valor adicional supera el costo de complejidad según pilotos. |

### Trabajo en paralelo

La preparación de los escenarios de S45.6 puede correr junto con S45.2, pero
la comparación final espera la síntesis de S45.5.

### Seguimiento

| Story | Estado | Evidencia esperada |
|---|---|---|
| S45.1 | Pending | Casos simple/complejo y decisión del router. |
| S45.2 | Pending | Paquetes mínimos de contexto por rol. |
| S45.3 | Pending | Hallazgos críticos y verificación de fuentes. |
| S45.4 | Pending | Registro de acuerdo, desacuerdo y pregunta abierta. |
| S45.5 | Pending | Síntesis ejecutiva probada con empresarios. |
| S45.6 | Pending | Comparativo de equipo vs. un solo coach. |

## Riesgos

| Riesgo | L/I | Mitigación |
|---|:---:|---|
| Teatro multi-agente sin ganancia real | M/H | Comparar casos contra un solo coach y eliminar roles sin valor. |
| Varios roles comparten el mismo error | M/H | Crítico y verificador deben revisar evidencia independiente. |
| Exceso de información compartida | M/H | Contexto mínimo, contratos locales y recibos de acceso. |
| El empresario recibe una conversación confusa | M/M | Un solo sintetizador y formato ejecutivo fijo. |

## Parking lot

- Paralelización real de especialistas → solo evaluar si la secuencia local no
  cumple tiempos de respuesta y el piloto demuestra valor adicional.
