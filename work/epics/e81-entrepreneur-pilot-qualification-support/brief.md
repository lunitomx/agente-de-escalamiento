---
epic_id: E81
title: Piloto empresarial de 3–5 a 20 participantes y soporte medible
document_status: ready_for_review
epic_status: planned
created: 2026-09-12
---

# E81 — Piloto empresarial de 3–5 a 20 participantes y soporte medible

## Problema y resultado

El recorrido reparado puede demostrar utilidad y autonomía con empresarios reales, manteniendo visible el esfuerzo de soporte y las razones de abandono.

**Resultado buscado:** Una decisión de ampliar, iterar o detener sustentada en 3–5 sesiones acompañadas y una cohorte posterior de 20 instalaciones independientes.

## Evidencia de entrada

Auditoría local del 2026-09-12 sobre HEAD `50e72f78758ea8422f627508028f9565e3a0ea70`, con cambios preexistentes ajenos a esta planificación. Hallazgos: H09, H10, H11, H12. Ver [registro de hallazgos y límites](../../../governance/pilot-readiness-2026-09-12.md). Las reproducciones se hicieron con datos sintéticos; no constituyen una prueba con empresarios ni con hardware macOS/Windows limpio.

## Encaje con el backlog

E81 organiza adopción y soporte del piloto; E42 sigue siendo dueño de hardware/aceptación y E68 de semántica/paridad/ciclo trimestral. Se reutilizan sus recibos por commit/hash/plataforma y nunca se sustituyen por métricas de uso.

Épicas relacionadas: E10, E42, E44, E45, E68, E70. La autoridad de estado es [scope.md](scope.md); este brief no inicia implementación ni declara reparado el producto.

## Éxito verificable

- **M1:** Matriz, protocolo y soporte listos; reparaciones verificadas antes de reclutar.
- **M2:** 3–5 empresarios observados y decisión explícita de ampliar/iterar.
- **M3:** Cohorte de veinte medida, utilidad y carga de soporte conocidas.
- **M4:** Decisión humana e informe con pendientes y handoff a gates existentes.

## Inversión y límites

Seis historias con tamaños relativos S/M/L; no hay velocidad histórica suficiente para prometer fechas. Implementar primero los límites y un recorrido mínimo real, luego integrar. Si una historia L requiere varios contratos inseparables, dividirla al diseñarla conservando sus requisitos y propietario.

Responsable de aceptación: dueño del producto. Responsable técnico: se asigna al iniciar cada historia. Evidencia externa y participantes: no disponibles por el hecho de crear esta épica.

- Contactar o inscribir empresarios automáticamente; usar datos reales sin autorización.
- Declarar completa E42/E68, rebajar sus criterios o reemplazar un trimestre por una semana.
- Telemetría automática, CRM/mesa de ayuda cloud o publicación automática del producto.

## Artefactos para ejecución

- [Alcance, requisitos, historias y secuencia](scope.md).
- [Pruebas de aceptación y evidencia de cierre](acceptance.md).
- [Programa y dependencias](../../../governance/pilot-readiness-2026-09-12.md).
