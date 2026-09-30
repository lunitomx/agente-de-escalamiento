---
epic_id: E79
title: Aislamiento por empresa, privacidad y seguridad local
document_status: ready_for_review
epic_status: planned
created: 2026-09-12
---

# E79 — Aislamiento por empresa, privacidad y seguridad local

## Problema y resultado

El empresario podrá confiar en qué empresa está activa, quién recibe su información y qué superficies locales pueden acceder a ella.

**Resultado buscado:** Cero lecturas o escrituras cruzadas entre empresas; acceso local delimitado; consentimiento y promesas de privacidad verificables antes de compartir información.

## Evidencia de entrada

Auditoría local del 2026-09-12 sobre HEAD `50e72f78758ea8422f627508028f9565e3a0ea70`, con cambios preexistentes ajenos a esta planificación. Hallazgos: H03, H07, H08. Ver [registro de hallazgos y límites](../../../governance/pilot-readiness-2026-09-12.md). Las reproducciones se hicieron con datos sintéticos; no constituyen una prueba con empresarios ni con hardware macOS/Windows limpio.

## Encaje con el backlog

E79 adelanta y posee el aislamiento mínimo urgente de E74; E74 reutiliza ese contrato para colaboración y reconciliación futura. No se implementan dos selectores, dos registries ni migraciones rivales.

Épicas relacionadas: E37, E41, E42, E52, E55, E74, E78, E80, E81. La autoridad de estado es [scope.md](scope.md); este brief no inicia implementación ni declara reparado el producto.

## Éxito verificable

- **M1:** Identidad canónica y frontera HTTP segura.
- **M2:** Dos empresas aisladas, legado conciliado y flujo de datos explicado.
- **M3:** Recorrido integrado sin cruces ni filtración en soporte.

## Inversión y límites

Seis historias con tamaños relativos S/M/L; no hay velocidad histórica suficiente para prometer fechas. Implementar primero los límites y un recorrido mínimo real, luego integrar. Si una historia L requiere varios contratos inseparables, dividirla al diseñarla conservando sus requisitos y propietario.

Responsable de aceptación: dueño del producto. Responsable técnico: se asigna al iniciar cada historia. Evidencia externa y participantes: no disponibles por el hecho de crear esta épica.

- Servicio multiusuario en internet, SSO, OAuth propio o colaboración realtime.
- Reasignar hechos antiguos por similitud de nombres o compartir SQLite.
- Prometer control sobre retención/borrado del proveedor IA que ESCALA no puede ejercer.

## Artefactos para ejecución

- [Alcance, requisitos, historias y secuencia](scope.md).
- [Pruebas de aceptación y evidencia de cierre](acceptance.md).
- [Programa y dependencias](../../../governance/pilot-readiness-2026-09-12.md).
