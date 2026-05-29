# Epic Scope: E18 — Escala Server, Interactive Dashboards & Memory System

## Objective

Construir un sistema completo para Escala que incluya:
1. **Mini servidor HTTP local** que sirva los 22 dashboards con datos en vivo
2. **SQLite como capa de persistencia** central (reemplazando YAML plano)
3. **Memoria neurosimbólica y grafo de conocimiento** (como RaiSE)
4. **escala-inicia / escala-cierra** — inicio y cierre de sesión con contexto, detección de cambios y aprendizaje
5. **Dashboards interactivos** con sliders, controles y persistencia
6. **Navegación jerárquica** Home → Decisión → Herramienta → Dashboard

## Background

El proyecto ScaleUp tiene 22 dashboards HTML estáticos (E14-E17) y ~30 skills de coaching. Hoy los skills guían al usuario a ingresar datos en worksheets markdown, pero no hay conexión entre los datos que el usuario ingresa y los dashboards. Tampoco hay memoria entre sesiones — cada sesión empieza en blanco.

La inspiración es RaiSE: un sistema con memoria persistente, grafo de conocimiento, detección de cambios entre sesiones, y un ciclo claro de inicio/cierre que captura aprendizaje.

## Architecture

```
.escala/
├── escala.db                          ← SQLite central
│   ├── companies                      ← perfil de empresa
│   ├── worksheets                     ← datos de cada herramienta (JSON column)
│   ├── sessions                       ← historial de sesiones
│   ├── changes_log                    ← auditoría de cambios (con diff)
│   ├── memory_facts                   ← hechos neurosimbólicos (como fact_store)
│   ├── entities                       ← entidades del grafo
│   └── relationships                  ← relaciones entre entidades
├── agent/
│   └── memory/
│       └── company-profile.yaml       ← perfil rápido (para skills)
└── my-company/
    ├── sessions/                      ← logs markdown de sesiones
    └── exports/                       ← planes exportados
```

### Flujo de sesión

```
escala-inicia
  ├── Carga perfil de empresa desde SQLite
  ├── Inyecta memoria de sesiones previas
  ├── Carga grafo de conocimiento
  ├── Detecta cambios desde último cierre
  ├── Verifica salud del server
  └── Presenta foco de sesión

        │
        ▼
  [Trabajo del día: skills, dashboards, datos]
        │
        ▼

escala-cierra
  ├── Captura aprendizaje del día
  ├── Detecta cambios en datos (diff worksheets)
  ├── Extrae nuevos hechos → memory_facts
  ├── Actualiza grafo de conocimiento
  ├── Persiste cambios a SQLite
  ├── Escribe log de sesión
  └── Genera resumen de cambios
```

## In Scope

### S18.1 — Server Core (refinado)
- Servidor HTTP minimalista extendiendo http.server
- Sistema de rutas API: GET/POST/PATCH para cada herramienta
- Capa de persistencia: SQLite con DAO layer Python
- Servir archivos estáticos (HTML, CSS, JS, vendor)
- CORS para desarrollo local
- Endpoints API base: /api/companies, /api/worksheets, /api/sessions
- Comando `escala-server start/stop/status`

### S18.2 — Navigation & Home
- Página principal: 4 tarjetas clickeables (Cash, Strategy, People, Execution)
- Cada tarjeta muestra score actual, última sesión, cambios recientes
- Sub-navegación: al hacer clic en una decisión, muestra lista de herramientas
- Breadcrumbs: Home > Cash > Power of One
- Indicador visual de datos modificados vs guardados
- Diseño responsive con dashboard-base.css

### S18.3 — Power of One Interactive (PILOT)
- HTML existente + sliders (range input) para 7 palancas
- Recalcular impacto en tiempo real
- Botón "Guardar" → POST /api/worksheets/cash/power-of-one
- Endpoint GET/POST con persistencia a SQLite
- Datos con marca de "modificado" / "guardado"
- NOTA: Los demás dashboards (S18.4-S18.7) heredan este patrón

