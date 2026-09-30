---
story_id: "S55.1"
epic_id: "E55"
title: "Contrato de hechos con procedencia"
jira_key: "ESCALA-21"
status: "complete"
created: "2026-08-21"
---

# S55.1 — Scope

## In Scope

- Definir el modelo `Fact` en Pydantic con campos de procedencia.
- Implementar `save_fact`, `load_facts`, `get_fact`, `delete_fact` en `coaching/evidence/facts.py`.
- Persistir en `.escala/agent/memory/facts.yaml` (partición por decision opcional).
- Agregar tests en `coaching/evidence/tests/test_facts.py`.
- Actualizar `escala-welcome/SKILL.md` para mencionar que los hechos se guardan con procedencia.

## Out of Scope

- Dashboard de evidencia (S55.2).
- Conciliación financiera (S55.4).
- Resolución de entidades (S55.5).
- Onboarding adaptativo (S55.3).
- Integraciones con Kokoro o APIs de terceros.

## Done when

- [x] Modelo `Fact` valida campos obligatorios y rechaza confianzas/descripciones inválidas.
- [x] `save_fact` persiste y `load_facts` recupera hechos por decisión.
- [x] Tests cubren guardado, carga, filtrado, actualización y borrado.
- [x] Regresión completa pasa.
- [x] Scope commit y merge a `main` (`155d4a3`).
