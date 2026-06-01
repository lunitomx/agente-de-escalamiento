# ESCALA — Agente de Escalamiento

> Para gente que aplica **Scaling Up** (Verne Harnish) y quiere un agente AI que
> guíe las 4 Decisiones: **Cash, Strategy, People, Execution**.

## ¿Qué es?

Escala es un **conjunto de instrucciones** para Claude Code, Codex CLI, o Hermes Agent.
Cuando los cargas, el LLM se convierte en un estratega que:

- Te guía a través del **Power of One** (7 palancas financieras)
- Construye contigo tu **Plan Estratégico de Una Página (OPSP)**
- Mapea tu **FACChart** (quién es responsable de qué)
- Evalúa tus **10 Hábitos de Ejecución** con scoring
- Guarda cada análisis en markdown para que puedas revisitarlo
- Se **auto-mejora** detectando patrones de uso

**Cero servidores.** Todo corre dentro del LLM. Tus datos se quedan en tu compu.

## Instalación

```bash
# 1. Clona el repo
git clone https://github.com/lunitomx/agente-de-escalamiento.git

# 2. Ábrelo con Claude Code (automático — lee su CLAUDE.md)
cd agente-de-escalamiento && code .

# 3. Dile: "Quiero escalar mi negocio"
```

> **🚀 No requiere setup.** El `CLAUDE.md` le dice a Claude Code quién eres al instante.
> Si usas **Codex CLI**: `codex --instructions CODEX.md`
> Si usas **Hermes**: corre `bash setup.sh` para instalar los skills localmente.


## Cómo usarlo

| Dile al agente... | Carga | Resultado |
|-------------------|-------|-----------|
| "Quiero escalar mi negocio" | Identidad | El agente sabe quién es |
| "Revisemos mis números" | Cash | Power of One + CCC |
| "Definamos la estrategia" | Strategy | OPSP + BHAG |
| "Hablemos del equipo" | People | FACChart + Valores |
| "Mejoremos la ejecución" | Execution | 10 Hábitos + Rhythms |
| "Revísate" | Evolve | Escanea y propone mejoras |
| "Muéstrame" | — | Genera HTML visual |

## Estructura

```
~/.escala/
├── AGENTS.md                 ← Identidad: dile esto al LLM
├── skills/                   ← Skills que el agente carga
│   ├── escala-core/          ← Siempre cargado
│   ├── escala-cash/          ← Power of One, CCC
│   ├── escala-strategy/      ← OPSP, BHAG, 7 Estratos
│   ├── escala-people/        ← FACChart, Topgrading
│   ├── escala-execution/     ← Hábitos, Rhythms
│   └── escala-evolve/        ← Auto-mejora
├── memoria/                  ← Tus análisis (markdown)
│   ├── indice.md
│   ├── analisis/             ← Cash, Strategy, People, Execution
│   ├── dashboard/            ← HTMLs visuales generados
│   └── evolucion/            ← Propuestas de mejora
└── mcp/server.py             ← Opcional (persistencia)
```

## Para Claude Code

Solo dile: `Quiero escalar mi negocio` y automáticamente leerá `~/.escala/AGENTS.md`.

## Para Codex CLI

```bash
codex --instructions ~/.escala/AGENTS.md
```

## Para Hermes Agent

Los skills se vinculan automáticamente durante `setup.sh` a `~/.hermes/skills/`.

## Créditos

- **Metodología:** Verne Harnish (Scaling Up), Alan Miltz (Power of One)
- **Implementación Power of One:** Humberto Martínez Barón
- **Creación:** Eduardo Muñoz Luna — Kokoro
