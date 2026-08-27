---
epic_id: E57
title: Autoridad de fuente y manifiesto verificable
status: active
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
- Contrato de transparencia: aviso de producto independiente/no oficial,
  revisión de afirmaciones de afiliación y registro de vocabulario permitido.

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
| 5 | S57.5 Transparencia | Aviso probado en rutas permitidas sin declarar patrocinio, afiliación o autorización inexistentes. |

## Criterios de terminación

- Todas las líneas quedan asignadas a una unidad o excluidas con motivo.
- Un cambio de archivo, hash o locator falla el validador.
- El clean export no contiene corpus, manifiestos detallados ni derivados denegados.
- El registro distingue permiso documentado, estado desconocido y pendiente de revisión.
- Se publica recibo de validación, sin incluir el contenido protegido.
- El onboarding y la documentación permitida incluyen una declaración de
  independencia aprobada por el gate de derechos.

## Dependencias y handoff

Depende de la frontera E36 y respeta la puerta única de E56. Entrega el manifiesto y política privada a E58; E59-E63 no pueden empezar extracción aprobable sin este contrato.

## Riesgos y no-gos

- No convertir el estado de derechos en una conclusión jurídica.
- No usar el manifiesto como un atajo para distribuir texto o derivados.
- No permitir que una exclusión silenciosa infle la métrica de cobertura.
- No mover ni duplicar `scaling_up_llamaparse.*`; el manifiesto lo referencia
  por ruta, hash y locator, y E58 decidirá la migración de conocimiento.
- No introducir menciones de metodología o marca en el export público sin una
  disposición documentada; el aviso público debe ser genérico e independiente.

## Plan de implementación

| Orden | Historia | Dependencia | Entrega y razón |
|---:|---|---|---|
| 1 | S57.1 Registro de fuentes y derechos | E36/E56 | Contrato privado de autoridad: ruta, hash, edición, origen, estado de derechos y frontera de distribución. Es el ancla de las demás historias. |
| 2 | S57.2 Manifiesto estructural | S57.1 | Generador determinista que cubre cada línea con una unidad o exclusión justificada; no interpreta el texto. |
| 3 | S57.3 Frontera de derivados | S57.1 | Regla explícita `sources/**` deny-by-default y prueba de clean export antes de producir más derivados. |
| 4 | S57.4 Verificadores de integridad | S57.2/S57.3 | Valida hashes, rangos, IDs, exclusiones y frontera; un cambio no registrado falla cerrado. |
| 5 | S57.5 Transparencia | S57.3/S57.4 | Aviso genérico de independencia, probado sólo en superficies permitidas. |

### Hitos

| Hito | Historias | Criterio de éxito |
|---|---|---|
| M1 — Autoridad privada | S57.1 | Ninguna fuente se presenta como autorizada si el registro dice `unknown` o `review_required`. |
| M2 — Cobertura reproducible | S57.2/S57.4 | El mismo input produce el mismo manifiesto y cualquier línea queda asignada o excluida con motivo. |
| M3 — Frontera segura | S57.3/S57.5 | Clean export falla cerrado ante corpus, manifiesto detallado o lenguaje de afiliación. |

### Progreso

| Story | Estado | Evidencia requerida |
|---|---|---|
| S57.1 | Done | Registro tipado, CLI segura y 8 pruebas de hash/derechos/ruta/recibo. |
| S57.2 | Done | Manifiesto privado de 407 unidades, cobertura total y 16 pruebas combinadas. |
| S57.3 | Pending | Política de frontera, build limpio y caso negativo. |
| S57.4 | Pending | CLI/script de validación y recibo sin texto protegido. |
| S57.5 | Pending | Copia independiente, tests de superficies permitidas y revisión de vocabulario. |

### Machine

```yaml
modules_affected:
  - path: sources/
    change: create
  - path: scripts/build_source_manifest.py
    change: create
  - path: scripts/validate_source_authority.py
    change: create
  - path: governance/public-boundary.yaml
    change: modify
  - path: governance/public-export.yaml
    change: modify
  - path: validators/public_export.py
    change: modify
  - path: tests/test_source_authority.py
    change: create
decisions:
  - id: E57-D1
    choice: El manifiesto es privado, determinista y sólo contiene metadatos, hashes y locators.
    rationale: Permite trazabilidad sin copiar ni publicar el corpus.
    constraint: No duplicar ni mover `scaling_up_llamaparse.*`.
  - id: E57-D2
    choice: El estado de derechos usa evidencia y `unknown`, no conclusiones jurídicas.
    rationale: Evita convertir una suposición técnica en autorización de distribución.
    constraint: `unknown` y `review_required` bloquean exportación.
  - id: E57-D3
    choice: `sources/**` se deniega explícitamente en el clean export.
    rationale: La política actual es deny-by-default, pero una regla explícita hace el límite auditable.
    constraint: No abrir excepciones para manifiestos detallados.
constraints:
  - La fuente privada y los derivados detallados nunca salen en un export público.
  - Cada línea del input queda cubierta o excluida con motivo estable.
  - No se interpreta ni normaliza conocimiento en E57; eso comienza en E58.
```
