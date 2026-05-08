# E10: ScaleUp Cross-Platform Distribution

## Objective

Construir los core Python coaching engines faltantes y distribuir el sistema ScaleUp completo (skills + knowledge + coaching engine + validators) como un bundle portable que funcione en Claude Code global, Hermes Agent y Codex — sin depender del repo de desarrollo.

## Value

Hoy ScaleUp solo funciona dentro de este repo. Al distribuirlo cross-platform:
- Eduardo puede usar ScaleUp en **cualquier proyecto** sin clonar el repo
- Los mismos skills corren en **Hermes** (agente persistente) y **Codex** (coding tasks)
- El coaching engine en Python garantiza **consistencia** entre plataformas
- Un solo `install` actualiza las 3 plataformas

## Current State (Gemba)

| Componente | Estado | Ubicación |
|-----------|--------|-----------|
| SKILL.md (39 skills) | Completos | `.claude/skills/scaleup-*` |
| Knowledge (90+ YAML) | Completo | `.scaleup/knowledge/` |
| Validators (11 Python) | Completos | `.scaleup/agent/validators/` |
| Agent Identity | Completo | `.scaleup/agent/identity/` |
| Sub-agents (4 markdown) | Completos | `.scaleup/agent/sub-agents/` |
| Coaching Engine: summary | Completo (engine+formatter+I/O) | `.scaleup/coaching/summary/` |
| Coaching Engine: welcome | **No existe** | — |
| Coaching Engine: diagnose | **No existe** | — |
| Coaching Engine: worksheet | **No existe** | — |
| Coaching Engine: progress | **No existe** | — |
| Coaching Engine: level | **No existe** | — |
| Coaching Engine: router | **No existe** | — |

12 skills ya invocan `python3 -m coaching.*` o referencian validators — pero solo `summary` tiene engine real.

## In Scope (MUST)

1. **Coaching engines** para welcome, diagnose, worksheet, progress, level, router — siguiendo el patrón engine+formatter+I/O de `summary/`
2. **Installer CLI** que copie el bundle completo a:
   - `~/.claude/skills/scaleup-*/` (Claude Code global)
   - `~/.hermes/skills/scaleup-*/` (Hermes Agent)
3. **Adapter layer** para Hermes: mapeo de tool calls (Bash→terminal, Read→process)
4. **Knowledge bundle**: los 90+ YAML portables sin dependencia de path absoluto
5. **Tests** para cada engine module

## In Scope (SHOULD)

- Versioning del bundle (para saber qué versión está instalada)
- `uninstall` command
- Codex awareness dentro de Hermes (skill que delegue coding tasks a Codex)

## Out of Scope

- **Web UI** para ScaleUp — otro épico
- **API REST** del coaching engine — otro épico
- **Nuevos skills** más allá de los 39 existentes — se agregan después
- **Hermes server setup** — el usuario ya tiene Hermes corriendo
- **Cambios al contenido de knowledge** — solo packaging

## Stories

### S10.1: Discovery & Skill Audit (XS)
Auditar los 39 skills y clasificarlos en 3 categorías:
- **Engine-backed**: necesitan core Python (welcome, diagnose, worksheet, progress, level, router)
- **Validator-only**: usan validators pero no necesitan engine propio
- **Pure SKILL.md**: instrucciones puras sin Python

Mapear diferencias de tool calls entre Claude Code y Hermes. Producir matriz de compatibilidad.

**Depends on:** nada

### S10.2: Welcome Engine (S)
Crear `coaching/welcome/` siguiendo el patrón de `summary/`:
- `engine.py` — lógica pura: validar datos de empresa, detectar growth stage
- `formatter.py` — render del profile YAML
- `__init__.py` — I/O: leer/escribir `my-company/profile.md`
- Tests

**Depends on:** S10.1

### S10.3: Diagnose Engine (M)
Crear `coaching/diagnose/`:
- `engine.py` — scoring de las 4 decisiones, cálculo de focus
- `formatter.py` — render del diagnóstico con scores y recomendaciones
- `__init__.py` — I/O: leer profile, escribir scores
- Tests

**Depends on:** S10.2

### S10.4: Worksheet Engine (M)
Crear `coaching/worksheet/`:
- `engine.py` — cargar worksheet desde ontología, guiar paso a paso
- `formatter.py` — render de worksheet con campos y prompts
- `__init__.py` — I/O: leer ontología YAML, escribir respuestas
- Tests

**Depends on:** S10.1

