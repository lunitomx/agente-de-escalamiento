---
epic_id: E68
title: Calificación semántica y cross-platform del MVP
status: planned
depends_on: [E67, E35]
---

# E68 — Calificación semántica y cross-platform del MVP

## Resultado

El MVP se prueba por la calidad de sus decisiones y artefactos, no sólo porque un archivo sea válido o un demo parezca correcto.

## Historias

| ID | Historia | Termina cuando |
|---|---|---|
| S68.1 | Suite de activación | Cada procedimiento tiene prompts should-trigger, should-not-trigger, ambiguos y secuencias. |
| S68.2 | Golden outputs | Se comprueba evidencia, campos, preguntas faltantes, límites y Who/What/When. |
| S68.3 | Ensayos aislados y A/B | Se comparan sesiones limpias con capacidad habilitada/deshabilitada, sin afirmar causalidad estadística indebida. |
| S68.4 | Calificación Codex/Claude | Corridas limpias se comparan por assertions semánticas y se reportan diferencias. |
| S68.5 | Piloto trimestral | Una empresa de prueba revisa un ciclo completo y aprueba/corrige cada artefacto. |

## Cierre

100% estructura válida; ≥90% precisión y recall de routing; ≥95% assertions de salida; diferencias explícitas; revisión humana de cada procedimiento y piloto trimestral antes de ampliar biblioteca.