### S18.4 — Cash Suite Interactive
- CASh Board: scoreboard editable
- Fundability: editores de métricas
- CCC: sliders para días de cada ciclo
- Recurring Revenue: editores MRR/ARR con proyección

### S18.5 — Strategy Suite Interactive
- BMC Board: canvas de 9 bloques editable
- Core Customer: tarjetas editables
- Brand Promises: medidores ajustables
- Diff Activities: matriz competitiva editable
- Sandbox: mapa configurable

### S18.6 — People Suite Interactive
- Core Values: tarjetas editables
- FACe: matriz editable
- Team Growth: radar chart editable
- DISC: composición editable
- Love/Loathe: balance board editable
- Hiring Pipeline: proceso de 7 pasos editable

### S18.7 — Execution Suite Interactive
- Rockefeller Habits: scoreboard editable
- WWW: task tracker interactivo
- Priorities: tablero editable
- Balanced KPIs: traffic lights editables
- Meeting Rhythms: calendario configurable
- Influencers: board editable
- Vision Summary: panel unificado

### S18.8 — SQLite Database Layer & Schema
- Esquema completo de base de datos
- Tablas: companies, worksheets, sessions, changes_log, memory_facts, entities, relationships
- DAO layer Python (repositorios por dominio)
- Migración desde YAML existente a SQLite
- Change tracking automático (versión de datos por sesión)
- Funciones de diff (qué cambió entre dos versiones)

### S18.9 — Memoria Neurosimbólica & Grafo de Conocimiento
- Sistema de hechos (facts) con: contenido, categoría, tags, trust_score, source, timestamp
- Grafo entidad-relación (entities → relationships)
- Entity resolution básica (misma entidad con diferentes nombres)
- Búsqueda semántica sobre hechos
- Inyección de contexto: al iniciar sesión, los hechos relevantes se cargan
- Persistencia a SQLite con respaldo JSON

### S18.10 — escala-inicia (Session Start Orchestrator)
- Comando: `escala-inicia` (o integrado en skill)
- Carga perfil de empresa desde SQLite
- Inyecta memoria de sesiones previas (últimas 3)
- Carga grafo de conocimiento: hechos relevantes
- Detecta cambios desde último cierre (diff en worksheets)
- Verifica salud del server (¿escala-server corriendo?)
- Muestra: "Bienvenido {empresa}. Última sesión: {fecha}. {N} cambios detectados."
- Pregunta: "¿En qué trabajamos hoy?"
- Adapta nivel Shu/Ha/Ri según historial

### S18.11 — escala-cierra (Session Close with Learning)
- Comando: `escala-cierra`
- Captura aprendizaje del día: "¿Qué aprendiste? ¿Qué decidiste?"
- Detecta cambios en datos: compara worksheets antes/después de la sesión
- Extrae nuevos hechos de los cambios realizados
- Actualiza grafo de conocimiento con nuevos facts
- Actualiza entidades y relaciones
- Persiste sesión en SQLite
- Escribe log markdown en .escala/my-company/sessions/
- Genera resumen: "Sesión {fecha} — {duración}. {N} cambios en datos. {N} nuevos hechos."

### S18.12 — Installation & Server Lifecycle
- Integrar con install.sh existente
- `escala-server` CLI completo: start, stop, status, migrate (SQLite)
- `escala-inicia` y `escala-cierra` como scripts CLI o skills
- Migración de datos existentes (YAML → SQLite)
- Health check endpoint
- Documentación completa

## Out of Scope
- Autenticación multi-usuario
- Despliegue cloud
- Integración con CRMs externos
- Exportación a PDF
- Multi-idioma
- App mobile nativa

## Dependencies
- E14-E17 dashboards (HTML, CSS framework, Chart.js)
- Escala skills existentes (escala-cash-power1, etc.)
- Python 3.8+ con sqlite3 (built-in)
- RaiSE como inspiración arquitectónica (no dependencia)

## Design Decisions

