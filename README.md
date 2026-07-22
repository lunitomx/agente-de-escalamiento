# ESCALA

Tu asesor de escalamiento empresarial instalado y ejecutado en tu propia
computadora. Organiza People, Strategy, Execution y Cash a partir de la
información real que le compartes, sin exigir formatos rígidos.

Te guía paso a paso a través de las 4 decisiones críticas para escalar: **People, Strategy, Execution y Cash**.

## Quick Start

1. **Abre una terminal** en la carpeta local del producto.

2. **Instala** los skills y el paquete Python:

   ```bash
   ./install.sh
   ```

3. **Abre** tu agente de terminal compatible en esa carpeta y escribe
   `/escala-welcome` para iniciar tu primera sesión.

El agente te guiará para crear tu perfil de empresa y hacer tu primer diagnóstico.

## Requisitos

- Python 3 y Git instalados.
- Claude Code, Hermes Agent o Codex CLI instalado localmente.
- Acceso de lectura y escritura a la carpeta donde guardarás tu empresa.

## Operación local

- ESCALA no requiere un servidor hospedado ni una cuenta central del producto.
- Los datos de tu empresa permanecen en la computadora y carpetas que elijas.
- Para compartir información con tu equipo, coloca los archivos de trabajo en
  una carpeta sincronizada de Google Drive u OneDrive.
- No coloques la base SQLite dentro de una carpeta sincronizada; cada
  instalación mantiene su base local y comparte sólo documentos de trabajo.

## Comandos disponibles

### Inicio

| Comando | Qué hace |
|---------|----------|
| `/escala-welcome` | Primera sesión: crea tu perfil y primer diagnóstico |
| `/escala-diagnose` | Diagnóstico completo de las 4 decisiones |
| `/escala-progress` | Dashboard de progreso y madurez |

### People — Personas

| Comando | Qué hace |
|---------|----------|
| `/escala-people` | Guía completa: personas correctas, accountability |
| `/escala-people-values` | Descubrimiento de Core Values |
| `/escala-people-fac` | Function Accountability Chart |
| `/escala-people-topgrading` | Proceso de contratación A-players |

### Strategy — Estrategia

| Comando | Qué hace |
|---------|----------|
| `/escala-strategy` | Guía completa: dirección estratégica clara |
| `/escala-strategy-opsp` | One-Page Strategic Plan |
| `/escala-strategy-7strata` | 7 Strata of Strategy |
| `/escala-strategy-swot` | Análisis SWOT/SWT |

### Execution — Ejecución

| Comando | Qué hace |
|---------|----------|
| `/escala-execution` | Guía completa: disciplina de ejecución |
| `/escala-execution-rhythms` | Cadencia de reuniones |
| `/escala-execution-priorities` | Prioridades trimestrales y Critical Number |
| `/escala-execution-habits` | Evaluación de los 10 hábitos de ejecución |

### Cash — Efectivo

| Comando | Qué hace |
|---------|----------|
| `/escala-cash` | Guía completa: flujo de efectivo |
| `/escala-cash-ccc` | Cash Conversion Cycle |
| `/escala-cash-power1` | Power of One |
| `/escala-cash-acceleration` | Estrategias de aceleración de cash |

## Estructura

```
.escala/
├── my-company/          # Tu información (perfil, metas, foco trimestral)
├── knowledge/           # Base de conocimiento operativo
│   ├── people/          # Herramientas de People
│   ├── strategy/        # Frameworks de Strategy
│   ├── execution/       # Checklists de Execution
│   └── cash/            # Herramientas de Cash
└── agent/               # Configuración local del agente
```

Los entregables editables se guardan en `work/`. Tú controlas esa carpeta, sus
respaldos y cualquier sincronización con tu equipo.
