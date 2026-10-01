---
epic_id: E84
title: Customer journey proactivo y tableros analíticos locales
status: complete
jira_key: "ESCALA-50"
closure_disposition: active
created: 2026-09-30
updated: 2026-09-30
depends_on: []
related: [E71, E73, E75, E79, E80, E83, E85]
---

# Scope E84

## Objetivo

1. ESCALA pregunta por el **customer journey** del cliente del empresario cuando detecta que hace falta (p.ej. al diagnosticar ventas, marketing o retención), sin esperar a que se lo pidan.
2. ESCALA **sugiere tableros visuales** como lo haría un experto en business analytics: qué medir, por qué y cómo verlo, y los genera **localmente**.

## Dentro

- Disparadores explícitos y probados de cuándo preguntar por el journey (y cuándo no).
- Modelo del journey por etapas con evidencia y huecos declarados.
- Recomendación de tablero: métricas, fuente de cada dato, frecuencia.
- Tableros como archivos locales en la carpeta de la empresa (p.ej. HTML autocontenido), sin publicar en la nube.

## Fuera

- Publicar tableros en servicios externos o enviarlos a terceros.
- Inventar cifras para llenar un tablero; un dato faltante se muestra como faltante.
- Reemplazar el módulo `coaching/dashboard` sin revisar primero qué entrega hoy.

## Incógnitas

1. Qué muestra hoy `coaching/dashboard` y si se extiende o se reemplaza.
2. Formato local que funcione igual desde Claude, Codex y ChatGPT.

Respuestas en `design.md`: (1) **extender**: `coaching/dashboard` es un resumen de progreso, que se queda intacto, y los tableros viven en el submódulo nuevo `coaching/dashboard/boards/`; (2) **HTML autocontenido, sin JS ni red, más su gemelo Markdown**, con el Markdown en el chat como piso garantizado; ninguna plataforma está verificada todavía (matriz en S84.4). Las dos son decisión propuesta, pendiente de confirmar por el dueño.

## Origen: customer journey de E71

Por decisión del dueño (2026-09-30), E71 (ESCALA-35) quedó absorbida por E83, y su customer journey (S71.5) pasa a E84. Se pliega así: el `JourneyHypothesis` de E71 (etapa, necesidad, touchpoint, fricción, evidencia, confianza, experimento) es el `JourneyStage` de S84.2. Su regla, "no afirmar que el cliente final fue entrevistado si no lo fue; conservar la evidencia de primera mano separada de la inferencia", es un criterio de terminado de este epic.

## Historias

| Historia | Jira | Entrega | Tamaño | Estado |
|---|---|---|:---:|---|
| S84.1 | `ESCALA-63` | Disparadores (cuándo sí y cuándo no preguntar) y entrevista del customer journey; procedimiento interno `escala-strategy-journey` | M | done |
| S84.2 | `ESCALA-64` | Modelo de journey con evidencia por origen, huecos, "dónde se pierden más" y una decisión; entrada al diagnóstico | M | done |
| S84.3 | `ESCALA-65` | Recomendador de tablero: máximo 2 propuestas, qué decisión sirve, métricas con fuente y periodo, factibilidad; ruta `dashboard` | M | done |
| S84.4 | `ESCALA-66` | Generador de tablero local (HTML autocontenido + Markdown) y matriz por plataforma | M | done |

## Cómo E84 evita añadir superficie

Se añade un solo procedimiento interno al catálogo (64 → 65; capacidades 65 → 66) y los tableros viven en `escala-dashboard`, que ya existe. No hay comandos públicos, alias, especialistas ni capacidades MVP nuevas, y el trigger de strategy no cambia. La primera regla del recomendador es señalar lo que ya existe (tracker, reporte de caja, progreso, research) antes de proponer algo nuevo.

## Decisiones propuestas (pendientes de confirmar por el dueño)

