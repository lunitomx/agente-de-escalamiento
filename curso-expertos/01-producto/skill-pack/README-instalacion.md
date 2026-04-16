# CUMBRE — Skill Pack v1

> Consejo Directivo Virtual de 4 voces con Protocolo de Honestidad y regla de NIEBLA 🌫️
> Funciona en **Claude Cowork** (macOS/Windows) y **Claude Code** (CLI).

---

## Qué se instala

12 skills que quedan disponibles como slash commands y se activan automáticamente según la intención del empresario:

| Skill | Invocas con | Para qué |
|-------|-------------|----------|
| Onboarding | `/cumbre-onboard` | Primera vez — conoce tu negocio (7 dimensiones) |
| Sesión abierta | `/cumbre` | Abre la Mesa con contexto cargado |
| Decidir | `/cumbre-decidir` | Elegir entre opciones — 4 voces deliberan |
| Rebotar | `/cumbre-rebotar` | Pensar en voz alta, sin decidir |
| Revisar | `/cumbre-revisar` | Evaluar decisión pasada vs. realidad |
| Dilema | `/cumbre-dilema` | Dos caminos, ambos duelen |
| Research | `/cumbre-research` | Investigar sector, competencia, benchmarks |
| Bitácora | `/cumbre-bitacora` | Registrar decisión tomada |
| Solo Veterano | `/cumbre-veterano` | Solo la voz de ciclos y patrones |
| Solo Retador | `/cumbre-retador` | Solo la voz que cuestiona |
| Solo Conector | `/cumbre-conector` | Solo la voz que une puntos |
| Solo Financiero | `/cumbre-financiero` | Solo la voz de los números |

---

## Estructura de cada skill

Cada skill es una **carpeta** con un archivo `SKILL.md` dentro:

```
skill-pack/
├── cumbre-onboard/
│   └── SKILL.md
├── cumbre-decidir/
│   └── SKILL.md
├── cumbre-research/
│   └── SKILL.md
... (12 carpetas)
```

El `SKILL.md` lleva frontmatter YAML con `name` y `description` — así Claude sabe cuándo activar cada skill.

---

## 🚀 Cómo instalar — 3 rutas según quién eres

### ⭐ Ruta 1 — Cowork UI con ZIPs (RECOMENDADA para empresarios)

Esta es la única ruta que funciona **sin tocar terminal ni Finder**. Ideal para usar en vivo durante la ponencia.

> ⚠️ **Importante:** Claude Cowork corre en sandbox y NO puede escribir a `~/.claude/skills/` desde el chat. Por eso pedirle al agente "instala estos skills" no funciona. La UI sí.

1. Descarga la carpeta `zips/` que viene con este pack. Son 12 ZIPs individuales + uno maestro (`cumbre-pack-completo.zip`).
2. Abre **Claude Cowork** → sidebar izquierdo → **Customize** → pestaña **Skills** → botón **+**.
3. Sube los ZIPs uno por uno (o arrastra los 12 a la vez si Cowork lo permite).
4. Cada skill aparece en la lista con un toggle on/off — déjalos todos encendidos.
5. ✅ Listo. Puedes escribir `/cumbre-onboard` en cualquier sesión.

### Ruta 2 — Finder manual (si no quieres UI pero tampoco terminal)

Los skills del repositorio están en carpetas sueltas. Puedes arrastrarlas desde Finder:

1. Abre dos ventanas de Finder.
2. En una, abre la carpeta `skill-pack/` de este proyecto.
3. En la otra, ve a: **Ir → Ir a la carpeta...** → escribe `~/.claude/skills/` → Enter. (Si no existe, créala primero.)
4. Selecciona las **12 carpetas** (de `cumbre` hasta `cumbre-veterano`, sin las ZIPs ni el README) y arrástralas a `~/.claude/skills/`.
5. Abre/reinicia Cowork o Claude Code. Los skills se detectan en la siguiente sesión.

### Ruta 3 — Terminal (para usuarios técnicos)

```bash
mkdir -p ~/.claude/skills
cp -R cumbre-* ~/.claude/skills/
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.claude\skills"
Copy-Item -Recurse cumbre-* "$HOME\.claude\skills\"
```

> ⚠️ Error común: **no anides** la carpeta. Debe quedar `~/.claude/skills/cumbre-onboard/SKILL.md`, NO `~/.claude/skills/cumbre-onboard/otra-carpeta/SKILL.md`.

---

## 📁 Crea tu carpeta de trabajo de CUMBRE

Los skills son el cerebro. Pero la memoria vive en tu carpeta de trabajo.

```bash
mkdir -p ~/cumbre
cd ~/cumbre
touch mi-empresa.md mercado.md decisiones.md dilemas-abiertos.md valores.md
```

Abre Claude Cowork (o Claude Code) **desde esa carpeta**. Los skills leen y escriben estos 5 archivos automáticamente.

---

## Primer uso — 30 segundos

1. Abre Claude Cowork apuntando a la carpeta `~/cumbre/` (o el path que hayas elegido).
2. Escribe: `/cumbre-onboard`
3. CUMBRE te hace 7 preguntas en conversación natural.
4. Al terminar, escribe: `/cumbre-research` (sale a internet a investigar tu sector).
5. Ya puedes usar `/cumbre-decidir`, `/cumbre-rebotar`, etc. para cualquier decisión.

**Siguientes sesiones:** abres Cowork en la carpeta y escribes `/cumbre`. Te recibe con contexto cargado.

---

## Estructura de archivos que CUMBRE va llenando

```
~/cumbre/
├── mi-empresa.md          ← 7 dimensiones del onboarding
├── mercado.md             ← research del sector (con fuentes)
├── decisiones.md          ← bitácora de decisiones
├── dilemas-abiertos.md    ← lo que está pendiente
└── valores.md             ← lo no negociable
```

CUMBRE lee estos archivos antes de cada sesión y los actualiza al cerrar.

---

## 🌫️ La regla de oro — NIEBLA

CUMBRE nunca asume ni inventa. Si extrapola un dato, lo marca:

```
🌫️ NIEBLA: Estoy asumiendo que tu margen ronda 35-45%.
Si tu realidad es distinta, corrígeme antes de seguir.
```

Así sabes qué está basado en hechos tuyos y qué en suposición.
**La niebla se disipa con un dato real.**

---

## ⚠️ El Protocolo de Honestidad

Cuando detecta que el problema rebasa a la IA (conflicto entre socios, crisis fiscal, decisión legal crítica, dueño agotado), CUMBRE **detiene el análisis** y sugiere acompañamiento humano:

> → **Expertos Certificados** — https://expertoscertificados.com/
> → **Karla Jaramillo** — 442 331 7171

No es publicidad. Es reconocer el límite.

---

## Requisitos

- **Claude Cowork** (cualquier plan pago de Anthropic, GA desde abril 2026), o
- **Claude Code** (CLI)

Los skills **no funcionan en Claude.ai web sin Cowork**. Para ese caso usa el archivo `../mega-prompt.md` (Nivel 1).

---

## Soporte y créditos

- Creador: **Eduardo Muñoz Luna** — fundador de MHServices, partner de Expertos Certificados
- Inspirado en principios probados de gestión empresarial. No reproduce metodologías con marca registrada.

*Un consejo honesto también sabe callarse. Y sabe cuándo dudar.*
