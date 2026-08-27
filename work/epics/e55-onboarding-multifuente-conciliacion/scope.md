---
epic_id: "E55"
title: "Onboarding multifuente y conciliación de métricas de negocio"
status: "active"
closure_disposition: "active"
created: "2026-08-21"
jira_key: "ESCALA-11"
source_issue: "https://github.com/lunitomx/agente-de-escalamiento/issues/9"
---

# E55 — Onboarding multifuente y conciliación de métricas de negocio

## Objetivo

Construir en ESCALA un flujo de onboarding que acepte múltiples fuentes de evidencia, las persista con procedencia y confianza, y permita conciliar métricas antes de diagnosticar las cuatro decisiones. El resultado es un acompañamiento más fluido y honesto: primero ordenar datos y definiciones, después diagnosticar, finalmente recomendar.

**Valor:** una persona puede compartir lo que ya tiene (conversación, archivos, exportaciones) y el agente distingue qué se sabe, qué falta y qué no es comparable, sin inventar scores ni fusionar entidades de forma agresiva.

## Historias

| ID | Historia | Tamaño | Estado | Termina cuando |
|---|---|:---:|:---:|---|
| S55.1 | Contrato de hechos con procedencia (`ESCALA-12`) | 5 | Complete | Un hecho se persiste con definición de métrica, periodo, base de fecha, fuente, nivel de confianza y flag de comparabilidad. |
| S55.2 | Dashboard de evidencia previo al diagnóstico (`ESCALA-13`) | 5 | Complete | Se muestra información conocida, pendiente y no comparable sin inventar scores. |
| S55.3 | Onboarding adaptativo de las cuatro decisiones (`ESCALA-14`) | 8 | In progress | El flujo lee hechos autorizados, omite preguntas respondidas, hace una pregunta a la vez y ramifica hacia vacíos reales. |
| S55.4 | Modelo nativo de conciliación financiera (`ESCALA-15`) | 8 | Complete | Se separan gasto entregado, cobro facturado, liquidación, registro contable, compras, cobros e ingreso atribuible; se bloquea comparación de métricas incompatibles. |
| S55.5 | Resolución conservadora de entidades (`ESCALA-16`) | 5 | Complete | Regla configurable: identificador primario + coincidencia exacta de nombre como respaldo; ambigüedades quedan sin fusionar. |
| S55.6 | Mapa de decisión y parking lot (`ESCALA-17`) | 3 | Complete | Hallazgos y datos faltantes se convierten en tareas trazables por decisión, prioridad y evidencia requerida. |
| S55.7 | Calificación, regresión y documentación (`ESCALA-18`) | 5 | Planned | Casos de multifuente, conciliación y boundary de privacidad pasan con evidencia; SKILL.md actualizado. |

## Criterios de terminación

- [x] Un hecho persistido conserva fuente, periodo, definición, base temporal, confianza y estado de comparabilidad (S55.1).
- [x] El dashboard puede existir antes del score y deja claro qué sí se sabe y qué falta (S55.2).
- [x] Un flujo de conciliación impide comparar métricas de naturaleza distinta sin advertencia explícita (S55.4).
- [ ] El onboarding reutiliza contexto, pregunta sólo vacíos y conserva una política de deduplicación auditable (S55.3).
- [x] El board recibe un paquete de evidencia y declara límites cuando aún faltan datos (S55.2/S55.6).
- [ ] Datos de empresa nunca salen del directorio local; persistencia bajo `.escala/`.
- [ ] Regresión completa pasa sin fallos nuevos.

## Dependencias

```text
S55.1 contrato de hechos ─┐
S55.2 dashboard ──────────┤→ S55.3 onboarding adaptativo → S55.6 mapa/parking lot
S55.4 conciliación ───────┤        ↑
S55.5 entidades ──────────┘        └→ S55.7 calificación
```

### Machine

```yaml
modules_affected:
  - path: coaching/welcome/
    change: extend
  - path: coaching/evidence/
    change: extend
  - path: coaching/diagnose/
    change: modify
  - path: .escala/agent/memory/
    change: extend
  - path: escala-skills/escala-welcome/
    change: modify
  - path: tests/
    change: add
decisions:
  - id: D1
    choice: "Hecho es la unidad mínima de evidencia con procedencia explícita."
    rationale: "Sin procedencia no se puede conciliar ni auditar."
    constraint: "Cada hecho debe tener fuente, periodo, definición y confianza."
  - id: D2
    choice: "Onboarding adaptativo lee hechos antes de preguntar."
    rationale: "Evita repetir lo que la empresa ya compartió."
    constraint: "No se puede asumir que un hecho ausente equivale a 'no sabe'; debe quedar como pendiente."
  - id: D3
    choice: "Conciliación conservadora: bloquear comparaciones incompatibles."
    rationale: "Mejor no calcular ROAS/escala que calcular con métricas distintas."
    constraint: "Nunca inferir equivalencia entre métricas de distinta naturaleza."
constraints:
  - "Solo archivos locales; sin APIs ni OAuth de terceros."
  - "No inventar scores ni fusionar entidades agresivamente."
  - "Distinguir validación técnica de aceptación humana."
```

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Modelo de hechos demasiado abstracto | Empezar con métricas de Cash (ingreso, gasto, cobro) que ya aparecen en el issue real. |
| Complejidad de conciliación financiera | Prototipar con un caso sintético de dos fuentes antes de generalizar. |
| Fusión agresiva de entidades | Regla configurable y fail-closed: sin identificador claro, queda ambiguo. |
| Confusión con épicar de consolidación de skills (E56) | Mantener límites claros: E55 es producto de onboarding; E56 es catálogo de skills. |
