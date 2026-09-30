---
epic_id: "E45"
title: "Equipo instalado de cuatro especialistas bajo demanda"
status: "in_progress"
jira_key: "ESCALA-46"
depends_on: ["E44", "E49"]
created: "2026-07-23"
---

# E45 — Equipo instalado de cuatro especialistas bajo demanda

## Objetivo

Resolver problemas empresariales complejos con cuatro especialistas instalados
por decisión —Cash, Execution, People y Strategy—, una crítica independiente y
verificación de evidencia, entregando una sola respuesta clara al dueño.

**Valor:** una caída de caja, por ejemplo, puede requerir Cash, Execution,
Strategy y People. E45 evita que ESCALA responda desde una sola perspectiva o
simule certeza cuando las áreas discrepan.

## Equipo estable, activación no permanente

| Perfil interno | Se activa cuando | No hace |
|---|---|---|
| `cash-analyst` | caja, conciliación, forecast, márgenes, CCC o decisiones financieras | asesoría fiscal/legal ni persiste cifras sin confirmación. |
| `execution-operator` | prioridades, reuniones, compromisos, KPIs o ritmo | calificar personas o reescribir estrategia. |
| `people-coach` | accountability, roles, capacidad, desarrollo o tensiones de equipo | inferir rasgos personales ni tomar decisiones laborales. |
| `strategy-analyst` | mercado, cliente, competencia, diferenciación, visión o customer journey | declarar datos de mercado sin fuente/fecha. |

E45 define el núcleo de roles y el router; E67 lo empaqueta para Codex y
Claude. No son cuatro chats ni cuatro procesos que sobreviven al Welcome.
`escala` guarda el estado autorizado y activa, como máximo, los roles
necesarios para cada intervención.

## Historias

| ID | Historia | Tamaño | Estado | Demostración de valor |
|---|---|:---:|:---:|---|
| S45.1 | Decidir cuándo se necesita un equipo | S | Implemented; pilot pending | Preguntas simples siguen rápidas; casos complejos explican por qué requieren revisión. |
| S45.2 | Dar a cada especialista el contexto mínimo | M | Implemented; pilot pending | Cash, People, Strategy o Execution reciben solo evidencia pertinente. |
| S45.3 | Incorporar al crítico y verificador | M | Implemented; pilot pending | Un rol desafía supuestos y otro confirma cifras, periodo y fuentes. |
| S45.4 | Resolver desacuerdos con evidencia | M | Implemented; pilot pending | El sistema distingue acuerdo, desacuerdo y pregunta que falta resolver. |
| S45.5 | Entregar una sola recomendación | M | Implemented; pilot pending | El dueño recibe alternativas, riesgo, decisión sugerida, acción y seguimiento. |
| S45.6 | Calificar casos transversales | M | Local fixtures; business pilot pending | Casos de tres o cuatro decisiones prueban valor frente a un solo coach. |
| S45.7 | Contratos e instalación de los cuatro perfiles | M | Implemented; E67 packaging pending | Cada perfil declara trigger, non-trigger, contexto mínimo, permisos, salida y límites; E67 lo instala sin exponer un comando público. |

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
local hasta que E74 habilite un workspace compartido aprobado. Incluso en ese
caso, cada rol recibe sólo el mínimo necesario; su caché o índice local nunca
se vuelve autoridad compartida.

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

## S45.7 — Contratos e instalación de los cuatro perfiles

Cada perfil declara trigger, non-trigger, contexto mínimo, permisos, salida,
límites y pruebas. E45 entrega esos contratos al adaptador E67; E67 es quien
los instala como definiciones privadas de plataforma.

**Termina cuando:** los cuatro contratos pasan pruebas de activación y E67
puede empaquetarlos sin convertirlos en comandos o conversaciones públicas.

## Dentro

- Router simple/complejo.
- Los cuatro perfiles, crítico, verificador y síntesis.
- Contexto mínimo y límites de trabajo.
- Desacuerdos visibles y una respuesta ejecutiva.
- Comparación frente a una respuesta de un solo coach.

## Fuera

- Personas ficticias o "consejeros" basados en figuras reales.
- Ejecución permanente de varios agentes o un quinto bot visible de research;
  research es una capacidad invocable por el perfil pertinente.
- Decisiones autónomas sobre personas, presupuesto o publicación.
- Compartir datos implícitamente entre instalaciones; E74 define el workspace
  compartido aprobado, su historial y la resolución explícita de conflictos.
- Mejora automática del producto → E46.

## Criterios de terminación

