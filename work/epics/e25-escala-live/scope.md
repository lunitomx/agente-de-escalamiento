# Epic Scope: E25 — Escala Live: Validación y Despliegue

**Status:** Complete
**Dependencies:** E23 (Agent skills), E24 (Evolve)
**Tamaño:** M

## Visión

Llevar Escala de "skills escritos" a "skills funcionando en producción". Validar que todo lo construido realmente funciona, instalarlo en el ecosistema real, documentar su uso, y demostrar el auto-mejora en acción.

## Stories

### Fase 1: Validación (S25.1-S25.3)

| Story | Size | Qué |
|-------|:----:|-----|
| **S25.1 — Smoke test escala-cash** | S | Cargar el skill, simular una entrevista Power of One con una empresa demo, verificar que calcula bien, guarda en memoria/, y puede generar HTML. |
| **S25.2 — Smoke test escala-strategy** | S | Cargar el skill, guiar OPSP completo con empresa demo, verificar guardado en memoria/. |
| **S25.3 — Smoke test escala-evolve** | S | Ejecutar el skill contra memoria/ real, verificar que detecta patrones, genera propuestas, guarda en evolucion/. |

### Fase 2: Infraestructura (S25.4-S25.5)

| Story | Size | Qué |
|-------|:----:|-----|
| **S25.4 — Instalar skills en Hermes** | S | Linkear `escala-agent/skills/*` → `~/.hermes/skills/`. Verificar que Hermes los carga correctamente. |
| **S25.5 — Despliegue público setup.sh** | S | Hostear `setup.sh` + `AGENTS.md` + skills en GitHub Pages o servidor para que `curl https://escala.sh | bash` funcione. |

### Fase 3: Cierre + Docs (S25.6-S25.7)

| Story | Size | Qué |
|-------|:----:|-----|
| **S25.6 — Cerrar E22 absorciones** | S | Revisar S22.10-S22.12. Si fueron absorbidas por E23/E24, cerrar con retrospectiva; si quedaron fuera de alcance, documentar el descarte. |
| **S25.7 — Documentación rápida** | S | Guía "Escala en 5 minutos": qué decirle al agente, ejemplos de prompts, estructura de skills. |

### Fase 4: Evolve en acción (S25.8)

| Story | Size | Qué |
|-------|:----:|-----|
| **S25.8 — Demostrar ciclo completo de auto-mejora** | M | Ejecutar evolve contra memoria/ real. Que genere una propuesta. Aprobarla. Aplicar el auto-patch. Verificar el cambio. Mostrar el ciclo completo. |

## Done Criteria

- [x] S25.1-S25.3: skills probados y funcionando
- [x] S25.4: skills linkeados en ~/.hermes/skills/
- [x] S25.5: instalación alternativa documentada (`git clone` + `bash setup.sh`)
- [x] S25.6: E22 cerrada formalmente
- [x] S25.7: guía rápida disponible
- [x] S25.8: ciclo completo evolve demostrado

## Closure Evidence

- Legacy tag: `epic/e25-complete` (created before S25.5 documentation repair)
- Final closure commit: `3794689 docs(e25): S25.5 done — epic complete`
- Story evidence: tracked retrospectives for S25.1, S25.2, S25.3, S25.4, S25.5, S25.7, and S25.8
- Closure note: original curl-pipe deployment was replaced by the approved local GitHub installation path: clone the repo and run `bash setup.sh`.
