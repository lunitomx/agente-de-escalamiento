# Epic Scope: E8 — Coaching Engine

## Objective

Convertir la ontología (E6) y la inteligencia de agente (E7) en una experiencia activa de coaching — guiar empresarios a través de worksheets, trackear progreso metodológico y adaptarse a su nivel de maestría.

**Novedad de E8:** Todos los skills se construyen con arquitectura cross-platform desde el día 1 — núcleo de lógica en Python (.scaleup/coaching/), con adaptadores delgados (SKILL.md) por plataforma (Claude Code primero, Hermes Agent y Codex después).

## In Scope

- Core coaching engine en Python (.scaleup/coaching/)
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

1. **Core Python module** en `.scaleup/coaching/{skill_name}/` — lógica de negocio pura, sin dependencia del agente
2. **CLAUDE.md / SKILL.md adapter** en `.claude/skills/scaleup-{skill_name}/SKILL.md` — invoca el core Python, pasa contexto de usuario
3. **Quality gate** en `.scaleup/agent/validators/` — validación en código, no LLM

Esto permite que en el futuro se agreguen adapters para Hermes y Codex sin reescribir la lógica de negocio.

## Done Criteria

- [ ] Todos los skills de coaching tienen core Python en `.scaleup/coaching/`
- [ ] Todos los skills tienen SKILL.md adapter que invoca el core
- [ ] Onboarding completo guía al usuario en < 10 minutos
- [ ] Diagnóstico produce priorización actionable entre 4 decisiones
- [ ] Todos los 34 worksheets son guiables y salvables
- [ ] Progress muestra avance preciso por decisión
- [ ] Tono de coaching se adapta visiblemente al nivel de maestría
- [ ] Sub-agentes se activan correctamente según reglas de routing
- [ ] Cada story tiene al menos 1 quality gate en Python
