# Design: E11 — Agente de Escalamiento (repo público)

## Gemba Findings

### Assets a migrar

| Componente | Cantidad | Ubicación |
|-----------|----------|-----------|
| Skills scaleup-* | 39 | `.claude/skills/scaleup-*/SKILL.md` |
| Knowledge base | ~90+ YAML | `.scaleup/knowledge/` (6 subdirectorios) |
| Coaching engines | 6 módulos | `.scaleup/coaching/` (welcome, diagnose, worksheet, progress, level, router) |
| Validators | 11 Python | `.scaleup/agent/validators/` |
| Identity | 2 archivos | `.scaleup/agent/identity/` |
| Sub-agents | 4 markdown | `.scaleup/agent/sub-agents/` |

### Patrones de anonimización detectados

| Patrón original | Ejemplo en skills | Anonimización |
|----------------|-------------------|---------------|
| `scaleup-` prefijo | `scaleup-execution-rockefeller` | `escala-` prefijo |
| "Scaling Up" literal | "7 Strata of Strategy de Scaling Up" | "7 Estratos de Estrategia" |
| "Rockefeller Habits" | "10 Rockefeller Habits" | "10 Hábitos de Ejecución" |
| "Verne Harnish" | Atribución directa | "Metodología inspirada en Verne Harnish" + ATTRIBUTIONS.md |
| Path absoluto interno | Cualquier `/Users/...` | Paths relativos |
| `.scaleup/` paths | `.scaleup/knowledge/...` | Mantener pero relativo al skill |
| Referencia al proyecto | "ScaliingUPAI", "ScaleUp Agent" | "Agente de Escalamiento" |

## Enfoque técnico

### Estructura del repo público

```
agente-de-escalamiento/
├── README.md
├── ATTRIBUTIONS.md
├── LICENSE (MIT)
├── .gitignore
├── install.sh                    # Instalador multiplataforma
├── escala-skills/                # Skills anonimizados
│   ├── escala-cash/
│   ├── escala-cash-acceleration/
│   ├── escala-cash-ccc/
│   ├── escala-cash-power1/
│   ├── escala-close/
│   ├── escala-close-capture/
│   ├── escala-close-log/
│   ├── escala-close-sync/
│   ├── escala-context-add/
│   ├── escala-context-query/
│   ├── escala-dashboard/
│   ├── escala-diagnose/
│   ├── escala-execution/
│   ├── escala-execution-priorities/
│   ├── escala-execution-rhythms/
│   ├── escala-execution-habits/   # antes rockefeller
│   ├── escala-export/
│   ├── escala-goal/
│   ├── escala-level/
│   ├── escala-people/
│   ├── escala-people-fac/
│   ├── escala-people-topgrading/
│   ├── escala-people-values/
│   ├── escala-progress/
│   ├── escala-pulse/
│   ├── escala-start/
│   ├── escala-start-load-profile/
│   ├── escala-start-load-sessions/
│   ├── escala-start-load-tasks/
│   ├── escala-start-present/
│   ├── escala-strategy/
│   ├── escala-strategy-7strata/
│   ├── escala-strategy-opsp/
│   ├── escala-strategy-swot/
│   ├── escala-task-add/
│   ├── escala-task-list/
│   ├── escala-task-update/
│   ├── escala-welcome/
│   └── escala-worksheet/
├── conocimiento/                 # Knowledge base anonimizado
│   ├── stages/
│   ├── cash/
│   ├── decisions/
│   ├── execution/
│   ├── people/
│   ├── strategy/
│   ├── ontology/
│   └── registry/
├── coaching/                     # Python engines (sin cambios internos)
│   ├── welcome/
│   ├── diagnose/
│   ├── worksheet/
│   ├── progress/
│   ├── level/
│   └── router/
└── validators/                   # Validators Python (sin cambios)
```

### Mapeo de nombres scaleup- → escala-

