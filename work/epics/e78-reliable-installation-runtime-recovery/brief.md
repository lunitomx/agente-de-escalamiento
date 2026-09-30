---
epic_id: E78
title: Instalación, runtime y recuperación verificables
document_status: ready_for_review
epic_status: planned
created: 2026-09-12
---

# E78 — Instalación, runtime y recuperación verificables

## Problema y resultado

Un empresario podrá instalar, ejecutar, actualizar y recuperar ESCALA sin depender del Python, los paquetes o las rutas personales del desarrollador.

**Resultado buscado:** Una versión identificable completa el recorrido instalar → primera operación → reiniciar → actualizar → recuperar, conservando datos y plataforma elegida.

## Evidencia de entrada

Auditoría local del 2026-09-12 sobre HEAD `50e72f78758ea8422f627508028f9565e3a0ea70`, con cambios preexistentes ajenos a esta planificación. Hallazgos: H01, H02, H05, H09, H10. Ver [registro de hallazgos y límites](../../../governance/pilot-readiness-2026-09-12.md). Las reproducciones se hicieron con datos sintéticos; no constituyen una prueba con empresarios ni con hardware macOS/Windows limpio.

## Encaje con el backlog

Reparación transversal de las rutas existentes de E10/E41. E78 es el único propietario de esta implementación correctiva; E10/E41 consumen sus recibos y E42 conserva la aceptación en equipos limpios.

Épicas relacionadas: E10, E41, E42, E67, E79, E81. La autoridad de estado es [scope.md](scope.md); este brief no inicia implementación ni declara reparado el producto.

## Éxito verificable

- **M1:** Artefacto y primera operación aislados del entorno del desarrollador.
- **M2:** Proceso real, actualización efectiva y recuperación de datos comprobados.
- **M3:** Recorrido integrado y handoff reproducible a E42/E81.

## Inversión y límites

Seis historias con tamaños relativos S/M/L; no hay velocidad histórica suficiente para prometer fechas. Implementar primero los límites y un recorrido mínimo real, luego integrar. Si una historia L requiere varios contratos inseparables, dividirla al diseñarla conservando sus requisitos y propietario.

Responsable de aceptación: dueño del producto. Responsable técnico: se asigna al iniciar cada historia. Evidencia externa y participantes: no disponibles por el hecho de crear esta épica.

- Crear un nuevo asesor, servidor central o instalador gráfico completo.
- Publicar paquetes o declarar Windows nativo/macOS calificados sin sus recibos E42.
- Crear entornos duplicados, instalar con pip global o descargar dependencias de manera implícita en modo anunciado como offline.

## Artefactos para ejecución

- [Alcance, requisitos, historias y secuencia](scope.md).
- [Pruebas de aceptación y evidencia de cierre](acceptance.md).
- [Programa y dependencias](../../../governance/pilot-readiness-2026-09-12.md).
