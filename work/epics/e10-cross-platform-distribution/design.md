# E10: Design — Cross-Platform Distribution

## Gemba Findings

### Patrón Existente: coaching/summary/

El único engine construido sigue una arquitectura de 3 capas limpia:

```
coaching/summary/
├── engine.py      # Lógica pura. No I/O. Dict in → Dict out.
├── formatter.py   # Render puro. Dict in → String out.
├── __init__.py    # I/O layer. Lee/escribe archivos. Orquesta engine+formatter.
├── __main__.py    # Entry point: python3 -m coaching.summary
└── tests/
    └── test_summary.py
```

**Contrato del engine:**
- `engine.py`: función pura `build_*(data: dict) -> dict`
- `formatter.py`: función pura `format_*(structured: dict) -> str`
- `__init__.py`: función `run(context: dict) -> {"output": str, "artifacts": dict, "errors": list[str]}`

Este patrón (PAT-L-24) se replica para todos los engines nuevos.

### Validators Existentes

11 validators en `.scaleup/agent/validators/` ya cubren validación de:
- welcome (profile completeness)
- diagnose (scores range/presence)
- worksheet (completion check)
- progress (score evolution)
- session, tasks, memory, pulse, dashboard, export, summary

Los engines **no duplican** validación — la invocan desde validators.

### Knowledge Ontology

90+ archivos YAML organizados por decisión:
```
knowledge/
├── decisions/          # 4 YAML: people, strategy, execution, cash
├── ontology/           # Schema y node-types
├── registry/           # worksheets.yaml (índice central)
├── stages/             # growth stages
├── retrieval.py        # Búsqueda programática
└── {decision}/
    ├── concepts/       # Conceptos teóricos
    ├── metrics/        # KPIs y métricas
    ├── tools/          # Herramientas de la metodología
    └── worksheets/     # Worksheets interactivos
```

`retrieval.py` usa paths relativos — portable sin cambios.

### Clasificación de Skills

| Categoría | Skills | Engine Necesario |
|-----------|--------|-----------------|
| **Engine-backed** (6) | welcome, diagnose, worksheet, progress, level, router | Sí — lógica de negocio compleja |
| **Validator-only** (6) | close-sync, export, dashboard, pulse, start, close | No — solo quality gates |
| **Sub-agent** (4) | people, strategy, execution, cash | No — orquestación LLM pura |
| **Decision-specific** (12) | people-values, people-fac, people-topgrading, strategy-opsp, strategy-7strata, strategy-swot, execution-rhythms, execution-priorities, execution-rockefeller, cash-ccc, cash-power1, cash-acceleration | No — SKILL.md con knowledge lookup |
| **Session/Task** (8) | start-load-profile, start-load-sessions, start-load-tasks, start-present, close-capture, close-log, task-add, task-list, task-update | No — file I/O directo |
| **Utility** (3) | goal, context-add, context-query | No — CRUD simple |

**Resultado:** Solo 6 skills necesitan engine Python. Los otros 33 se portan como SKILL.md puro.

## Arquitectura de Distribución

### Bundle Structure

```
scaleup-bundle/
├── install.sh                    # Installer CLI
├── VERSION                       # Semver del bundle
├── skills/                       # 39 SKILL.md (Claude Code format)
│   ├── scaleup-welcome/SKILL.md
│   ├── scaleup-diagnose/SKILL.md
│   └── ...
├── skills-hermes/                # 39 SKILL.md (Hermes adapter)
│   ├── scaleup-welcome/SKILL.md
│   └── ...
├── coaching/                     # Python engine modules
│   ├── __init__.py
│   ├── summary/
│   ├── welcome/
│   ├── diagnose/
│   ├── worksheet/
│   ├── progress/
│   ├── level/
│   └── router/
├── knowledge/                    # 90+ YAML ontology
│   └── (same structure as .scaleup/knowledge/)
├── agent/
│   ├── identity/core.md
│   ├── sub-agents/
│   └── validators/
└── templates/
    └── my-company/               # Template para datos de usuario
        ├── profile.md
        └── ...
```

### Installation Targets

#### Claude Code Global (`~/.claude/`)
```
~/.claude/
├── skills/scaleup-*/SKILL.md     # Symlinks or copies
├── scaleup/                      # Engine + knowledge
│   ├── coaching/
│   ├── knowledge/
│   ├── agent/
│   └── VERSION
└── CLAUDE.md                     # Append ScaleUp instructions
```

Skills reference engine via: `python3 -m coaching.{module} --context '{...}'`
PYTHONPATH set to `~/.claude/scaleup/` by the skill's bash calls.

#### Hermes Agent (`~/.hermes/`)
```
~/.hermes/
├── skills/scaleup-*/SKILL.md     # Hermes-adapted versions
└── scaleup/                      # Same engine + knowledge
    ├── coaching/
    ├── knowledge/
    └── agent/
```

### Tool Call Mapping (Claude → Hermes)

| Claude Code | Hermes | Notes |
|-------------|--------|-------|
| `Bash("command")` | `terminal("command")` | Direct rename |
| `Read("path")` | `terminal("cat path")` o `process("read", path)` | Depends on Hermes version |
| `Edit(file, old, new)` | `terminal("sed -i ...")` o `process("edit", ...)` | May need Python helper |
| `Write(file, content)` | `terminal("cat > file << 'EOF'\n...\nEOF")` | Heredoc pattern |
| `AskUserQuestion(...)` | Hermes native prompt | Different API |

### Key Decisions

**ADR-001: Engine Location for Global Install**

Opciones evaluadas:
1. ~~pip install~~ — overhead de packaging, el usuario no quiere gestionar virtualenvs
2. **Copy + PYTHONPATH** — simple, portable, sin dependencias externas ← **elegido**
3. ~~Symlink al repo~~ — rompe si se mueve el repo

Los skills invocan el engine con:
```bash
PYTHONPATH=~/.claude/scaleup python3 -m coaching.diagnose --context '{...}'
```

**ADR-002: Hermes Adapter Strategy**

Opciones evaluadas:
1. ~~Un solo SKILL.md universal~~ — las diferencias de tool calls son reales
2. **SKILL.md duplicados con adapter** — cada plataforma tiene su versión ← **elegido**
3. ~~Preprocessor que genera~~ — complejidad innecesaria para 39 archivos

El installer genera las versiones Hermes desde las de Claude Code aplicando el mapping de tool calls.

## Dependency Graph

```
S10.1 (Discovery)
  │
  ├── S10.2 (Welcome Engine)
  │     │
  │     └── S10.3 (Diagnose Engine)
  │           │
  │           └── S10.5 (Progress + Level)
  │                 │
  │                 └── S10.6 (Router)
  │
  └── S10.4 (Worksheet Engine)
  
S10.6 ──→ S10.7 (Claude Global Installer)
              │
              ├── S10.8 (Hermes Adapter)
              │
              └── S10.9 (Unified Installer)
                    ↑
              S10.8 ─┘
```

No hay ciclos. S10.4 (Worksheet) puede ejecutarse en paralelo con S10.2-S10.3.

## Patterns to Apply

- **PAT-L-24**: engine+formatter+I/O isolator (de summary/)
- **BASE-009**: Retrospective antes de cerrar el épico
- Commitear artifacts inmediatamente al crearlos (lección de E9)
