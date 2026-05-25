---
epic_id: "E11"
title: "Agente de Escalamiento — repositorio público"
status: "complete"
completed: "2026-05-24"
---

# Retrospectiva E11 — Agente de Escalamiento

## Resumen

Épica completada en una sola sesión. 6 historias ejecutadas secuencialmente:

| Historia | Estado |
|----------|--------|
| S11.1: Crear repo público y estructura base | ✅ |
| S11.2: Anonimización profunda de 39 skills | ✅ |
| S11.3: Sistema de atribución | ✅ |
| S11.4: Instalabilidad multiplataforma | ✅ |
| S11.5: Documentación para estudiantes | ✅ |
| S11.6: Push y verificación final | ✅ |

## Entregables

- **Repo público:** `https://github.com/lunitomx/agente-de-escalamiento`
- **39 skills anonimizados:** scaleup-* → escala-*, sin marcas registradas
- **ATTRIBUTIONS.md:** 17 skills con atribución inline + tabla completa de autores
- **install.sh:** Instalación automática en Claude Code, Hermes Agent, Codex CLI
- **README completo:** FAQ, primeros pasos, comandos, licencia educativa

## Decisiones clave

1. **Script de migración automatizado** en lugar de editar 39 skills manualmente
2. **LICENCE sin copyright personal** — aviso de uso educativo exclusivo
3. **Atribución inline + ATTRIBUTIONS.md** — cada skill referencia al autor sin revelar fuentes del proyecto
4. **Instalador detecta plataforma** — un solo script para Claude Code, Hermes, Codex

## Lecciones

- Validar LICENSE con el usuario antes del primer commit
- El mapeo de 39 referencias cruzadas requiere verificación posterior con grep
- Algunos conceptos ("7 Strata" sin "of Strategy") no se capturan con regex simples

## Done Criteria

- [x] Repo `agente-de-escalamiento` creado y público en GitHub
- [x] Todos los skills scaleup-* migrados y anonimizados
- [x] Cada mención a metodología incluye atribución al autor original
- [x] README documenta instalación en Hermes, Codex CLI y Claude Code
- [x] Un estudiante puede instalar y usar el agente en < 10 minutos
- [x] Repositorio no contiene referencias al proyecto interno ScaliingUPAI

## Patrones extraídos

- **PAT-E11-001**: Repos públicos con contenido inspirado → aviso educativo, sin copyright personal
- **PAT-E11-002**: Migraciones masivas → script de transformación + verificación con grep post-migración
