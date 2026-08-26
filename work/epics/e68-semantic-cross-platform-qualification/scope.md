---
epic_id: E68
title: Calificación semántica y cross-platform del MVP
status: planned
depends_on: [E67, E35]
---

# Scope E68

## Objetivo

Calificar el MVP por activación correcta, comportamiento ante ambigüedad, calidad del artifacto, honestidad de incertidumbre y resultado comparable entre plataformas.

## Dentro

- Suites should-trigger, should-not-trigger, ambiguas y multi-paso por procedimiento.
- Golden cases que evalúan campos, evidencia, preguntas faltantes, límites y Who/What/When.
- Corridas aisladas de Codex y Claude y comparación de assertions semánticas.
- Experimentos A/B capability habilitada/deshabilitada para medir valor relativo sin sobreinterpretar.
- Revisión humana individual por procedimiento y un piloto de ciclo trimestral.
- Extensión de E35: versiones de expected behavior y gates de regresión.

## Fuera

- Declarar calidad por la prosa o una única demo.
- Hacer pruebas con información identificable de clientes sin autorización.
- Automatizar promoción o publicación tras una suite verde.
- Abrir toda la biblioteca; E69 depende de este gate.

## Historias y secuencia

| Orden | Historia | Entrega verificable |
|---:|---|---|
| 1 | S68.1 Activación | Dataset y medición de precision/recall. |
| 2 | S68.2 Golden outputs | Assertions estructurales y semánticas. |
| 3 | S68.3 Aislado/A-B | Recibos de sesiones limpias y comparación. |
| 4 | S68.4 Cross-platform | Reporte de diferencias y acciones. |
| 5 | S68.5 Piloto | Aceptación/correcciones de un ciclo real autorizado. |

## Criterios de terminación

- 100% de validación estructural de procedimientos.
- ≥90% precision y recall de routing en el conjunto acordado.
- ≥95% assertions de salida aprobadas.
- Diferencias Codex/Claude declaradas y evaluadas, no ocultas.
- Una persona revisa cada procedimiento y un piloto trimestral completa el ciclo MVP.

## Handoff y riesgos

E69 sólo abre con este gate. Un score bajo devuelve el procedimiento a E65/E67; no se maquilla con prompts adicionales sin identificar la causa.
