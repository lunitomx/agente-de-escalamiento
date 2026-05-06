# Retrospective: E8 — Coaching Engine

## Status: CLOSED
## Date: 2026-05-06

## Summary

E8 construyó el Coaching Engine de ScaleUp con arquitectura cross-platform (core Python + adapters SKILL.md). Seis skills de coaching creados como núcleos Python portables, con adapters delgados para Claude Code y quality gates en código.

**Novedad arquitectónica:** Todos los skills de E8 nacen con arquitectura de 3 capas — core Python (`.scaleup/coaching/`), adapter SKILL.md (`.claude/skills/`), quality gate Python (`.scaleup/agent/validators/`). Esto permite portar a Hermes Agent y Codex sin reescribir lógica de negocio.

## Stories

| ID | Name | Size | Status | Notes |
|----|------|------|--------|-------|
| S8.1 | Coaching Core + Welcome | L | DONE | Core structure + welcome intake + stage detection + profile creation |
| S8.2 | Diagnosis Engine | L | DONE | 20 structured questions (5x4 decisions), scoring 1-5, priority detection |
| S8.3 | Worksheet Guidance Engine | XL | DONE | 34-worksheet registry integration, step-by-step guidance, state persistence |
| S8.4 | Progress Tracker | M | DONE | Dashboard per decision, completion %, next worksheet suggestion |
| S8.5 | Level-Aware Coaching | M | DONE | Shu/Ha/Ri detection from avg score, tone/depth adaptation, manual override |
| S8.6 | Sub-agent Router | S | DONE | Deterministic routing by lowest score, explicit request override |

## Key Architecture Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Core Python en `.scaleup/coaching/{skill}/` con `run(context) -> dict` | Entry point estándar para invocación desde cualquier agente |
| D2 | Adapter SKILL.md solo invoca core vía stdin JSON | Cero lógica de negocio en el adapter |
| D3 | Quality gates en código Python, no LLM | Validación determinística, no dependiente del modelo |
| D4 | Misma estructura de datos que E7 | company-profile.yaml como source of truth única |
| D5 | Router determinístico por score mínimo | Sin juicio LLM para routing — reglas en código |

## Metrics

| Metric | Value |
|--------|-------|
| Core Python modules | 6 (welcome, diagnose, worksheet, progress, level, router) + 1 shared (core) |
| Lines of core Python | ~7,500 total across all modules |
| SKILL.md adapters | 5 updated + CLAUDE.md updated |
| Quality gates | 4 (welcome, diagnose, worksheet, progress) |
| Stories planned/completed | 6/6 |
| Cross-platform ready | All cores invocable standalone via stdin JSON |

## Parking Lot

- **E10 (future):** Adapt existing 20 skills (pre-E8) to orchestration pattern + cross-platform architecture
- **Port to Hermes Agent:** Create Hermes-compatible skill definitions that invoke same core Python modules
- **Port to Codex:** Create Codex-compatible tool definitions that invoke same core Python modules
- **Worksheet engine edge cases:** Resume incomplete worksheets, handle multi-session worksheets