- **DD1:** SQLite como base única — sin servidor externo
- **DD2:** Server con http.server nativo — sin Flask/FastAPI
- **DD3:** DAO layer separado del server (arquitectura limpia)
- **DD4:** Change tracking vía versioning de worksheets por sesión
- **DD5:** Memoria neurosimbólica inspirada en RaiSE fact_store
- **DD6:** Grafo entidad-relación en SQLite (tablas separadas)
- **DD7:** S18.3 Power of One es el piloto — valida patrón
- **DD8:** HTMLs funcionan sin server (modo degradado)
- **DD9:** escala-inicia/cierra funcionan sin server (solo SQLite)

## Stories

| ID | Name | Dependencies |
|----|------|-------------|
| S18.1 | Server Core (HTTP + routing + static) | Ninguna |
| S18.2 | Navigation & Home | S18.1 |
| S18.3 | Power of One Interactive (PILOT) | S18.1 |
| S18.4 | Cash Suite Interactive | S18.1, S18.3 |
| S18.5 | Strategy Suite Interactive | S18.1 |
| S18.6 | People Suite Interactive | S18.1 |
| S18.7 | Execution Suite Interactive | S18.1 |
| S18.8 | SQLite Database Layer & Schema | S18.1 |
| S18.9 | Memoria Neurosimbólica & Grafo | S18.8 |
| S18.10 | escala-inicia (Session Start) | S18.8, S18.9 |
| S18.11 | escala-cierra (Session Close) | S18.8, S18.9 |
| S18.12 | Installation & Lifecycle | S18.1-S18.11 |

## Implementation Plan

> Added by rai-epic-plan — 2026-05-29

### Story Sequence

| Order | Story | Size | Dependencies | Milestone | Rationale |
|:-----:|-------|:----:|--------------|-----------|-----------|
| 1 | S18.1 — Server Core | XL | Ninguna | M1 | Walking skeleton: primero el esqueleto — HTTP, routing, estáticos, CLI. Todo depende de esto. |
| 2 | S18.3 — Power of One PILOT | L | S18.1 | M1 | Valida el patrón completo: UI ↔ server ↔ persistencia. Sin S18.8 aún — guardado simple en servidor. |
| 3 | S18.8 — SQLite Layer | XL | S18.1 | M1 | Esquema completo, DAO layer, migración YAML→SQLite. Reemplaza persistencia temporal de S18.3. |
| 4 | S18.2 — Navigation & Home | M | S18.1 | M1 | Home con 4 tarjetas, breadcrumbs. Necesario para navegar a dashboards. |
| 5 | S18.5 — Strategy Suite | M | S18.1 | M2 | Core MVP — paralelizable con S18.6, S18.7 |
| 6 | S18.6 — People Suite | M | S18.1 | M2 | Core MVP — paralelizable con S18.5, S18.7 |
| 7 | S18.7 — Execution Suite | M | S18.1 | M2 | Core MVP — paralelizable con S18.5, S18.6 |
| 8 | S18.4 — Cash Suite | M | S18.1, S18.3 | M2 | Hereda patrón del piloto S18.3. Va después de validar el patrón. |
| 9 | S18.9 — Memory & Graph | L | S18.8 | M3 | Memoria neurosimbólica + grafo. Necesita SQLite primero. |
| 10 | S18.10 — escala-inicia | M | S18.8, S18.9 | M3 | Paralelizable con S18.11 |
| 11 | S18.11 — escala-cierra | M | S18.8, S18.9 | M3 | Paralelizable con S18.10 |
| 12 | S18.12 — Installation & Lifecycle | M | S18.1-S18.11 | M4 | Capstone: migration, docs, health checks. Todo lo demás debe existir. |

### Milestones

