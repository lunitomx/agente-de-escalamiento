---
epic_id: E67
title: Capacidades internas y adaptadores portables
status: planned
depends_on: [E65, E56]
---

# Scope E67

## Objetivo

Conectar los procedimientos del MVP al orquestador `escala` mediante capacidades internas versionadas y adaptadores por plataforma, conservando una sola experiencia pública para el empresario.

## Dentro

- Mapa `procedure → capability → lifecycle → evidencia` en el catálogo canónico.
- Enrutamiento explicable desde intención/evidencia disponible a capacidad interna.
- Adaptador de instalación Codex y adaptador Claude con extensiones aisladas del core.
- Verificación de que los aliases de compatibilidad no alojan lógica propia.
- Pruebas de paridad de rutas, artifacts y límites entre plataformas.

## Fuera

- Publicar un skill/command por cada procedimiento.
- Reescribir ontología, metodología o los contratos de datos E55.
- Depender de una capacidad exclusiva de una plataforma dentro del núcleo.
- Prometer soporte de versiones/plataformas sin corrida limpia de E68.

## Historias y secuencia

| Orden | Historia | Entrega verificable |
|---:|---|---|
| 1 | S67.1 Capability map | Catálogo completo y validado para las seis intervenciones. |
| 2 | S67.2 Codex adapter | Instalación limpia con una sola puerta pública. |
| 3 | S67.3 Claude adapter | Mismo core semántico con empaque específico mínimo. |
| 4 | S67.4 Paridad/migración | Reporte de rutas y aliases sin duplicación. |

## Criterios de terminación

- Instalación nueva muestra sólo `escala`.
- Las seis rutas MVP producen contratos semánticamente equivalentes en ambas plataformas.
- Core portable no contiene instrucciones exclusivas de una plataforma.
- Ningún alias ejecuta una segunda implementación.

## Handoff y riesgos

E68 recibe builds instalables y una matriz de paridad. No se intenta corregir diferencias de modelo ocultándolas: se reportan y se prueban.
