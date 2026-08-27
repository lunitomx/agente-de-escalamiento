---
epic_id: E57
title: Autoridad de fuente y manifiesto verificable
status: planned
depends_on: [E36, E56]
---

# E57 — Autoridad de fuente y manifiesto verificable

## Resultado

Cada unidad del corpus privado tiene identidad, ubicación, hash, tipo y disposición. Ningún corpus ni derivado llega al export público por accidente.

## Historias

| ID | Historia | Termina cuando |
|---|---|---|
| S57.1 | Registro de fuentes y derechos | Cada fuente tiene propietario, uso permitido conocido/desconocido, vigencia y revisión requerida; desconocido bloquea distribución. |
| S57.2 | Manifiesto estructural | Se generan `source_id`, sección, páginas/líneas, tipo, hash y exclusiones justificadas. |
| S57.3 | Frontera privada de derivados | La política deny-by-default bloquea corpus crudo, manifiestos detallados y ontología derivada hasta disposición explícita. |
| S57.4 | Verificadores de integridad | Un cambio de fuente o locator inválido falla de forma determinista. |
| S57.5 | Transparencia de metodología | El producto declara de forma verificable que es independiente y no oficial, sin afirmaciones de afiliación ni uso no aprobado de marcas. |

## Cierre

- 100% de líneas asignadas a una unidad o excluidas con motivo.
- Un clean export no contiene corpus ni derivados privados.
- No se afirma licencia o permiso que no conste en el registro.
- El aviso de independencia se prueba en onboarding, materiales de producto y distribución permitida.

## Fuera

No extrae conceptos ni escribe procedimientos: habilita E58-E63.