- [x] Los cuatro perfiles tienen contratos y pruebas de trigger/non-trigger.
- [x] El router deja casos simples con un solo coach.
- [x] Los roles reciben contexto mínimo y verificable.
- [x] El crítico encuentra un supuesto o riesgo sembrado.
- [x] El verificador bloquea una fuente, cálculo o periodo inválido.
- [x] Los desacuerdos muestran evidencia y la pregunta para resolverlos.
- [x] La síntesis es una sola respuesta ejecutiva para el empresario.
- [ ] La calificación demuestra valor frente a un solo análisis o reduce el
      equipo si no lo demuestra.
- [x] Los límites de rondas, tiempo y privacidad se cumplen en el router local: máximo una aclaración, presupuesto declarado y evidencia personal/financiera fail-closed fuera de su contexto consentido.
- [ ] Retrospectiva y aceptación empresarial completadas.

## Dependencias

```text
E49 evidencia y revisión      E44 decisiones y resultados
          \                    /
           \                  /
            S45.7 contratos → S45.1 router → S45.2 contexto → S45.3 crítico/verificador
                                                               ↓
                                                    S45.4 desacuerdos → S45.5 síntesis
                                                                                 ↓
                                                                       S45.6 casos transversales
```

- E49 debe aportar evidencia y límites confiables.
- E44 debe aportar decisiones y resultados para valorar el impacto.
- E67 consume los contratos E45 para empaquetar los perfiles y adaptadores por
  plataforma; no bloquea el diseño del router.
- Casos redactados que crucen decisiones sin exponer empresa real.

## Plan de implementación

### Secuencia

| Orden | Historia | Razonamiento | Habilita |
|---:|---|---|---|
| 1 | S45.7 | Fija contratos antes de que una plataforma dicte la arquitectura. | S45.1-S45.3 y E67 |
| 2 | S45.1 | El primer riesgo es convertir todo en trabajo multi-agente. | S45.2-S45.6 |
| 3 | S45.2 | Define límites de información antes de sumar roles. | S45.3-S45.5 |
| 4 | S45.3 | Prueba la diferencia entre producir más texto y revisar mejor. | S45.4-S45.5 |
| 5 | S45.4 | Los desacuerdos deben resolverse antes de diseñar la síntesis. | S45.5 |
| 6 | S45.5 | Convierte los roles en valor comprensible para el dueño. | S45.6 |
| 7 | S45.6 | Mide si el equipo merece existir antes de pasar a E46. | Gate hacia E46 |

### Hitos

| Hito | Historias | Criterio de éxito |
|---|---|---|
| M0 — Contratos | S45.7 | Cuatro perfiles privados y evaluables quedan listos para empaquetar. |
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
| S45.1 | Implemented; pilot pending | Casos simple/complejo y decisión del router. |
| S45.2 | Implemented; pilot pending | Paquetes mínimos de contexto por rol. |
| S45.3 | Implemented; pilot pending | Hallazgos críticos y verificación de fuentes. |
| S45.4 | Implemented; pilot pending | Registro de acuerdo, desacuerdo y pregunta abierta. |
| S45.5 | Implemented; pilot pending | Síntesis ejecutiva probada con empresarios. |
| S45.6 | Local fixtures; business pilot pending | Comparativo de equipo vs. un solo coach. |
| S45.7 | Implemented; E67 packaging pending | Contratos de Cash, Execution, People y Strategy con pruebas. |

## Evidencia local (2026-08-27)

- Módulo local: `escala_server/specialist_team.py`.
- API: `POST /api/advisor/team-review`, una sola síntesis para el empresario con estado, restricción, evidencia, supuestos, alternativas, riesgo, acción y campos explícitamente vacíos cuando no se puede proponer dueño/cadencia.
- Calificación técnica reproducible: `scripts/qualify_e44_e45.py`, con caso simple de un especialista, Cash bloqueado por periodo/unidad ausentes y desacuerdo transversal visible sin votación por mayoría.
- Protocolo de piloto: `../e44-outcome-learning-and-accountability/pilot-protocol.md` y `validators/e44_e45_business_pilot.py` obligan dos comparativos, contexto mínimo, una respuesta ejecutiva, límite de ronda y decisión honesta de retener/reducir/seguir midiendo; falta su ejecución empresarial.
- Pruebas: casos simple, transversal, contexto mínimo, ausencia de periodo/unidad,
  desacuerdo de precio, contratos de cuatro roles, límites de ronda/tiempo y privacidad consentida; incluye `tests/test_qualify_e44_e45.py`.
- Pendiente de cierre: comparación con un solo coach y piloto empresarial; la
  calificación sintética no los sustituye y la instalación como definiciones de plataforma pertenece a E67.

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
