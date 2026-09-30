---
story_id: "S55.1"
epic_id: "E55"
title: "Contrato de hechos con procedencia"
jira_key: "ESCALA-21"
status: "complete"
created: "2026-08-21"
---

# S55.1 — Contrato de hechos con procedencia

## User story

Como empresario usando ESCALA,
quiero que cada dato que comparta (una cifra, una fecha, una definición) se guarde con su fuente, periodo y confianza,
para que el agente no mezcle métricas que parecen iguales pero no lo son.

## Criterios de aceptación

### AC1: Modelo de hecho

Dado un hecho nuevo,
cuando se persiste,
entonces conserva: identificador, definición de métrica, periodo, fecha base, fuente, nivel de confianza, flag de comparabilidad, valor, unidad y decisión asociada.

### AC2: Guardado con autorización implícita del flujo

Dado un hecho validado,
cuando el usuario o skill lo guarda,
entonces se escribe en `.escala/agent/memory/facts.yaml` (o partición equivalente) sin salir del directorio local.

### AC3: Carga filtrada

Dado un directorio con hechos persistidos,
cuando se cargan por decisión (People, Strategy, Execution, Cash),
entonces se devuelven solo los hechos de esa decisión.

### AC4: Regresión

Dado el contrato de hechos,
cuando corren los tests,
entonces todos pasan y no hay referencias rotas.

## Ejemplos (SbE)

| Campo | Ejemplo 1 | Ejemplo 2 |
|---|---|---|
| metric_definition | Ingreso atribuible mensual | Gasto en publicidad entregado por plataforma |
| period | 2026-07 | 2026-07 |
| basis_date | 2026-07-31 | 2026-07-31 |
| source | export_plataforma_julio.csv | conversacion_onboarding |
| confidence | high | medium |
| comparable | true | false |
| value | 125000 | 45000 |
| unit | MXN | MXN |
| decision | cash | cash |