### S10.5: Progress & Level Engines (S)
Crear `coaching/progress/` y `coaching/level/`:
- Progress: calcular scores, worksheets completados, sugerir siguiente acción
- Level: detectar Shu/Ha/Ri basado en scores y actividad
- Tests para ambos

**Depends on:** S10.3

### S10.6: Router Engine (S)
Crear `coaching/router/`:
- `engine.py` — routing determinístico: score más bajo → sub-agente correspondiente
- `__init__.py` — I/O: leer profile scores, retornar decisión de routing
- Tests

**Depends on:** S10.5

### S10.7: Claude Code Global Installer (M)
Script `install.sh` que:
- Copie los 39 SKILL.md a `~/.claude/skills/scaleup-*/`
- Copie knowledge a `~/.claude/knowledge/scaleup/` (o path configurable)
- Copie coaching engine a un path accesible por Python
- Actualice CLAUDE.md global con las instrucciones de ScaleUp
- Soporte `--update` para actualizar sin perder datos de usuario

**Depends on:** S10.6

### S10.8: Hermes Adapter Layer (M)
Crear adapter SKILL.md para cada skill que traduzca:
- `Bash` → `terminal()`
- `Read` → `process()` / `terminal("cat ...")`
- `Edit` → `terminal("sed ...")` o write pattern de Hermes
- Instalar en `~/.hermes/skills/scaleup-*/`
- Incluir knowledge y coaching engine

**Depends on:** S10.7

### S10.9: Unified Installer & Versioning (S)
Script `scaleup-install` que:
- Detecte plataformas disponibles (Claude Code, Hermes)
- Instale/actualice en todas las detectadas
- Escriba `.scaleup-version` en cada destino
- Soporte `scaleup-install --status` para ver qué está instalado dónde

**Depends on:** S10.7, S10.8

## Done Criteria

- [ ] Los 6 coaching engines construidos y testeados (welcome, diagnose, worksheet, progress, level, router)
- [ ] `scaleup-install` instala exitosamente en Claude Code global
- [ ] `scaleup-install` instala exitosamente en Hermes
- [ ] Ejecutar `/scaleup-welcome` desde un proyecto vacío (fuera de este repo) funciona
- [ ] Ejecutar `/scaleup-diagnose` en Hermes produce el mismo output que en Claude Code
- [ ] Retrospectiva completada

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Hermes tool call mapping no es 1:1 | Media | Alta | S10.1 discovery mapea diferencias antes de construir |
| Knowledge paths rotos al mover de repo | Alta | Media | Usar paths relativos al skill, no absolutos |
| Python modules no accesibles desde global install | Media | Alta | Usar `PYTHONPATH` o instalar como package |

## Parking Lot

- Dashboard web para ScaleUp
- API REST del coaching engine
- Publicar skills como "tap" de Hermes (GitHub repo público)
- ScaleUp en Claude Desktop (MCP server)

---

## Implementation Plan

### Sequencing Strategy: Walking Skeleton + Risk-First

El riesgo principal es que el patrón engine+formatter+I/O no escale bien a los otros módulos. Por eso:
1. **S10.1** primero — discovery elimina incertidumbre sobre Hermes y clasifica skills
2. **S10.2** (Welcome) como walking skeleton — prueba el patrón en el engine más simple
3. Una vez probado el patrón, los engines restantes se construyen con confianza
4. La distribución va al final porque depende de que todos los engines existan

### Story Sequence

| # | Story | Size | Depends On | Enables | Rationale |
|---|-------|------|-----------|---------|-----------|
| 1 | S10.1: Discovery & Skill Audit | XS | — | Todo lo demás | Elimina incertidumbre: mapeo Hermes, clasificación real |
| 2 | S10.2: Welcome Engine | S | S10.1 | S10.3 | Walking skeleton: prueba el patrón PAT-L-24 en el engine más simple |
| 3 | S10.4: Worksheet Engine | M | S10.1 | — | **Paralelo con S10.3** — independiente, toca ontología no profile |
| 4 | S10.3: Diagnose Engine | M | S10.2 | S10.5 | Necesita el patrón validado de Welcome. Usa validators/diagnose.py existente |
| 5 | S10.5: Progress + Level | S | S10.3 | S10.6 | Dos engines pequeños, ambos leen scores de diagnose |
| 6 | S10.6: Router Engine | S | S10.5 | S10.7 | Último engine — routing determinístico basado en scores |
| 7 | S10.7: Claude Code Global Installer | M | S10.6 | S10.8, S10.9 | Primera plataforma de distribución — la que Eduardo usa a diario |
| 8 | S10.8: Hermes Adapter Layer | M | S10.7 | S10.9 | Adapta tool calls, usa installer como base |
| 9 | S10.9: Unified Installer & Versioning | S | S10.7, S10.8 | — | Cierra el loop: un comando para todo |

