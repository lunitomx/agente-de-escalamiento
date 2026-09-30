---
epic_id: E80
title: Diagnósticos honestos e ingreso de información útil
document_status: ready_for_review
epic_status: planned
created: 2026-09-12
---

# E80 — Diagnósticos honestos e ingreso de información útil

## Problema y resultado

Un empresario obtendrá un primer resultado útil si ESCALA distingue evidencia de contenido rellenado, aprovecha los documentos disponibles y pide sólo la información que cambia la decisión.

**Resultado buscado:** Un plan lleno de placeholders nunca aparece como negocio saludable; cada conclusión y gráfico explica evidencia, periodo, límites y siguiente acción.

## Evidencia de entrada

Auditoría local del 2026-09-12 sobre HEAD `50e72f78758ea8422f627508028f9565e3a0ea70`, con cambios preexistentes ajenos a esta planificación. Hallazgos: H04, H06, H09, H12. Ver [registro de hallazgos y límites](../../../governance/pilot-readiness-2026-09-12.md). Las reproducciones se hicieron con datos sintéticos; no constituyen una prueba con empresarios ni con hardware macOS/Windows limpio.

## Encaje con el backlog

E80 repara las superficies actuales de diagnóstico, dashboard e intake. E73 conserva la recomendación y generación avanzada de dashboards; E75 conserva deep dives. Se reutilizan facts y consentimiento de E49/E52/E55.

Épicas relacionadas: E37, E38, E40, E49, E52, E55, E73, E75, E78, E79, E81. La autoridad de estado es [scope.md](scope.md); este brief no inicia implementación ni declara reparado el producto.

## Éxito verificable

- **M1:** Indicadores interpretables y regresión de placeholders cerrada.
- **M2:** Documento → evidencia → acción → reanudación con empresa autorizada.
- **M3:** Coherencia de todas las superficies y handoff semántico a E68/E81.

## Inversión y límites

Seis historias con tamaños relativos S/M/L; no hay velocidad histórica suficiente para prometer fechas. Implementar primero los límites y un recorrido mínimo real, luego integrar. Si una historia L requiere varios contratos inseparables, dividirla al diseñarla conservando sus requisitos y propietario.

Responsable de aceptación: dueño del producto. Responsable técnico: se asigna al iniciar cada historia. Evidencia externa y participantes: no disponibles por el hecho de crear esta épica.

- Certificar salud empresarial mediante un índice compuesto arbitrario.
- OCR universal, extracción cloud implícita o interpretación automática de cualquier estado financiero.
- Crear otro motor de facts, otro framework financiero o la biblioteca completa de procedimientos.

## Artefactos para ejecución

- [Alcance, requisitos, historias y secuencia](scope.md).
- [Pruebas de aceptación y evidencia de cierre](acceptance.md).
- [Programa y dependencias](../../../governance/pilot-readiness-2026-09-12.md).