| Nombre original | Nombre anonimizado |
|----------------|-------------------|
| scaleup-cash | escala-cash |
| scaleup-cash-acceleration | escala-cash-acceleration |
| scaleup-cash-ccc | escala-cash-ccc |
| scaleup-cash-power1 | escala-cash-power1 |
| scaleup-close | escala-close |
| scaleup-close-capture | escala-close-capture |
| scaleup-close-log | escala-close-log |
| scaleup-close-sync | escala-close-sync |
| scaleup-context-add | escala-context-add |
| scaleup-context-query | escala-context-query |
| scaleup-dashboard | escala-dashboard |
| scaleup-diagnose | escala-diagnose |
| scaleup-execution | escala-execution |
| scaleup-execution-priorities | escala-execution-priorities |
| scaleup-execution-rhythms | escala-execution-rhythms |
| scaleup-execution-rockefeller | escala-execution-habits |
| scaleup-export | escala-export |
| scaleup-goal | escala-goal |
| scaleup-level | escala-level |
| scaleup-people | escala-people |
| scaleup-people-fac | escala-people-fac |
| scaleup-people-topgrading | escala-people-topgrading |
| scaleup-people-values | escala-people-values |
| scaleup-progress | escala-progress |
| scaleup-pulse | escala-pulse |
| scaleup-start | escala-start |
| scaleup-start-load-profile | escala-start-load-profile |
| scaleup-start-load-sessions | escala-start-load-sessions |
| scaleup-start-load-tasks | escala-start-load-tasks |
| scaleup-start-present | escala-start-present |
| scaleup-strategy | escala-strategy |
| scaleup-strategy-7strata | escala-strategy-7strata |
| scaleup-strategy-opsp | escala-strategy-opsp |
| scaleup-strategy-swot | escala-strategy-swot |
| scaleup-task-add | escala-task-add |
| scaleup-task-list | escala-task-list |
| scaleup-task-update | escala-task-update |
| scaleup-welcome | escala-welcome |
| scaleup-worksheet | escala-worksheet |

### Atribución requerida

Cada skill que mencione un concepto metodológico debe incluir al final:

> *Esta herramienta está inspirada en [metodología], desarrollada por [autor].*

Ejemplos concretos:
- **7 Estratos de Estrategia** → inspirado en *The 7 Strata of Strategy* de Verne Harnish
- **Hábitos de Ejecución** → inspirado en *The Rockefeller Habits* de Verne Harnish
- **Plan Estratégico de Una Página (OPSP)** → inspirado en *The One-Page Strategic Plan* de Verne Harnish
- **Topgrading** → inspirado en la metodología de Brad Smart
- **Function Accountability Chart** → inspirado en *The Function Accountability Chart* de Verne Harnish
- **Power of One** → inspirado en *The Power of One* de Verne Harnish
- **Cash Conversion Cycle** → principio financiero general
- **SWOT/SWT** → metodología de análisis estratégico general

### Instalación

El script `install.sh` detectará la plataforma:

- **Claude Code**: Copia skills a `~/.claude/skills/escala-*/`
- **Hermes Agent**: Copia skills a `~/.hermes/skills/escala-*/`
- **Codex CLI**: Skills en formato compatible en `~/.codex/skills/escala-*/`

### Lo que NO se migra

- Archivos de empresa (`my-company/`) — datos del usuario
- Skills de RaiSE, Kokoro u otras categorías
- `.scaleup/coaching/summary/` — es parte de otro flujo
- Datos de sesiones individuales

## Decisiones arquitectónicas

1. **Skills autocontenidos**: cada skill incluye paths relativos, no absolutos
2. **Coaching engine como Python inline**: cada skill que necesita engine lo invoca con `python3 -m coaching.<modulo>` desde el directorio del repo
3. **ATTRIBUTIONS.md centralizado**: archivo único en la raíz para no duplicar atribuciones en cada skill
4. **Versión inicial (v1.0.0)**: etiquetar el primer release
