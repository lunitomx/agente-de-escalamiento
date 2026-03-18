# Epic Scope: E3 — Agent Framework

## Objective

Hacer que el repo `lunitomx/scaleupagent` sea instalable: un empresario clona, abre Claude Code, y tiene un agente ScaleUp experto.

## In Scope

- CLAUDE.md del producto con identidad ScaleUp, instrucciones, y slash commands
- .gitignore para excluir archivos de desarrollo (RaiSE, PDF, build/)
- README.md con instrucciones de instalación y uso
- Estructura `.scaleup/` con defaults limpios para el usuario final
- Conexión de todos los slash commands a los 19 skills existentes

## Out of Scope

- CLI installer (pip/npm) — no es necesario, el repo se clona
- Tests automatizados — eso es E4
- Publicación en GitHub — eso es E5
- Cambios al contenido de knowledge base o skills existentes

## Planned Stories

| ID | Story | Size |
|----|-------|------|
| S3.1+S3.5 | CLAUDE.md del producto — Identidad + slash commands | M | done |
| S3.2 | .gitignore + limpieza del repo | S | done |
| S3.3 | README.md — Quick start para el empresario | M | done |
| S3.4 | Estructura `.scaleup/` con defaults para usuario final | S | done |

## Done Criteria

- [ ] Un directorio clonado contiene todo lo necesario para que Claude Code funcione como agente ScaleUp
- [ ] No hay archivos de desarrollo (RaiSE governance, build/, PDF) en el producto final
- [ ] Los 19 skills son invocables via slash commands documentados
- [ ] README explica en < 1 minuto de lectura cómo instalar y usar
