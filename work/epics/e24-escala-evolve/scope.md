# Epic Scope: E24 — Escala Evolve (Auto-Mejora)

**Status:** Deferred/Backlog
**Dependencies:** E23 (Agent-based skills), `~/.escala/memoria/` operativa
**Tamaño:** M

## Visión

Un **agente que se mejora a sí mismo**. Cada interacción en Escala deja una huella en `memoria/`. El skill `escala-evolve` lee esas huellas, detecta patrones, identifica ineficiencias, y propone mejoras a sus propios skills — usando la inteligencia del LLM para auto-diagnosticarse.

## Principios de diseño

1. **No modifica sin aprobación** — El agente propone, el humano decide
2. **Basado en evidencia** — Toda mejora debe justificarse con datos de `memoria/`
3. **Mejora progresiva** — Cada revisión construye sobre la anterior
4. **Sin dependencia externa** — Todo corre dentro del LLM + markdown
5. **Auto-documentación** — Cada mejora deja un .md en `memoria/evolucion/`

## Lo que cambia

| Sin evolve | Con evolve |
|-----------|------------|
| Skills estáticos | Skills que se ajustan según uso real |
| El humano detecta problemas | El agente los detecta solo |
| Sin métricas de efectividad | Score de uso y satisfacción por skill |
| Skills nunca se actualizan | Skills reciben patches basados en datos |

## Stories

### Fase 1: Fundación

| Story | Size | Qué |
|-------|:----:|-----|
| **S24.1 — Skill escala-evolve** | M | Skill que escanea `memoria/`, extrae patrones de uso, identifica gaps y propone mejoras. Análisis de: frecuencia de skills, datos faltantes, scores, recomendaciones repetidas. Guarda en `memoria/evolucion/`. |
| **S24.2 — Registro de evolución** | S | Sistema de versionado de mejoras. Cada propuesta se guarda con: fecha, skill afectado, problema detectado, cambio propuesto, estado (propuesta/aprobada/aplicada/rechazada). Changelog en `memoria/evolucion/changelog.md`. |

### Fase 2: Automatización

| Story | Size | Qué |
|-------|:----:|-----|
| **S24.3 — Post-sesión automático** | M | Se integra con `escala-close`. Después de cerrar una sesión, ejecuta un mini-análisis de los nuevos .md creados y extrae patrones. Sin interferir con la experiencia del usuario. |
| **S24.4 — Cron semanal** | S | Revisión periódica cada 7 días. Escanea toda `memoria/`, busca tendencias a largo plazo, propone mejoras acumulativas. Usa cron job de Hermes. |

### Fase 3: Auto-modificación

| Story | Size | Qué |
|-------|:----:|-----|
| **S24.5 — Auto-patch con aprobación** | L | El agente puede modificar sus propios skills basado en hallazgos aprobados. Genera un diff, lo presenta al usuario, y solo aplica con confirmación. Incluye rollback si algo sale mal. |

## Done Criteria

- [ ] `escala-evolve` skill puede escanear `memoria/` y detectar al menos 3 tipos de patrones
- [ ] Registro de evolución funcional con estados (propuesta/aprobada/aplicada/rechazada)
- [ ] Post-sesión automático funciona sin intervención del usuario
- [ ] Cron semanal envía resumen de hallazgos
- [ ] Auto-patch con aprobación: genera diff, espera confirmación, aplica, permite rollback

## Governance correction

Corrected status: **Deferred/Backlog**. The retrospective claims all five stories
were completed, but this scope's Done Criteria are all still open and no
independent evidence is cited here for the weekly cron, post-session automation,
or approved auto-patch rollback path.

Backlog action: no active epic is currently open from this folder. If evolve is
revived, split the unfinished automation and auto-patch work into new scoped
stories with file paths, automation evidence, and tests.

## Riesgos

| Riesgo | L/I | Mitigación |
|--------|:---:|------------|
| El agente propone cambios inútiles | M/M | Filtro de calidad: solo propuestas con evidencia sólida |
| Auto-modificación rompe skills | H/M | Rollback automático + diff antes de aplicar |
| Demasiadas propuestas = ruido | M/L | Agregación semanal, no diaria |
| Skills cambian sin que usuario sepa | M/H | Siempre pedir aprobación explícita |
