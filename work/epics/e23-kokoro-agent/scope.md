# Epic Scope: E23 — Kokoro Agent Package

**Status:** Draft
**Dependencies:** E21 (Verne), E22 (Auditoría y correcciones)
**Tamaño:** XL

## Visión

Un paquete que se instala en **1 comando** en cualquier LLM (Claude, Codex,
Hermes) y lo convierte en Kokoro — el Guardián de la Riqueza.

El agente **es la interfaz**. No el servidor, no el dashboard. Claude/Codex
habla contigo, usa skills, guarda en markdown, genera HTML cuando lo necesitas.

## Arquitectura

```
~/.kokoro/                        ← Instalación limpia, un comando
├── AGENTS.md                     ← Le dice al LLM: "eres Kokoro"
├── setup.sh                      ← curl https://kokoro.sh | bash
│
├── skills/                       ← Skills universales (Claude/Codex/Hermes)
│   ├── kokoro-core/              ← Identidad + memoria markdown
│   ├── escala-cash/              ← Power of One, CCC
│   ├── escala-strategy/          ← OPSP, BHAG, Core Customer
│   ├── escala-people/            ← FACe, Topgrading, Valores
│   └── escala-execution/         ← Daily Huddle, Rockefeller Habits
│
├── memoria/                      ← ⭐ Base de conocimiento markdown
│   ├── dailys/                   ← 2026-05-30-score-10-12.md
│   ├── analisis/                 ← power-of-one-abril-2026.md
│   └── dashboard/                ← HTMLs generados por el agente
│
└── mcp/                          ← Opcional (solo para persistencia)
    └── server.py
```

## Principios de diseño

1. **Agent-first** — Claude/Codex es quien analiza, decide, genera. El servidor es opcional.
2. **Memoria = Markdown** — cada interacción produce un .md con frontmatter (tipo, fecha, empresa, links). El agente busca, linkea, sintetiza.
3. **Dashboard = HTML generado por IA** — no hay HTML fijo. Claude genera Chart.js + CSS cuando lo necesitas, para ese momento.
4. **Un comando** — `curl https://kokoro.sh | bash` instala skills + memoria + setup en cualquier LLM.
5. **Compatible** — Hermes skills + Claude Code + Codex + OpenClaude. AGENTS.md para todos.

## Lo que cambia respecto a E1-E22

| Antes (servidor) | Ahora (agente) |
|------------------|----------------|
| Backend Python `escala_server/` | `~/.kokoro/memoria/` markdown |
| HTML fijo en `static/dashboards/` | HTML generado por Claude cuando se necesita |
| API REST para guardar datos | Agente escribe .md directamente |
| Worksheets SQLite con schemas | Markdown con frontmatter YAML |
| El servidor analiza (template-based) | Claude analiza con su inteligencia real |
| Dashboard es el centro | **La conversación es el centro** |

## Stories

### Fase 1: Package & Setup (S23.1-S23.2)

| Story | Size | Qué |
|-------|:----:|-----|
| **S23.1 — Package Structure** | M | Crear `~/.kokoro/` con AGENTS.md, setup.sh, estructura de carpetas. AGENTS.md le dice al LLM quién es Kokoro, su estrategia (Proyector), su método (4 fases), y cómo usar la memoria. |
| **S23.2 — Setup Script** | S | `setup.sh` que instala skills en Claude (`~/.claude/skills/`), Codex, Hermes. Un comando. |

### Fase 2: Memoria Markdown (S23.3-S23.5)

| Story | Size | Qué |
|-------|:----:|-----|
| **S23.3 — Memoria Core** | M | Skill `kokoro-core` que gestiona `memoria/`. Cada interacción: (1) agente escribe .md con frontmatter, (2) links a análisis relacionados, (3) índice `memoria/indice.md` que se actualiza. |
| **S23.4 — Búsqueda y síntesis** | M | El agente sabe buscar en `memoria/` por fecha, tipo, empresa, keyword. Sintetiza: "esta semana tu score promedio fue 8/12, mejorando vs la anterior". |
| **S23.5 — Dashboard generado** | M | El agente puede generar un HTML con Chart.js (desde CDN) que visualice los datos de `memoria/`. No hay HTML fijo. Se genera bajo demanda. |

### Fase 3: Skills Refactor (S23.6-S23.10)

| Story | Size | Qué |
|-------|:----:|-----|
| **S23.6 — escala-cash refactor** | M | Skill reescrito para que Claude guíe el Power of One en conversación, use su inteligencia, guarde en `memoria/analisis/`, genere HTML si aplica. |
| **S23.7 — escala-strategy refactor** | M | Igual para Strategy: OPSP, BHAG, Core Customer. Claude entrevista, deduce, guarda. |
| **S23.8 — escala-people refactor** | M | Igual para People: FACe, Topgrading, Valores. Claude construye el organigrama contigo en conversación. |
| **S23.9 — escala-execution refactor** | M | Igual para Execution: Daily Huddle, Rockefeller Habits, Prioridades. Claude analiza transcripts reales. |
| **S23.10 — kokoro-core (identidad)** | S | Skill de identidad: quién es Kokoro, su estrategia Proyector, cómo guiar la conversación. Se carga siempre. |

### Fase 4: MCP Server (S23.11)

| Story | Size | Qué |
|-------|:----:|-----|
| **S23.11 — MCP Server opcional** | S | Servidor MCP mínimo para compartir `memoria/` entre sesiones y LLMs. Solo lectura/escritura de markdown. Nada más. |

## Done Criteria

- [ ] `curl https://kokoro.sh | bash` instala todo
- [ ] Claude/Codex/Hermes carga AGENTS.md y sabe que es Escala
- [ ] Cada análisis guarda .md en `memoria/` con frontmatter + links
- [ ] El agente puede buscar y sintetizar análisis anteriores
- [ ] El agente puede generar HTML visual bajo demanda
- [ ] Skills funcionan en Claude, Codex y Hermes
- [ ] Servidor MCP opcional funcional
- [ ] El servidor `escala_server/` legacy queda como compatible pero no necesario

## Progress Tracking

| Story | Size | Status | Notes |
|-------|:----:|:------:|-------|
| S23.1 — Package Structure | M | ✅ Done | AGENTS.md + setup.sh + estructura |
| S23.2 — Setup Script | S | ✅ Done | curl | bash + auto-detección + ~/.escala/ |
| S23.3 — Memoria Core | M | Pending | — |
| S23.4 — Búsqueda y síntesis | M | Pending | — |
| S23.5 — Dashboard Generado | M | Pending | — |
| S23.6 — escala-cash refactor | M | Pending | — |
| S23.7 — escala-strategy refactor | M | Pending | — |
| S23.8 — escala-people refactor | M | Pending | — |
| S23.9 — escala-execution refactor | M | Pending | — |
| S23.10 — Identidad Core | S | Pending | — |
| S23.11 — MCP Server opcional | S | Pending | — |

## Risks

| Riesgo | L/I | Mitigación |
|--------|:---:|------------|
| Skills existentes muy acopladas al server | H/M | Refactor progresivo. Skills hablan con server O escriben .md. Ambos coexisten. |
| Claude/Codex diffieran en formato de skills | M/M | AGENTS.md universal. Skills en formato Hermes (el más completo). Claude y Codex lo leen como instrucciones. |
| Memoria markdown sin estructura se vuelve caos | M/M | Frontmatter YAML obligatorio. Índice auto-generado. Plantilla de .md en el skill. |
