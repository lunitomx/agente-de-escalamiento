# ScaleUp Agent AI — Product Roadmap

> Master plan for the ScaleUp Coach AI product.
> A GitHub repo any entrepreneur clones, opens in Claude Code, and gets an expert Scaling Up coaching agent running locally. No servers, no databases, no API keys beyond Claude.

---

## Vision

Turn the Scaling Up methodology (Verne Harnish) into an interactive, local-first AI coaching agent. The entrepreneur gets persistent memory, structured guidance through 34 worksheets across 4 Decisions (People, Strategy, Execution, Cash), and measurable progress tracking — all inside Claude Code.

## Architecture Principles

1. **Ontology over RAG** — A curated domain graph (nodes + relationships + pointers), not chunked text in a vector store.
2. **Shared belief system** — Agent and user share the Scaling Up methodology as the common framework. This constrains the LLM toward useful, methodology-aligned outputs.
3. **Skills = processes within the ontology** — Each skill is an observable, measurable, repeatable process grounded in the methodology graph.
4. **Neuro-symbolic memory** — Deterministic retrieval algorithms over structured data. No embedding search.
5. **Level-aware coaching** — Shu/Ha/Ri adaptation: beginners get step-by-step, advanced users get strategic nudges.
6. **Everything local** — Clone repo = get the full brain. Privacy by architecture.

---

## Epic Sequence

```
E3 (Agent Framework) ──► E6 (Knowledge Ontology) ──► E7 (Agent Intelligence)
       DONE                      DONE                       DONE
                                                              │
                                                              ▼
                                                    E8 (Coaching Engine) ──► E9 (Value-Add)
                                                             DONE                    DONE
                                                              │
                                                              ▼
                                                  E10 (Cross-Platform Dist.)
                                                             DONE

E11 (Agente de Escalamiento — repo público) ── DONE
E12 (Codex Compat — absorbed into E11) ── CANCELLED
E13 (Auditoría y Cierre) ── IN PROGRESS (2026-05-25)
```

---

## Epic Inventory

| Epic | Objective | Status | Stories | Tests |
|------|-----------|--------|---------|-------|
| E3 — Agent Framework | Repo installable, skills invocables | ✅ DONE | 5/5 | — |
| E6 — Knowledge Ontology | Ontología estructurada + retrieval | ✅ DONE | 7/7 | — |
| E7 — Agent Intelligence | Memoria persistente, sesiones, tareas | ✅ DONE | 6/6 | 41 |
| E8 — Coaching Engine | Core Python coaching cross-platform | ✅ DONE | 6/6 | ~100 |
| E9 — Value-Add | Export, pulse, dashboard, summaries | ✅ DONE | 4/4 | ~34 |
| E10 — Cross-Platform Dist. | Skills para Claude, Hermes, Codex | ✅ DONE | 9/9 | — |
| E11 — Agente de Escalamiento | Repo público + anonimización | ✅ DONE | 6/6 | — |
| E12 — Codex & Auto-Update | Absorbido por E11 | ❌ CANCELLED | — | — |
| E13 — Auditoría y Cierre | Sanear repo, cerrar epics, fix tests | 🔄 IN PROGRESS | 7/9 | 139 |

## E13 — Auditoría y Cierre

**Status:** 7/9 stories done (2026-05-25)

| Story | Status | Description |
|-------|--------|-------------|
| S13.1 | ✅ | Close E12 — absorbed into E11 |
| S13.2 | ✅ | Fix test_finds_overdue (date drift) |
| S13.3 | ✅ | Close E6 — Knowledge Ontology |
| S13.4 | ✅ | Close E7 — Agent Intelligence |
| S13.5 | ✅ | Close E8 — Coaching Engine |
| S13.6 | ✅ | Add tests for diagnose, level, router (+34 tests) |
| S13.7 | ✅ | Sync install.sh to root coaching/ |
| S13.8 | ✅ | Remove orphaned .scaleup/coaching/ |
| S13.9 | 🔄 | Update product-roadmap.md |

## Next After E13

| Initiative | Priority | Rationale |
|------------|----------|-----------|
| E4 — Validation | HIGH | End-to-end testing before public distribution |
| E5 — Distribution | HIGH | Public GitHub release v1.0.0 |
| Port to Hermes Agent | MEDIUM | Reach more users |
| Port to Codex CLI | MEDIUM | Already started in E11 |

---

## Risk Register

| Risk | Mitigation |
|------|-----------|
| Ontology design too complex | Start with minimal viable graph. Add incrementally. |
| Context window limits with large ontology | Selective loading per session. Never load full ontology. |
| Session memory corruption | YAML with schema validation. Backup on session close. |
| Sync drift between dev and distributable coaching code | Resuelto en E13 — install.sh apunta al mismo directorio fuente |

---

*Created: 2026-03-17 | Last updated: 2026-05-25*
*Status: Active | Owner: Eduardo Muñoz Luna*
