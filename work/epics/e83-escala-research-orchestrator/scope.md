---
epic_id: E83
title: ESCALA research — orquestador de investigación de negocio
status: complete
jira_key: "ESCALA-49"
closure_disposition: active
created: 2026-09-30
updated: 2026-09-30
depends_on: []
related: [E75, E80]
---

# Scope E83

## Objetivo

Un orquestador de varios pasos que ayuda al empresario a investigar su entorno con la disciplina de `rai-research` (pregunta concreta, fuentes calificadas, triangulación ≥3 fuentes, búsqueda de evidencia en contra, recomendación, reporte) adaptada a lenguaje de negocio, y cuyo resultado alimenta el diagnóstico en vez de quedar como documento suelto.

## Módulos iniciales

1. **Benchmark research** — cómo lo hacen empresas comparables (precios, oferta, canales, métricas).
2. **Market research** — cómo está TU mercado: tamaño, demanda, clientes, competidores.
3. **Strengths / weaknesses & trends research** — fortalezas y debilidades frente al mercado, y tendencias que afectan al negocio.

## Dentro

- Encuadre: convertir la inquietud del empresario en una pregunta investigable y decir qué decisión informa.
- Catálogo de evidencia con nivel de confianza y fecha; separar dato, supuesto e inferencia.
- Reporte local en la carpeta de la empresa y enlace a la evidencia del diagnóstico (E80).

## Fuera

- Presentar como hecho algo con una sola fuente o sin fecha.
- Comprar o conectar bases de datos de pago.
- Enviar información de la empresa a servicios externos sin consentimiento (las búsquedas no llevan datos privados).

## Incógnitas

1. No todos los clientes del usuario tienen búsqueda web; definir el comportamiento sin ella (pedir fuentes al usuario, declarar el límite).
2. ¿El orden de módulos es fijo o lo elige ESCALA según la restricción diagnosticada?

## Historias

| Historia | Entrega | Tamaño | Estado |
|---|---|:---:|---|
| S83.1 | Contrato del orquestador: encuadre, catálogo de evidencia, reporte, modo sin búsqueda (`ESCALA-57`) | M | complete — `coaching/research/`, `escala-strategy-research` |
| S83.2 | Módulo benchmark (`ESCALA-58`) | M | complete — modo `benchmark`, acción `comparables` |
| S83.3 | Módulo mercado (`ESCALA-59`) | M | complete — modo `mercado`, `market_size`, palabras de giro |
| S83.4 | Módulo fortalezas/debilidades y tendencias, alimenta al SWT (`ESCALA-60`) | S | complete — lado y negocios confirmados, reuso del benchmark, acción `swt`, integración de los tres modos |
| S83.5 | Integración con diagnóstico y verificación por plataforma con y sin búsqueda web (`ESCALA-61`) | S | complete — `diagnosis.py`, `sampling.py`, acción `check_sources` |

Orden de ejecución: S83.1 → S83.2 → S83.5 → S83.3 → S83.4. Diseño detallado en `design.md`.

Cambios frente al borrador (sin tocar Jira): el aviso sin búsqueda (una línea + fuentes pegadas; decisión del dueño 2026-09-30: se asume búsqueda disponible) va en S83.1 y S83.5 queda con la integración y la matriz verificada por plataforma; S83.4 baja de M a S porque no produce documento propio (alimenta a `escala-strategy-swt`) y reusa los comparables de S83.2.

Detalle por historia (dependencia → entrega concreta):

- S83.1 (sin dependencias): `coaching/research/` (modelos, `grade_claim`, `check_queries`, reporte local e índice en `.escala/my-company/research/`) + procedimiento interno `escala-strategy-research` (catálogo 63 → 64, capacidades 64 → 65) + palabras de ruta `mercado`, `competidor`, `tendencias`, `benchmark` + reglas sin búsqueda + **test de privacidad** de búsquedas.
- S83.2 (depende de S83.1): modo `benchmark` con comparables confirmados y tabla con fuente/fecha por celda; primera investigación completa que termina en decisión.
- S83.5 (depende de S83.1; usa S83.2 como caso real): `to_diagnostic_inputs`, reporte vencido como `stale`, oferta desde el diagnóstico, muestreo de URLs/extractos, matriz verificada por plataforma.
- S83.3 (depende de S83.1; blanda de S83.5): modo `mercado`; sin segmento/geografía no hay tamaño; rango + método o "no estimable todavía".
- S83.4 (depende de S83.1 y S83.2; blanda de S83.3): modo `fortalezas-tendencias` + paso final en `escala-strategy-swt`.

## Decisiones propuestas — pendientes de confirmar por el dueño