- U3: E84 absorbe el núcleo de E73 (ESCALA-37, asesor de tableros), igual que E83 absorbió a E71. El dueño aplica la disposición en Jira.
- U4: rutas. Strategy suma `marketing` y `prospecto`, y una ruta `dashboard` (`tablero`, `dashboard`, `grafica`, `indicador`) va primera.
- U5: ESCALA no insiste. Tras un "no" o "después", 30 días sin volver a preguntar, y nunca más de una pregunta por conversación.
- U6: los conteos del journey viven en `.escala/my-company/journey/`, no en `facts.yaml` (que está en una ruta que git no ignora).
- U7: E80 corrige el idioma y los comandos del tablero de progreso actual; mientras tanto, el procedimiento lo resume en español.

## Criterios de terminado

- Los disparadores T1-T5 y los bloqueos N1-N6 están cubiertos por tests, incluidos los casos en que **no** se pregunta.
- El journey separa lo que dice el dueño, los datos con periodo, lo que dijeron los clientes y los supuestos, y nunca afirma que se entrevistó a clientes si no fue así.
- Un dato faltante aparece como "falta" en el journey, la recomendación y el tablero; ninguna cifra se estima.
- Cada módulo termina en una decisión del dueño, con "todavía no" más dato y fecha como opción válida; nada se guarda sin su sí.
- Los tableros se guardan sólo en `.escala/my-company/tableros/`; la salida no contiene `http`, `<script`, `@import` ni `url(`; nunca se publican.
- La matriz por plataforma tiene un comando de reproducción por fila, y lo que no se probó dice "no verificado".
- El catálogo sube a 65/66 con tests verdes y los casos de rutas actuales no cambian.
- Gates verdes (tests, pyright strict, lint); sin datos reales en el repo.

### Machine
```yaml
epic_id: E84
jira_key: ESCALA-50
stories:
  - id: S84.1
    jira: ESCALA-63
    size: M
    depends_on: []
  - id: S84.2
    jira: ESCALA-64
    size: M
    depends_on: [S84.1]
  - id: S84.3
    jira: ESCALA-65
    size: M
    depends_on: [S84.1]
  - id: S84.4
    jira: ESCALA-66
    size: M
    depends_on: [S84.3]
execution_order: [S84.1, S84.2, S84.3, S84.4]
critical_path: [S84.1, S84.3, S84.4]
external_dependencies: [E73 disposition (owner), E80 S80.2, E83 S83.5 (soft), E85 (ChatGPT Work)]
```

## Implementation Plan

Estrategia: riesgo primero. Van primero las reglas que más pueden fallarle al dueño: insistir de más e inventar o exagerar evidencia. Luego el recomendador y, al final, el generador, que tiene un patrón probado en el repo (E38). Son 4 historias y 20 puntos (M = 5; escala Fibonacci del proyecto). No hay datos de calibración para este dominio: los tamaños son hipótesis y se recalibran tras S84.1.

| # | Historia | Jira | Tam. | Pts | Depende de | Por qué en esta posición | Habilita |
|---|---|---|:---:|:---:|---|---|---|
| 1 | S84.1 | `ESCALA-63` | M | 5 | - | Camino crítico y mayor riesgo de experiencia (insistir de más). Fija los modelos base, el procedimiento y el cambio de catálogo | S84.2, S84.3 |
| 2 | S84.2 | `ESCALA-64` | M | 5 | S84.1 (dura), E83 S83.5 (blanda) | Reglas de honestidad (primera mano contra supuesto, periodos iguales) y la costura con el diagnóstico, que sólo acepta hechos locales | M1; patrón journey en S84.3 |
| 3 | S84.3 | `ESCALA-65` | M | 5 | S84.1 (dura: T4), S84.2 (blanda: patrón de ventas/journey) | Decide qué medir. Sin propuesta aceptada no hay nada que generar. Toca rutas del catálogo después de S84.1 | S84.4 |
| 4 | S84.4 | `ESCALA-66` | M | 5 | S84.3 (dura) | Riesgo técnico bajo (patrón E38), pero incluye la matriz por plataforma y el recorrido completo, así que va última | M2, M3 |

Dependencias: S84.1 → {S84.2, S84.3}; S84.3 → S84.4; S84.2 → S84.3 (blanda). Sin ciclos. Externas (no bloquean): disposición de E73 por el dueño (si no absorbe, S84.3 se reduce y pierde la memoria de decisiones), E80 S80.2 (idioma del progreso), E83 S83.5 (si no llega, S84.2 usa `DiagnosticEvidence` directamente) y E85 (ChatGPT Work).

