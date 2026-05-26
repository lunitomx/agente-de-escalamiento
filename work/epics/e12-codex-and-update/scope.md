# E12 — Codex Compatibilidad + Auto-Update

**Status:** CANCELLED — Absorbido por E11

## Objetivo

Hacer que el agente-de-escalamiento funcione en Codex CLI y tenga un mecanismo de auto-actualización desde GitHub.

## In Scope

1. **CODEX.md** — archivo en la raíz del repo `agente-de-escalamiento` con identidad, metodología y comandos ScaleUp para que Codex CLI lo lea al arrancar
2. **escala-update** — skill que al invocarse hace `git pull` del repo y re-ejecuta `install.sh` para actualizar skills locales
3. **update.sh** — script standalone para usuarios sin agente

## Out of Scope

- Modificar skills existentes (solo agregar)
- MCP server (eso sería Camino B)

## Razón de Cancelación

Todo el trabajo planeado para E12 fue absorbido y completado dentro de E11 (Agente de Escalamiento), cerrado formalmente el 2026-05-24. El repo público `github.com/lunitomx/agente-de-escalamiento` ya contiene CODEX.md, update.sh, y el install.sh guarda la ruta del repo. E12 quedó como un artefacto duplicado — solo scope.md, sin stories ni código.

## Stories Planeadas

| ID | Nombre | Descripción |
|----|--------|-------------|
| S12.1 | CODEX.md | Creado en E11 |
| S12.2 | escala-update skill | Creado en E11 |
| S12.3 | install.sh guardar ruta | Creado en E11 |
| S12.4 | update.sh script | Creado en E11 |
