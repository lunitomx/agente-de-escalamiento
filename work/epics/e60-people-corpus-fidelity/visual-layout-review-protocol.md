---
epic_ids: ["E60", "E61", "E62"]
document_status: "ready-for-authorized-review"
---

# Protocolo de revisión visual de Growth Tools

## Propósito y límite

Validar topología, columnas, filas, agrupaciones y campos dependientes contra
un activo visual autorizado. No basta un parser de texto o una imagen descrita.
El PDF, capturas o imágenes no se guardan, versionan ni exportan desde este
repositorio.

## Antes de revisar

- Obtener acceso lícito al activo y registrar sólo URL, edición, páginas y
  referencia opaca de revisor.
- Mantener el activo fuera del worktree; `asset_persisted` debe ser `false`.
- Comparar contra los recibos semánticos privados existentes, no contra memoria
  del revisor.

## Qué validar

- E60 People: OPPP, FACe y PACe.
- E61 Strategy: SWT, Seven Strata, OPSP y Vision Summary.
- E62 Execution: WWW y Rockefeller Habits Checklist.

Para cada formulario se confirma número de página, ejes/columnas/filas,
campos obligatorios y relaciones espaciales. Una discrepancia no se corrige en
silencio: deja el resultado fuera de `pass` y vuelve a la cola de revisión.

## Recibo

El recibo privado debe cumplir `validators/form_layout_review.py` y se valida
sin leer el activo:

```text
uv run python scripts/check_form_layout_review.py <recibo-privado.json>
```

El validador admite `pass` sólo con inspección manual, derechos
`private-validation-only`, cero activos persistidos, cero discrepancias y una
referencia opaca de revisor. Cada scope E60–E62 conserva abierto el gate hasta
que exista su recibo correspondiente.