Camino crítico: S84.1 → S84.3 → S84.4.

Oportunidades de paralelo (opcionales, no cambian el orden acordado): tras S84.1, S84.2 (`coaching/journey/`) y S84.3 (`coaching/dashboard/boards/`) tocan paquetes distintos. Sus puntos de contacto son `escala-skills/catalog.yaml` (rutas) y `tests/test_capability_catalog.py`; si corren en paralelo, S84.3 se integra después de S84.1 y S84.2 rebasa.

## Milestones

| Hito | Historias | Criterio de éxito verificable | Demo |
|---|---|---|---|
| M1 Journey proactivo | S84.1, S84.2 | "Mucha gente pregunta pero pocos compran" dispara **una** pregunta; "después" silencia 30 días; el journey de la empresa sintética separa orígenes, marca los faltantes, calcula la pérdida sólo con periodos iguales, termina en una decisión guardada en `.escala/my-company/journey/` y entra al diagnóstico siguiente como evidencia local; catálogo 65/66 verde | Conversación sintética "Pan Rico" |
| M2 Tablero local | S84.3, S84.4 | "Tablero de mis ventas" llega a máximo 2 propuestas con fuente, periodo y factibilidad; un pedido de caja señala el reporte existente; el HTML aceptado no tiene referencias externas, muestra "Falta" y la decisión; sin números no se genera; matriz por plataforma llena | Pedido → propuesta → decisión → archivo local |
| M3 Epic complete | todas | Criterios de terminado cumplidos; recorrido sintético completo journey → tablero, más revisión de una transcripción para confirmar que no insiste; gates verdes; sin datos reales en el repo | Listo para `/rai-epic-close` |

Checkpoint de integración: S84.2 prueba la costura journey → diagnóstico en M1; S84.4 (última) corre el recorrido completo antes de M3.

## Progress Tracking

| Historia | Tam. | Pts | Estado | Real | Notas |
|---|:---:|:---:|---|---|---|
| S84.1 | M | 5 | done | M | `ESCALA-63`; catálogo 65/66 |
| S84.2 | M | 5 | done | M | `ESCALA-64`; demo M1 Pan Rico en test |
| S84.3 | M | 5 | done | M | `ESCALA-65`; ruta `dashboard` primera |
| S84.4 | M | 5 | done | M | `ESCALA-66`; recorrido sintético completo en test (M2) |

### Sequencing Risks

1. **Solape con E73 (ESCALA-37).** Si el dueño no confirma la absorción, habría dos epics de tableros. Mitigación: la disposición se pide al cerrar este plan, y S84.3 tiene una versión reducida.
2. **Insistir de más.** Los tests prueban la función, no la conducta del agente. Mitigación: la bandera por conversación es entrada explícita, y M3 exige revisar una transcripción.
3. **Privacidad de conteos.** `.escala/agent/memory/` no está ignorado por git. Mitigación: E84 escribe sólo en `my-company/`; el hallazgo pasa a E79.
4. **Plataformas no verificadas.** Puede que ningún cliente abra el HTML. Mitigación: el Markdown en el chat es el piso, y la matriz se llena en S84.4 antes de afirmar nada.
5. **Rutas.** Poner la ruta `dashboard` primera saca de cash los pedidos visuales de caja. Mitigación: la regla de no redundancia señala el reporte de caja, con el caso fijado en un test.


## Decisiones del dueño (2026-09-30)

Confirmadas todas las decisiones propuestas del diseño (U1–U7): extender `coaching/dashboard` con `boards/`; HTML autocontenido + Markdown; E84 absorbe E73 (ESCALA-37); rutas propuestas con la ruta dashboard primero; 30 días sin volver a preguntar tras "no"/"después" y máximo una pregunta por conversación; conteos del journey en `.escala/my-company/journey/`; E80 corrige el inglés y los comandos del tablero de progreso. `.escala/agent/memory/` ya se ignora en git (ded54cb).
