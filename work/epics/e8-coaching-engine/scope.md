# Epic Scope: E8 — Coaching Engine

**Status:** Complete
**Audited:** 2026-08-24

## Objective

Convertir la ontología (E6) y la inteligencia de agente (E7) en una experiencia activa de coaching — guiar empresarios a través de worksheets, trackear progreso metodológico y adaptarse a su nivel de maestría.

**Novedad de E8:** Todos los skills se construyen con arquitectura cross-platform desde el día 1 — núcleo de lógica en Python (`coaching/` después de la consolidación de E13), con adaptadores delgados (SKILL.md) por plataforma.

## In Scope

- Core coaching engine en Python (`coaching/`)
- Sistema de onboarding (/scaleup-welcome) con detección de etapa
- Motor de diagnóstico (/scaleup-diagnose) con scoring estructurado
- Motor de guía de worksheets (/scaleup-worksheet) con validación
- Dashboard de progreso (/scaleup-progress) por decisión
- Coaching adaptativo por nivel (Shu/Ha/Ri)
- Routing a sub-agentes de decisión
- SKILL.md adapters para Claude Code
- Quality gates en Python (validadores)

## Out of Scope

- Exportación o dashboards avanzados (E9)
- Adaptadores para Hermes Agent y Codex (post-E8, será E10 o epic separada)
- Modificación de la ontología (E6 cerrado)
- Interfaz gráfica — todo es conversacional
- Integración con servicios externos

## Planned Stories

| ID | Story | Size | Status | Depends |
|----|-------|------|--------|---------|
| S8.1 | Coaching Core + Welcome — estructura base del engine Python + skill welcome | L | **done** | — |
| S8.2 | Diagnosis Engine — assessment estructurado 4 decisiones con scoring | L | **done** | S8.1 |
| S8.3 | Worksheet Engine — guía paso a paso de worksheets desde ontología | XL | **done** | S8.1, E6 |
| S8.4 | Progress Tracker — dashboard de avance por decisión | M | **done** | S8.2 |
| S8.5 | Level-Aware Coaching — adaptación Shu/Ha/Ri | M | **done** | S8.2 |
| S8.6 | Sub-agent Router — routing a sub-agentes de decisión | S | **done** | S8.1 |

Critical path: S8.1 → S8.2 → S8.3, S8.2 → S8.4, S8.2 → S8.5

## Dependencies

- E6 Knowledge Ontology (DONE) — worksheets, conceptos, relaciones
- E7 Agent Intelligence (DONE) — memoria persistente, task board, session lifecycle
- Python 3.10+ (ya existente en el proyecto)
- PyYAML (ya existente en el proyecto)

## Cross-Platform Architecture Requirement

Cada skill de E8 DEBE construirse con:

1. **Core Python module** en `coaching/{skill_name}/` — lógica de negocio pura, sin dependencia del agente
2. **CLAUDE.md / SKILL.md adapter** en `.claude/skills/scaleup-{skill_name}/SKILL.md` — invoca el core Python, pasa contexto de usuario
3. **Quality gate** en `.scaleup/agent/validators/` — validación en código, no LLM

Esto permite que en el futuro se agreguen adapters para Hermes y Codex sin reescribir la lógica de negocio.

## Done Criteria

- [x] Los 6 skills del coaching engine tienen core Python en `coaching/`
- [x] Los skills tienen SKILL.md adapters que invocan el core
- [x] Onboarding y detección de etapa entregados
- [x] Diagnóstico produce priorización entre 4 decisiones
- [x] Los 15 worksheets registrados actualmente son guiables y salvables
- [x] Progress muestra avance por decisión
- [x] Tono de coaching se adapta al nivel Shu/Ha/Ri
- [x] Routing determinístico activa la decisión correspondiente
- [ ] No se demostró un quality gate Python distinto por cada una de las 6 stories; la retrospectiva registra 4 gates

### Audit Note — 2026-08-24

El scope original heredó la cifra incorrecta de 34 worksheets; el registro real
de E6 contiene 15. E13 movió la fuente canónica desde `.scaleup/coaching/` a
`coaching/`. E8 permanece cerrada, con la cobertura de gates individuales
registrada como desviación histórica aceptada.
