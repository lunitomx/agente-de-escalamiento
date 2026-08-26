# Retrospectiva: E28 — Instalación Portátil y Runtime Visual

**Cierre:** 2026-08-26
**Resultado:** Complete

## Qué cambió

- Se eliminó la dependencia funcional de GNU `sed -i` del instalador.
- El paquete instalado ahora incluye el runtime HTTP, API, dependencias y
  estáticos necesarios para una experiencia visual real.
- La puerta natural puede abrir, reutilizar y cerrar un servidor local sin que
  la persona conozca comandos, rutas o puertos.
- Los datos y backups de la empresa fuente siguen fuera del artefacto distribuido.

## Evidencia

- Suite completa `tests/test_scaleup_installer.py` verde mediante RaiSE gate.
- Smokes HTTP ejecutados sobre instalaciones limpias Claude, Hermes y Codex.
- Prueba adversarial con un binario `sed` que falla siempre.
- Validación de sintaxis del instalador, compilación de la puerta y diff limpio.

## Aprendizaje

Un dashboard existente en el repositorio no genera valor si el instalador no
transporta su runtime. Las futuras vistas deben probarse desde el artefacto
instalado, no solamente desde el checkout de desarrollo.

## Siguiente

E29 consume este runtime para convertir Business Pulse en una vista ejecutiva
honesta, persistente y accionable con datos reales o estados vacíos explícitos.
