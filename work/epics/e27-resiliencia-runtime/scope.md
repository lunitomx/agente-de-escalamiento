# Epic Scope: E27 — El Dashboard No Se Cae

**Status:** Draft
**Dependencies:** Ninguna
**Tamaño:** S (1 historia, ~1h)
**Origen:** Auditoría Fable 5 (2026-06-09)

## Visión

Si el usuario abre su dashboard de Power of One y ve pantalla blanca, Escala murió para él. Un JSON malformado no debería tumbar nada. Esta épica es mínima: una sola historia que pone defensa donde el usuario toca el producto.

## Stories

| Story | Size | Qué |
|-------|:----:|-----|
| **S27.1 — Error handling en handlers HTTP** | S | `do_POST` y `do_PATCH` con try/except. `json.JSONDecodeError` → 400. `Exception` → 500 con mensaje, sin traceback. |

## Done Criteria

- [ ] POST con body inválido devuelve 400, no pantalla blanca
- [ ] Handler que falla devuelve 500 controlado
- [ ] Servidor sigue respondiendo después del error