### Parallel Work Streams

```
Stream A (Profile):  S10.1 → S10.2 → S10.3 → S10.5 → S10.6
Stream B (Ontology): S10.1 → S10.4
                                        ↓ (merge after S10.6)
Stream C (Distribution):          S10.7 → S10.8 → S10.9
```

**S10.3 y S10.4 pueden ejecutarse en paralelo** — tocan módulos distintos (profile vs ontología). Stream B es independiente hasta que se necesite para el installer.

### Critical Path

```
S10.1 → S10.2 → S10.3 → S10.5 → S10.6 → S10.7 → S10.8 → S10.9
```

S10.4 (Worksheet) está fuera del critical path — puede retrasarse sin bloquear la distribución.

## Milestones

### M1: Walking Skeleton (S10.1 + S10.2)
**Stories:** S10.1, S10.2
**Success criteria:**
- [ ] Matriz de compatibilidad Claude↔Hermes documentada
- [ ] `coaching/welcome/` construido con engine+formatter+I/O
- [ ] `python3 -m coaching.welcome --context '{...}'` produce output correcto
- [ ] Tests pasan
- [ ] Patrón PAT-L-24 validado para replicar en otros engines

**Demo:** Ejecutar welcome engine desde CLI y verificar que genera profile correcto.

### M2: Engines Complete (S10.3 + S10.4 + S10.5 + S10.6)
**Stories:** S10.3, S10.4, S10.5, S10.6
**Success criteria:**
- [ ] Los 6 coaching engines construidos (welcome, diagnose, worksheet, progress, level, router)
- [ ] Todos los tests pasan
- [ ] `python3 -m coaching.router --context '{...}'` retorna sub-agente correcto
- [ ] Engines invocan validators existentes (no duplican validación)

**Demo:** Flujo completo CLI: welcome → diagnose → router decide sub-agente → progress muestra dashboard.

### M3: E2E Cross-Platform (S10.7 + S10.8 + S10.9)
**Stories:** S10.7, S10.8, S10.9
**Success criteria:**
- [ ] `scaleup-install` instala en Claude Code global exitosamente
- [ ] `scaleup-install` instala en Hermes exitosamente
- [ ] `/scaleup-welcome` funciona desde un proyecto vacío (fuera de este repo)
- [ ] `/scaleup-diagnose` en Hermes produce output equivalente
- [ ] `scaleup-install --status` muestra versión instalada en cada plataforma

**Demo:** Abrir un proyecto nuevo, ejecutar `/scaleup-welcome`, completar onboarding, ejecutar `/scaleup-diagnose`.

### M4: Epic Complete
- [ ] Done criteria del épico cumplidos
- [ ] Retrospectiva completada (BASE-009)
- [ ] Parking lot actualizado

## Sequencing Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| El patrón de summary/ no escala a engines más complejos (diagnose tiene scoring logic) | M1 se invalida, hay que rediseñar | S10.2 es el skeleton — si falla, se adapta el patrón antes de construir los demás |
| Hermes tool call mapping tiene edge cases no cubiertos en S10.1 | S10.8 requiere más trabajo del esperado | S10.1 debe incluir un smoke test: portar 1 skill a Hermes y verificar E2E |
| PYTHONPATH approach no funciona en contextos restringidos (sandboxed Claude Code) | Engines no ejecutan desde global install | Fallback: inline el engine como script en cada SKILL.md (pierde DRY pero funciona) |

## Progress Tracking

| Story | Status | Started | Completed | Notes |
|-------|--------|---------|-----------|-------|
| S10.1: Discovery | pending | — | — | |
| S10.2: Welcome Engine | pending | — | — | |
| S10.3: Diagnose Engine | pending | — | — | |
| S10.4: Worksheet Engine | pending | — | — | Paralelo con S10.3 |
| S10.5: Progress + Level | pending | — | — | |
| S10.6: Router Engine | pending | — | — | |
| S10.7: Claude Global Installer | pending | — | — | |
| S10.8: Hermes Adapter | pending | — | — | |
| S10.9: Unified Installer | pending | — | — | |

| Milestone | Target | Status |
|-----------|--------|--------|
| M1: Walking Skeleton | — | pending |
| M2: Engines Complete | — | pending |
| M3: E2E Cross-Platform | — | pending |
| M4: Epic Complete | — | pending |
