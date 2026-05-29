# Epic Scope: E19 — Board Directivo Sintético

> **Status:** Draft
> **Dependencies:** E18 (infraestructura completa)
> **Epic type:** Producto nuevo (post-E18)

## Objective

Construir un sistema donde Escala pueda sugerir, crear y gestionar un board directivo sintético — miembros con personalidades, frameworks y lentes de figuras reales del mundo empresarial — que actúen como agentes de coaching y revisión de la empresa.

## Architecture (conceptual)

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

## In Scope

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

## Dependencies

- E18 (escala-server, escala.db, escala-inicia/cierra, memoria/grafo)
- Capacidad de research vía web scraping / APIs
- Data inicial de figuras (libros, transcripts)

## Done Criteria

- [ ] Escala sugiere al menos 3 miembros de board basado en perfil de empresa
- [ ] Cada miembro tiene un alma .md con framework, preguntas, lente, principios
- [ ] Cada miembro puede responder a un problema desde su framework
- [ ] Board meeting simulado donde miembros debaten un problema
- [ ] Dailys son revisadas por miembros del board
- [ ] Sistema funciona con data de al menos 3 figuras
