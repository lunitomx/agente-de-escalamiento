---
epic_id: "E43"
date: "2026-07-31"
status: "done"
---

# E43 — Retrospectiva

## Resultado

Épica completada con éxito. Todas las historias (S43.1-S43.6) están mergeadas a
`main` y pasan los gates locales.

| Story | Estado | Evidencia |
|---|---|---|
| S43.1 | Done | `coaching.decision` confirmado |
| S43.2 | Done | `coaching.evidence` produce paquetes trazables |
| S43.3 | Done | `coaching.selector` elige herramienta según área + evidencia |
| S43.4 | Done | `coaching.reviewer` detecta contradicciones y bloquea respuestas inseguras |
| S43.5 | Done | `coaching.responder` genera respuesta ejecutiva de 5 bloques |
| S43.6 | Done | `coaching.qualifier` ejecuta 8 casos (4 positivos, 4 negativos) con 100% de éxito |

## Criterios de terminación

- [x] Toda recomendación relevante nombra evidencia o declara el hueco de información.
- [x] Los cálculos pueden verificarse contra sus fuentes (periodo y fuente en cada recibo).
- [x] Una contradicción conocida se presenta como contradicción (`blocked`).
- [x] Una pregunta ausente bloquea la conclusión cuando altera la decisión (`clarify`/`blocked`).
- [x] La respuesta no expone tecnicismos innecesarios al empresario (markdown ejecutivo).
- [x] Los cuatro pilares tienen casos positivos y negativos aprobados.
- [x] Línea base E42: se establece evidencia de calificación con 8 casos; no se requiere métrica adicional.
- [x] Autoridad local y prohibición de SQLite mantenidas (solo archivos locales).
- [x] Retrospectiva y evidencia de calificación completadas.

## Qué funcionó

- Separar cada paso en un módulo puro (`decision`, `evidence`, `selector`, `reviewer`, `responder`, `qualifier`) facilitó tests y reutilización.
- El patrón `run(context) -> {output, artifacts, errors}` se mantuvo consistente en todos los módulos.
- Los gates (`rai gate check`) detectaron rápidamente problemas de formato y lint.

## Qué mejorar

- S43.6 podría tener casos con contenido real de worksheets en lugar de solo metadatos, pero eso requeriría parseo adicional y queda fuera del alcance M.
- La detección de contradicciones es heurística (confianza baja + mismo periodo); en el futuro podría comparar valores numéricos.

## Decisiones clave

- Mantener el módulo `coaching.selector` con catálogo determinista en código.
- No generar respuesta ejecutiva cuando la revisión no autoriza.
- Calificar con casos de datos para no depender de archivos locales en el test de E43.
