# ScaleUp Agent

Tu coach AI de escalamiento empresarial. Implementa la metodología **Scaling Up** de Verne Harnish directamente en tu terminal con Claude Code.

Te guía paso a paso a través de las 4 decisiones críticas para escalar: **People, Strategy, Execution y Cash**.

## Quick Start

1. **Clona** este repositorio
   ```bash
   git clone https://github.com/lunitomx/scaleupagent.git
   cd scaleupagent
   ```

2. **Abre** Claude Code en el directorio
   ```bash
   claude
   ```

3. **Escribe** `/scaleup-welcome` para iniciar tu primera sesión

El agente te guiará para crear tu perfil de empresa y hacer tu primer diagnóstico.

## Requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) instalado
- Suscripción activa a Claude (Pro, Team, o Enterprise)

## Comandos disponibles

### Inicio

| Comando | Qué hace |
|---------|----------|
| `/scaleup-welcome` | Primera sesión: crea tu perfil y primer diagnóstico |
| `/scaleup-diagnose` | Diagnóstico completo de las 4 decisiones |
| `/scaleup-progress` | Dashboard de progreso y madurez |

### People — Personas

| Comando | Qué hace |
|---------|----------|
| `/scaleup-people` | Guía completa: personas correctas, accountability |
| `/scaleup-people-values` | Descubrimiento de Core Values |
| `/scaleup-people-fac` | Function Accountability Chart |
| `/scaleup-people-topgrading` | Proceso de contratación A-players |

### Strategy — Estrategia

| Comando | Qué hace |
|---------|----------|
| `/scaleup-strategy` | Guía completa: dirección estratégica clara |
| `/scaleup-strategy-opsp` | One-Page Strategic Plan |
| `/scaleup-strategy-7strata` | 7 Strata of Strategy |
| `/scaleup-strategy-swot` | Análisis SWOT/SWT |

### Execution — Ejecución

| Comando | Qué hace |
|---------|----------|
| `/scaleup-execution` | Guía completa: disciplina de ejecución |
| `/scaleup-execution-rhythms` | Cadencia de reuniones |
| `/scaleup-execution-priorities` | Prioridades trimestrales y Critical Number |
| `/scaleup-execution-rockefeller` | Evaluación de los 10 Rockefeller Habits |

### Cash — Efectivo

| Comando | Qué hace |
|---------|----------|
| `/scaleup-cash` | Guía completa: flujo de efectivo |
| `/scaleup-cash-ccc` | Cash Conversion Cycle |
| `/scaleup-cash-power1` | Power of One |
| `/scaleup-cash-acceleration` | Estrategias de aceleración de cash |

## Estructura

```
.scaleup/
├── my-company/          # Tu información (perfil, metas, foco trimestral)
├── knowledge/           # Base de conocimiento Scaling Up
│   ├── people/          # Herramientas de People
│   ├── strategy/        # Frameworks de Strategy
│   ├── execution/       # Checklists de Execution
│   └── cash/            # Herramientas de Cash
└── agent/               # Configuración del agente (no modificar)
```

## Basado en

**Scaling Up** de Verne Harnish — el framework usado por más de 80,000 empresas en el mundo para escalar con éxito. Este agente transforma la metodología en guía práctica, paso a paso, adaptada a tu empresa.
