# Epic Scope: E28 — Deuda Técnica Que Muerde al Usuario

**Status:** Draft
**Dependencies:** Ninguna
**Tamaño:** S (3 historias, ~3h)
**Origen:** Auditoría Fable 5 (2026-06-09)

## Visión

Tres bugs que el usuario SÍ va a sentir: dashboards con JavaScript roto, migración que falla si se re-ejecuta, parser YAML casero que puede corromper datos. Arreglos quirúrgicos, sin refactors innecesarios.

## Stories

| Story | Size | Qué |
|-------|:----:|-----|
| **S28.1 — pyyaml + eliminar parser casero** | S | Agregar `pyyaml` a `pyproject.toml`. Reemplazar ~340 LOC de parser YAML casero en `migrate.py` con `yaml.safe_load()`. |
| **S28.2 — Arreglar migrate.py** | S | Corregir columnas SQL inexistentes (`data_json` → `data`, etc). O eliminar si la migración ya fue one-shot. |
| **S28.3 — json.dumps() en dashboards** | S | `generate_dashboards.py:498`: reemplazar `str().replace().replace()` con `json.dumps()`. JavaScript válido. |

## Done Criteria

- [ ] S28.1: parser casero eliminado. `read_yaml_file` usa `yaml.safe_load()`
- [ ] S28.2: `migrate_from_yaml(":memory:", tmp)` no lanza error
- [ ] S28.3: dashboards generados con JavaScript sintácticamente válido
