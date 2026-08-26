---
epic_id: E70
title: Calificación total y gate de distribución
status: planned
depends_on: [E36, E42, E68, E69]
---

# E70 — Calificación total y gate de distribución

## Resultado

Una decisión de distribución se toma sobre evidencia: cobertura, fidelidad, instalación, privacidad, export limpio, límites y disposición de derechos.

## Historias

| ID | Historia | Termina cuando |
|---|---|---|
| S70.1 | Matriz de release | Cada `source_id` llega a nodo, procedimiento, capability, test y estado. |
| S70.2 | Gate de instalación | Codex y Claude se prueban en instalaciones limpias y el empresario ve una sola puerta. |
| S70.3 | Gate local-first | Datos, SQLite, carpeta compartida y falta de conectores se prueban contra los invariantes E36. |
| S70.4 | Gate de frontera/IP | Export limpio no contiene corpus/derivados prohibidos; la disposición de derechos queda explícita, no inferida. |
| S70.5 | Aceptación humana y límites | Se publican límites conocidos, brechas externas y evidencia de aceptación. |

## Cierre

0 hallazgos críticos; matriz completa; clean export verificable; aceptación humana; y decisión explícita de no publicar o de publicar con revisión de derechos correspondiente. No se publica automáticamente.
