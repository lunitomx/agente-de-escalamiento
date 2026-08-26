---
epic_id: E57
title: Autoridad de fuente y manifiesto verificable
status: planned
depends_on: [E36, E56]
---

# Scope E57

## Objetivo

Crear la cadena privada de custodia para cada fuente metodológica antes de extraer conocimiento: autoridad, derechos conocidos/desconocidos, identidad estable, locator, hash, clasificación y frontera de exportación.

## Dentro

- Registro de fuentes con propietario, edición, procedencia, revisión y estado de uso/distribución.
- Manifiesto jerárquico determinista: capítulo, sección, página/líneas, tipo de contenido, hash y `source_id` estable.
- Clasificación de unidades: definición, pregunta, acción, warning, fórmula, herramienta, tabla/formulario, ejemplo y referencia externa.
- Exclusiones explícitas y verificables para material no metodológico o ilegible.
- Extensión de la política E36 para negar por defecto corpus y derivados detallados en exportaciones públicas.
- Validadores de hash, locator, cobertura de líneas y frontera de exportación.

## Fuera

- Extraer, normalizar o interpretar reglas del libro.
- Dar una opinión legal o asumir que un uso privado autoriza distribución.
- Cambiar la experiencia de `escala`, memoria o skills.
- Reescribir historial Git o mover material sin una migración autorizada.

## Historias y secuencia

| Orden | Historia | Entrega verificable |
|---:|---|---|
| 1 | S57.1 Registro de fuentes y derechos | Registro versionado que declara evidencia disponible y bloqueos. |
| 2 | S57.2 Manifiesto estructural | JSONL privado con `source_id`, locator, hash y content type. |
| 3 | S57.3 Frontera de derivados | Reglas deny-by-default y dry run de export. |
| 4 | S57.4 Validadores | Reporte reproducible de integridad y exclusiones. |

## Criterios de terminación

- Todas las líneas quedan asignadas a una unidad o excluidas con motivo.
- Un cambio de archivo, hash o locator falla el validador.
- El clean export no contiene corpus, manifiestos detallados ni derivados denegados.
- El registro distingue permiso documentado, estado desconocido y pendiente de revisión.
- Se publica recibo de validación, sin incluir el contenido protegido.

## Dependencias y handoff

Depende de la frontera E36 y respeta la puerta única de E56. Entrega el manifiesto y política privada a E58; E59-E63 no pueden empezar extracción aprobable sin este contrato.

## Riesgos y no-gos

- No convertir el estado de derechos en una conclusión jurídica.
- No usar el manifiesto como un atajo para distribuir texto o derivados.
- No permitir que una exclusión silenciosa infle la métrica de cobertura.
