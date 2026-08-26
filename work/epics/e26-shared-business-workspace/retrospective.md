# E26 — Retrospectiva de cierre

**Cerrada:** 2026-08-26
**Resultado:** Complete

## Resultado entregado

- Carpeta empresarial portable con manifiesto mínimo y documentos Markdown/YAML.
- SQLite, WAL, SHM y respaldos por computadora fuera de la carpeta compartida.
- Migración segura de la memoria E22 a estado local, con copia de respaldo.
- Índice reconstruible, digest determinístico, trazabilidad por archivo y eliminación/renombre idempotentes.
- Contribuciones append-only, responsables declarados, detección de secretos, conflictos y conciliación confirmada.
- Flujo en lenguaje natural para preparar, revisar y reconstruir una carpeta, distribuido por los instaladores de Claude y Codex.

## Evidencia reproducible

Se ejecutó con `RAISE_TEST_WORKER_BUDGET=0 rai gate check gate-tests --scope ...`:

- `tests/test_shared_workspace.py`: contrato, dos estados locales, migración, recuperación, renombre, conciliación, datos sensibles, colaboración offline/reconexión y copia en conflicto, conversación e instalación Claude/Codex.
- `tests/test_project_memory_runtime.py`
- `tests/test_project_memory_migration.py`
- `tests/test_project_memory_context.py`
- `tests/test_scaleup_conversation.py`
- `tests/test_scaleup_installer.py`

Los gates pasaron y `git diff --check` no reportó errores. Los smokes verifican el frontdoor que instalan ambos targets; la interfaz visual específica de ChatGPT Work/Claude Cowork sigue como investigación en Parking Lot, no es una dependencia del workspace local-first.

## Aprendizajes

La unidad compartida debe ser documentación legible y no una base de datos. La sincronización, permisos y resolución de copias siguen perteneciendo al proveedor de archivos; ScaleUp conserva evidencia y exige una decisión humana al conciliar.
