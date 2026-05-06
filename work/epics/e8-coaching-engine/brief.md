# Epic Brief: E8 — Coaching Engine

## Hypothesis

Si construimos los 6 skills de coaching con núcleo Python cross-platform (`.scaleup/coaching/`) + adapters delgados (SKILL.md), entonces la lógica de negocio será portable a Hermes Agent y Codex sin reescribir, y los quality gates en código garantizarán consistencia.

## Success Metrics

| Metric | Target |
|--------|--------|
| Core Python modules creados | 6 módulos (welcome, diagnose, worksheet, progress, level, router) |
| SKILL.md adapters actualizados | 5 adapters + CLAUDE.md |
| Quality gates en Python | 4 validadores (welcome, diagnose, worksheet, progress) |
| Cross-platform ready | Todo core module es invocable standalone via stdin/stdin JSON |
| New user onboarding | < 10 minutos guiado por core Python |
| Diagnóstico | Scoring estructurado, priorización determinística |

## Appetite

6 stories (1XL + 2L + 2M + 1S). Arquitectura nueva (core + adapters). Sin dependencias externas — solo PyYAML (ya existente).

## Rabbit Holes

- No duplicar lógica entre core Python y SKILL.md — el adapter solo invoca el core
- No sobrecargar el core con features de presentación — devuelve dict, el adapter formatea
- El worksheet engine es el más complejo (34 worksheets) — priorizar el loop básico step-by-step
- El nivel de coaching se detecta automáticamente pero permite override manual