- **Incógnita 1 (sin búsqueda web):** modo "con tus fuentes": el dueño pasa 2-3 fuentes, las reglas de confirmación no se relajan, el reporte declara el límite y la memoria del modelo nunca es fuente. Ver `design.md` U1 / D3.
- **Incógnita 2 (orden de módulos):** no hay orden fijo; ESCALA propone un modo según la restricción diagnosticada (o el pedido del dueño), uno por conversación, y no propone investigación para People/Execution. Ver `design.md` U2 / D2.
- **E71 (ESCALA-35):** E83 absorbe su contrato, encuadre, mercado y competidores; su customer journey pasa a E84. La disposición de E71 la aplica el dueño. Ver D8.

## Criterios de terminado

- Desde `escala`, sin nombrar comandos, "¿cómo está mi mercado?", "¿cuánto cobra mi competencia?" y "¿qué tendencias vienen para mi sector?" llegan a la investigación.
- Cada investigación termina en una decisión elegida por el dueño, guardada sólo con su sí.
- Nada se presenta como confirmado con menos de 3 fuentes independientes con fecha; lo contrario y lo no encontrado siempre se muestran.
- Sin búsqueda web el flujo funciona con fuentes del dueño y declara el límite; la memoria del modelo nunca aparece como fuente.
- Ninguna búsqueda generada contiene nombre, personas ni cifras de la empresa (test de privacidad).
- El siguiente diagnóstico parte de la decisión confirmada; ninguna URL entra en facts ni en evidencia de diagnóstico.
- Cero comandos, alias o especialistas nuevos; catálogo +1; un solo SWT.

### Machine
```yaml
modules_affected:
  - path: coaching/research/
    change: create
  - path: escala-skills/escala-strategy-research/SKILL.md
    change: create
  - path: escala-skills/catalog.yaml
    change: modify
  - path: tests/test_capability_catalog.py
    change: modify
  - path: escala-skills/escala-strategy-swt/SKILL.md
    change: modify
decisions:
  - id: D1
    choice: "Un procedimiento interno con tres modos; sin comandos, alias ni especialistas nuevos"
    rationale: "Experiencia ultra simple, una sola puerta"
    constraint: "capabilities/mvp/catalog.json no cambia"
  - id: D2
    choice: "Modo elegido por la restricción diagnosticada o el pedido del dueño (propuesta)"
    rationale: "E75: sin orden editorial"
    constraint: "Uno por conversación"
  - id: D3
    choice: "Sin búsqueda: fuentes del dueño y límite declarado (propuesta)"
    rationale: "Funciona en cualquier cliente sin prometer capacidades"
    constraint: "La memoria del modelo nunca es fuente"
constraints:
  - "Confirmado sólo con 3 o más fuentes independientes con fecha"
  - "Reportes sólo en .escala/my-company/research/; tests sintéticos"
  - "No afirmar búsqueda web por plataforma sin la matriz de S83.5; ChatGPT Work no verificado (E85)"
```

## Implementation Plan

Estrategia: riesgo primero con esqueleto temprano. 5 historias, 21 puntos (M = 5, S = 3; escala Fibonacci del proyecto). Sin datos de calibración para este dominio: los tamaños son hipótesis y se recalibran tras S83.1.

| # | Historia | Jira | Tam. | Pts | Depende de | Por qué en esta posición | Habilita |
|---|---|---|:---:|:---:|---|---|---|
| 1 | S83.1 | `ESCALA-57` | M | 5 | - | Camino crítico: contrato, reglas de confirmación, privacidad de búsquedas, modo sin búsqueda y la entrada por `escala`. Todo lo demás lo hereda | S83.2-S83.5 |
| 2 | S83.2 | `ESCALA-58` | M | 5 | S83.1 (dura) | Victoria rápida y el modo más concreto para el dueño (precios); es el primer recorrido completo pregunta → fuentes → decisión | S83.5 (caso real), S83.4 |
| 3 | S83.5 | `ESCALA-61` | S | 3 | S83.1 (dura), S83.2 (blanda) | Riesgo primero: la costura con el diagnóstico (que sólo acepta hechos locales) y la búsqueda real por plataforma son lo más incierto; se prueban con un modo antes de construir dos más | M2 |
| 4 | S83.3 | `ESCALA-59` | M | 5 | S83.1 (dura), S83.5 (blanda) | Modo con más riesgo de falsa precisión (tamaños); llega con reglas y matriz ya probadas | M3 |
| 5 | S83.4 | `ESCALA-60` | S | 3 | S83.1 (dura), S83.2 (dura), S83.3 (blanda) | Reusa comparables y encuadre; toca `escala-strategy-swt`. Por ser la última, corre la verificación de costuras de los tres modos | M3, M4 |

