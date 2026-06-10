# Epic Scope: E28 — Deuda Técnica Crítica

**Status:** Draft
**Dependencies:** E26.2 (pyyaml en pyproject.toml)
**Tamaño:** S (3 stories, ~3h)
**Origen:** Auditoría Fable 5 (2026-06-09) — Tema 2 (hallazgos A1, A3, A5, A10)

## Visión

Eliminar código roto y código reinventado. migrate.py tiene columnas SQLite que no existen. El parser YAML casero de 340 líneas no tiene tests y existe solo porque PyYAML no está declarado. generate_dashboards.py serializa JSON con replace() en vez de json.dumps(). Esta épica limpia la deuda técnica crítica detectada en la auditoría.

## Stories

| Story | Size | Qué |
|-------|:----:|-----|
| **S28.1 — Reemplazar parser YAML casero con PyYAML** | S | Agregar `pyyaml` a `pyproject.toml` (S26.2). Reemplazar `_parse_simple_yaml` y todas las funciones auxiliares (~340 LOC) en `migrate.py` con `yaml.safe_load()`. Eliminar: `_parse_yaml_value`, `_parse_yaml_list`, `_parse_yaml_mapping`, `_collect_block_string`, `_parse_inline_mapping`, `_parse_scalar`, `_strip_quotes`, `_make_default`. |
| **S28.2 — Arreglar o eliminar migrate.py** | S | Corregir queries SQL: `data_json` → `data` en worksheets, `(id, data_json)` → columnas reales en companies. Agregar 3 tests con DB `:memory:`. Si la migración ya ocurrió y no se re-ejecuta, eliminar el archivo completo (decisión de Eduardo en preguntas abiertas). |
| **S28.3 — json.dumps() en generate_dashboards.py** | S | `escala_server/cash/generate_dashboards.py:498`: reemplazar `str(db["metrics"]).replace(...)` con `json.dumps(db["metrics"])`. Verificar que dashboards generados tienen JavaScript válido. |

## Done Criteria

- [ ] S28.1: `_parse_simple_yaml` y funciones auxiliares eliminadas. `read_yaml_file` usa `yaml.safe_load()`.
- [ ] S28.2: `migrate_from_yaml(":memory:", tmpdir)` no lanza excepción. Tests pasan.
- [ ] S28.3: `json.dumps()` usado sin replaces manuales. HTML generado tiene JavaScript válido.
