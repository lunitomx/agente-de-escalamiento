---
epic_id: E83
title: ESCALA research — orquestador de investigación de negocio
status: planned
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

## Historias (borrador)

| Historia | Entrega | Tamaño | Estado |
|---|---|:---:|---|
| S83.1 | Contrato del orquestador: encuadre, catálogo de evidencia, reporte | M | planned |
| S83.2 | Módulo benchmark | M | planned |
| S83.3 | Módulo mercado | M | planned |
| S83.4 | Módulo fortalezas/debilidades y tendencias | M | planned |
| S83.5 | Integración con diagnóstico y degradación sin búsqueda web | S | planned |
