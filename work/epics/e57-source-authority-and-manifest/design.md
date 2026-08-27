---
epic_id: E57
status: active
---

# E57 — Diseño: autoridad de fuente y manifiesto verificable

## Gemba

- El corpus privado existente vive en `scaling_up_llamaparse.md` y
  `scaling_up_llamaparse.txt`; la frontera E36 ya los deniega en export público.
- `conocimiento/` es una representación histórica y no debe cambiarse ni usarse
  como segunda autoridad durante E57.
- `governance/public-boundary.yaml` ya es deny-by-default, pero no nombra
  `sources/**`; la regla explícita evita que el manifiesto futuro dependa sólo
  de esa omisión.
- El clean-export vigente ya comprueba rutas, contenido y dependencias. E57 lo
  extiende; no crea otro exportador.
- El grafo RaiSE no está construido. La consulta se registró como vacía y no
  bloquea este diseño.

## Diseño elegido

Se agrega una única raíz privada `sources/` para metadatos, nunca para una copia
adicional del corpus:

```text
scaling_up_llamaparse.md     ← input privado existente, inmutable en E57
sources/source-registry.yaml ← una entrada por fuente y postura de derechos
sources/source-manifest.jsonl ← unidades estructurales y exclusiones, privado
scripts/build_source_manifest.py
scripts/validate_source_authority.py
```

El registro expresa `documented`, `unknown` o `review_required`; no ofrece
opiniones legales. El builder calcula SHA-256 del input, genera IDs estables a
partir de ruta/locator/tipo y registra una exclusión cuando no puede clasificar
una línea. El validador rechaza mutaciones de hash, huecos, solapes, locators
imposibles, IDs duplicados y una política de export que permita `sources/**`.

La única afirmación pública permitida es un aviso genérico de independencia. No
introduce una marca, afiliación, patrocinio ni autorización no documentada. Las
menciones metodológicas detalladas permanecen privadas y bloqueadas por la
frontera E36 hasta una disposición distinta.

## Alternativas descartadas

1. **Mover el libro a `sources/`:** duplica/mueve material protegido y rompe
   referencias históricas sin beneficio para el contrato.
2. **Guardar sólo un vector index:** no permite demostrar cobertura, locator ni
   exclusiones.
3. **Permitir export del manifiesto sin texto:** aun metadatos detallados pueden
   revelar el contenido/estructura protegida; se mantiene privado.
4. **Declarar “uso permitido” desde el código:** el sistema sólo registra
   evidencia y bloqueos; no sustituye revisión jurídica.

## Contratos principales

- Fuente: `source_id`, ruta relativa, edición/origen conocido, SHA-256,
  `rights_status`, evidencia y `distribution_state`.
- Unidad: `source_id`, `locator`, `line_start`, `line_end`, `content_type`,
  hash de unidad y, cuando aplique, `exclusion_reason`.
- Regla de cobertura: todo rango del archivo pertenece exactamente a una unidad
  o a una exclusión justificada; los rangos no se solapan.
- Frontera: `sources/**`, corpus y derivados detallados no son elegibles para
  clean export; el verificador falla cerrado.

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
    choice: Metadatos privados y deterministas en vez de una nueva copia del corpus.
    rationale: Trazabilidad sin redistribución ni duplicación.
    constraint: El corpus existente no se mueve en E57.
  - id: E57-D2
    choice: Derechos expresados como evidencia y estados de revisión.
    rationale: El código no emite conclusiones legales.
    constraint: Un estado no documentado bloquea la distribución.
  - id: E57-D3
    choice: Un único clean-export existente extendido con una denegación explícita.
    rationale: Evita rutas de publicación paralelas.
    constraint: Ningún manifiesto detallado puede ser excepción.
constraints:
  - No extraer ni normalizar metodología en esta épica.
  - No incluir texto protegido en reportes, fixtures ni recibos.
  - Mantener a SQLite fuera de la autoridad y de cualquier sincronización.
```
