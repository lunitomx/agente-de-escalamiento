# Board Directivo Sintético — Visión General

> **Archivado:** 2026-05-29
> **Épica original:** E19 (dividida en E19-book-ingestion, E20, E21)
> **Ver también:** work/epics/e20-contextual-skills/, work/epics/e21-verne-board-member/

---

## Objetivo Original

Construir un sistema donde Escala pueda sugerir, crear y gestionar un board directivo sintético — miembros con personalidades, frameworks y lentes de figuras reales del mundo empresarial — que actúen como agentes de coaching y revisión de la empresa.

## División Acordada

La visión original se dividió en 3 sub-épicas para mejor delimitación:

| Sub-épica | Propósito | Estado |
|-----------|-----------|--------|
| **E19** — Book Ingestion & Knowledge Graph | El conocimiento estructurado (fuentes → grafo) | ✅ Completa |
| **E20** — Contextual Skills | Skills que consultan el grafo | ✅ Completa |
| **E21** — Verne Lens Board Member | Primer asesor board sintético | ✅ Completa; lente sintética trazable y local |

## Arquitectura Conceptual (referencia)

```
escala-board/
├── miembros/
│   ├── verne-harnish.md        ← Alma: Rockefeller Habits, Scaling Up
│   ├── alex-hormozi.md         ← Alma: $100M Offers, Value Equation
│   ├── jim-collins.md          ← Alma: Good to Great, Hedgehog
│   └── ...
├── engine/
│   ├── discoverer.py           ← Sugiere miembros según perfil de empresa
│   ├── embodiment.py           ← Construye el alma desde textos (research multi-agente)
│   └── oracle.py               ← Cada miembro responde desde su lente
├── sessions/
│   └── board-meeting-{fecha}.md ← Transcripciones de debates entre miembros
└── reviews/
    └── {miembro}-review-{fecha}.md ← Observaciones sobre dailys/datos
```

## In Scope (visión completa)

1. **Discovery Engine** — Sugerir miembros de board basado en perfil de empresa (industria, etapa, métricas, gaps)
2. **Embodiment Pipeline** — Research multi-agente que extrae alma de figuras desde libros, podcasts, transcripts
3. **Board Member Agent** — Cada miembro como agente que analiza datos de la empresa desde su framework
4. **Cross-talk** — Miembros conversan entre sí sobre problemas específicos
5. **Daily Review** — Cada miembro revisa tus dailys y da observaciones desde su lente
6. **Data Ingestion** — Subir textos de figuras para profundizar el alma

## Out of Scope

- Miembros de board reales (humanos) — esto es sintético
- Reemplazar decisión humana — es asesoría, no ejecución
- Integración con calendarios o videollamadas