Dependencias: S83.1 → {S83.2, S83.3, S83.4, S83.5}; S83.2 → S83.4. Sin ciclos. Externas (no bloquean): E75 S75.3 (si no llega, la entrada desde el diagnóstico es una sugerencia en texto), E85 (ChatGPT Work), disposición de E71 por el dueño.

Camino crítico: S83.1 → S83.2 → S83.4.

Oportunidades de paralelo (opcionales, no cambian el orden acordado): S83.5 y S83.3 sólo comparten S83.1; pueden ir en paralelo tras S83.2 (archivos distintos: integración con `coaching/diagnose` vs modo `mercado`). Punto de contacto compartido: fixtures sintéticos de `coaching/research/tests/` (acordar nombres antes).

## Milestones

| Hito | Historias | Criterio de éxito verificable | Demo |
|---|---|---|---|
| M1 Esqueleto | S83.1, S83.2 | Desde `escala`, "¿cuánto cobra mi competencia?" llega a un benchmark que termina en una decisión guardada en `.escala/my-company/research/`; test de privacidad verde; sin búsqueda, el flujo usa fuentes del dueño y declara el límite; catálogo 63 → 64 y 64 → 65 con tests verdes | Conversación con empresa sintética, con y sin búsqueda |
| M2 Ciclo cerrado | S83.5 | El diagnóstico siguiente recibe la decisión como evidencia local y los hallazgos externos como supuestos; reporte vencido entra `stale`; matriz por plataforma con comando de reproducción; muestreo de URLs/extractos | Diagnóstico → benchmark → decisión → diagnóstico |
| M3 Tres modos | S83.3, S83.4 | Mercado sin segmento/geografía no da tamaño; tamaños con rango y método; SWT incorpora evidencia externa marcada sin crear otro SWT | Una investigación por modo |
| M4 Epic complete | todas | Criterios de terminado cumplidos; gates (tests, pyright strict, lint) verdes; sin datos reales en el repo | Listo para `/rai-epic-close` |

Checkpoint de integración: S83.5 prueba la costura research → diagnóstico en M2; S83.4 (última) corre el flujo sintético completo de los tres modos, con y sin búsqueda, antes de M4.

## Progress Tracking

| Historia | Tam. | Pts | Estado | Real | Notas |
|---|:---:|:---:|---|---|---|
| S83.1 | M | 5 | done | M | `ESCALA-57` |
| S83.2 | M | 5 | done | M | `ESCALA-58` |
| S83.5 | S | 3 | done | M | `ESCALA-61` |
| S83.3 | M | 5 | done | M | `ESCALA-59` |
| S83.4 | S | 3 | done | S | `ESCALA-60` |

### Sequencing Risks

1. **Pocas fuentes con fecha para negocios locales (U5):** casi todo queda "por confirmar" y la decisión se siente débil. Se ve en S83.2; mitigación: la opción "todavía no, primero consigo X para [fecha]" es una decisión válida y concreta.
2. **La búsqueda y las citas ocurren en el cliente, fuera del módulo (U7):** los tests prueban reglas, no conducta del agente. Mitigación: muestreo de URLs/extractos en S83.5, antes de construir S83.3/S83.4.
3. **E75 S75.3 no llega a tiempo o E71 sigue abierto:** la entrada desde el diagnóstico queda como sugerencia en texto y hay dos epics de research en el backlog. Mitigación: S83.5 no simula el hand-off; la disposición de E71 se pide al dueño al cerrar este plan.


## Decisiones del dueño (2026-09-30)

- U1: se asume búsqueda web (Claude y ChatGPT la traen); sin búsqueda, una línea de aviso y cómo prenderla, y se sigue con fuentes que pegue el dueño.
- U2: ESCALA elige el modo según la restricción diagnosticada; el pedido del dueño gana.
- E71 (ESCALA-35) queda absorbida por E83; su customer journey (S71.5) pasa a E84.
- Matriz de verificación de S83.5: Claude Code, Codex, claude.ai/Desktop y ChatGPT Work (esta última queda como no verificada hasta E85).
- (2026-09-30, segunda ronda) Cifras: bloqueo estricto de números redondos que se parezcan a una cifra privada (se prefiere rechazar a filtrar).
- Antigüedad: máximo 90 días para todos los modos, sin excepción para tamaño de mercado.
- Tamaño de mercado (S83.3): el INEGI no es fuente principal (el dueño no lo usa); buscar varias fuentes recientes — cámaras y asociaciones del giro, prensa, reportes de industria, datos publicados por competidores. Sin 3 fuentes de ≤90 días queda "por confirmar" con lo encontrado.
- Palabras de giro permitidas (S83.3): lista de tipos de negocio (tortillería, panadería, taller, consultorio, restaurante, …) que nunca cuentan como nombre privado, para poder buscar competidores que las comparten con el nombre de la empresa.
