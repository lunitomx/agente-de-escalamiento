# Epic Scope: E28 — Instalación Portátil y Runtime Visual

**Status:** Complete — 2026-08-26
**Issues:** #1, #2
**Dependencies:** E18/E22 como runtime histórico
**Tamaño:** L

## Outcome

Una instalación limpia incluye la puerta pública, el runtime HTTP local, sus
activos estáticos y una ruta API mínima; funciona con BSD sed y GNU sed.

## Stories

1. S28.1 — Compatibilidad macOS/BSD sed.
2. S28.2 — Bundle explícito de servidor, handlers, router, módulos requeridos y static.
3. S28.3 — Smoke de instalación y HTTP en los tres targets.
4. S28.4 — Documentación de apertura local sin pasos técnicos.

## Acceptance criteria

- [x] La adaptación de skills no depende de GNU sed.
- [x] Codex, Claude y Hermes reciben server, handlers, router, static y dependencias.
- [x] Un smoke desde destination-root inicia el servidor y obtiene un estático/API mínimo.
- [x] Los datos de empresa permanecen fuera del runtime distribuido.
- [x] La guía pública explica cómo abrir y cerrar el panel local en lenguaje natural.

## Evidencia de cierre

- `tests/test_scaleup_installer.py`: instalación aislada, falso `sed`, bundle visual,
  HTTP/API/estático, exclusión de memoria fuente y apertura/cierre natural.
- `RAISE_TEST_WORKER_BUDGET=0 rai gate check gate-tests --scope tests/test_scaleup_installer.py`
  → todos los tests pasan.
- `bash -n .scaleup/install.sh`, compilación de `scaleup-frontdoor` y
  `git diff --check` sin errores.