| Milestone | Stories | Success Criteria |
|-----------|---------|------------------|
| **M1: Walking Skeleton** | S18.1, S18.3, S18.8, S18.2 | `escala-server start` sirve HTMLs. Power of One con sliders que guardan/cargan datos. SQLite con todas las tablas. Navegación Home funciona. |
| **M2: Core MVP** | +S18.5, S18.6, S18.7, S18.4 | Los 22 dashboards son interactivos con datos desde SQLite. Todos los patrones de edición/persistencia funcionan. |
| **M3: Memory & Sessions** | +S18.9, S18.10, S18.11 | `escala-inicia` carga contexto con memoria de sesiones previas. `escala-cierra` captura aprendizaje, detecta cambios, actualiza grafo. |
| **M4: Epic Complete** | +S18.12 | Instalación completa con `install.sh`. Migración YAML→SQLite. Documentación. Health check endpoint. |

### Parallel Work Streams

```
Time →
Stream 1 (Foundation):  S18.1 ───► S18.8 ─────────────► S18.9 ──► S18.10/S18.11 ──► S18.12
                                         ↓
Stream 2 (Dashboards):  S18.3 ──► S18.2 ──► S18.5/S18.6/S18.7 ──► S18.4
```

**Merge points:**
- S18.1 → split: Stream 1 (database) + Stream 2 (dashboards)
- S18.8/S18.2 → Stream 2 adopta persistencia SQLite
- S18.9 → Stream 1 continua a sesiones; Stream 2 converge en M2

### Progress Tracking

| Story | Size | Status | Actual | Velocity | Notes |
|-------|:----:|:------:|:------:|:--------:|-------|
| S18.1 — Server Core | XL | Done | — | — | http.server, routing, static, CLI |
| S18.2 — Navigation & Home | M | Pending | — | — | 4 tarjetas, breadcrumbs, responsive |
| S18.3 — Power of One PILOT | L | Pending | — | — | Sliders, recálculo, guardado |
| S18.4 — Cash Suite | M | Pending | — | — | Hereda patrón S18.3 |
| S18.5 — Strategy Suite | M | Pending | — | — | BMC, Core Customer, Brand Promises |
| S18.6 — People Suite | M | Pending | — | — | Values, FACe, Team, DISC |
| S18.7 — Execution Suite | M | Pending | — | — | RH Habits, WWW, Priorities, KPIs |
| S18.8 — SQLite Layer | XL | Pending | — | — | Schema, DAO, migración YAML |
| S18.9 — Memory & Graph | L | Pending | — | — | Facts, entities, semantic search |
| S18.10 — escala-inicia | M | Pending | — | — | Session start orchestrator |
| S18.11 — escala-cierra | M | Pending | — | — | Session close with learning |
| S18.12 — Install & Lifecycle | M | Pending | — | — | CLI, migration, docs |

### Sequencing Risks

| Risk | L/I | Mitigation |
|------|:---:|------------|
| S18.8 (SQLite) como XL + S18.9 (Memory) como L crean cuello de botella en Stream 1 | H/M | S18.8 y S18.9 se dividen en sub-stories si es necesario. Stream 2 (dashboards) avanza en paralelo mientras. |
| S18.3 no tiene S18.8 como dependencia — guardado inicial sin SQLite puede requerir refactor | M/L | Diseñar interfaz de persistencia abstracta desde S18.1 para que S18.8 la implemente después. |
| 22 dashboards existentes (E14-E17) pueden tener dependencias HTML/CSS no documentadas | M/M | Auditoría rápida de dashboards existentes antes de S18.3. |

## Status: In Progress

## Done Criteria
- [ ] `escala.db` con todas las tablas
- [ ] `escala-server start` sirve 22 dashboards con datos reales desde SQLite
- [ ] Power of One con sliders que persisten a SQLite
- [ ] Navegación Home → Decisión → Herramienta → Dashboard
- [ ] `escala-inicia` carga contexto, memoria, grafo y detecta cambios
- [ ] `escala-cierra` captura aprendizaje, detecta cambios, actualiza grafo
- [ ] Cada modificación se registra con timestamp, sesión y diff
- [ ] Migración YAML → SQLite funcional
- [ ] Documentación completa
