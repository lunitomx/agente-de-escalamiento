# 🚀 Agente de Escalamiento

**Asistente de IA para escalar negocios.** Instalable en Claude Code, Hermes Agent y Codex CLI.

Este agente guía al emprendedor a través de las **4 decisiones estratégicas** fundamentales para escalar un negocio: Personas, Estrategia, Ejecución y Cash.

> Inspirado en metodologías probadas de escalamiento de negocios. Ver [ATTRIBUTIONS.md](ATTRIBUTIONS.md) para referencias completas a los autores originales.

## ⚡ Instalación rápida

```bash
git clone https://github.com/lunitomx/agente-de-escalamiento.git
cd agente-de-escalamiento
chmod +x install.sh
./install.sh
```

El instalador detecta automáticamente qué plataforma tienes instalada (Claude Code, Hermes Agent, Codex CLI) y configura los skills correspondientes.

## 📋 Comandos disponibles

Una vez instalado, puedes usar cualquiera de estos comandos desde tu terminal de IA:

### Diagnóstico
- `/escala-diagnose` — Diagnóstico completo de tu empresa en las 4 decisiones
- `/escala-welcome` — Primera sesión: perfil de empresa
- `/escala-pulse` — Quarterly Pulse Check

### Personas
- `/escala-people` — Sub-agente Personas
- `/escala-people-fac` — Mapa de Funciones y Responsabilidades
- `/escala-people-topgrading` — Proceso de contratación
- `/escala-people-values` — Descubrimiento de Valores Centrales

### Estrategia
- `/escala-strategy` — Sub-agente Estrategia
- `/escala-strategy-7strata` — 7 Estratos de Estrategia
- `/escala-strategy-opsp` — Plan Estratégico de Una Página
- `/escala-strategy-swot` — Análisis FODA

### Ejecución
- `/escala-execution` — Sub-agente Ejecución
- `/escala-execution-priorities` — Prioridades trimestrales
- `/escala-execution-rhythms` — Cadencia de reuniones
- `/escala-execution-habits` — Hábitos de Ejecución

### Cash
- `/escala-cash` — Sub-agente Cash
- `/escala-cash-acceleration` — Aceleración de Cash
- `/escala-cash-ccc` — Ciclo de Conversión de Efectivo
- `/escala-cash-power1` — Análisis Power of One

### Seguimiento
- `/escala-goal` — Meta SMART anual
- `/escala-progress` — Dashboard de progreso
- `/escala-dashboard` — Progress Dashboard
- `/escala-level` — Nivel de coaching (Shu/Ha/Ri)
- `/escala-export` — Plan de Acción exportable

## 📁 Estructura del proyecto

```
agente-de-escalamiento/
├── escala-skills/       # Skills del agente (instalables)
├── conocimiento/        # Base de conocimiento estructurada
├── coaching/            # Motores Python de coaching
├── validators/          # Validadores Python
├── install.sh           # Instalador multiplataforma
├── ATTRIBUTIONS.md      # Atribuciones a autores originales
└── README.md
```

## 📄 Licencia

MIT — libre para uso educativo y comercial.

## 🙏 Atribuciones

Este proyecto se inspira en metodologías desarrolladas por líderes del escalamiento de negocios. Consulta [ATTRIBUTIONS.md](ATTRIBUTIONS.md) para la lista completa de referencias y autores.
