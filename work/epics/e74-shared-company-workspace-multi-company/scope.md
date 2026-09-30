---
epic_id: E74
title: Workspace compartido por empresa y colaboración multiempresa local
status: planned
depends_on: [E37, E52, E55, E67, E79]
---

# Scope E74

## Transferencia del mínimo correctivo — 2026-09-12

El aislamiento local urgente, identidad/selector y migración del estado global
son propiedad de [E79](../e79-company-isolation-privacy-local-security/scope.md).
E74 consume ese resolver y sus pruebas en S74.1/S74.2 y añade únicamente lo
necesario para colaboración/reconciliación. No se crean un segundo selector,
registro de empresas o migración, ni se espera a E74 para corregir H03.

## Objetivo

Extender el límite local de E37 hacia colaboración basada en archivos, con una
fuente compartible por empresa, aislamiento multiempresa y SQLite estrictamente
local/regenerable. Esta épica crea un ADR porque modifica la suposición previa
de que todo estado canónico vive sólo en una máquina.

## Dentro

- ADR que define qué estado puede ser compartible, qué sigue local y cómo
  invalida o complementa las invariantes de E37 sin crear contradicción.
- Topología por empresa: identificador, directorio, manifest, profile, facts,
  decisions, artifacts, history, inbox y permissions/policies versionados.
- YAML/Markdown con schema, versiones, provenance, owner, aprobación y estado
  de revisión; archivos no válidos no se promueven.
- Registro local de workspaces y selector de empresa con guardas contra mezcla.
- Propuestas de cambio, revisión humana, conflictos explícitos, locks lógicos y
  recibos de reconciliación.
- SQLite local como índice/cache derivado y regenerable por cada instalación;
  pruebas que prohíben compartirlo.
- Compatibilidad con carpeta filesystem ya sincronizada, sin identificar ni
  depender de proveedor cloud.

## Fuera

- Multiwriter ciego con last-write-wins.
- OAuth, API de Drive, control de presencia, chat realtime o servidor central.
- Compartir secretos, tokens, conversaciones privadas o estado sensible sin una
  política/consentimiento específico.
- Inferir que dos empresas con nombres parecidos son la misma entidad.

## Dependencias y secuencia

```text
E37 boundary + E52 consent + E55 facts
              ↓
S74.1 ADR → S74.2 empresas → S74.3 estado portable
                                ↓
              S74.4 conflictos → S74.5 cache → S74.6 qualification
```

E67 permite que los cuatro perfiles respeten el mismo selector/paquete mínimo
de empresa. E72/E73 escriben sólo artifacts aprobados en esta topología.

## Criterios de terminación

- Dos empresas pueden convivir sin lectura o escritura cruzada en pruebas.
- Un segundo colaborador ve estado aprobado desde el workspace compartido, pero
  un cambio conflictivo queda pendiente de reconciliación explícita.
- SQLite aparece sólo fuera del directorio compartido y se reconstruye desde el
  estado portable sin pérdida de aprobaciones/historia.
- Todas las escrituras de estado indican empresa, owner, versión y aprobación.
- Casos offline, duplicados, borrador, conflicto y archivo corrupto fallan de
  forma visible y no destruyen un estado aprobado.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Drive genera copias en conflicto | hashes/revisión/estado pending; nunca last-write-wins. |
| YAML se vuelve una base de datos informal | schemas pequeños, append-only history y cache derivado. |
| Colaboración rompe privacidad | límites por empresa/artefacto, consentimiento y paquetes mínimos. |
| Ambigüedad con E37 | ADR primero y pruebas explícitas de ambos límites. |
