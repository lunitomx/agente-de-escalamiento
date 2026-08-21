# ESCALA

Tu asesor de escalamiento empresarial **local**. Organiza People, Strategy,
Execution y Cash a partir de la información real que le compartes, sin exigir
formatos rígidos.

La **experiencia conversacional** se ejecuta a través de un agente de terminal
compatible (Claude Code, Hermes Agent o Codex CLI) que carga los skills de
ESCALA. Sin uno de esos agentes, puedes usar el paquete Python, la API REST y
los dashboards directamente.

Te guía paso a paso a través de las 4 decisiones críticas para escalar: **People, Strategy, Execution y Cash**.

## Quick Start (con agente de IA)

1. **Abre una terminal** en la carpeta local del producto.

2. **Instala** los skills y el paquete Python:

   ```bash
   ./install.sh
   ```

3. **Abre** tu agente de terminal compatible en esa carpeta y escribe
   `/escala-welcome` para iniciar tu primera sesión.

El agente te guiará para crear o actualizar tu perfil de empresa y hacer tu
primer diagnóstico.

## Requisitos

- Python 3 y Git instalados.
- **Claude Code, Hermes Agent o Codex CLI** instalado localmente para la
  experiencia conversacional con `/escala-*`.
- Acceso de lectura y escritura a la carpeta donde guardarás tu empresa.

## Modo sin agente de IA

Si prefieres no usar Claude, Hermes o Codex, ESCALA también funciona como
paquete Python y servidor web local:

```bash
# Perfil de empresa
python -m coaching.welcome

# Diagnóstico
python -m coaching.diagnose

# Servidor web con dashboards
python -m escala_server
```

Endpoints disponibles: `POST /api/cash/power-of-one`, `POST /api/advisor/ask`,
`GET/POST /api/worksheets/{decision}/{tool}`, entre otros. Ver
`escala_server/README.md` para la referencia completa.

## Operación local

- ESCALA no requiere un servidor hospedado ni una cuenta central del producto.
- Los datos de tu empresa permanecen en la computadora y carpetas que elijas.
- Para compartir información con tu equipo, coloca los archivos de trabajo en
  una carpeta sincronizada de Google Drive u OneDrive.
- No coloques la base SQLite dentro de una carpeta sincronizada; cada
  instalación mantiene su base local y comparte sólo documentos de trabajo.
- Los reportes de bugs y mejoras se generan localmente con
  `/escala-bugreport` en `~/.escala/feedback/outbox/`. No hay telemetría ni
  envío automático; si quieres compartir uno, copia el archivo manualmente a
  una carpeta sincronizada que tú controles.

## Comandos disponibles (skills para agente de IA)

Los comandos `/escala-*` son **skills** que el agente de terminal compatible
carga e interpreta. No son ejecutables por sí solos; el agente los traduce en
preguntas, cálculos y entregables.

### Inicio

| Comando | Qué hace |
|---------|----------|
| `/escala-welcome` | Primera sesión: crea tu perfil y primer diagnóstico |
| `/escala-diagnose` | Diagnóstico completo de las 4 decisiones |
| `/escala-progress` | Dashboard de progreso y madurez |

### Reportes

| Comando | Qué hace |
|---------|----------|
| `/escala-bugreport` | Captura un bug o mejora sin leer datos de la empresa y deja un JSON local listo para compartir |

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
