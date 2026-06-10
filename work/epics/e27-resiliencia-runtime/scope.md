# Epic Scope: E27 — Resiliencia Runtime

**Status:** Draft
**Dependencies:** Ninguna
**Tamaño:** S (3 stories, ~3h)
**Origen:** Auditoría Fable 5 (2026-06-09) — Tema 3

## Visión

El servidor no debe crashear con JSON malformado. Un POST con `{invalid` no debería tumbar el worker thread. CORS no debería ser `*` por defecto si el servidor se expone en red. Esta épica agrega defensa runtime sin cambiar de framework.

## Stories

| Story | Size | Qué |
|-------|:----:|-----|
| **S27.1 — Error handling en handlers HTTP** | S | Envolver `do_POST` y `do_PATCH` en try/except. `json.JSONDecodeError` → 400. `Exception` → 500 con mensaje controlado (sin leak de traceback). Extraer lógica común a `_handle_api_request`. |
| **S27.2 — CORS configurable** | S | Agregar `--cors-origins` al CLI (`__main__.py`). Default: `http://localhost:8080`. Si es `*`, advertir en stderr. Modificar `CORSHandler` para aceptar orígenes. |
| **S27.3 — Tests de resiliencia** | S | Test de integración: iniciar server en puerto aleatorio, POST con body inválido → 400, POST con body válido pero handler que lanza → 500. Verificar que servidor sigue respondiendo después del error. |

## Done Criteria

- [ ] S27.1: POST con `{invalid` devuelve 400 JSON, no crashea.
- [ ] S27.2: `curl -H "Origin: https://evil.com"` no recibe CORS allow. Con `--cors-origins *` sí.
- [ ] S27.3: Tests pasan — servidor sobrevive a errores y sigue respondiendo.
