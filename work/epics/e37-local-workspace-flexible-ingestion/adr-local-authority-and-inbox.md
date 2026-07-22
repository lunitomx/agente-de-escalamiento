---
adr_id: "E37-ADR-001"
title: "Local Data Authority and Non-Destructive File Inbox"
status: "accepted"
date: "2026-07-22"
owners:
  - "ESCALA product owner"
  - "E37 implementation"
---

# E37-ADR-001: Local Data Authority and Non-Destructive File Inbox

## Context

El producto debe instalarse y operar en la máquina de la persona que lo
instala. El equipo puede intercambiar documentos mediante una carpeta local o
una carpeta ya sincronizada por Google Drive/OneDrive, pero esa carpeta no debe
transportar SQLite ni el estado canónico de la empresa. La implementación
actual tiene DAOs SQLite locales y un `class_intake` específico para clases,
pero no un contrato genérico que pueda aceptar excels, documentos,
transcripciones y entradas fallidas sin filtrar rutas o duplicar fuentes.

## Decision

1. `data_root` y `database_path` son autoridad local explícita y se validan
   antes de crear directorios, inicializar SQLite o importar contenido.
2. `exchange_root` es una bandeja de documentos; el producto usa operaciones
   de filesystem y no conoce ni invoca APIs de Drive/OneDrive.
3. El database path dentro de `exchange_root`, incluso por symlink resuelto,
   bloquea la operación de forma fail-closed.
4. Cada fuente se perfila primero en modelos Pydantic estrictos con fingerprint,
   procedencia relativa, capacidad declarada, preguntas y estado de extracción.
5. El inbox es idempotente por fingerprint y no destructivo: duplicados,
   corruptos, cifrados, grandes y no soportados generan disposición local y
   receipt; el archivo original no se borra ni se sobrescribe.
6. La promoción de un perfil a hechos de empresa pertenece a E38-E40 y no se
   mezcla con el parser de entrada.

## Alternatives Considered

### Guardar SQLite junto a la carpeta compartida

Rechazado. Un cliente de sincronización podría copiar WAL, journal o una base
  parcialmente escrita y romper autoridad, privacidad e integridad.

### Detectar Drive/OneDrive por nombre de carpeta

Rechazado. Los nombres son convenciones locales, no una prueba de sincronía;
  la configuración de rol y la guarda de containment son más seguras.

### Mover o borrar automáticamente archivos problemáticos

Rechazado. La carpeta pertenece al usuario/equipo y una operación destructiva
  haría difícil recuperar la evidencia original. La disposición se registra
  localmente y el archivo queda intacto.

### Reutilizar `coaching.class_intake`

Rechazado como núcleo genérico. Su contrato está hecho para clases, persiste
  rutas absolutas y no perfila tablas o documentos empresariales. Se conserva
  para compatibilidad, mientras el nuevo registry es source-neutral.

## Consequences

### Positive

- La autoridad de datos es verificable antes de tocar SQLite.
- Un equipo puede compartir documentos ordinarios sin convertir ESCALA en SaaS.
- Los archivos del empresario entran tal como existen y sus límites quedan
  visibles.
- Reintentos seguros y receipts redacted hacen posible una auditoría local.

### Costs and Constraints

- Cada formato necesita un adapter local o se marca explícitamente como
  `unsupported`.
- La detección de ambigüedad produce preguntas que el empresario debe contestar;
  el producto no puede prometer interpretación universal.
- E41 debe empaquetar los adapters y E42 debe probarlos con una empresa
  sintética antes de declarar cobertura completa.

## Revisit Conditions

Revisar solo si el dueño cambia explícitamente el producto a hosted/multi-writer
o si una nueva plataforma exige otro mecanismo de almacenamiento. Cualquier
cambio requiere un ADR nuevo; no se modifica esta decisión silenciosamente.
