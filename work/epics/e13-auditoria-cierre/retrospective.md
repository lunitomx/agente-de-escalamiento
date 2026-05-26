# E13 — Auditoría y Cierre de Epics (ScaleUp Agent)

**Status:** COMPLETE
**Date:** 2026-05-25

## Summary

Épica de saneamiento del repositorio ScaleUp Agent. Se cerraron formalmente 4 epics que estaban huérfanos (E6, E7, E8, E12), se reparó 1 test roto, se añadieron 34 tests nuevos a módulos críticos, se sincronizó la fuente de verdad del coaching engine (install.sh → root coaching/), se eliminaron 2,447 líneas de dead code, y se actualizó el roadmap del producto.

## Stories

| ID | Name | Status | Impact |
|----|------|--------|--------|
| S13.1 | Close E12 — Codex & Auto-Update | ✅ Done | E12 cerrado como cancelled (absorbido por E11) |
| S13.2 | Fix test_finds_overdue | ✅ Done | Test reparado (date drift 2026→2099) |
| S13.3 | Close E6 — Knowledge Ontology | ✅ Done | Close commit + retrospectiva |
| S13.4 | Close E7 — Agent Intelligence | ✅ Done | Close commit + retrospectiva (ghost close reparado) |
| S13.5 | Close E8 — Coaching Engine | ✅ Done | Close commit (retrospectiva ya existía) |
| S13.6 | Add tests for diagnose, level, router | ✅ Done | +34 tests, 3 nuevos test suites |
| S13.7 | Sync coaching sources | ✅ Done | install.sh ahora apunta a root coaching/ |
| S13.8 | Cleanup residues | ✅ Done | −2,447 líneas, 42 archivos eliminados, 5 skills actualizados |
| S13.9 | Update product-roadmap.md | ✅ Done | Roadmap compactado de 254→105 líneas |

## Metrics

| Metric | Value |
|--------|-------|
| Stories planned/completed | 9/9 |
| Epics cerrados formalmente | 4 (E6, E7, E8, E12) |
| Tests añadidos | +34 (103 → 139, 0 fallas) |
| Dead code eliminado | −2,447 líneas, 42 archivos |
| Commits en main | 18 commits en 9 merges |
| Archivos tocados | 66 files, +420/−2,665 líneas |

## What we learned

1. **Ghost closes son comunes** — E7 y E8 tenían todo el código implementado y tracking marcado como done, pero nunca recibieron el close commit formal. El scope.md se actualiza manualmente pero el close commit requiere ceremonia explícita.
2. **E12 fue un epic duplicado** — se creó después de que E11 ya estaba en marcha, y todo su scope fue absorbido por E11. Lección: antes de crear un nuevo epic, verificar si su scope puede ser una story adicional de un epic existente.
3. **Doble fuente de verdad es peligroso** — `coaching/` y `.scaleup/coaching/` divergieron arquitectónicamente (flat modules vs engine/formatter split). La solución fue unificar apuntando install.sh al directorio activo y eliminar el orphanado.
4. **Tests con fechas fijas se rompen con el tiempo** — `test_finds_overdue` usaba `due:2026-05-01` como fixture. Al llegar esa fecha, el test falló. Buena práctica: usar fechas lejanas (2099) en fixtures de tests.

## Parking Lot

- Port del módulo `summary` (existía en `.scaleup/coaching/summary/` pero no en `coaching/`) — si se necesita, crear como nuevo módulo en `coaching/summary/`
- Validación E2E post-sync: instalar desde cero con `install.sh` y verificar que todos los comandos funcionan
- E4 (Validation) y E5 (Distribution) como siguientes epics prioritarios
