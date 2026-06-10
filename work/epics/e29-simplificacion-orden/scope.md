# Epic Scope: E29 — Simplificación y Orden

**Status:** Draft
**Dependencies:** E26.2 (pyyaml en pyproject.toml), E28.1 (parser YAML reemplazado)
**Tamaño:** M (3 stories, ~5h)
**Origen:** Auditoría Fable 5 (2026-06-09) — Temas 4 y 5 (hallazgos A6, A9)

## Visión

El proyecto ya tomó las decisiones correctas de arquitectura — YAML declarativo para conocimiento, separación de concerns. Pero no las terminó de aplicar: VerneHandler tiene 140 líneas de templates hardcodeados que deberían estar en `conocimiento/`. Las épicas E18-E22 tienen directorios duplicados que confunden al graph builder. Esta épica termina la simplificación.

## Stories

| Story | Size | Qué |
|-------|:----:|-----|
| **S29.1 — Extraer templates Verne a YAML** | M | Mover `_VERNE_TEMPLATES` (~60 líneas) y `_DAILY_CHECKLIST` (~30 líneas) de `verne_handler.py:72-165` a `conocimiento/coaching/verne-templates.yaml`. `VerneHandler.__init__` carga con `yaml.safe_load()`. Tests existentes deben pasar sin cambios. Objetivo: `verne_handler.py` < 350 LOC. |
| **S29.2 — Consolidar épicas duplicadas E18-E22** | S | Para cada par (e18-class-to-skill vs e18-escala-server, e19-book-ingestion vs e19-strategy-core, etc.), determinar canónica (la que tiene retrospectiva). Mover no-canónica a `work/epics/_archived/`. Reconstruir graph: `rai graph build`. Verificar 0 warnings de duplicados. |
| **S29.3 — .gitattributes + limpieza** | S | Crear `.gitattributes` con `* text=auto` + LF forzado en `.yaml`, `.yml`, `.md`, `.py`. Ejecutar `git add --renormalize .`. Verificar que no hay cambios spurios. |

## Done Criteria

- [ ] S29.1: `test_verne_handler.py` pasa sin cambios. `verne_handler.py` < 350 LOC. Templates en YAML.
- [ ] S29.2: 5 directorios en `_archived/`. Graph sin warnings de duplicados. Una épica por número.
- [ ] S29.3: `.gitattributes` existe. `git status` limpio tras renormalize.
