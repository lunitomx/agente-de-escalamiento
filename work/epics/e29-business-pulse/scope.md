# Epic Scope: E29 — Business Pulse Basado en Datos

**Status:** Complete — 2026-08-26
**Issue:** #3
**Dependency:** E28
**Tamaño:** XL

## Stories

1. S29.1 — Modelo y API de Business Pulse.
2. S29.2 — Vista ejecutiva: cuatro decisiones, prioridad, plan y timeline.
3. S29.3 — Estados vacíos, procedencia y CTAs de captura.
4. S29.4 — Power of One con carga, edición, cálculo y persistencia real.
5. S29.5 — Navegación desde cada decisión y pruebas/demo sintética etiquetada.

## Acceptance criteria

- [x] Diagnóstico o plan actualiza la vista al recargar.
- [x] Cada dato muestra fuente y fecha, o un estado pendiente accionable.
- [x] No hay cifras ficticias presentadas como datos de empresa.
- [x] Power of One persiste un escenario real local.
- [x] Demo sintética está claramente aislada de datos de empresa.

## Evidencia de cierre

- `tests/test_business_pulse.py`: vacío honesto, refresh, procedencia, plan,
  persistencia Power of One, demo aislada y HTTP real.
- `tests/test_escala_server.py` y `tests/test_escala_daos.py`: contrato API y
  persistencia versionada.
- `tests/test_scaleup_installer.py`: Business Pulse instalado y servido en
  Claude, Hermes y Codex.
- JavaScript externo e inline validado con `node --check`.
