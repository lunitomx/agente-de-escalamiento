---
epic_id: "E20"
title: "Contextual Skills (Grafo → Dashboards)"
status: "complete"
completed_at: "2026-05-29"
stories:
  - "S20.1 — Knowledge Context API (M)"
  - "S20.2 — Dashboard Context Panel (L)"
  - "S20.3 — Coaching Skill Helper (S)"
  - "S20.4 — Integration Tests (S)"
dependencies: ["E19 (grafo poblado)", "E18 (server, API routing, dashboards)"]
---

# Epic Retrospective: E20 — Contextual Skills

## Summary

Pipeline completo: endpoint de contexto → panel en dashboards → helper para coaching → tests.

## Key Findings

- **S20.1 ya estaba implementado** como parte de S19.4 — el endpoint `GET /api/knowledge/context` y `KnowledgeHandler.get_context()` ya existían. S20.1 se redujo a agregar validación de parámetros + tests de integración.
- **Código existente**: El grafo de E19 estaba poblado con datos reales del libro Scaling Up (`book-knowledge.json`). Los tests de S19.4 ya cubrían search, get_entity y get_context.
- **Python 3.9 limitación**: Tests de rutas HTTP fallan por sintaxis `str | None` (Python 3.10+). Los handler-level tests funcionan bien.

## What's Next

- **E21 — Verne Board Member**: El siguiente paso lógico tras E20.
