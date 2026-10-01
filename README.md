# ESCALA

Tu asesor de escalamiento empresarial **local**. Organiza People, Strategy,
Execution y Cash a partir de la información real que le compartes, sin exigir
formatos rígidos.

La **experiencia conversacional** se ejecuta a través de un agente de terminal
compatible (Claude Code, Hermes Agent o Codex CLI) que carga los skills de
ESCALA. Sin uno de esos agentes, puedes usar el paquete Python, la API REST y
los dashboards directamente.

Te guía paso a paso a través de las 4 decisiones críticas para escalar: **People, Strategy, Execution y Cash**.

## Independencia metodológica

ESCALA es un producto independiente. No es un producto oficial ni está
afiliado, patrocinado, aprobado o respaldado por ninguna persona u organización
externa. Las metodologías, conceptos o materiales que decidas aportar no crean
una relación oficial ni autorizan su distribución.

## Para el dueño: instalación en 3 pasos

1. Abre la app Terminal (en Mac: Cmd + Espacio, escribe "Terminal").
2. Pega esta línea y presiona Enter:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/lunitomx/agente-de-escalamiento/main/instalar.sh | sh
   ```

3. Cuando diga "Listo", pega `cd ~/ESCALA && claude` y cuéntale a ESCALA qué te
   preocupa hoy.

No hay que elegir nada: el instalador prepara lo que falte (uv y su Python,
Claude Code), deja ESCALA en `~/ESCALA` y lo conecta con Claude junto con sus
especialistas internos. Para actualizar, pega otra vez la misma línea.
Si vas a invitar empresarios a probarlo, comparte la guía de
[Piloto privado](PILOTO-EMPRESARIOS.md).

## Instalación manual (equipo técnico)

Desde una copia del repositorio, instala ESCALA sólo en el agente que elijas:

```bash
./install.sh --platform claude
```

Para instalar la puerta conversacional en todos los agentes detectados usa
`./install.sh --all-platforms`. Si únicamente quieres el skill, sin runtime
Python standalone, agrega `--skills-only`. Abre el agente en esa carpeta.

## Requisitos

- Una Mac o Linux (en Windows, WSL2) y una cuenta de Claude para usar Claude
  Code. `instalar.sh` instala lo demás.
- Para la instalación manual: Python 3, Git y `uv`; `--skills-only` no requiere
  `uv`. Claude Code, Hermes Agent o Codex CLI instalado localmente.
- Acceso de lectura y escritura a la carpeta donde guardarás tu empresa.

## Modo sin agente de IA

Si prefieres no usar Claude, Hermes o Codex, ESCALA también funciona como
paquete Python y servidor web local:

```bash
# Perfil de empresa
.venv/bin/python -m coaching.welcome

# Diagnóstico
.venv/bin/python -m coaching.diagnose

# Servidor web con dashboards
.venv/bin/python -m escala_server
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
- Los reportes de bugs y mejoras se generan localmente cuando se los describes a ESCALA; se guardan en
  `~/.escala/feedback/outbox/`. No hay telemetría ni
  envío automático; si quieres compartir uno, copia el archivo manualmente a
  una carpeta sincronizada que tú controles.

## Un solo agente, muchas capacidades internas

La instalación distribuye una sola puerta pública: **ESCALA**. Háblale con tus
palabras: “no tengo cash”, “mi equipo no se hace responsable”, “necesito mi
plan de una página”, “¿cómo vamos?” o “quiero retomar lo anterior”. No necesitas conocer
comandos ni carpetas.

ESCALA consulta un catálogo canónico y carga internamente la capacidad que
corresponde: Cash, People, Strategy, Execution, diagnóstico, memoria,
dashboards, sesiones o reportes. Cada respuesta explica lo que entendió, la
evidencia o límite disponible y el siguiente paso.

Las instalaciones anteriores siguen teniendo aliases
temporales hasta 2027-01-01. Esos aliases redirigen al mismo contrato canónico;
no conservan una segunda implementación.

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
